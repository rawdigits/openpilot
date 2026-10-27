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
import threading
from pathlib import Path
from unittest.mock import Mock, patch

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
from openpilot.selfdrive.test.longitudinal_maneuvers import test_longitudinal
from openpilot.sunnypilot.mads import helpers as mads_helpers
from openpilot.sunnypilot.selfdrive.car import cruise_ext

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

  # row 9
  def test_uncustomized_mpc_costs(self):
    self.assertEqual(long_mpc.J_EGO_COST, 5.)
    self.assertEqual([long_mpc.get_jerk_factor(p) for p in (Personality.aggressive, Personality.standard, Personality.relaxed)],
                     [0.5, 1.0, 1.0])

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

  # row 45
  def test_known_maneuver_failures(self):
    titles = ('steady state following a car at 20m/s, then lead decel to 0mph at 2m/s^2',
              'steady state following a car at 20m/s, then lead decel to 0mph at 3m/s^2')
    self.assertEqual(test_longitudinal.KNOWN_FAILURES, {(e2e, False, t) for e2e in (True, False) for t in titles})


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
    self.params = Mock(spec=["put", "get"])
    self.params.get.return_value = 1
    self.bridge = RivianBridge(params=self.params, start=False)
    self.CP, self.CP_SP = rivian_params(self.angle_kit)
    with patch("opendbc.car.rivian.carstate.RivianBridge", return_value=self.bridge):
      self.cs = CarState(self.CP, self.CP_SP)
    self.assertIs(self.cs.bridge, self.bridge)
    self.parsers = self.cs.get_can_parsers(self.CP, self.CP_SP)
    if self.angle_kit:
      self.parsers[Bus.alt].vl["WheelButtons_Fwd"]["RightButton_Scroll"] = 255
    self.set_speeds(24., 25.)

  def poll(self, **state):
    data = {"stale": False, "set_speed_ms": 25., "follow_personality": 1, **state}
    with patch.object(rivian_bridge.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(data).encode())) as get:
      self.bridge._poll_once()
    return get

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

  # row 18
  def test_poll_interval_and_timeout(self):
    self.assertEqual(rivian_bridge.POLL_INTERVAL, 0.3)
    self.poll().assert_called_once_with(f"{self.bridge.url}/state", timeout=1)

  # row 19
  def test_url_precedence(self):
    self.assertEqual(rivian_bridge.DEFAULT_URL, "http://172.28.1.64:8082")
    self.assertEqual(rivian_bridge.DATA_CONF, Path("/data/rivian-bridge.conf"))
    self.assertEqual(rivian_bridge.REPO_CONF, ROOT / "rivian-bridge.conf")
    self.assertEqual(rivian_bridge.REPO_CONF.read_text().strip(), rivian_bridge.DEFAULT_URL)
    with tempfile.TemporaryDirectory() as d:
      repo, data = Path(d) / "repo.conf", Path(d) / "data.conf"
      with patch.object(rivian_bridge, "REPO_CONF", repo), patch.object(rivian_bridge, "DATA_CONF", data):
        self.assertEqual(rivian_bridge._read_bridge_url(), rivian_bridge.DEFAULT_URL)
        data.write_text("http://data:1\n")
        self.assertEqual(rivian_bridge._read_bridge_url(), "http://data:1")
        repo.write_text("http://repo:2\n")
        self.assertEqual(rivian_bridge._read_bridge_url(), "http://repo:2")

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

  # rows 10, 21, 22: bridge follow levels 1-4 arrive as personality 0/1/2/2, synced
  # every frame regardless of gas, written only from the worker, deduplicated
  def test_follow_sync(self):
    for enabled in (False, True):
      self.engage(enabled)
      for level, personality in ((1, 0), (2, 1), (3, 2), (4, 2)):
        with self.subTest(enabled=enabled, level=level):
          self.bridge._last_written_personality = None
          self.poll(follow_level=level, follow_personality=personality)
          self.params.put.reset_mock()
          ret = self.update()
          self.assertFalse(ret.gasPressed)
          self.params.put.assert_not_called()
          worker = threading.Thread(target=self.bridge._sync_personality)
          worker.start()
          worker.join(timeout=2)
          self.params.put.assert_called_once_with("LongitudinalPersonality", personality)
          self.bridge._sync_personality()
          self.params.put.assert_called_once()
    for invalid in (-1, 3):
      self.poll(follow_personality=invalid)
      self.assertEqual(self.bridge.follow_personality, -1)

  # row 23
  def test_poll_thread_off_rt_cores(self):
    self.assertEqual(rivian_bridge.BACKGROUND_CORES, {0, 1, 2, 3})
    self.assertEqual(rivian_bridge.RT_CORES, {4, 5, 7})
    with patch.object(rivian_bridge.os, "sched_setscheduler") as scheduler, \
         patch.object(rivian_bridge.os, "sched_setaffinity") as affinity, \
         patch.object(rivian_bridge.os, "cpu_count", return_value=8):
      rivian_bridge._drop_rt_scheduling_for_this_thread()
    scheduler.assert_called_once_with(0, os.SCHED_OTHER, os.sched_param(0))
    affinity.assert_called_once_with(0, {0, 1, 2, 3})
    order = []
    with patch.object(rivian_bridge, "_drop_rt_scheduling_for_this_thread", side_effect=lambda: order.append("sched")), \
         patch.object(self.bridge, "_poll_once", side_effect=lambda: order.append("http")), \
         patch.object(rivian_bridge.time, "sleep", side_effect=InterruptedError):
      with self.assertRaises(InterruptedError):
        self.bridge._poll_loop()
    self.assertEqual(order, ["sched", "http"])

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
        self.bridge._read_sign_offset()
        self.assertEqual(self.bridge.sign_offset, offset)
        self.poll(stale=True)
        self.engage(False)
        self.update()
        self.engage()
        self.cs.sign_speed = 10.
        ret = self.update(tsr=60)
        self.assertAlmostEqual(ret.cruiseState.speedCluster, sign * (1 + 0.05 * offset) if offset else 25., places=5)
    self.params.get.return_value = 1
    self.bridge._read_sign_offset()
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
