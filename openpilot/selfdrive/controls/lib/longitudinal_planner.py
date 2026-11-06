#!/usr/bin/env python3
import math
import numpy as np

import openpilot.cereal.messaging as messaging
from openpilot.cereal import log
from opendbc.car.interfaces import ACCEL_MIN, ACCEL_MAX
from openpilot.common.constants import CV
from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.common.realtime import DT_MDL
from openpilot.selfdrive.modeld.constants import ModelConstants
from openpilot.selfdrive.controls.lib.longcontrol import LongCtrlState
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import LongitudinalMpc, LongitudinalPlanSource
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import T_IDXS as T_IDXS_MPC
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import MPC_SOURCES
from openpilot.selfdrive.controls.lib.drive_helpers import CONTROL_N, get_accel_from_plan, get_lead_accel_min, get_stop_speed, should_stop
from openpilot.selfdrive.car.cruise import V_CRUISE_MAX, V_CRUISE_UNSET
from openpilot.common.swaglog import cloudlog

from openpilot.sunnypilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlannerSP

A_CRUISE_MAX_VALS = [1.6, 1.2, 0.8, 0.6]
# yeet-angle-tune: aggressive pulls away harder behind a lead that speeds up.
# Within ACCEL_MAX (2.0, ISO 15622 and the Rivian panda limit).
A_CRUISE_MAX_VALS_AGGRESSIVE = [2.0, 1.8, 1.4, 1.1]
A_CRUISE_MAX_BP = [0., 10.0, 25., 40.]
J_CRUISE_VALS = [1.6, 1.2, 0.8, 0.6]
J_CRUISE_VALS_AGGRESSIVE = [2.0, 1.8, 1.4, 1.1]
A_CRUISE_MIN = -1.2
CONTROL_N_T_IDX = ModelConstants.T_IDXS[:CONTROL_N]
ALLOW_THROTTLE_THRESHOLD = 0.4
MIN_ALLOW_THROTTLE_SPEED = 2.5

# Hard braking for a lead past ACCEL_MIN (yeet-angle-brake, see MPC_TUNING.md): the stock MPC (ACCEL_MIN) always runs and
# is used unless its plan is cap-limited, at ACCEL_MIN within the first HARD_BRAKE_T s or running into a present lead.
# Then the hard MPC (lead_accel_min) is used until the stock plan is not cap-limited for HARD_BRAKE_EXIT_T s and the planner
# output is back above ACCEL_MIN.
HARD_BRAKE_T = 1.0
HARD_BRAKE_CAP_MARGIN = 0.05
HARD_BRAKE_EXIT_T = 1.0

# Lookup table for turns
_A_TOTAL_MAX_V = [1.7, 3.2]
_A_TOTAL_MAX_BP = [20., 40.]

def get_max_accel(v_ego, personality=log.LongitudinalPersonality.standard):
  if personality == log.LongitudinalPersonality.aggressive:
    return np.interp(v_ego, A_CRUISE_MAX_BP, A_CRUISE_MAX_VALS_AGGRESSIVE)
  return np.interp(v_ego, A_CRUISE_MAX_BP, A_CRUISE_MAX_VALS)

def get_cruise_jerk(v_ego, personality=log.LongitudinalPersonality.standard):
  if personality == log.LongitudinalPersonality.aggressive:
    return np.interp(v_ego, A_CRUISE_MAX_BP, J_CRUISE_VALS_AGGRESSIVE)
  return np.interp(v_ego, A_CRUISE_MAX_BP, J_CRUISE_VALS)

def get_coast_accel(pitch):
  return np.sin(pitch) * -5.65 - 0.3  # fitted from data using xx/projects/allow_throttle/compute_coast_accel.py

def get_cruise_accel(e2e, v_cruise, v_ego, a_cruise_prev, angle_steers, CP, dt, accel_coast, allow_throttle,
                     personality=log.LongitudinalPersonality.standard):
  max_accel = ACCEL_MAX if e2e else get_max_accel(v_ego, personality)

  if not e2e:
    a_total_max = np.interp(v_ego, _A_TOTAL_MAX_BP, _A_TOTAL_MAX_V)
    a_y = v_ego ** 2 * angle_steers * CV.DEG_TO_RAD / (CP.steerRatio * CP.wheelbase)
    a_x_allowed = math.sqrt(max(a_total_max ** 2 - a_y ** 2, 0.))
    max_accel = min(max_accel, a_x_allowed)
    if not allow_throttle:
      clipped_accel_coast = max(accel_coast, ACCEL_MIN)
      coast_limit = np.interp(v_ego, [MIN_ALLOW_THROTTLE_SPEED, MIN_ALLOW_THROTTLE_SPEED*2], [max_accel, clipped_accel_coast])
      max_accel = min(max_accel, coast_limit)

  target_accel = np.clip(v_cruise - v_ego, A_CRUISE_MIN, max_accel)
  j_cruise = get_cruise_jerk(v_ego, personality)
  target_accel = float(np.clip(target_accel, a_cruise_prev - j_cruise * dt, a_cruise_prev + j_cruise * dt))

  return target_accel


class LongitudinalPlanner(LongitudinalPlannerSP):
  def __init__(self, CP, CP_SP, init_v=0.0, init_a=0.0, dt=DT_MDL):
    self.CP = CP
    self.mpc = LongitudinalMpc(dt=dt)
    LongitudinalPlannerSP.__init__(self, self.CP, CP_SP, self.mpc)
    self.fcw = False
    self.dt = dt
    self.allow_throttle = True
    self.stop_speed = get_stop_speed(CP)
    self.lead_accel_min = get_lead_accel_min(CP)
    # only for cars that brake harder than ACCEL_MIN for a lead
    self.mpc_hard = LongitudinalMpc(dt=dt) if self.lead_accel_min < ACCEL_MIN else None
    self.hard_brake = False
    self.hard_brake_exit_t = 0.0

    self.v_desired_filter = FirstOrderFilter(init_v, 2.0, self.dt)
    self.a_cruise = init_a
    self.output_a_target = init_a
    self.output_should_stop = False

    self.v_desired_trajectory = np.zeros(CONTROL_N)
    self.a_desired_trajectory = np.zeros(CONTROL_N)
    self.j_desired_trajectory = np.zeros(CONTROL_N)

  def update(self, sm):
    LongitudinalPlannerSP.update(self, sm)

    if len(sm['carControl'].orientationNED) == 3:
      accel_coast = get_coast_accel(sm['carControl'].orientationNED[1])
    else:
      accel_coast = ACCEL_MAX

    v_ego = sm['carState'].vEgo
    v_cruise_kph = min(sm['carState'].vCruise, V_CRUISE_MAX)
    v_cruise = v_cruise_kph * CV.KPH_TO_MS
    if sm['controlsState'].forceDecel:
      v_cruise = 0.0

    long_control_off = sm['controlsState'].longControlState == LongCtrlState.off

    # Reset current state when not engaged, or user is controlling the speed
    reset_state = long_control_off if self.CP.openpilotLongitudinalControl else not sm['selfdriveState'].enabled
    # PCM cruise speed may be updated a few cycles later, check if initialized
    v_cruise_initialized = sm['carState'].vCruise != V_CRUISE_UNSET
    reset_state = reset_state or not v_cruise_initialized

    throttle_probs = sm['modelV2'].meta.disengagePredictions.gasPressProbs
    throttle_prob = throttle_probs[1] if len(throttle_probs) > 1 else 1.0
    self.allow_throttle = throttle_prob > ALLOW_THROTTLE_THRESHOLD or v_ego <= MIN_ALLOW_THROTTLE_SPEED

    steer_angle_without_offset = sm['carState'].steeringAngleDeg - sm['vehicleParameters'].angleOffsetDeg

    if reset_state:
      self.v_desired_filter.x = v_ego
      self.output_a_target = np.clip(sm['carState'].aEgo, ACCEL_MIN, ACCEL_MAX)
      self.a_cruise = self.output_a_target

    # Prevent divergence, smooth in current v_ego
    self.v_desired_filter.x = max(0.0, self.v_desired_filter.update(v_ego))

    # No change cost when user is controlling the speed, or when standstill
    prev_accel_constraint = not (reset_state or sm['carState'].standstill)

    # Get new v_cruise and a_target from Smart Cruise Control and Speed Limit Assist
    v_cruise, self.output_a_target = LongitudinalPlannerSP.update_targets(self, sm, self.v_desired_filter.x, self.output_a_target, v_cruise)

    self.mpc.set_weights(prev_accel_constraint, personality=sm['selfdriveState'].personality)
    self.mpc.set_cur_state(self.v_desired_filter.x, self.output_a_target)
    self.mpc.update(sm['radarState'], personality=sm['selfdriveState'].personality)
    mpc = self.update_hard_brake(sm, prev_accel_constraint, reset_state)

    self.v_desired_trajectory = np.interp(CONTROL_N_T_IDX, T_IDXS_MPC, mpc.v_solution)
    self.a_desired_trajectory = np.interp(CONTROL_N_T_IDX, T_IDXS_MPC, mpc.a_solution)
    self.j_desired_trajectory = np.interp(CONTROL_N_T_IDX, T_IDXS_MPC[:-1], mpc.j_solution)

    # TODO counter is only needed because radar is glitchy, remove once radar is gone
    self.fcw = self.mpc.crash_cnt > 2 and not sm['carState'].standstill
    if self.fcw:
      cloudlog.info("FCW triggered")

    # Save starting point for next iteration
    a_prev = self.output_a_target

    action_t =  self.CP.longitudinalActuatorDelay + DT_MDL
    output_a_target_mpc = get_accel_from_plan(self.v_desired_trajectory, self.a_desired_trajectory, CONTROL_N_T_IDX,
                                              action_t=action_t)
    output_should_stop_mpc = should_stop(v_ego, output_a_target_mpc, self.stop_speed)
    output_a_target_e2e = sm['modelV2'].action.desiredAcceleration
    output_should_stop_e2e = sm['modelV2'].action.shouldStop

    is_e2e = self.is_e2e(sm)

    self.a_cruise = get_cruise_accel(is_e2e, v_cruise, v_ego,
                                     self.a_cruise, steer_angle_without_offset, self.CP, self.dt,
                                     accel_coast, self.allow_throttle, sm['selfdriveState'].personality)
    cruise_should_stop = should_stop(v_ego, self.a_cruise, self.stop_speed)

    # each source is clipped to its own floor before taking the min: only the hard MPC braking for a present
    # lead goes past ACCEL_MIN (mpc.a_min), cruise and e2e stay at ACCEL_MIN. Ties at the floor go to the
    # lowest unclipped source, as with a single ACCEL_MIN clip after the min.
    candidates = [(output_a_target_mpc, mpc.a_min, mpc.source, output_should_stop_mpc),
                  (self.a_cruise, ACCEL_MIN, LongitudinalPlanSource.cruise, cruise_should_stop)]
    if is_e2e:
      candidates.append((output_a_target_e2e, ACCEL_MIN, LongitudinalPlanSource.e2e, output_should_stop_e2e))

    a_floor_min = min(candidates, key=lambda c: (max(c[0], c[1]), c[0]))
    output_a_target, a_floor, self.mpc.source = max(a_floor_min[0], a_floor_min[1]), a_floor_min[1], a_floor_min[2]
    self.output_should_stop = any(c[3] for c in candidates)
    self.output_a_target = np.clip(output_a_target, a_floor, ACCEL_MAX)

    self.v_desired_filter.x = self.v_desired_filter.x + self.dt * (self.output_a_target + a_prev) / 2.0

  def update_hard_brake(self, sm, prev_accel_constraint, reset_state):
    """Runs the hard MPC next to the stock one and returns the MPC whose plan is used this cycle."""
    if self.mpc_hard is None:
      return self.mpc
    personality = sm['selfdriveState'].personality
    self.mpc_hard.set_weights(prev_accel_constraint, personality=personality)
    self.mpc_hard.set_cur_state(self.v_desired_filter.x, self.output_a_target)
    self.mpc_hard.update(sm['radarState'], personality=personality, lead_accel_min=self.lead_accel_min)

    a_plan_min = np.min(self.mpc.a_solution[T_IDXS_MPC <= HARD_BRAKE_T])
    cap_limited = self.mpc.source in MPC_SOURCES and (a_plan_min <= ACCEL_MIN + HARD_BRAKE_CAP_MARGIN or self.mpc.lead_crash)
    hard_available = self.mpc_hard.a_min < ACCEL_MIN
    if reset_state or not hard_available:
      self.hard_brake = False
    elif cap_limited:
      self.hard_brake = True
      self.hard_brake_exit_t = 0.0
    elif self.hard_brake:
      self.hard_brake_exit_t += self.dt
      if self.hard_brake_exit_t >= HARD_BRAKE_EXIT_T and self.output_a_target > ACCEL_MIN:
        self.hard_brake = False
    return self.mpc_hard if self.hard_brake else self.mpc

  def publish(self, sm, pm):
    plan_send = messaging.new_message('longitudinalPlan')

    plan_send.valid = sm.all_checks()

    longitudinalPlan = plan_send.longitudinalPlan
    longitudinalPlan.modelMonoTime = sm.logMonoTime['modelV2']
    longitudinalPlan.processingDelay = (plan_send.logMonoTime / 1e9) - sm.logMonoTime['modelV2']
    longitudinalPlan.solverExecutionTime = self.mpc.solve_time

    longitudinalPlan.speeds = self.v_desired_trajectory.tolist()
    longitudinalPlan.accels = self.a_desired_trajectory.tolist()
    longitudinalPlan.jerks = self.j_desired_trajectory.tolist()

    longitudinalPlan.hasLead = sm['radarState'].leadOne.present
    longitudinalPlan.longitudinalPlanSource = self.mpc.source
    longitudinalPlan.fcw = self.fcw

    longitudinalPlan.aTarget = float(self.output_a_target)
    longitudinalPlan.shouldStop = bool(self.output_should_stop)
    longitudinalPlan.allowBrake = True
    longitudinalPlan.allowThrottle = bool(self.allow_throttle)

    pm.send('longitudinalPlan', plan_send)

    self.publish_longitudinal_plan_sp(sm, pm)
