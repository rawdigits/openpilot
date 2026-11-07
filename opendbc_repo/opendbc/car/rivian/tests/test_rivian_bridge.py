"""Rivian CarState with the TCM bridge values. yeet-angle-bridged: the HTTP side and the Params writes are in
rivianbridged (openpilot/sunnypilot/selfdrive/car/tests/test_rivianbridged.py); here card's plain values only."""
import builtins
import importlib
import sys
import unittest
from unittest.mock import patch

from opendbc.car import Bus, gen_empty_fingerprint
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.rivian import rivian_bridge
from opendbc.car.rivian.carstate import CarState
from opendbc.car.rivian.interface import CarInterface
from opendbc.car.rivian.rivian_bridge import BridgeValues, RivianBridge
from opendbc.car.rivian.values import CAR


def bridge_values(**state) -> BridgeValues:
  """A bridge /state response as rivianbridged hands it to card: stale unless "stale" is exactly False, values raw."""
  values = BridgeValues(stale=state.get("stale", True) is not False)
  for key in ("set_speed_ms", "follow_level", "follow_personality"):
    if key in state:
      setattr(values, key, state[key])
  return values


def poll(bridge: RivianBridge, **state) -> None:
  """One rivianBridgeSP message, keeping the Params values card already has."""
  data = {"stale": False, "set_speed_ms": 25., "follow_personality": 1, **state}
  values = bridge_values(**data)
  for key in ("sign_offset", "button_source", "scroll_invert", "personality_param"):
    setattr(values, key, getattr(bridge.values, key))
  bridge.apply(values)


class TestRivianBridge(unittest.TestCase):
  def setUp(self):
    self.bridge = RivianBridge()
    fingerprint = gen_empty_fingerprint()
    fingerprint[0][0x321] = 8  # Gen1
    fingerprint[1].update({0x1310: 8, 0x131a: 8})  # angle + longitudinal kit
    self.cp = CarInterface.get_params(CAR.RIVIAN_R1, fingerprint, [], True, False, False)
    self.cp_sp = CarInterface.get_params_sp(self.cp, CAR.RIVIAN_R1, fingerprint, [], True, False, False)
    with patch("opendbc.car.rivian.carstate.RivianBridge", return_value=self.bridge):
      self.cs = CarState(self.cp, self.cp_sp)
    self.parsers = self.cs.get_can_parsers(self.cp, self.cp_sp)
    self.parsers[Bus.alt].vl["WheelButtons_Fwd"]["RightButton_Scroll"] = 255
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_Unit"] = 0
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_VehicleSpeed"] = 72

  def poll(self, **state):
    poll(self.bridge, **state)

  def engage(self, enabled=True):
    self.parsers[Bus.cam].vl["ACM_Status"]["ACM_FeatureStatus"] = int(enabled)

  def set_ego_speeds(self, true_speed, dash_speed, metric=True):
    self.parsers[Bus.pt].vl["ESP_Status"]["ESP_Vehicle_Speed"] = true_speed * CV.MS_TO_KPH
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_Unit"] = 0 if metric else 1
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_VehicleSpeed"] = dash_speed * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH)

  def test_speed_frames_bridge_target(self):
    self.engage()
    self.poll(set_speed_ms=30.)
    for metric in (True, False):
      with self.subTest(metric=metric):
        self.set_ego_speeds(24., 25., metric)
        ret, _ = self.cs.update(self.parsers)
        self.assertAlmostEqual(ret.cruiseState.speed, 30. * 0.96, places=5)
        self.assertAlmostEqual(ret.cruiseState.speedCluster, 30., places=5)
        self.assertAlmostEqual(ret.vEgoRaw, 24., places=5)
        self.assertAlmostEqual(ret.vEgo, 24., places=5)
        self.assertAlmostEqual(ret.vEgoCluster, 25., places=5)

  def test_speed_frames_gas_override(self):
    self.engage()
    self.poll(set_speed_ms=25.)
    self.set_ego_speeds(24., 25.)
    self.cs.update(self.parsers)
    self.parsers[Bus.pt].vl["VDM_PropStatus"]["VDM_AcceleratorPedalPosition"] = 10
    # Dash speed exceeds the dash target even though true speed is below it.
    self.set_ego_speeds(24.96, 26.)
    ret, _ = self.cs.update(self.parsers)
    self.assertAlmostEqual(ret.cruiseState.speed, 24.96, places=5)
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 26., places=5)
    self.set_ego_speeds(28.8, 30.)
    ret, _ = self.cs.update(self.parsers)
    self.assertAlmostEqual(ret.cruiseState.speed, 28.8, places=5)
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 30., places=5)
    self.parsers[Bus.pt].vl["VDM_PropStatus"]["VDM_AcceleratorPedalPosition"] = 0
    self.set_ego_speeds(24., 25.)
    ret, _ = self.cs.update(self.parsers)
    self.assertAlmostEqual(ret.cruiseState.speed, 28.8, places=5)
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 30., places=5)
    self.poll(set_speed_ms=27.)
    ret, _ = self.cs.update(self.parsers)
    self.assertAlmostEqual(ret.cruiseState.speed, 27. * 0.96, places=5)
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 27., places=5)

  def test_speed_frames_single_unit_bridge_changes(self):
    self.engage()
    self.set_ego_speeds(25., 25.)
    self.poll(set_speed_ms=30.)
    self.cs.update(self.parsers)
    for step in (CV.KPH_TO_MS, CV.MPH_TO_MS):
      for dash_target in (30. + step, 30.):
        with self.subTest(step=step, dash_target=dash_target):
          self.poll(set_speed_ms=dash_target)
          ret, _ = self.cs.update(self.parsers)
          self.assertAlmostEqual(ret.cruiseState.speed, dash_target, places=5)
          self.assertAlmostEqual(ret.cruiseState.speedCluster, dash_target, places=5)

  def test_speed_frames_hold_ratio_at_low_speed(self):
    self.engage()
    self.poll(set_speed_ms=30.)
    self.set_ego_speeds(24., 25.)
    self.cs.update(self.parsers)
    for true_speed, dash_speed in ((4., 5.), (5., 6.), (6., 5.), (0., 0.), (24., 0.)):
      with self.subTest(true_speed=true_speed, dash_speed=dash_speed):
        self.set_ego_speeds(true_speed, dash_speed)
        for _ in range(20):
          ret, _ = self.cs.update(self.parsers)
        self.assertAlmostEqual(ret.cruiseState.speed, 30. * 0.96, places=5)
        self.assertAlmostEqual(ret.cruiseState.speedCluster, 30., places=5)

  def test_speed_frames_startup_fallback(self):
    self.engage()
    self.poll(set_speed_ms=30.)
    for true_speed, dash_speed in ((0., 0.), (4., 5.)):
      with self.subTest(true_speed=true_speed, dash_speed=dash_speed):
        self.set_ego_speeds(true_speed, dash_speed)
        ret, _ = self.cs.update(self.parsers)
        self.assertAlmostEqual(ret.cruiseState.speed, 30., places=5)
        self.assertAlmostEqual(ret.cruiseState.speedCluster, 30., places=5)

  def test_speed_frames_filter(self):
    self.engage()
    self.poll(set_speed_ms=30.)
    self.set_ego_speeds(24., 25.)
    self.cs.update(self.parsers)
    self.set_ego_speeds(23., 25.)
    ret, _ = self.cs.update(self.parsers)
    self.assertGreater(ret.cruiseState.speed, 30. * 0.92)
    self.assertLess(ret.cruiseState.speed, 30. * 0.96)
    for _ in range(3000):  # 30 s at 100 Hz: converge without changing the dash target
      ret, _ = self.cs.update(self.parsers)
    self.assertAlmostEqual(ret.cruiseState.speed, 30. * 0.92, delta=0.01)
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 30., places=5)

  def test_speed_frames_ratio_bounds(self):
    self.engage()
    self.poll(set_speed_ms=30.)
    self.set_ego_speeds(20., 25.)
    ret, _ = self.cs.update(self.parsers)
    self.assertAlmostEqual(ret.cruiseState.speed, 30. * 0.90, places=5)
    self.set_ego_speeds(30., 25.)
    for _ in range(6000):
      ret, _ = self.cs.update(self.parsers)
      self.assertLessEqual(ret.cruiseState.speed, 30.)
    self.assertAlmostEqual(ret.cruiseState.speed, 30., places=4)
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 30., places=5)

  def test_speed_frames_kit_buttons_and_stalk(self):
    self.engage()
    self.poll(set_speed_ms=25.)
    for metric in (True, False):
      with self.subTest(metric=metric):
        # Reengagement reapplies the bridge target in dash units.
        self.engage(False)
        self.cs.update(self.parsers)
        self.engage()
        self.set_ego_speeds(24., 25., metric)
        self.cs.update(self.parsers)
        buttons = self.parsers[Bus.alt].vl["WheelButtons_Fwd"]
        buttons["RightButton_RightClick"] = 2
        ret, _ = self.cs.update(self.parsers)
        # yeet-angle-standalone: the bridge has a target, so it alone applies the press (no double handling)
        dash_target = 25.
        self.assertAlmostEqual(ret.cruiseState.speed, dash_target * 0.96, places=5)
        self.assertAlmostEqual(ret.cruiseState.speedCluster, dash_target, places=5)
        buttons["RightButton_RightClick"] = 0
        self.parsers[Bus.pt].vl["VDM_AdasSts"]["VDM_UserAdasRequest"] = 3
        self.set_ego_speeds(28.8, 30., metric)
        ret, _ = self.cs.update(self.parsers)
        self.assertAlmostEqual(ret.cruiseState.speed, 28.8, places=5)
        self.assertAlmostEqual(ret.cruiseState.speedCluster, 30., places=5)
        self.parsers[Bus.pt].vl["VDM_AdasSts"]["VDM_UserAdasRequest"] = 0

  def test_bridge_speed_gas_override_and_reengage(self):
    self.engage()
    self.poll()
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(ret.cruiseState.speed, 25.)
    self.parsers[Bus.pt].vl["VDM_PropStatus"]["VDM_AcceleratorPedalPosition"] = 10
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_VehicleSpeed"] = 108
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(ret.cruiseState.speed, 30.)
    self.parsers[Bus.pt].vl["VDM_PropStatus"]["VDM_AcceleratorPedalPosition"] = 0
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(ret.cruiseState.speed, 30.)
    self.poll(set_speed_ms=27.)
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(ret.cruiseState.speed, 27.)
    self.engage(False)
    self.cs.update(self.parsers)
    self.engage()
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(ret.cruiseState.speed, 27.)

  def test_kit_speed_buttons_suppressed_stalk_still_works(self):
    # yeet-angle-standalone: with a fresh bridge target the wheel buttons no longer change the set speed themselves
    self.engage()
    self.poll()
    self.cs.update(self.parsers)
    buttons = self.parsers[Bus.alt].vl["WheelButtons_Fwd"]
    buttons["RightButton_RightClick"] = 2
    ret, _ = self.cs.update(self.parsers)
    self.assertAlmostEqual(ret.cruiseState.speed, 25., places=5)
    buttons["RightButton_RightClick"] = 0
    ret, _ = self.cs.update(self.parsers)
    self.assertAlmostEqual(ret.cruiseState.speed, 25., places=5)
    self.parsers[Bus.pt].vl["VDM_AdasSts"]["VDM_UserAdasRequest"] = 3
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_VehicleSpeed"] = 108
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(ret.cruiseState.speed, 30.)

  def test_speed_validation_and_kit_clamp(self):
    self.engage()
    self.poll(set_speed_ms=100.)
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(ret.cruiseState.speed, 50.)
    for invalid in (None, "30", -1., float("nan"), float("inf"), True):
      self.poll(set_speed_ms=invalid)
      ret, _ = self.cs.update(self.parsers)
      self.assertEqual(ret.cruiseState.speed, 50.)

  def test_stale_values_do_not_update(self):
    self.engage()
    self.poll()
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(ret.cruiseState.speed, 25.)
    for stale in (True, "false", None):
      self.poll(stale=stale, set_speed_ms=30., follow_personality=2)
      ret, _ = self.cs.update(self.parsers)
      self.assertEqual(ret.cruiseState.speed, 25.)
    # card's own message timeout (rivianbridged gone): stale, whatever the last message said
    self.poll(set_speed_ms=30.)
    self.bridge.message_stale = True
    self.assertTrue(self.bridge.stale)
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(ret.cruiseState.speed, 25.)
    self.bridge.message_stale = False
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(ret.cruiseState.speed, 30.)

  def test_defaults_before_first_message(self):
    bridge = RivianBridge()
    self.assertTrue(bridge.stale)
    self.assertEqual((bridge.set_speed_ms, bridge.follow_level, bridge.follow_personality, bridge.bridge_personality),
                     (0, -1, -1, -1))
    self.assertEqual((bridge.sign_offset, bridge.button_source, bridge.scroll_invert, bridge.personality_param),
                     (1, rivian_bridge.ButtonSource.AUTO, False, None))

  def test_value_validation(self):
    for level in (0, 5, -1, "2", 2.0, True, None):
      self.poll(follow_level=level)
      self.assertEqual(self.bridge.follow_level, -1)
    for personality in (-1, 3, "1", None, True, 1.0):
      self.poll(follow_personality=personality)
      self.assertEqual(self.bridge.follow_personality, -1)
    for level, personality in ((1, 0), (2, 1), (3, 2), (4, 2)):
      self.poll(follow_level=level, follow_personality=0)
      self.assertEqual(self.bridge.bridge_personality, personality)
    self.poll(follow_personality=2)
    self.assertEqual(self.bridge.bridge_personality, 2)

  def test_gap_event_has_only_one_owner(self):
    self.poll(follow_personality=2)
    buttons = self.parsers[Bus.alt].vl["WheelButtons_Fwd"]
    buttons["RightButton_Scroll"] = 1
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(len(ret.buttonEvents), 0)
    self.poll(stale=True)
    buttons["RightButton_Scroll"] = 2
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(len(ret.buttonEvents), 1)
    self.assertEqual(ret.buttonEvents[0].type, "gapAdjustCruise")
    # no valid personality: the native gap cycling is back
    self.poll(follow_personality=None)
    buttons["RightButton_Scroll"] = 3
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(len(ret.buttonEvents), 1)

  def test_comma_level_published_for_rivianbridged(self):
    # Bridge source: nothing for rivianbridged to write from the wheel
    self.bridge.button_source = rivian_bridge.ButtonSource.BRIDGE
    self.poll(follow_level=3)
    _, ret_sp = self.cs.update(self.parsers)
    self.assertEqual((ret_sp.rivianCommaGap, ret_sp.rivianCommaFollowLevel), (False, 0))
    # Comma (kit wheel buttons forwarded): the wheel's level, starting at the fresh bridge's
    self.bridge.button_source = rivian_bridge.ButtonSource.AUTO
    vl_all = self.parsers[Bus.alt].vl_all["WheelButtons_Fwd"]
    self.parsers[Bus.alt].vl["WheelButtons_Fwd"]["RightButton_Scroll"] = 10
    vl_all["RightButton_Scroll"] = [10]
    _, ret_sp = self.cs.update(self.parsers)
    self.assertEqual((ret_sp.rivianCommaGap, ret_sp.rivianCommaFollowLevel), (True, 3))
    self.parsers[Bus.alt].vl["WheelButtons_Fwd"]["RightButton_Scroll"] = 11
    vl_all["RightButton_Scroll"] = [11]
    _, ret_sp = self.cs.update(self.parsers)
    self.assertEqual((ret_sp.rivianCommaGap, ret_sp.rivianCommaFollowLevel), (True, 4))

  def test_no_io_on_the_card_path(self):
    # The Rivian CarState path (rivian_bridge, carstate) must not import or call Params, urllib, sockets or files, and
    # must not start threads or take locks: a fresh import and 200 updates with every guard tripping on use.
    forbidden = ("urllib", "socket", "http", "threading", "openpilot.common.params", "openpilot")
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
      if any(name == f or name.startswith(f + ".") for f in forbidden):
        raise AssertionError(f"card path imported {name}")
      return real_import(name, *args, **kwargs)

    saved = {k: sys.modules.pop(k) for k in ("opendbc.car.rivian.rivian_bridge",)}
    try:
      with patch.object(builtins, "__import__", guarded_import):
        module = importlib.import_module("opendbc.car.rivian.rivian_bridge")
      for name in ("urllib", "threading", "json", "os", "Path", "Params"):
        self.assertFalse(hasattr(module, name), name)
    finally:
      sys.modules.update(saved)

    def fail(*args, **kwargs):
      raise AssertionError("I/O on the card path")
    with patch("builtins.open", fail), patch("socket.socket", fail), patch("threading.Thread.start", fail), \
         patch("urllib.request.urlopen", fail), patch.object(builtins, "__import__", guarded_import):
      self.engage()
      self.poll(follow_level=2)
      for i in range(200):
        if i == 100:
          self.poll(stale=True)
        self.cs.update(self.parsers)

  def test_stock_long_has_no_bridge(self):
    self.cp.openpilotLongitudinalControl = False
    cs = CarState(self.cp, self.cp_sp)
    self.assertIsNone(cs.bridge)


if __name__ == "__main__":
  unittest.main()
