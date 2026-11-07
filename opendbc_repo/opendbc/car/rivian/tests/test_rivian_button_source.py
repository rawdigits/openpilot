"""yeet-angle-standalone: RivianButtonSource (Auto / Comma / Bridge) and the directional scroll-wheel gap."""
import io
import json
import threading
import unittest
from unittest.mock import Mock, patch

from opendbc.car import Bus, gen_empty_fingerprint, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.rivian import rivian_bridge
from opendbc.car.rivian.carstate import CarState
from opendbc.car.rivian.interface import CarInterface
from opendbc.car.rivian.rivian_bridge import ButtonSource, RivianBridge
from opendbc.car.rivian.values import CAR
from opendbc.sunnypilot.car.rivian.carstate_ext import BUTTONS_TIMEOUT_FRAMES, scroll_delta

GAP = structs.CarState.ButtonEvent.Type.gapAdjustCruise


class TestRivianButtonSource(unittest.TestCase):
  def setUp(self):
    self.params = Mock(spec=["put"])
    self.bridge = RivianBridge(params=self.params, start=False)
    fingerprint = gen_empty_fingerprint()
    fingerprint[0][0x321] = 8  # Gen1
    fingerprint[1].update({0x1310: 8, 0x131a: 8})  # angle + longitudinal kit
    self.cp = CarInterface.get_params(CAR.RIVIAN_R1, fingerprint, [], True, False, False)
    self.cp_sp = CarInterface.get_params_sp(self.cp, CAR.RIVIAN_R1, fingerprint, [], True, False, False)
    with patch("opendbc.car.rivian.carstate.RivianBridge", return_value=self.bridge):
      self.cs = CarState(self.cp, self.cp_sp)
    self.parsers = self.cs.get_can_parsers(self.cp, self.cp_sp)
    self.buttons = self.parsers[Bus.alt].vl["WheelButtons_Fwd"]
    self.buttons["RightButton_Scroll"] = 255
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_Unit"] = 0
    self.set_ego_speeds(25., 25.)

  def set_ego_speeds(self, true_speed, dash_speed):
    self.parsers[Bus.pt].vl["ESP_Status"]["ESP_Vehicle_Speed"] = true_speed * CV.MS_TO_KPH
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_VehicleSpeed"] = dash_speed * CV.MS_TO_KPH

  def poll(self, **state):
    data = {"stale": False, "set_speed_ms": 25., "follow_personality": 1, **state}
    with patch.object(rivian_bridge.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(data).encode())):
      self.bridge._poll_once()

  def engage(self, enabled=True):
    self.parsers[Bus.cam].vl["ACM_Status"]["ACM_FeatureStatus"] = int(enabled)

  def step(self, scroll=None, right=0, left=0, received=True):
    """One 100 Hz frame. received: a WheelButtons_Fwd frame arrived this cycle (vl_all), as from the kit at ~20 Hz."""
    if scroll is not None:
      self.buttons["RightButton_Scroll"] = scroll
    self.buttons["RightButton_RightClick"] = right
    self.buttons["RightButton_LeftClick"] = left
    vl_all = self.parsers[Bus.alt].vl_all["WheelButtons_Fwd"]
    vl_all.clear()
    if received:
      vl_all["RightButton_Scroll"] = [self.buttons["RightButton_Scroll"]]
    ret, _ = self.cs.update(self.parsers)
    return ret

  def gap_events(self, ret):
    return [b for b in ret.buttonEvents if b.type == GAP]

  def run_poll_thread_once(self):
    worker = threading.Thread(target=lambda: (self.bridge._sync_personality(), self.bridge._sync_follow_level()))
    worker.start()
    worker.join(timeout=2)
    self.assertFalse(worker.is_alive())

  def writes(self, key):
    return [c.args[1] for c in self.params.put.call_args_list if c.args[0] == key]

  # *** source selection ***

  def test_auto_with_forwarded_buttons_is_comma(self):
    self.poll()
    with self.assertLogs(rivian_bridge.carlog, "WARNING") as logs:
      self.step(scroll=10)
    self.assertEqual(self.cs.button_source, "comma")
    self.assertTrue(self.bridge.comma_gap)
    self.assertIn("rivian buttons: source=comma reason=auto, forwarded buttons", logs.output[-1])

  def test_auto_without_forwarded_buttons_is_bridge(self):
    self.poll()
    for received in (False, True):  # nothing at all, or the kit sending only invalid (255) scroll counters
      with self.subTest(received=received):
        self.step(scroll=255, received=received)
        self.assertEqual(self.cs.button_source, "bridge")
        self.assertFalse(self.bridge.comma_gap)

  def test_auto_without_kit_harness_is_bridge(self):
    self.cp_sp.flags = 0
    with patch("opendbc.car.rivian.carstate.RivianBridge", return_value=self.bridge):
      cs = CarState(self.cp, self.cp_sp)
    cs.update_forwarded_buttons(self.parsers)
    cs.update_button_source()
    self.assertFalse(cs.forwarded_buttons)
    self.assertEqual(cs.button_source, "bridge")

  def test_auto_falls_back_after_buttons_timeout(self):
    self.poll()
    self.step(scroll=10)
    self.assertEqual(self.cs.button_source, "comma")
    for _ in range(BUTTONS_TIMEOUT_FRAMES):
      self.step(received=False)
    self.assertEqual(self.cs.button_source, "comma")  # within ~1 s
    with self.assertLogs(rivian_bridge.carlog, "WARNING") as logs:
      self.step(received=False)
    self.assertEqual(self.cs.button_source, "bridge")
    self.assertIn("source=bridge reason=auto, no forwarded buttons", logs.output[-1])
    # and back once they return
    self.step(scroll=11)
    self.assertEqual(self.cs.button_source, "comma")

  def test_forced_bridge_with_forwarded_buttons(self):
    self.bridge.button_source = ButtonSource.BRIDGE
    self.poll()
    ret = self.step(scroll=10)
    self.assertEqual(self.cs.button_source, "bridge")
    self.assertFalse(self.bridge.comma_gap)
    self.assertEqual(self.gap_events(ret), [])  # the bridge (fresh, with a gap) owns it

  def test_forced_comma(self):
    self.bridge.button_source = ButtonSource.COMMA
    self.poll()
    self.step(scroll=10)
    self.assertEqual(self.cs.button_source, "comma")

  def test_forced_comma_without_buttons_falls_back_once(self):
    self.bridge.button_source = ButtonSource.COMMA
    self.poll()
    with self.assertLogs(rivian_bridge.carlog, "WARNING") as logs:
      for _ in range(50):
        self.step(scroll=255, received=False)
    self.assertEqual(self.cs.button_source, "bridge")
    self.assertEqual(logs.output, ["WARNING:carlog:rivian buttons: source=bridge reason=comma selected but no forwarded buttons"])

  def test_source_param_read_from_poll_thread(self):
    params = Mock(spec=["put", "get", "get_bool"])
    params.get.side_effect = lambda key, return_default=False: {"RivianButtonSource": 2, "TrafficSignOffset": 1,
                                                               "LongitudinalPersonality": 0}[key]
    params.get_bool.side_effect = lambda key: key == "RivianScrollInvert"
    bridge = RivianBridge(params=params, start=False)
    bridge._read_button_params()
    self.assertEqual((bridge.button_source, bridge.scroll_invert, bridge.personality_param), (ButtonSource.BRIDGE, True, 0))
    params.get.side_effect = lambda key, return_default=False: {"RivianButtonSource": 7, "LongitudinalPersonality": None}[key]
    bridge._read_button_params()  # invalid values keep the last good ones
    self.assertEqual((bridge.button_source, bridge.personality_param), (ButtonSource.BRIDGE, 0))

  # *** set speed ***

  def test_bridge_fresh_suppresses_comma_speed_buttons(self):
    self.bridge.button_source = ButtonSource.BRIDGE
    self.engage()
    self.poll(set_speed_ms=25.)
    self.step(scroll=10)
    for frames, kwargs in ((1, {"right": 2}), (1, {}), (1, {"left": 2}), (1, {}), (200, {"right": 2}), (200, {"left": 2})):
      for _ in range(frames):
        ret = self.step(**kwargs)
        self.assertAlmostEqual(ret.cruiseState.speedCluster, 25., places=5)
    # the bridge's own (the truck's) reaction to the press is what moves it
    self.poll(set_speed_ms=26.)
    ret = self.step()
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 26., places=5)

  def test_bridge_without_target_keeps_comma_speed_buttons(self):
    self.bridge.button_source = ButtonSource.BRIDGE
    self.poll(set_speed_ms=0)
    self.step(scroll=10)
    self.engage()
    ret = self.step(right=2)
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 25. + CV.KPH_TO_MS, places=5)

  def test_bridge_stale_falls_back_to_comma_speed_buttons(self):
    for source in (ButtonSource.AUTO, ButtonSource.BRIDGE):
      with self.subTest(source=source):
        self.setUp()
        self.bridge.button_source = source
        self.poll(set_speed_ms=25.)
        self.step(scroll=255, received=False)
        self.engage()
        self.poll(stale=True)
        self.step(scroll=255, received=False)
        ret = self.step(scroll=255, received=False, right=2)
        self.assertAlmostEqual(ret.cruiseState.speedCluster, 25. + CV.KPH_TO_MS, places=5)
        ret = self.step(scroll=255, received=False)
        # hold: next 10 kph multiple after 66 frames (0.66 s)
        for _ in range(66):
          ret = self.step(scroll=255, received=False, right=2)
        self.assertAlmostEqual(ret.cruiseState.speedCluster, 100. * CV.KPH_TO_MS, places=5)

  def test_comma_ignores_bridge_set_speed(self):
    self.poll(set_speed_ms=25.)
    self.step(scroll=10)  # disengaged: set speed follows the dash speed (25)
    self.engage()
    self.assertEqual(self.cs.button_source, "comma")
    ret = self.step(right=2)
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 25. + CV.KPH_TO_MS, places=5)
    self.step()
    for bridge_speed in (30., 20.):
      self.poll(set_speed_ms=bridge_speed)
      ret = self.step()
      self.assertAlmostEqual(ret.cruiseState.speedCluster, 25. + CV.KPH_TO_MS, places=5)
    ret = self.step(left=2)
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 25., places=5)

  def test_comma_engage_and_stalk(self):
    self.poll(set_speed_ms=30.)
    self.set_ego_speeds(22., 22.)
    self.step(scroll=10)
    self.engage()
    ret = self.step()
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 22., places=5)  # engage = current speed, not the bridge's 30
    self.parsers[Bus.pt].vl["VDM_AdasSts"]["VDM_UserAdasRequest"] = 3
    self.set_ego_speeds(24., 24.)
    ret = self.step()
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 24., places=5)

  def test_comma_sign_offset_still_applies(self):
    self.poll(set_speed_ms=30.)
    self.step(scroll=10)
    self.engage()
    self.bridge.sign_offset = 2  # +10 %
    self.parsers[Bus.adas].vl["ACM_tsrCmd"]["ACM_tsrSpdDisClsMain"] = 55  # mph, within 9 m/s of 25 m/s
    ret = self.step()
    self.assertAlmostEqual(ret.cruiseState.speedCluster, 55 * CV.MPH_TO_MS * 1.1, places=5)

  # *** gap ***

  def test_scroll_delta_wraparound(self):
    for prev, cur, delta in ((10, 11, 1), (11, 10, -1), (254, 0, 2), (0, 254, -2), (255, 0, 1), (0, 255, -1), (253, 1, 4), (1, 253, -4), (5, 5, 0)):
      with self.subTest(prev=prev, cur=cur):
        self.assertEqual(scroll_delta(prev, cur), delta)

  def comma_at_level(self, level, scroll=100):
    self.poll(follow_level=level)
    self.step(scroll=scroll)
    self.assertEqual(self.cs.button_source, "comma")
    self.assertEqual(self.bridge.comma_follow_level, level)

  def test_initial_level_from_fresh_bridge(self):
    self.comma_at_level(3)

  def test_initial_level_from_personality(self):
    self.poll(stale=True)
    for personality, level in ((0, 1), (1, 2), (2, 4)):
      with self.subTest(personality=personality):
        self.bridge.comma_follow_level = 0
        self.bridge.personality_param = personality
        self.step(scroll=50)
        self.assertEqual(self.bridge.comma_follow_level, level)

  def test_first_sample_and_invalid_are_not_steps(self):
    self.poll(follow_level=2)
    with self.assertLogs(rivian_bridge.carlog, "WARNING") as logs:
      self.step(scroll=200)  # first sample: reference only
      self.step(scroll=255)  # invalid
      self.step(scroll=200)
    self.assertEqual(self.bridge.comma_follow_level, 2)
    self.assertFalse(any("gap delta" in line for line in logs.output))

  def test_scroll_steps_direction_wrap_and_invert(self):
    for invert in (False, True):
      # from level 2: (start, scroll, level, inverted level); 0 -> 254 is two steps down across the wrap
      for start, scroll, normal, inverted in ((253, 254, 3, 1), (0, 254, 1, 4), (100, 101, 3, 1), (101, 100, 1, 3)):
        with self.subTest(invert=invert, start=start, scroll=scroll):
          self.setUp()
          self.bridge.scroll_invert = invert
          self.comma_at_level(2, scroll=start)
          with self.assertLogs(rivian_bridge.carlog, "WARNING") as logs:
            ret = self.step(scroll=scroll)
          want = inverted if invert else normal
          self.assertEqual(self.bridge.comma_follow_level, want)
          self.assertEqual(self.gap_events(ret), [])
          delta = scroll_delta(start, scroll)
          self.assertIn(f"rivian buttons: gap delta={delta} invert={invert} level=2->{want}", logs.output[-1])

  def test_clamp_no_wrap(self):
    self.comma_at_level(3, scroll=250)
    for scroll in (251, 252, 253, 254, 255, 0, 1):  # up, farther; 255 is skipped
      self.step(scroll=scroll)
    self.assertEqual(self.bridge.comma_follow_level, 4)
    for scroll in (0, 255, 254, 253, 252, 251, 250, 249, 248):
      self.step(scroll=scroll)
    self.assertEqual(self.bridge.comma_follow_level, 1)
    self.step(scroll=240)  # a multi-step jump still clamps
    self.assertEqual(self.bridge.comma_follow_level, 1)

  def test_comma_writes_level_and_personality_like_the_bridge(self):
    self.comma_at_level(2)
    # LongitudinalPersonality written on change only: levels 3 and 4 share personality 2
    for scroll, level, personalities in ((101, 3, [2]), (102, 4, []), (101, 3, []), (100, 2, [1]), (99, 1, [0])):
      with self.subTest(level=level):
        self.params.reset_mock()
        self.step(scroll=scroll)
        self.params.put.assert_not_called()  # no I/O in the control loop
        self.run_poll_thread_once()
        self.assertEqual(self.writes("RivianFollowLevel"), [level])
        self.assertEqual(self.writes("LongitudinalPersonality"), personalities)
    # the bridge's own level and personality are ignored while Comma owns the gap
    self.params.reset_mock()
    self.poll(follow_level=4, follow_personality=2)
    self.step(scroll=99)
    self.run_poll_thread_once()
    self.assertEqual(self.writes("RivianFollowLevel"), [])
    self.assertEqual(self.writes("LongitudinalPersonality"), [])

  def test_comma_level_kept_without_bridge(self):
    self.poll(stale=True)
    self.bridge.personality_param = 1
    self.step(scroll=10)
    self.step(scroll=11)
    self.run_poll_thread_once()
    self.assertEqual(self.writes("RivianFollowLevel"), [3])
    self.assertEqual(self.writes("LongitudinalPersonality"), [2])

  def test_no_gap_event_in_comma(self):
    self.comma_at_level(2)
    for scroll in (101, 102, 103, 0, 50):
      self.assertEqual(self.gap_events(self.step(scroll=scroll)), [])

  def test_gap_event_still_filtered_in_bridge(self):
    self.bridge.button_source = ButtonSource.BRIDGE
    self.poll(follow_level=2)
    self.step(scroll=10)
    self.assertEqual(self.gap_events(self.step(scroll=11)), [])
    # stale bridge: native gap cycling, as before
    self.poll(stale=True)
    self.assertEqual(len(self.gap_events(self.step(scroll=12))), 1)

  def test_back_to_bridge_restores_its_level(self):
    self.comma_at_level(2)
    self.step(scroll=101)
    self.run_poll_thread_once()
    self.bridge.button_source = ButtonSource.BRIDGE
    self.params.reset_mock()
    self.step(scroll=101)
    self.assertEqual(self.bridge.comma_follow_level, 0)
    self.run_poll_thread_once()
    self.assertEqual(self.writes("RivianFollowLevel"), [2])


if __name__ == "__main__":
  unittest.main()
