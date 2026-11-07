"""Guards for Ryan's yeetfollow customizations on yeet-angle (automotive/openpilot#4).

One test per PARITY.md row that has code on this base, pinning the exact value or
behavior, so an upstream rebase that silently drops a customization fails CI.
Rivian rows run in both the angle-kit (0x1310, with the 0x131a long harness) and
the torque-fallback paths.
"""
import io
import json
import os
import re
import subprocess
import tempfile
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from opendbc.car import Bus, gen_empty_fingerprint, structs
from opendbc.car import interfaces as car_interfaces
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.rivian import rivian_bridge
from opendbc.car.rivian.carcontroller import MAX_STEERING_ANGLE
from opendbc.car.rivian.carstate import CarState
from opendbc.car.rivian.ext_controller import TOI_MAX_ANGLE_DEG
from opendbc.car.rivian.interface import CarInterface
from opendbc.car.rivian.rivian_bridge import RivianBridge
from opendbc.car.rivian.values import CAR, CarControllerParams, RivianFlags
from opendbc.car.interfaces import ACCEL_MIN
from opendbc.safety.tests.libsafety import libsafety_py
from opendbc.sunnypilot.car.rivian import carstate_ext
from openpilot.cereal import log
from openpilot.common.basedir import BASEDIR
from openpilot.common.parameterized import parameterized, parameterized_class
from openpilot.common.params import Params
from openpilot.common.test import OpenpilotTestCase
from openpilot.selfdrive.car import cruise
from openpilot.selfdrive.controls.lib import drive_helpers, longitudinal_planner
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib import long_mpc
from openpilot.selfdrive.monitoring.policy import DRIVER_MONITOR_SETTINGS
from openpilot.selfdrive.selfdrived.helpers import ExcessiveActuationCheck
from openpilot.selfdrive.test.longitudinal_maneuvers.plant import Plant
from openpilot.selfdrive.test.longitudinal_maneuvers import test_longitudinal
from openpilot.sunnypilot.mads import helpers as mads_helpers
from openpilot.sunnypilot.selfdrive.car import cruise_ext, rivianbridged
from openpilot.sunnypilot.selfdrive.car.rivian_bridge_reader import bridge_values
from openpilot.system.manager.process_config import managed_processes

ROOT = Path(BASEDIR)
Personality = log.LongitudinalPersonality


def rivian_params(angle_kit: bool):
  fingerprint = gen_empty_fingerprint()
  fingerprint[0][0x321] = 8  # Gen1
  if angle_kit:
    # kit path with the long harness: the only kit setup where openpilot long and the bridge run
    fingerprint[1].update({0x1310: 8, 0x131a: 8})
  CP = CarInterface.get_params(CAR.RIVIAN_R1, fingerprint, [], angle_kit, False, False)
  CP_SP = CarInterface.get_params_sp(CP, CAR.RIVIAN_R1, fingerprint, [], angle_kit, False, False)
  return CP, CP_SP


class TestLongitudinalTuning(OpenpilotTestCase):
  # rows 1, 2
  def test_comfort_brake_and_stop_distance(self):
    self.assertEqual(long_mpc.COMFORT_BRAKE, 3.0)
    self.assertEqual(long_mpc.STOP_DISTANCE, 3.0)
    self.assertAlmostEqual(long_mpc.get_safe_obstacle_distance(0., 1.10), 3.0)
    self.assertAlmostEqual(long_mpc.get_stopped_equivalence_factor(6.), 6.)
    # 20 m/s standard: 400/6 + 22 + 3
    self.assertAlmostEqual(long_mpc.get_safe_obstacle_distance(20., 1.10), 400 / 6 + 25)
    # the maneuver tests' "resume from a stop" start gap follows STOP_DISTANCE
    self.assertIs(test_longitudinal.STOP_DISTANCE, long_mpc.STOP_DISTANCE)

  # rows 3, 4
  def test_cruise_accel_limits(self):
    self.assertEqual(longitudinal_planner.A_CRUISE_MAX_VALS, [1.6, 1.2, 0.8, 0.6])
    self.assertEqual(longitudinal_planner.A_CRUISE_MAX_BP, [0., 10.0, 25., 40.])
    self.assertEqual(longitudinal_planner.A_CRUISE_MIN, -1.2)

  # rows 5, 6, 7
  def test_mpc_costs(self):
    self.assertEqual(long_mpc.A_CHANGE_COST, 100.)
    self.assertEqual(long_mpc.DANGER_ZONE_COST, 60.)
    self.assertEqual(long_mpc.LEAD_DANGER_FACTOR, 0.85)

  # row 8
  @parameterized.expand([(Personality.aggressive, 0.60), (Personality.standard, 1.10), (Personality.relaxed, 1.80)])
  def test_t_follow(self, personality, t_follow):
    self.assertEqual(long_mpc.get_T_FOLLOW(personality), t_follow)

  # row 9 (the aggressive jerk factor is the yeet-angle-tune row 47)
  def test_uncustomized_mpc_costs(self):
    self.assertEqual(long_mpc.J_EGO_COST, 5.)
    self.assertEqual([long_mpc.get_jerk_factor(p) for p in (Personality.standard, Personality.relaxed)], [1.0, 1.0])

  # row 10
  def test_personality_mapping(self):
    self.assertEqual((Personality.aggressive, Personality.standard, Personality.relaxed), (0, 1, 2))
    self.assertEqual(long_mpc.get_T_FOLLOW(), 1.10)
    self.assertEqual(Params().get("LongitudinalPersonality", return_default=True), Personality.standard)

  # row 43
  def test_mpc_tuning_doc_matches(self):
    rows = dict(re.findall(r"^\| (\S+(?: \S+)*?) \|[^|]*\| ([^|]+) \|$", (ROOT / "MPC_TUNING.md").read_text(), re.M))
    self.assertEqual(rows["A_CHANGE_COST"].strip(), "100")
    self.assertEqual(rows["DANGER_ZONE_COST"].strip(), "60")
    self.assertEqual(rows["LEAD_DANGER_FACTOR"].strip(), "0.85")
    self.assertEqual(rows["COMFORT_BRAKE"].strip(), "3.0 m/s²")
    self.assertEqual(rows["STOP_DISTANCE"].strip(), "3.0 m")

  # row 45: the yeet-angle-tune aggressive tune clears the 4 known cases (row 47)
  def test_known_maneuver_failures(self):
    self.assertEqual(test_longitudinal.KNOWN_FAILURES, set())


class TestAggressiveTune(OpenpilotTestCase):
  """yeet-angle-tune (row 47): snappier aggressive following. Standard and relaxed keep the values above."""

  def test_values(self):
    self.assertEqual(long_mpc.COMFORT_BRAKE_AGGRESSIVE, 3.5)
    self.assertEqual(long_mpc.JERK_FACTOR_AGGRESSIVE, 0.2)
    # yeet-angle-brake-tune: a notch more pull-away, and half the MPC jerk cost
    self.assertEqual(longitudinal_planner.A_CRUISE_MAX_VALS_AGGRESSIVE, [2.0, 1.8, 1.4, 1.1])
    self.assertEqual(longitudinal_planner.J_CRUISE_VALS_AGGRESSIVE, [2.0, 1.8, 1.4, 1.1])
    self.assertEqual(longitudinal_planner.A_CRUISE_MAX_VALS, [1.6, 1.2, 0.8, 0.6])
    self.assertEqual(longitudinal_planner.J_CRUISE_VALS, [1.6, 1.2, 0.8, 0.6])
    self.assertEqual(long_mpc.J_EGO_FACTOR_AGGRESSIVE, 0.5)
    self.assertEqual((long_mpc.J_EGO_COST, long_mpc.A_CHANGE_COST), (5., 100.))

  def test_personality_selection(self):
    self.assertEqual([long_mpc.get_comfort_brake(p) for p in (Personality.aggressive, Personality.standard, Personality.relaxed)],
                     [3.5, 3.0, 3.0])
    self.assertEqual(long_mpc.get_comfort_brake(), 3.0)
    self.assertEqual(long_mpc.get_jerk_factor(Personality.aggressive), 0.2)
    self.assertEqual([long_mpc.get_j_ego_factor(p) for p in (Personality.aggressive, Personality.standard, Personality.relaxed)],
                     [0.5, 1.0, 1.0])
    for v, aggressive, other in ((0., 2.0, 1.6), (10., 1.8, 1.2), (25., 1.4, 0.8), (40., 1.1, 0.6), (17.5, 1.6, 1.0)):
      self.assertAlmostEqual(longitudinal_planner.get_max_accel(v, Personality.aggressive), aggressive)
      self.assertAlmostEqual(longitudinal_planner.get_cruise_jerk(v, Personality.aggressive), aggressive)
      for p in (Personality.standard, Personality.relaxed):
        self.assertAlmostEqual(longitudinal_planner.get_max_accel(v, p), other)
      self.assertAlmostEqual(longitudinal_planner.get_max_accel(v), other)

  def test_within_accel_limits(self):
    # openpilot's ACCEL_MAX (ISO 15622 comfort limit) and the Rivian panda limit (rivian.h max_accel 200 = 2.0 m/s²)
    self.assertEqual((car_interfaces.ACCEL_MIN, car_interfaces.ACCEL_MAX), (-3.5, 2.0))
    # yeet-angle-brake: the Rivian brakes to -6.5 for a present lead (TestRivianHardBrake), max accel is unchanged
    self.assertEqual((CarControllerParams.ACCEL_MIN, CarControllerParams.ACCEL_MAX), (-6.5, 2.0))
    rivian_h = (ROOT / "opendbc_repo/opendbc/safety/modes/rivian.h").read_text()
    self.assertIn(".max_accel = 200,", rivian_h)
    self.assertIn(".min_accel = -650,", rivian_h)
    self.assertLessEqual(max(longitudinal_planner.A_CRUISE_MAX_VALS_AGGRESSIVE), car_interfaces.ACCEL_MAX)
    # the MPC must be able to command the comfortable brake it plans around, also at the -3.5 floor
    # it has without a present lead
    self.assertLessEqual(long_mpc.COMFORT_BRAKE_AGGRESSIVE, -car_interfaces.ACCEL_MIN)

  @parameterized.expand([(0.,), (10.,), (20.,), (35.,)])
  def test_steady_state_gap_unchanged(self, v):
    # the comfort brake terms cancel when pace-matched: same desired gap as with 3.0
    t_follow = long_mpc.get_T_FOLLOW(Personality.aggressive)
    cb = long_mpc.get_comfort_brake(Personality.aggressive)
    gap = long_mpc.get_safe_obstacle_distance(v, t_follow, cb) - long_mpc.get_stopped_equivalence_factor(v, cb)
    self.assertAlmostEqual(gap, t_follow * v + long_mpc.STOP_DISTANCE)
    self.assertAlmostEqual(gap, long_mpc.get_safe_obstacle_distance(v, t_follow) - long_mpc.get_stopped_equivalence_factor(v))

  def test_mpc_uses_personality_comfort_brake(self):
    radar = log.RadarState.new_message()
    radar.leadOne.present = True
    radar.leadOne.dRel = 40.
    radar.leadOne.vLead = 15.
    radar.leadOne.aLeadTau = 1.5
    radar.leadTwo = radar.leadOne
    mpc = long_mpc.LongitudinalMpc()
    mpc.set_cur_state(20., 0.)
    for personality, cb in ((Personality.aggressive, 3.5), (Personality.standard, 3.0), (Personality.relaxed, 3.0)):
      mpc.set_weights(personality=personality)
      mpc.update(radar, personality=personality)
      self.assertTrue((mpc.params[:, 6] == cb).all())
      self.assertEqual(mpc.solution_status, 0)

  def test_cruise_accel_uses_personality(self):
    CP, _ = rivian_params(True)
    def cruise_accel(personality, a_prev, v_ego=10.):
      return longitudinal_planner.get_cruise_accel(False, 30., v_ego, a_prev, 0., CP, 0.05, 2.0, True, personality)
    # accel limit at 10 m/s: 1.8 aggressive vs 1.2 otherwise, but the 1.7 total-accel cap (_A_TOTAL_MAX_V below 20 m/s)
    # binds aggressive there even when driving straight; at 25 m/s the table binds (1.4)
    self.assertAlmostEqual(longitudinal_planner.get_max_accel(10., Personality.aggressive), 1.8)
    for v_ego, limit in ((10., 1.7), (25., 1.4)):
      a = 0.
      for _ in range(60):
        a = cruise_accel(Personality.aggressive, a, v_ego)
      self.assertAlmostEqual(a, limit)
    self.assertAlmostEqual(cruise_accel(Personality.standard, 1.2), 1.2)
    self.assertAlmostEqual(cruise_accel(Personality.relaxed, 1.2), 1.2)
    # jerk limit: 1.8 m/s³ at 10 m/s aggressive vs 1.2 otherwise
    self.assertAlmostEqual(cruise_accel(Personality.aggressive, 0.), 1.8 * 0.05)
    self.assertAlmostEqual(cruise_accel(Personality.standard, 0.), 1.2 * 0.05)

  def test_mpc_jerk_cost_weights(self):
    # [obstacle, x, v, a, a-change, jerk]: aggressive jerk cost 0.2 * 0.5 * 5, a-change cost 0.2 * 100
    mpc = long_mpc.LongitudinalMpc()
    for personality, a_change, j_ego in ((Personality.aggressive, 20., 0.5), (Personality.standard, 100., 5.), (Personality.relaxed, 100., 5.)):
      with patch.object(mpc, "set_cost_weights") as set_cost_weights:
        mpc.set_weights(personality=personality)
      weights = set_cost_weights.call_args.args[0]
      self.assertEqual(weights[0], long_mpc.X_EGO_OBSTACLE_COST)
      self.assertAlmostEqual(weights[4], a_change)
      self.assertAlmostEqual(weights[5], j_ego)

  def test_tuning_doc_matches(self):
    rows = dict(re.findall(r"^\| (\S+(?: \S+)*?) \|[^|]*\| ([^|]+) \|$", (ROOT / "MPC_TUNING.md").read_text(), re.M))
    self.assertEqual(rows["COMFORT_BRAKE aggressive"].strip(), "3.5 m/s²")
    self.assertEqual(rows["Jerk factor aggressive"].strip(), "0.2")
    self.assertEqual(rows["J_EGO_COST factor aggressive"].strip(), "0.5")
    self.assertEqual(rows["A_CRUISE_MAX_VALS aggressive"].strip(), "[2.0, 1.8, 1.4, 1.1]")
    self.assertEqual(rows["J_CRUISE_VALS aggressive"].strip(), "[2.0, 1.8, 1.4, 1.1]")


@parameterized_class(("angle_kit",), [(True,), (False,)])
class TestRivianLongitudinalTune(OpenpilotTestCase):
  angle_kit: bool

  def setUp(self):
    super().setUp()
    self.CP, self.CP_SP = rivian_params(self.angle_kit)
    self.assertEqual(bool(self.CP.flags & RivianFlags.ANGLE_KIT), self.angle_kit)

  # row 11
  def test_stop_speed(self):
    self.assertEqual(drive_helpers.STOP_SPEED_BRAND, {"rivian": 0.25})
    self.assertEqual(drive_helpers.get_stop_speed(self.CP), 0.25)
    self.assertEqual(longitudinal_planner.LongitudinalPlanner(self.CP, self.CP_SP).stop_speed, 0.25)
    self.assertFalse(drive_helpers.should_stop(0.27, -1., drive_helpers.get_stop_speed(self.CP)))
    self.assertTrue(drive_helpers.should_stop(0.24, -1., drive_helpers.get_stop_speed(self.CP)))
    other = structs.CarParams(brand="toyota")
    self.assertEqual(drive_helpers.get_stop_speed(other), 0.3)

  # rows 12, 13, 14
  def test_long_tune(self):
    self.assertAlmostEqual(self.CP.longitudinalActuatorDelay, 0.35, places=6)
    self.assertEqual(self.CP.stopAccel, 0.)
    self.assertEqual(list(self.CP.longitudinalTuning.kiV), [0.])

  # rows 16, 17 (kit: with the long harness)
  def test_openpilot_long_and_radar(self):
    self.assertTrue(self.CP.openpilotLongitudinalControl)
    self.assertFalse(self.CP.radarUnavailable)


@parameterized_class(("angle_kit",), [(True,), (False,)])
class TestRivianBridge(OpenpilotTestCase):
  angle_kit: bool

  def setUp(self):
    super().setUp()
    self.params = Mock(spec=["put", "get", "get_bool"])
    self.params.get.return_value = 1
    self.params.get_bool.return_value = False
    self.bridge = RivianBridge()
    # yeet-angle-bridged: the HTTP side and the Params live in rivianbridged, card hands its values to the bridge
    self.state = rivianbridged.BridgeState()
    self.bridged = rivianbridged.RivianBridged(self.state, self.params)
    self.CP, self.CP_SP = rivian_params(self.angle_kit)
    with patch("opendbc.car.rivian.carstate.RivianBridge", return_value=self.bridge):
      self.cs = CarState(self.CP, self.CP_SP)
    self.assertIs(self.cs.bridge, self.bridge)
    self.parsers = self.cs.get_can_parsers(self.CP, self.CP_SP)
    if self.angle_kit:
      self.parsers[Bus.alt].vl["WheelButtons_Fwd"]["RightButton_Scroll"] = 255
    self.set_speeds(24., 25.)

  def poll(self, **state):
    """One bridge state through rivianbridged (Params read, written) and its rivianBridgeSP message into card's bridge."""
    data = {"stale": False, "set_speed_ms": 25., "follow_personality": 1, **state}
    self.state.set(data, rivianbridged.DEFAULT_URLS[0], False)
    self.bridged.read_params()
    self.bridged.update_bridge()
    self.bridged.sync_params()
    self.bridge.apply(bridge_values(self.bridged.message().rivianBridgeSP))

  def engage(self, enabled=True):
    self.parsers[Bus.cam].vl["ACM_Status"]["ACM_FeatureStatus"] = int(enabled)

  def set_speeds(self, true_speed, dash_speed):
    self.parsers[Bus.pt].vl["ESP_Status"]["ESP_Vehicle_Speed"] = true_speed * CV.MS_TO_KPH
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_Unit"] = 0
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_VehicleSpeed"] = dash_speed * CV.MS_TO_KPH

  def gas(self, pressed):
    self.parsers[Bus.pt].vl["VDM_PropStatus"]["VDM_AcceleratorPedalPosition"] = 10 if pressed else 0

  def update(self, tsr=0):
    self.parsers[Bus.adas].vl["ACM_tsrCmd"]["ACM_tsrSpdDisClsMain"] = tsr
    return self.cs.update(self.parsers)[0]

  # row 18: yeet-angle-bridged, rivianbridged polls GET /state at 0.1 s with a 1 s timeout when the bridge has no
  # /stream (SSE, the primary source); stale after 2 s polled, 1 s streamed
  def test_poll_interval_and_timeout(self):
    self.assertEqual(rivianbridged.POLL_INTERVAL, 0.1)
    self.assertEqual(rivianbridged.HTTP_TIMEOUT, 1.0)
    self.assertEqual(rivian_bridge.STALE_AFTER, 2.0)
    self.assertEqual(rivianbridged.STREAM_STALE_AFTER, 1.0)
    calls = []
    def urlopen(url, timeout):
      calls.append((url, timeout))
      if url.endswith("/stream"):
        raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
      return io.BytesIO(json.dumps({"stale": False}).encode())
    conn = rivianbridged.BridgeConnection(self.state, ["http://a:1"], urlopen=urlopen, sleep=lambda dt: None)
    conn.step()
    conn.step()
    self.assertEqual(calls, [("http://a:1/stream", 1.0), ("http://a:1/state", 1.0)])

  # row 19: Nebula first, truck LAN fallback, /data override wins, one URL per line
  def test_url_precedence(self):
    nebula, lan = "http://192.168.4.34:8082", "http://172.28.1.64:8082"
    self.assertEqual(rivianbridged.DEFAULT_URLS, (nebula, lan))
    self.assertEqual(rivianbridged.DATA_CONF, Path("/data/rivian-bridge.conf"))
    self.assertEqual(rivianbridged.REPO_CONF, ROOT / "rivian-bridge.conf")
    self.assertEqual(rivianbridged.REPO_CONF.read_text().split(), [nebula, lan])
    with tempfile.TemporaryDirectory() as d:
      repo, data = Path(d) / "repo.conf", Path(d) / "data.conf"
      with patch.object(rivianbridged, "REPO_CONF", repo), patch.object(rivianbridged, "DATA_CONF", data):
        self.assertEqual(rivianbridged.read_bridge_urls(), [nebula, lan])
        repo.write_text("http://repo:2\nhttp://repo:3\n")
        self.assertEqual(rivianbridged.read_bridge_urls(), ["http://repo:2", "http://repo:3"])
        data.write_text("http://data:1\n")
        self.assertEqual(rivianbridged.read_bridge_urls(), ["http://data:1"])

  # row 19: failover one URL per poll, sticks to the last URL that answered
  def test_url_failover(self):
    nebula, lan = rivianbridged.DEFAULT_URLS
    def poll(conn, up):
      calls = []
      def urlopen(url, timeout):
        calls.append(url)
        if url.removesuffix("/state") not in up:
          raise TimeoutError
        return io.BytesIO(json.dumps({"stale": False}).encode())
      conn._urlopen = urlopen
      conn.poll_once()
      return calls
    conn = rivianbridged.BridgeConnection(self.state, [nebula, lan], sleep=lambda dt: None)
    self.assertEqual(poll(conn, {nebula, lan}), [f"{nebula}/state"])
    self.assertEqual(poll(conn, {lan}), [f"{nebula}/state"])
    self.assertEqual(poll(conn, {lan}), [f"{lan}/state"])
    self.assertEqual(poll(conn, {nebula, lan}), [f"{lan}/state"])
    self.assertEqual(poll(conn, {nebula}), [f"{lan}/state"])
    self.assertEqual(poll(conn, {nebula}), [f"{nebula}/state"])
    self.bridged.update_bridge()
    self.assertFalse(self.bridged.stale)

  # row 20: bridge set speed in dash m/s, planner gets the true-speed frame
  def test_set_speed_and_dash_conversion(self):
    self.engage()
    self.poll(set_speed_ms=30.)
    for _ in range(3):
      ret = self.update()
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 30., places=5)
    self.assertAlmostEqual(ret.cruiseState.speed, 30. * 24. / 25., places=5)
    self.assertAlmostEqual(ret.vEgoCluster, 25., places=5)

  # row 20: gas override held until the stalk changes the bridge speed
  def test_gas_override_held_until_stalk_change(self):
    self.engage()
    self.poll(set_speed_ms=25.)
    self.update()
    self.gas(True)
    self.set_speeds(28.8, 30.)
    self.assertAlmostEqual(self.update().cruiseState.speedCluster, 30., places=5)
    self.gas(False)
    self.set_speeds(24., 25.)
    self.assertAlmostEqual(self.update().cruiseState.speedCluster, 30., places=5)
    self.poll(set_speed_ms=25.)
    self.assertAlmostEqual(self.update().cruiseState.speedCluster, 30., places=5)
    # one-unit stalk step (1 kph) is a change
    self.poll(set_speed_ms=25. + CV.KPH_TO_MS)
    self.assertAlmostEqual(self.update().cruiseState.speedCluster, 25. + CV.KPH_TO_MS, places=5)
    # and it ends the override: the bridge target owns the set speed again, so a new sign is ignored
    self.assertAlmostEqual(self.update(tsr=60).cruiseState.speedCluster, 25. + CV.KPH_TO_MS, places=5)

  # rows 10, 21, 22: bridge follow levels 1-4 arrive as personality 0/1/2/2, synced regardless of gas and
  # deduplicated, written only by rivianbridged (never from card's update)
  def test_follow_sync(self):
    for enabled in (False, True):
      self.engage(enabled)
      for level, personality in ((1, 0), (2, 1), (3, 2), (4, 2)):
        with self.subTest(enabled=enabled, level=level):
          self.bridged._last_written_personality = None
          self.params.put.reset_mock()
          self.poll(follow_level=level, follow_personality=personality)
          self.params.put.assert_any_call("LongitudinalPersonality", personality)
          self.params.put.reset_mock()
          ret = self.update()
          self.assertFalse(ret.gasPressed)
          self.params.put.assert_not_called()
          self.poll(follow_level=level, follow_personality=personality)
          self.params.put.assert_not_called()
    for invalid in (-1, 3):
      self.poll(follow_personality=invalid)
      self.assertEqual(self.bridge.follow_personality, -1)

  # row 23: yeet-angle-bridged, the bridge is its own process (normal priority, background cores), not a card thread
  def test_bridge_off_card(self):
    self.assertEqual(rivianbridged.BACKGROUND_CORES, [0, 1, 2, 3])
    for name in ("threading", "urllib", "os"):
      self.assertFalse(hasattr(rivian_bridge, name), name)
    self.assertIn("rivianbridged", managed_processes)

  # rows 24, 25
  def test_set_speed_bounds(self):
    self.assertEqual(carstate_ext.MAX_SET_SPEED, 50.0)
    self.assertEqual(carstate_ext.MIN_SET_SPEED, 1.0)
    self.engage()
    self.poll(set_speed_ms=100.)
    self.assertEqual(self.update().cruiseState.speedCluster, 50.)
    self.engage(False)
    self.poll(stale=True)
    self.set_speeds(0., 0.)
    self.assertEqual(self.update().cruiseState.speedCluster, 1.0)

  # row 27
  def test_traffic_sign_offset(self):
    self.assertEqual(Params().get("TrafficSignOffset", return_default=True), 1)
    sign = 60 * CV.MPH_TO_MS
    for offset in (0, 1, 2, 3):
      with self.subTest(offset=offset):
        self.params.get.return_value = offset
        self.poll(stale=True)
        self.assertEqual(self.bridge.sign_offset, offset)
        self.engage(False)
        self.update()
        self.engage()
        self.cs.sign_speed = 10.
        ret = self.update(tsr=60)
        self.assertAlmostEqual(ret.cruiseState.speedCluster, sign * (1 + 0.05 * offset) if offset else 25., places=5)
    self.params.get.return_value = 1
    self.poll(stale=True)
    # invalid signs, signs more than 9 m/s away, and a fresh bridge target are ignored
    for tsr in (0, 254, 255, 85):
      with self.subTest(tsr=tsr):
        self.engage(False)
        self.update()
        self.engage()
        self.cs.sign_speed = 10.
        self.assertAlmostEqual(self.update(tsr=tsr).cruiseState.speedCluster, 25., places=5)
    self.poll(set_speed_ms=25.)
    self.update()
    self.assertAlmostEqual(self.update(tsr=60).cruiseState.speedCluster, 25., places=5)
    # 253 = unlimited, capped at MAX_SET_SPEED
    self.update(tsr=253)
    self.assertEqual(self.cs.sign_speed, 50.)

  # row 28
  def test_bridge_owns_gap(self):
    if not self.angle_kit:
      self.assertNotIn(Bus.alt, self.parsers)  # stock harness: no scroll wheel at all
      return
    self.poll(follow_personality=2)
    self.parsers[Bus.alt].vl["WheelButtons_Fwd"]["RightButton_Scroll"] = 1
    self.assertEqual(len(self.update().buttonEvents), 0)
    self.poll(stale=True)
    self.parsers[Bus.alt].vl["WheelButtons_Fwd"]["RightButton_Scroll"] = 2
    self.assertEqual([b.type for b in self.update().buttonEvents], ["gapAdjustCruise"])


def run_plant(CP, CP_SP, secs, speed, distance_lead, lead_bp, lead_v, e2e=False, lead=True, cruise=50., desired_accel=None,
              desired_accel_t=0.):
  """Drive the real planner in the maneuver plant, returns (accel, planner source) per step."""
  plant = Plant(lead_relevancy=lead, speed=speed, distance_lead=distance_lead, e2e=e2e)
  plant.planner = planner = longitudinal_planner.LongitudinalPlanner(CP, CP_SP, init_v=speed)
  if desired_accel is not None:
    update = planner.update
    def update_with_model_accel(sm):
      if plant.current_time >= desired_accel_t:
        sm['modelV2'].action.desiredAcceleration = desired_accel
      update(sm)
    planner.update = update_with_model_accel
  out = []
  while plant.current_time < secs:
    plant.step(float(np.interp(plant.current_time, lead_bp, lead_v)), 1.0, cruise)
    out.append((planner.output_a_target, planner.mpc.source))
  return out


@parameterized_class(("angle_kit",), [(True,), (False,)])
class TestRivianHardBrake(OpenpilotTestCase):
  # yeet-angle-brake: -6.5 m/s^2 (~0.66 g) only while the MPC brakes for a present lead
  angle_kit: bool

  def setUp(self):
    super().setUp()
    self.CP, self.CP_SP = rivian_params(self.angle_kit)
    self.assertTrue(self.CP.openpilotLongitudinalControl)

  def test_limits(self):
    self.assertEqual(ACCEL_MIN, -3.5)
    self.assertEqual(CarControllerParams.ACCEL_MIN, -6.5)
    self.assertEqual(drive_helpers.get_lead_accel_min(self.CP), -6.5)
    self.assertEqual(drive_helpers.get_lead_accel_min(structs.CarParams(brand="honda")), ACCEL_MIN)
    self.assertEqual(CarInterface.get_pid_accel_limits(self.CP, self.CP_SP, 30., 30.), (-6.5, 2.0))
    self.assertEqual(longitudinal_planner.LongitudinalPlanner(self.CP, self.CP_SP).lead_accel_min, -6.5)
    src = (ROOT / "opendbc_repo/opendbc/safety/modes/rivian.h").read_text()
    limits = re.search(r"RIVIAN_LONG_LIMITS = \{(.*?)\n  \};", src, re.S).group(1)
    self.assertIn(".min_accel = -650,", limits)
    self.assertIn(".max_accel = 200,", limits)
    # cruise and comfort braking stay
    self.assertEqual(longitudinal_planner.A_CRUISE_MIN, -1.2)
    self.assertEqual(long_mpc.COMFORT_BRAKE, 3.0)

  def test_hard_lead_brake(self):
    # 30 m/s, lead 30 m ahead brakes at 8 m/s^2: the MPC goes past -3.5 for the lead, down to -6.5 and no further
    # (at 6 m/s^2 the aggressive tune, yeet-angle-brake-tune, starts braking early enough to peak at -6.3)
    out = run_plant(self.CP, self.CP_SP, 8., 30., 30., [0., 1., 4.75], [30., 30., 0.])
    accels = [a for a, _ in out]
    self.assertAlmostEqual(min(accels), -6.5, places=3)
    self.assertTrue(all(src in long_mpc.MPC_SOURCES for a, src in out if a < ACCEL_MIN))
    # other brands keep -3.5 in the same maneuver
    honda = self.CP.copy()
    honda.brand = "honda"
    self.assertGreaterEqual(min(a for a, _ in run_plant(honda, self.CP_SP, 8., 30., 30., [0., 1., 4.75], [30., 30., 0.])), ACCEL_MIN)

  def test_no_hard_brake_without_lead(self):
    # cruise drop and force-decel-like slowdowns stay on A_CRUISE_MIN, the MPC without a lead stays on ACCEL_MIN
    out = run_plant(self.CP, self.CP_SP, 5., 30., 200., [0., 5.], [0., 0.], lead=False, cruise=0.)
    self.assertGreaterEqual(min(a for a, _ in out), longitudinal_planner.A_CRUISE_MIN - 1e-6)
    planner = longitudinal_planner.LongitudinalPlanner(self.CP, self.CP_SP)
    self.assertEqual(planner.mpc.a_min, ACCEL_MIN)

  def test_e2e_model_accel_not_extended(self):
    # experimental mode: a model asking for -9 is clipped at -3.5, with or without a (far) lead
    for lead in (False, True):
      out = run_plant(self.CP, self.CP_SP, 3., 30., 150., [0., 3.], [30., 30.], e2e=True, lead=lead, desired_accel=-9.)
      self.assertAlmostEqual(min(a for a, _ in out), ACCEL_MIN, places=6)
      self.assertEqual(out[-1][1], log.LongitudinalPlan.LongitudinalPlanSource.e2e)

  def test_e2e_does_not_cap_lead_braking(self):
    # experimental mode asking for more than the MPC (from 2 s, while it brakes hard for the lead)
    # must not cap the MPC's lead braking at -3.5
    out = run_plant(self.CP, self.CP_SP, 8., 30., 30., [0., 1., 4.75], [30., 30., 0.], e2e=True, desired_accel=-9., desired_accel_t=2.)
    self.assertAlmostEqual(min(a for a, _ in out), -6.5, places=3)
    self.assertTrue(all(src in long_mpc.MPC_SOURCES for a, src in out if a < ACCEL_MIN))

  def test_excessive_actuation_margin(self):
    # same 3.5 m/s^2 margin past the car's limit as stock (-7 for -3.5): -10 for the Rivian, other brands unchanged
    self.assertEqual(ExcessiveActuationCheck(self.CP)._accel_min_excessive, -10.)
    self.assertEqual(ExcessiveActuationCheck(structs.CarParams(brand="honda"))._accel_min_excessive, ACCEL_MIN * 2)
    self.assertEqual(ExcessiveActuationCheck()._accel_min_excessive, ACCEL_MIN * 2)


class TestCruiseAndSteering(OpenpilotTestCase):
  # row 26
  def test_v_cruise_max(self):
    self.assertEqual(cruise.V_CRUISE_MAX, 180)
    self.assertEqual(cruise_ext.V_CRUISE_MAX, 180)
    self.assertEqual(car_interfaces.V_CRUISE_MAX, 180)

  # row 31
  def test_max_steering_angle(self):
    self.assertEqual(MAX_STEERING_ANGLE, 90.0)
    self.assertEqual(TOI_MAX_ANGLE_DEG, 90)

  # row 32
  def test_torque_only_steering_limits(self):
    self.assertEqual(CarControllerParams.STEER_MAX_LOOKUP, ([9, 17], [350, 250]))
    src = (ROOT / "opendbc_repo/opendbc/safety/modes/rivian.h").read_text()
    limits = re.search(r"RIVIAN_TORQUE_ONLY_STEERING_LIMITS = \{(.*?)\n  \};", src, re.S).group(1)
    for field in (".max_torque = 350,", "{9., 17., 17.},", "{350, 250, 250},", ".max_rate_up = 3,", ".max_rate_down = 5,",
                  ".max_rt_delta = 125,", ".driver_torque_multiplier = 2,", ".driver_torque_allowance = 100,"):
      self.assertIn(field, limits)


class TestDriverMonitoring(OpenpilotTestCase):
  # rows 33, 34
  def test_timeouts(self):
    s = DRIVER_MONITOR_SETTINGS()
    self.assertEqual((s._WHEELTOUCH_POLICY_ALERT_1_TIMEOUT, s._WHEELTOUCH_POLICY_ALERT_2_TIMEOUT,
                      s._WHEELTOUCH_POLICY_ALERT_3_TIMEOUT), (115., 124., 130.))
    self.assertEqual((s._VISION_POLICY_ALERT_1_TIMEOUT, s._VISION_POLICY_ALERT_2_TIMEOUT,
                      s._VISION_POLICY_ALERT_3_TIMEOUT), (103., 105., 111.))

  # row 35
  def test_pose_thresholds(self):
    s = DRIVER_MONITOR_SETTINGS()
    self.assertEqual((s._POSE_PITCH_THRESHOLD, s._POSE_PITCH_THRESHOLD_SLACK), (0.7133, 0.7237))
    self.assertEqual((s._POSE_YAW_THRESHOLD, s._POSE_YAW_THRESHOLD_SLACK), (0.7020, 0.8042))


@parameterized_class(("angle_kit",), [(True,), (False,)])
class TestRivianMads(OpenpilotTestCase):
  angle_kit: bool

  # rows 36, 37
  def test_disengage_on_brake_and_no_main_cruise(self):
    CP, CP_SP = rivian_params(self.angle_kit)
    params = Params()
    params.put("MadsSteeringMode", mads_helpers.MadsSteeringModeOnBrake.REMAIN_ACTIVE, block=True)
    self.assertTrue(mads_helpers.get_mads_limited_brands(CP, CP_SP, params))
    self.assertEqual(mads_helpers.read_steering_mode_param(CP, CP_SP, params), mads_helpers.MadsSteeringModeOnBrake.DISENGAGE)
    self.assertIn("rivian", mads_helpers.MADS_NO_ACC_MAIN_BUTTON)
    params.put_bool("MadsMainCruiseAllowed", True, block=True)
    mads_helpers.set_car_specific_params(CP, CP_SP, params)
    self.assertEqual(params.get("MadsSteeringMode"), mads_helpers.MadsSteeringModeOnBrake.DISENGAGE)
    self.assertTrue(params.get_bool("MadsUnifiedEngagementMode"))
    self.assertFalse(params.get_bool("MadsMainCruiseAllowed"))


class TestSafetyCustomizations(OpenpilotTestCase):
  def setUp(self):
    super().setUp()
    self.safety = libsafety_py.libsafety
    self.safety.init_tests()

  # row 38
  def test_mads_requests_lateral_on_op_engage(self):
    self.safety.set_mads_params(True, True, False)
    self.safety.tick_mads_state(True, False, False, False, False)
    self.assertFalse(self.safety.get_controls_allowed_lateral())
    # no ACC main or MADS button on the Rivian: the op engage rising edge alone turns lateral on
    self.safety.tick_mads_state(True, False, True, False, False)
    self.assertTrue(self.safety.get_controls_allowed_lateral())

  # row 41: Rivian and Tesla ignition counters are independent
  def test_rivian_ignition_counter_scoping(self):
    def rivian(counter, on):
      return libsafety_py.make_CANPacket(0x152, 0, bytes([0, counter, 0, 0, 0, 0, 0, (1 if on else 0) << 4]))

    def tesla(counter):
      return libsafety_py.make_CANPacket(0x221, 0, bytes([0, 0, 0, 0, 0, 0, counter << 4, 0]))

    self.safety.set_ignition_can(False)
    self.safety.ignition_can_hook(rivian(0, True))
    self.safety.ignition_can_hook(tesla(7))
    self.safety.ignition_can_hook(tesla(9))
    self.safety.ignition_can_hook(rivian(1, True))
    self.assertTrue(self.safety.get_ignition_can())
    self.safety.ignition_can_hook(rivian(14, False))
    self.safety.ignition_can_hook(rivian(0, False))
    self.assertFalse(self.safety.get_ignition_can())


class TestBootRecovery(OpenpilotTestCase):
  # row 40: run the launcher's recovery block on a fake checkout and cache
  def test_build_corruption_cleanup(self):
    launcher = (ROOT / "launch_chffrplus.sh").read_text()
    block = re.search(r"\n(  # Recover build state.*?)\n\n", launcher, re.S)
    self.assertIsNotNone(block, "boot recovery block missing from launch_chffrplus.sh")
    with tempfile.TemporaryDirectory() as d:
      tree, cache = Path(d) / "openpilot", Path(d) / "scons_cache"
      files = {
        "cache/a.lock": b"", "cache/empty": b"", "cache/good": b"x",
        "tree/x.o": b"", "tree/x.os": b"", "tree/x.so": b"", "tree/x.a": b"", "tree/ok.o": b"x",
        "tree/y.o.tmp": b"x", "tree/y.os.tmp": b"x",
        "tree/third_party/z.so": b"", "tree/.venv/z.so": b"", "tree/.git/z.o": b"", "tree/third_party/z.o.tmp": b"x",
      }
      for name, data in files.items():
        path = (cache if name.startswith("cache/") else tree) / name.split("/", 1)[1]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
      script = block.group(1).replace("/data/scons_cache", str(cache))
      subprocess.run(["bash", "-c", script], env={**os.environ, "DIR": str(tree)}, check=True)
      kept = {f"cache/{p.relative_to(cache)}" for p in cache.rglob("*") if p.is_file()} | \
             {f"tree/{p.relative_to(tree)}" for p in tree.rglob("*") if p.is_file()}
    self.assertEqual(kept, {"cache/good", "tree/ok.o", "tree/third_party/z.so", "tree/.venv/z.so", "tree/.git/z.o",
                            "tree/third_party/z.o.tmp"})


if __name__ == "__main__":
  import unittest
  unittest.main()
