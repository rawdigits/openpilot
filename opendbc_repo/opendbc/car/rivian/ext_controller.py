import math
from collections import deque
import numpy as np

from opendbc.car.lateral import (
  apply_driver_steer_torque_limits, common_fault_avoidance,
  apply_steer_angle_limits_vm, get_max_angle_delta_vm, get_max_angle_vm,
)
from opendbc.car.carlog import carlog
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.rivian.values import CarControllerParams as CCP
from opendbc.car.vehicle_model import VehicleModel

# EPAS angle envelope (EPAS_High_Angle_Cmd_Err)
EPAS_FW_MAX_ANGLE_BP = [0.0, 2.78, 5.56, 8.33, 12.50, 16.67, 22.22, 27.78]  # m/s
EPAS_FW_MAX_ANGLE_V  = [500, 500,  250,  150,  85,    56,    40,    25   ]  # deg

# EPAS windowed rate limit (EPAS_High_Actual_Angle_Rate_Err)
EPAS_FW_RATE_BP = [5.56, 8.33, 12.50, 16.67]  # m/s
EPAS_FW_RATE_V  = [4.50, 1.50, 0.60,  0.18 ]  # deg/frame

EPAS_FW_ANGLE_MARGIN = 0.98
EPAS_FW_RATE_MARGIN  = 0.94

# final per-frame cap inside panda's jerk limit
PANDA_STEP_MARGIN = 0.9

MIN_TORQUE_FRAMES = 50
HANDOFF_EXIT_DEG = 15.0       # hand back to angle when the wheel is within this of the commanded angle
UNWIND_HANDOFF_RATE = 40.0    # max wheel speed in deg/s to hand back to angle
HANDOFF_MAX_ANGLE_DEG = 25.0  # no handoff to angle mid-turn

# light-torsion presence, bridges capacitive dropouts while hands slide on the wheel
PRESENCE_TORQUE_THRESHOLD = 1.5
PRESENCE_MIN_FRAMES = 30      # frames above threshold to latch (0.3s)
PRESENCE_HOLD_FRAMES = 100    # latch hold (1.0s)
HANDS_OFF_EXIT_FRAMES = 75    # hands-off time before handing back to angle (0.75s)
EAC_RECOVER_FRAMES = 15       # angle frames with the EPAS EAC not active before falling back to torque

# the EPAS inhibits EAC (EacStatus 0) after a drop and stays there while ACM_EacEnabled is 0,
# so from torque we periodically request angle again at the measured wheel angle
EAC_PROBE_FRAMES = 50              # angle request window per retry (0.5s)
EAC_PROBE_MAX_RATE = 2.0           # deg/s, wheel settled enough to start angle where it is
EAC_PROBE_MAX_GAP = 0.5            # deg, sent angle vs wheel, the jerk limit lets the request trail a moving wheel
EAC_RETRY_INTERVAL_FRAMES = 300    # wait after a failed retry (3s), doubles per failure
EAC_RETRY_MAX_INTERVAL_FRAMES = 1200  # up to 12s
EAC_STABLE_FRAMES = 1000           # EAC active this long (10s) resets the retry backoff

# EacErrorCode 11 EPAS_Vehspd_Max_Thd_Err dropped EAC at ~101 and 104 mph, hand to torque just before
EAC_MAX_SPEED = 160. * CV.KPH_TO_MS   # 99.4 mph
EAC_REARM_SPEED = 155. * CV.KPH_TO_MS  # 96.3 mph

# blip the TOI request bit at high angle so the EPAS does not latch ToiFlt
TOI_MAX_ANGLE_DEG = 90
TOI_MAX_ANGLE_FRAMES = 89        # frames held high before a blip (~0.9s)
TOI_BLIP_FRAMES = 2              # frames to release ACM_lkaActToi


class _RateBudget:
  # sliding-window budget for the EPAS rate limit; history is CAN-quantized to 0.1 deg
  WINDOW_USER_FRAMES = 16
  WINDOW_TIME_S = 0.16

  def __init__(self):
    self.history = deque([0.0] * self.WINDOW_USER_FRAMES, maxlen=self.WINDOW_USER_FRAMES)

  def push(self, sent_angle: float) -> None:
    self.history.append(round(sent_angle * 10) / 10)

  def bounds(self, threshold_dps: float, margin: float):
    cmd_oldest = self.history[0]
    budget = threshold_dps * self.WINDOW_TIME_S * margin
    return cmd_oldest - budget, cmd_oldest + budget


def get_safety_CP():
  from opendbc.car.rivian.interface import CarInterface
  return CarInterface.get_non_essential_params("RIVIAN_R1")


class ExternalController:
  def __init__(self):
    self.VM_safety = VehicleModel(get_safety_CP())

    # hands-on
    self.wheel_touch_cnt = 0
    self.torsion_cnt = 0
    self.hands_on = False
    # torsion observer states
    self.wheel_angle = None  # rad
    self.wheel_rate = 0.0    # rad/s
    self.column_angle_last = 0.0
    self.presence_cnt = 0
    self.presence_hold = 0
    self.hands_off_frames = 0

    # cooperative torque mode
    self.torque_active = False
    self.torque_active_frames = 0
    self.lat_active_last = False
    self.eac_dead_frames = 0
    self.overspeed = False

    # angle retry from torque while the EPAS sits inhibited
    self.eac_probe_frames = 0  # frames into the current retry, 0 when not retrying
    self.eac_retry_wait = 0
    self.eac_retry_interval = EAC_RETRY_INTERVAL_FRAMES
    self.eac_retries = 0
    self.eac_stable_frames = 0
    self.eac_active_frames = 0  # consecutive frames on angle with the EPAS active, for the drop log
    # ACM_EacEnabled, angle_active or retrying
    self.eac_request = False

    # angle command
    self.apply_angle_last = 0.0
    self.angle_active = False
    self.rate_budget = _RateBudget()

    # cooperative torque
    self.apply_torque_last = 0
    # decoupled from torque_active so a blip does not flip angle or feature mode
    self.toi_angle_limit_counter = 0
    self.toi_act_cmd = False     # sent into ACM_lkaActToi, low for 2 frames during a blip

  def update(self, CS, lat_active: bool, actuators):
    self._update_hands_on(CS)
    # computed by the angle controller in controlsd with live vehicle parameters
    desired_angle = float(actuators.steeringAngleDeg)
    self._update_torque_active(CS, lat_active, desired_angle)
    self._update_angle(CS, lat_active, desired_angle)
    self._update_torque(CS, actuators)

  def _update_wheel_touched(self, wheel_touched, wheel_touched_min_count):
    self.wheel_touch_cnt += 1 if wheel_touched else -1
    self.wheel_touch_cnt = int(np.clip(self.wheel_touch_cnt, 0, wheel_touched_min_count * 2 + 1))
    return self.wheel_touch_cnt > wheel_touched_min_count

  def _update_torsion(self, torque, torque_threshold, torsion_min_count):
    abs_torque = abs(torque)
    self.torsion_cnt += max(1, math.ceil(abs_torque / torque_threshold)) if abs_torque > torque_threshold else -1
    self.torsion_cnt = int(np.clip(self.torsion_cnt, 0, torsion_min_count * 2 + 1))
    return self.torsion_cnt > torsion_min_count

  def _update_torsion_presence(self, torque):
    # sustained light torque, latched
    self.presence_cnt = self.presence_cnt + 1 if abs(torque) > PRESENCE_TORQUE_THRESHOLD else 0
    if self.presence_cnt >= PRESENCE_MIN_FRAMES:
      self.presence_hold = PRESENCE_HOLD_FRAMES
    elif self.presence_hold > 0:
      self.presence_hold -= 1
    return self.presence_hold > 0

  def _update_driver_torque(self, CS):
    # EPAS angle control itself loads the torsion bar, model the wheel's reaction and subtract it
    inertia = 0.0205    # kg*m^2
    stiffness = 51.0    # Nm/rad
    damping = 0.156     # Nm/(rad/s)
    friction = 0.141    # Nm, tanh-blended over 0.0066 rad/s
    substeps = 10

    column_angle = math.radians(CS.out.steeringAngleDeg)
    if self.wheel_angle is None:
      self.wheel_angle = self.column_angle_last = column_angle
    h = 0.01 / substeps
    for i in range(substeps):
      c = self.column_angle_last + (column_angle - self.column_angle_last) * (i + 1) / substeps
      bar_torque = stiffness * (self.wheel_angle - c)
      accel = (-bar_torque - damping * self.wheel_rate - friction * math.tanh(self.wheel_rate / 0.0066)) / inertia
      self.wheel_rate += accel * h
      self.wheel_angle += self.wheel_rate * h
    self.column_angle_last = column_angle
    return CS.out.steeringTorque - stiffness * (self.wheel_angle - column_angle)

  def _update_hands_on(self, CS):
    # hands-on if any of: capacitive sensor, EPAS-side level, or torsion bar
    driver_torque = self._update_driver_torque(CS)
    calibration = CS.sccm_wheel_touch["SCCM_WheelTouch_Calibration"]
    wheel_touch = self._update_wheel_touched(CS.sccm_wheel_touch["SCCM_WheelTouch_CapacitiveValue"] > calibration * 0.9, 25)
    torsion = self._update_torsion(driver_torque, 3.0, 9)
    presence = self._update_torsion_presence(driver_torque)
    self.hands_on = wheel_touch or torsion or CS.hands_on_level > 1
    self.hands_off_frames = 0 if self.hands_on or presence else self.hands_off_frames + 1

  def _handback_ok(self, CS, gap: float) -> bool:
    # hands off and the wheel settled near the commanded angle, inside what the EPAS and panda accept
    if self.torque_active_frames < MIN_TORQUE_FRAMES or self.hands_off_frames < HANDS_OFF_EXIT_FRAMES or self.overspeed:
      return False
    fw_max = float(np.interp(CS.out.vEgoRaw, EPAS_FW_MAX_ANGLE_BP, EPAS_FW_MAX_ANGLE_V)) * EPAS_FW_ANGLE_MARGIN
    # no handoff to an angle the ISO lat-accel envelope won't let us command, panda would block it
    iso_max = get_max_angle_vm(max(CS.out.vEgoRaw, 1.0), self.VM_safety, CCP)
    in_envelope = abs(CS.out.steeringAngleDeg) < min(fw_max, HANDOFF_MAX_ANGLE_DEG, iso_max)
    # only once the wheel motion fits the EPAS rate budget
    thr_dps = float(np.interp(CS.out.vEgoRaw, EPAS_FW_RATE_BP, EPAS_FW_RATE_V)) * 100.0
    lo, hi = self.rate_budget.bounds(thr_dps, EPAS_FW_RATE_MARGIN)
    rate_settled = lo <= CS.out.steeringAngleDeg <= hi and abs(CS.out.steeringRateDeg) < UNWIND_HANDOFF_RATE
    return in_envelope and rate_settled and gap < HANDOFF_EXIT_DEG

  def _update_torque_active(self, CS, lat_active: bool, desired_angle: float):
    self.torque_active_frames = self.torque_active_frames + 1 if self.torque_active else 0

    # EPAS available and no published EacErrorCode
    epas_ready = CS.eac_status == 1 and CS.eac_error_code == 0
    # is the EPAS actually steering on angle
    eac_active = CS.eac_status == 2
    # how far the wheel is from the angle openpilot wants
    gap = abs(desired_angle - CS.out.steeringAngleDeg)

    if CS.out.vEgoRaw > EAC_MAX_SPEED and not self.overspeed:
      self.overspeed = True
      carlog.warning("rivian eac: above %.1f m/s, angle handed to torque", EAC_MAX_SPEED)
    elif CS.out.vEgoRaw < EAC_REARM_SPEED and self.overspeed:
      self.overspeed = False
      carlog.warning("rivian eac: below %.1f m/s, angle may re-arm", EAC_REARM_SPEED)

    handback_ok = self.torque_active and self._handback_ok(CS, gap)

    if not lat_active:
      self.torque_active = False
    # enter torque the moment the driver touches the wheel, which is when the EPAS drops angle control
    elif self.hands_on and CS.out.steeringPressed:
      self.torque_active = True
    # the EPAS drops angle above its speed threshold (EacErrorCode 11), hand to torque before it does
    elif self.overspeed:
      self.torque_active = True
    # EPAS lost angle and won't recover, torque re-arms it
    elif self.eac_dead_frames >= EAC_RECOVER_FRAMES:
      self.torque_active = True
    # fresh engage while EPAS is not ready yet
    elif not self.lat_active_last and not epas_ready:
      self.torque_active = True
    # hand back to angle once hands off and the wheel is settled near the commanded angle,
    # when the EPAS is available or a retry brought it straight to active
    elif handback_ok and (epas_ready or (self.eac_probe_frames > 0 and eac_active)):
      self.torque_active = False

    # log every EPAS drop while on angle, to find why it releases 2 -> 1 with err 0 shortly after engage (#10)
    on_angle = lat_active and not self.torque_active
    if on_angle and eac_active:
      self.eac_active_frames += 1
    elif self.eac_active_frames > 0:
      if on_angle:
        carlog.warning("rivian eac: drop 2 -> %d err %d after %d frames active, v %.1f, wheel %.1f rate %.1f, sent %.1f desired %.1f, "
                       "torque %.2f hands_on_level %d", CS.eac_status, CS.eac_error_code, self.eac_active_frames, CS.out.vEgoRaw,
                       CS.out.steeringAngleDeg, CS.out.steeringRateDeg, self.apply_angle_last, desired_angle, CS.out.steeringTorque,
                       CS.hands_on_level)
      self.eac_active_frames = 0

    # count consecutive frames we are trying to steer on angle but the EPAS EAC is not active
    if lat_active and not self.torque_active and not eac_active:
      self.eac_dead_frames += 1
    else:
      self.eac_dead_frames = 0

    # retry angle while the EPAS is inhibited without an error, only from a settled, hands-off torque state
    probe_ok = (lat_active and self.torque_active and handback_ok and not CS.out.steeringPressed and
                abs(CS.out.steeringRateDeg) < EAC_PROBE_MAX_RATE and CS.eac_error_code == 0 and
                abs(self.apply_angle_last - CS.out.steeringAngleDeg) < EAC_PROBE_MAX_GAP)
    self._update_eac_probe(CS, lat_active, probe_ok, eac_active)

    self.lat_active_last = lat_active

  def _eac_backoff(self):
    self.eac_retries += 1
    self.eac_retry_wait = self.eac_retry_interval
    self.eac_retry_interval = min(self.eac_retry_interval * 2, EAC_RETRY_MAX_INTERVAL_FRAMES)

  def _update_eac_probe(self, CS, lat_active: bool, probe_ok: bool, eac_active: bool):
    self.eac_retry_wait = max(self.eac_retry_wait - 1, 0)
    self.eac_stable_frames = self.eac_stable_frames + 1 if lat_active and not self.torque_active and eac_active else 0

    if lat_active and not self.torque_active and self.eac_probe_frames > 0:
      carlog.warning("rivian eac: angle re-armed after %d retries (%d frames)", self.eac_retries + 1, self.eac_probe_frames)
      # a re-arm counts as a retry until angle holds, if the EPAS drops it again the next retry waits
      self._eac_backoff()

    # the backoff only resets on disengage or once angle has held, so a flapping EPAS stays rate limited
    if not lat_active or self.eac_stable_frames >= EAC_STABLE_FRAMES:
      self.eac_retries = 0
      self.eac_retry_interval = EAC_RETRY_INTERVAL_FRAMES

    if not lat_active or not self.torque_active:
      self.eac_probe_frames = 0
    elif self.eac_probe_frames > 0:
      if not probe_ok or CS.eac_status == 4 or self.eac_probe_frames >= EAC_PROBE_FRAMES:
        carlog.warning("rivian eac: retry %d failed, EacStatus %d err %d after %d frames, next in %d frames",
                       self.eac_retries + 1, CS.eac_status, CS.eac_error_code, self.eac_probe_frames, self.eac_retry_interval)
        self.eac_probe_frames = 0
        self._eac_backoff()
      else:
        self.eac_probe_frames += 1
    elif probe_ok and CS.eac_status == 0 and self.eac_retry_wait == 0:
      self.eac_probe_frames = 1

  def _update_angle(self, CS, lat_active: bool, desired_angle: float):
    self.angle_active = lat_active and not self.torque_active
    self.eac_request = self.angle_active or self.eac_probe_frames > 0

    # a retry holds the wheel where torque has it, so the EPAS taking over is not a step
    apply_angle = desired_angle if self.angle_active else CS.out.steeringAngleDeg

    # use future v_ego so the jerk limit ramps the angle down before the lat-accel envelope shrinks
    v_lookahead = max(CS.out.vEgoRaw + max(CS.out.aEgo, 0.0), 1.0)
    apply_angle = apply_steer_angle_limits_vm(apply_angle, self.apply_angle_last, v_lookahead,
                                              CS.out.steeringAngleDeg, self.eac_request, CCP, self.VM_safety)

    if self.eac_request:
      # EPAS absolute envelope
      fw_max = float(np.interp(CS.out.vEgoRaw, EPAS_FW_MAX_ANGLE_BP, EPAS_FW_MAX_ANGLE_V)) * EPAS_FW_ANGLE_MARGIN
      apply_angle = float(np.clip(apply_angle, -fw_max, fw_max))

      # EPAS windowed rate budget
      thr_dps = float(np.interp(CS.out.vEgoRaw, EPAS_FW_RATE_BP, EPAS_FW_RATE_V)) * 100.0
      lo, hi = self.rate_budget.bounds(thr_dps, EPAS_FW_RATE_MARGIN)
      apply_angle = float(np.clip(apply_angle, lo, hi))

      # panda's per-frame jerk limit
      step = get_max_angle_delta_vm(max(CS.out.vEgoRaw, 1.0), self.VM_safety, CCP) * PANDA_STEP_MARGIN
      apply_angle = float(np.clip(apply_angle, self.apply_angle_last - step, self.apply_angle_last + step))

    self.apply_angle_last = apply_angle
    self.rate_budget.push(apply_angle)

  def _update_torque(self, CS, actuators):
    if not self.torque_active:
      self.apply_torque_last = 0
      self.toi_act_cmd = False
      self.toi_angle_limit_counter = 0
      return

    v_ego = CS.out.vEgoRaw
    steer_max = round(float(np.interp(v_ego, CCP.STEER_MAX_LOOKUP[0], CCP.STEER_MAX_LOOKUP[1])))
    new_torque = int(round(float(actuators.torque) * steer_max))
    apply_torque = apply_driver_steer_torque_limits(new_torque, self.apply_torque_last,
                                                    CS.out.steeringTorque, CCP, steer_max)

    # blip the TOI request when held at high angle, torque drops to 0 so the rate limiter ramps back from 0
    self.toi_angle_limit_counter, toi_act = common_fault_avoidance(
      abs(CS.out.steeringAngleDeg) >= TOI_MAX_ANGLE_DEG, self.torque_active,
      self.toi_angle_limit_counter, TOI_MAX_ANGLE_FRAMES, TOI_BLIP_FRAMES)
    if not toi_act:
      apply_torque = 0

    self.toi_act_cmd = toi_act
    self.apply_torque_last = apply_torque
