"""Guards for Ryan's yeetfollow customizations on yeetfollow-19 (AGNOS 19.7 base, torque steering, no angle kit).

One test per PARITY.md row, pinning the exact value or behavior. Row numbers match PARITY.md.
See automotive/openpilot#4.
"""
import io
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from openpilot.cereal import log, services
from opendbc.car import Bus, gen_empty_fingerprint, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.rivian import rivian_bridge, values as rivian_values
from opendbc.car.rivian.carstate import CarState
from opendbc.car.rivian.interface import CarInterface
from opendbc.car.rivian.rivian_bridge import RivianBridge
from opendbc.car.rivian.values import CAR, RivianSafetyFlags
from opendbc.safety import ALTERNATIVE_EXPERIENCE
from opendbc.safety.tests.common import CANPackerSafety
from opendbc.safety.tests.libsafety import libsafety_py
from opendbc.sunnypilot.car.rivian import carstate_ext, mads as rivian_mads
from openpilot.common.test import OpenpilotTestCase
from openpilot.selfdrive.car import cruise
from openpilot.selfdrive.controls.lib import drive_helpers, longitudinal_planner
from openpilot.selfdrive.controls.lib.longcontrol import LongControl, LongCtrlState
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib import long_mpc
from openpilot.selfdrive.monitoring.policy import DRIVER_MONITOR_SETTINGS
from openpilot.selfdrive.test.longitudinal_maneuvers import test_longitudinal
from openpilot.sunnypilot.mads import helpers as mads_helpers
from openpilot.sunnypilot.selfdrive.car import cruise_ext

ROOT = Path(__file__).resolve().parents[3]
OPENDBC = ROOT / "opendbc_repo" / "opendbc"
Personality = log.LongitudinalPersonality


def stock_harness_params():
  # Gen1 R1 on the stock harness: no angle kit (0x1310) and no long harness (0x131a)
  fingerprint = gen_empty_fingerprint()
  fingerprint[0][0x321] = 8
  cp = CarInterface.get_params(CAR.RIVIAN_R1, fingerprint, [], False, False, False)
  cp_sp = CarInterface.get_params_sp(cp, CAR.RIVIAN_R1, fingerprint, [], False, False, False)
  return cp, cp_sp


class RivianCarStateCase(OpenpilotTestCase):
  def setUp(self):
    self.cp, self.cp_sp = stock_harness_params()
    self.params = Mock(spec=["put", "get"])
    self.bridge = RivianBridge(params=self.params, start=False)
    with patch("opendbc.car.rivian.carstate.RivianBridge", return_value=self.bridge):
      self.cs = CarState(self.cp, self.cp_sp)
    self.parsers = self.cs.get_can_parsers(self.cp, self.cp_sp)
    self.set_speeds(25., 25.)

  def poll(self, **state):
    data = {"stale": False, "set_speed_ms": 25., "follow_personality": 1, **state}
    with patch.object(rivian_bridge.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(data).encode())):
      self.bridge._poll_once()

  def engage(self, enabled=True):
    self.parsers[Bus.cam].vl["ACM_Status"]["ACM_FeatureStatus"] = int(enabled)

  def set_speeds(self, true_speed, dash_speed):
    self.parsers[Bus.pt].vl["ESP_Status"]["ESP_Vehicle_Speed"] = true_speed * CV.MS_TO_KPH
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_Unit"] = 0
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_VehicleSpeed"] = dash_speed * CV.MS_TO_KPH

  def update(self):
    ret, _ = self.cs.update(self.parsers)
    return ret


# *** Longitudinal / follow-distance tuning ***

class TestLongitudinalTuning(OpenpilotTestCase):
  def test_01_comfort_brake(self):
    self.assertEqual(long_mpc.COMFORT_BRAKE, 3.0)

  def test_02_stop_distance(self):
    self.assertEqual(long_mpc.STOP_DISTANCE, 3.0)

  def test_03_cruise_max_accel(self):
    # no MPC cruise obstacle on this base, the planner clip equals yeetfollow's
    self.assertEqual(longitudinal_planner.A_CRUISE_MAX_VALS, [1.6, 1.2, 0.8, 0.6])
    self.assertFalse(hasattr(long_mpc, "CRUISE_MAX_ACCEL"))

  def test_04_cruise_min_accel(self):
    self.assertEqual(longitudinal_planner.A_CRUISE_MIN, -1.2)

  def test_05_a_change_cost(self):
    self.assertEqual(long_mpc.A_CHANGE_COST, 100.)

  def test_06_danger_zone_cost(self):
    self.assertEqual(long_mpc.DANGER_ZONE_COST, 60.)

  def test_07_lead_danger_factor(self):
    self.assertEqual(long_mpc.LEAD_DANGER_FACTOR, 0.85)

  def test_08_t_follow(self):
    self.assertEqual(long_mpc.get_T_FOLLOW(Personality.aggressive), 0.60)
    self.assertEqual(long_mpc.get_T_FOLLOW(Personality.standard), 1.10)
    self.assertEqual(long_mpc.get_T_FOLLOW(Personality.relaxed), 1.80)

  def test_09_base_mpc_costs(self):
    self.assertEqual(long_mpc.J_EGO_COST, 5.)
    self.assertEqual([long_mpc.get_jerk_factor(p) for p in (Personality.aggressive, Personality.standard, Personality.relaxed)],
                     [0.5, 1.0, 1.0])

  def test_10_personality_mapping(self):
    self.assertEqual((Personality.aggressive, Personality.standard, Personality.relaxed), (0, 1, 2))
    keys = (ROOT / "openpilot/common/params_keys.h").read_text()
    self.assertIn('{"LongitudinalPersonality", {PERSISTENT | BACKUP, INT, std::to_string(static_cast<int>(cereal::LongitudinalPersonality::STANDARD))}}',
                  keys)

  def test_11_rivian_stop_speed(self):
    cp, _ = stock_harness_params()
    self.assertEqual(drive_helpers.get_stop_speed(cp), 0.25)
    self.assertTrue(drive_helpers.should_stop(0.24, 0., drive_helpers.get_stop_speed(cp)))
    self.assertFalse(drive_helpers.should_stop(0.26, 0., drive_helpers.get_stop_speed(cp)))
    self.assertEqual(drive_helpers.get_stop_speed(structs.CarParams(brand="toyota")), 0.3)

  def test_12_rivian_long_actuator_delay(self):
    cp, _ = stock_harness_params()
    self.assertAlmostEqual(cp.longitudinalActuatorDelay, 0.35, places=5)

  def test_13_rivian_stop_accel(self):
    cp, cp_sp = stock_harness_params()
    self.assertEqual(cp.stopAccel, 0.)
    # the stopping state ramps down to stopAccel and holds there
    lc = LongControl(cp, cp_sp)
    cs = structs.CarState(vEgo=0.1)
    for _ in range(200):
      accel = lc.update(True, cs, -1., True, (-3.5, 2.))
    self.assertEqual(lc.long_control_state, LongCtrlState.stopping)
    self.assertEqual(accel, 0.)

  def test_14_rivian_long_ki(self):
    cp, _ = stock_harness_params()
    self.assertEqual(list(cp.longitudinalTuning.kiV), [0.])

  def test_15_stopping_decel_rate_base(self):
    # n/a: base longcontrol hard-codes the stop ramp, kept as is
    src = (ROOT / "openpilot/selfdrive/controls/lib/longcontrol.py").read_text()
    self.assertIn("output_accel -= 1.0 * DT_CTRL", src)

  def test_16_rivian_op_long_always(self):
    cp, _ = stock_harness_params()
    self.assertTrue(cp.openpilotLongitudinalControl)
    self.assertTrue(cp.alphaLongitudinalAvailable)
    self.assertTrue(cp.safetyConfigs[0].safetyParam & RivianSafetyFlags.LONG_CONTROL)

  def test_17_rivian_radar_available(self):
    cp, _ = stock_harness_params()
    self.assertFalse(cp.radarUnavailable)


# *** Rivian bridge, cruise and set speed ***

class TestRivianBridgeCruise(RivianCarStateCase):
  def test_18_bridge_poll_rate_and_timeout(self):
    self.assertEqual(rivian_bridge.POLL_INTERVAL, 0.3)
    with patch.object(rivian_bridge.urllib.request, "urlopen", return_value=io.BytesIO(b"{}")) as get:
      self.bridge._poll_once()
    get.assert_called_once_with(f"{self.bridge.url}/state", timeout=1)

  def test_19_bridge_url_precedence(self):
    self.assertEqual(rivian_bridge.DEFAULT_URL, "http://172.28.1.64:8082")
    self.assertEqual(rivian_bridge.REPO_CONF, ROOT / "rivian-bridge.conf")
    self.assertEqual(rivian_bridge.DATA_CONF, Path("/data/rivian-bridge.conf"))
    self.assertEqual((ROOT / "rivian-bridge.conf").read_text().strip(), "http://172.28.1.64:8082")

  def test_20_bridge_set_speed_and_gas_override(self):
    self.engage()
    self.poll(set_speed_ms=30.)
    ret = self.update()
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 30., places=5)
    # dash-speed setpoint fix: the planner gets the true-speed equivalent
    self.set_speeds(24., 25.)
    for _ in range(3000):
      ret = self.update()
    self.assertAlmostEqual(ret.cruiseState.speed, 30. * 0.96, delta=0.01)
    # gas override is held until the bridge set speed changes
    self.parsers[Bus.pt].vl["VDM_PropStatus"]["VDM_AcceleratorPedalPosition"] = 10
    self.set_speeds(33.6, 35.)
    self.update()
    self.parsers[Bus.pt].vl["VDM_PropStatus"]["VDM_AcceleratorPedalPosition"] = 0
    self.set_speeds(24., 25.)
    self.assertAlmostEqual(self.update().cruiseState.speedCluster, 35., places=5)
    self.poll(set_speed_ms=31.)
    self.assertAlmostEqual(self.update().cruiseState.speedCluster, 31., places=5)

  def test_21_follow_sync_independent_of_gas_and_engagement(self):
    for enabled in (False, True):
      self.engage(enabled)
      for personality in (0, 1, 2):
        self.poll(follow_personality=personality)
        ret = self.update()
        self.assertFalse(ret.gasPressed)
        self.assertEqual(self.bridge._requested_personality, personality)

  def test_22_personality_write_off_control_loop(self):
    self.poll(follow_personality=2)
    self.update()
    self.params.put.assert_not_called()
    self.bridge._sync_personality()
    self.bridge._sync_personality()
    self.params.put.assert_called_once_with("LongitudinalPersonality", 2)

  def test_23_poll_thread_off_rt_cores(self):
    self.assertEqual(rivian_bridge.BACKGROUND_CORES, {0, 1, 2, 3})
    order = []
    with patch.object(rivian_bridge, "_drop_rt_scheduling_for_this_thread", side_effect=lambda: order.append("scheduler")), \
         patch.object(self.bridge, "_poll_once", side_effect=lambda: order.append("http")), \
         patch.object(rivian_bridge.time, "sleep", side_effect=InterruptedError):
      with self.assertRaises(InterruptedError):
        self.bridge._poll_loop()
    self.assertEqual(order[:2], ["scheduler", "http"])

  def test_24_max_set_speed(self):
    self.assertEqual(carstate_ext.MAX_SET_SPEED, 50.)
    self.engage()
    self.poll(set_speed_ms=100.)
    self.assertEqual(self.update().cruiseState.speedCluster, 50.)

  def test_25_min_set_speed(self):
    self.assertEqual(carstate_ext.MIN_SET_SPEED, 1.0)
    self.engage()
    self.poll(set_speed_ms=1.5)
    self.assertEqual(self.update().cruiseState.speedCluster, 1.5)

  def test_26_v_cruise_max_180(self):
    from opendbc.car import interfaces
    self.assertEqual(cruise.V_CRUISE_MAX, 180)
    self.assertEqual(cruise_ext.V_CRUISE_MAX, 180)
    self.assertEqual(interfaces.V_CRUISE_MAX, 180)

  def test_27_traffic_sign_offset(self):
    keys = (ROOT / "openpilot/common/params_keys.h").read_text()
    self.assertIn('{"TrafficSignOffset", {PERSISTENT | BACKUP, INT, "1"}}', keys)
    self.engage()
    self.poll(stale=True)
    self.set_speeds(25., 25.)
    self.cs.set_speed_cluster = 25.
    # a new 55 mph sign within 9 m/s of the set speed moves it to sign + 5 %
    self.parsers[Bus.adas].vl["ACM_tsrCmd"]["ACM_tsrSpdDisClsMain"] = 55
    self.assertAlmostEqual(self.update().cruiseState.speedCluster, 55 * CV.MPH_TO_MS * 1.05, places=5)
    # 255 (invalid) and an unchanged sign leave the driver's choice alone
    self.cs.set_speed_cluster = 20.
    for tsr in (255, 55):
      self.parsers[Bus.adas].vl["ACM_tsrCmd"]["ACM_tsrSpdDisClsMain"] = tsr
      self.assertAlmostEqual(self.update().cruiseState.speedCluster, 20., places=5)
    # Off disables it
    self.bridge.sign_offset = 0
    self.parsers[Bus.adas].vl["ACM_tsrCmd"]["ACM_tsrSpdDisClsMain"] = 45
    self.assertAlmostEqual(self.update().cruiseState.speedCluster, 20., places=5)

  def test_28_gap_from_bridge(self):
    # the stock harness has no gap button on CAN; the bridge personality is the only gap source
    self.assertFalse(self.cp_sp.flags)
    self.assertNotIn(Bus.alt, self.parsers)
    self.poll(follow_personality=0)
    self.assertEqual(len(self.update().buttonEvents), 0)
    self.assertEqual(self.bridge._requested_personality, 0)

  def test_29_no_ui_set_speed_buttons(self):
    self.assertNotIn("uiSetSpeed", services.SERVICE_LIST)

  def test_30_no_wifi_set_speed(self):
    keys = (ROOT / "openpilot/common/params_keys.h").read_text()
    self.assertNotIn('{"setSpeed"', keys)
    self.assertNotIn("UiSetSpeed", services.SERVICE_LIST)

  def test_31_max_steering_angle_90(self):
    self.assertEqual(rivian_mads.MAX_STEERING_ANGLE, 90.)
    ctrl = rivian_mads.MadsCarController()
    cc, cc_sp = structs.CarControl(latActive=True), structs.CarControlSP()
    cc_sp.mads.available = True
    cs = Mock(out=structs.CarState(steeringAngleDeg=89.))
    self.assertTrue(ctrl.mads_status_update(cc, cc_sp, cs).lat_active)
    cs.out.steeringAngleDeg = -90.5
    self.assertFalse(ctrl.mads_status_update(cc, cc_sp, cs).lat_active)


class TestTorqueSteeringSafety(unittest.TestCase):
  """Row 32: yeetfollow torque steering, no angle-kit messages."""

  def setUp(self):
    self.packer = CANPackerSafety("rivian_primary_actuator")
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(structs.CarParams.SafetyModel.rivian, RivianSafetyFlags.LONG_CONTROL)
    self.safety.init_tests()

  def _torque(self, torque, steer_req=1):
    return self.packer.make_can_msg_safety("ACM_lkaHbaCmd", 0, {"ACM_lkaStrToqReq": torque, "ACM_lkaActToi": steer_req})

  def test_32_torque_steering_limits(self):
    cp, _ = stock_harness_params()
    self.assertEqual(cp.steerControlType, structs.CarParams.SteerControlType.torque)
    self.assertEqual(rivian_values.CarControllerParams.STEER_MAX_LOOKUP, ([9, 17], [350, 250]))
    self.safety.set_controls_allowed(True)
    self.assertTrue(self.safety.safety_tx_hook(self._torque(3)))
    self.safety.set_desired_torque_last(0)
    self.safety.set_rt_torque_last(0)
    self.assertFalse(self.safety.safety_tx_hook(self._torque(4)))  # max_rate_up 3
    # no steer-request tolerance: torque without steer_req is blocked
    self.safety.set_desired_torque_last(3)
    self.safety.set_rt_torque_last(3)
    self.assertFalse(self.safety.safety_tx_hook(self._torque(3, steer_req=0)))
    # angle kit messages (ACM_Status, ACM_SteeringControl) are not whitelisted
    for name in ("ACM_Status", "ACM_SteeringControl"):
      self.assertFalse(self.safety.safety_tx_hook(self.packer.make_can_msg_safety(name, 0, {})))

  def test_no_angle_kit_code(self):
    self.assertFalse((OPENDBC / "car/rivian/ext_controller.py").exists())
    self.assertFalse(hasattr(rivian_values.RivianFlags, "ANGLE_KIT"))
    for path in (OPENDBC / "car/rivian").glob("*.py"):
      self.assertNotIn("0x1310", path.read_text(), path)
    self.assertNotIn("angle_kit", (OPENDBC / "safety/modes/rivian.h").read_text())


# *** Driver monitoring ***

class TestDriverMonitoring(OpenpilotTestCase):
  def setUp(self):
    self.s = DRIVER_MONITOR_SETTINGS()

  def test_33_wheel_touch_timeout(self):
    self.assertEqual((self.s._WHEELTOUCH_POLICY_ALERT_1_TIMEOUT, self.s._WHEELTOUCH_POLICY_ALERT_2_TIMEOUT,
                      self.s._WHEELTOUCH_POLICY_ALERT_3_TIMEOUT), (115., 124., 130.))

  def test_34_vision_timeout(self):
    self.assertEqual((self.s._VISION_POLICY_ALERT_1_TIMEOUT, self.s._VISION_POLICY_ALERT_2_TIMEOUT,
                      self.s._VISION_POLICY_ALERT_3_TIMEOUT), (103., 105., 111.))

  def test_35_pose_thresholds(self):
    self.assertEqual((self.s._POSE_PITCH_THRESHOLD, self.s._POSE_PITCH_THRESHOLD_SLACK), (0.7133, 0.7237))
    self.assertEqual((self.s._POSE_YAW_THRESHOLD, self.s._POSE_YAW_THRESHOLD_SLACK), (0.7020, 0.8042))


# *** MADS ***

class TestMads(OpenpilotTestCase):
  def test_36_mads_steering_mode(self):
    keys = (ROOT / "openpilot/common/params_keys.h").read_text()
    self.assertIn('{"MadsSteeringMode", {PERSISTENT | BACKUP, INT, "0"}}', keys)
    self.assertNotIn('"MadsPauseLateralOnBrake"', keys)
    self.assertEqual(ALTERNATIVE_EXPERIENCE.MADS_DISENGAGE_LATERAL_ON_BRAKE, 2048)

  def test_37_rivian_mads_disengage_on_brake(self):
    cp, cp_sp = stock_harness_params()
    params = Mock()
    self.assertIn("rivian", mads_helpers.MADS_NO_ACC_MAIN_BUTTON)
    self.assertTrue(mads_helpers.get_mads_limited_brands(cp, cp_sp, params))
    self.assertEqual(mads_helpers.read_steering_mode_param(cp, cp_sp, params), mads_helpers.MadsSteeringModeOnBrake.DISENGAGE)

  def test_38_mads_lateral_on_op_engage(self):
    src = (OPENDBC / "safety/sunnypilot/mads.h").read_text()
    self.assertIn("(m_mads_state.op_controls_allowed.transition == MADS_EDGE_RISING)", src)

  def test_39_tesla_mads_untouched(self):
    # n/a for the R1S: Tesla keeps the base MADS handling
    self.assertIn("tesla", mads_helpers.MADS_NO_ACC_MAIN_BUTTON)


# *** Boot, build, firmware, repo ***

class TestBootBuildRepo(unittest.TestCase):
  def test_40_boot_recovery(self):
    src = (ROOT / "launch_chffrplus.sh").read_text()
    self.assertIn("rm -f /data/scons_cache/*.lock", src)
    self.assertIn("find /data/scons_cache -type f -size 0 -delete", src)
    self.assertIn("\\( -name '*.o.tmp' -o -name '*.os.tmp' \\) -delete", src)
    self.assertIn("! -path '*/third_party/*' ! -path '*/.venv/*' ! -path '*/.git/*'", src)

  def test_41_ignition_counter_per_brand(self):
    self.assertIn("static int prev_counter_rivian = -1;", (OPENDBC / "safety/ignition.h").read_text())

  def test_42_opendbc_in_tree(self):
    self.assertTrue((OPENDBC / "car/rivian/rivian_bridge.py").is_file())
    self.assertFalse((ROOT / "opendbc_repo/.git").exists())
    # release trees don't ship .gitmodules
    if (ROOT / ".gitmodules").exists():
      self.assertNotIn("opendbc", (ROOT / ".gitmodules").read_text())

  def test_43_mpc_tuning_doc(self):
    doc = (ROOT / "MPC_TUNING.md").read_text()
    for row in ("| COMFORT_BRAKE | 2.5 m/s² | 3.0 m/s² |", "| STOP_DISTANCE | 6.0 m | 3.0 m |",
                "| Rivian stop speed (yeetfollow `vEgoStopping`) | 0.3 m/s | 0.25 m/s |"):
      self.assertIn(row, doc)

  @unittest.skipUnless((ROOT / ".forgejo").is_dir(), "source tree only, release trees exclude .forgejo")
  def test_44_forgejo_prebuilt_ci(self):
    wf = (ROOT / ".forgejo/workflows/prebuilt.yml").read_text()
    self.assertIn("yeetfollow-19", wf)
    self.assertIn("runs-on: linux-arm64", wf)
    self.assertIn("secrets.GH_PREBUILT_TOKEN", wf)
    self.assertIn('PREBUILT_BRANCH="$BRANCH-prebuilt"', (ROOT / ".forgejo/prebuilt/build.sh").read_text())

  def test_45_known_tuning_xfails(self):
    self.assertEqual(test_longitudinal.KNOWN_FAILURE_REASON, "known: yeetfollow tuning, see automotive/openpilot#4")
    self.assertEqual(test_longitudinal.KNOWN_FAILURES, {
      (e2e, False, f'steady state following a car at 20m/s, then lead decel to 0mph at {a}m/s^2')
      for e2e in (True, False) for a in (2, 3)
    })

  def test_46_no_opendbc_task_file(self):
    # n/a: administrative
    self.assertFalse((ROOT / "opendbc_repo/TASK.md").exists())


if __name__ == "__main__":
  unittest.main()
