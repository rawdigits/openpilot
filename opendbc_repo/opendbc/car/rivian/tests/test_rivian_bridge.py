import io
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from opendbc.car import Bus, gen_empty_fingerprint
from opendbc.car.rivian import rivian_bridge
from opendbc.car.rivian.carstate import CarState
from opendbc.car.rivian.interface import CarInterface
from opendbc.car.rivian.rivian_bridge import RivianBridge
from opendbc.car.rivian.values import CAR


class TestRivianBridge(unittest.TestCase):
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
    self.parsers[Bus.alt].vl["WheelButtons_Fwd"]["RightButton_Scroll"] = 255
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_Unit"] = 0
    self.parsers[Bus.adas].vl["Cluster"]["Cluster_VehicleSpeed"] = 72

  def poll(self, **state):
    data = {"stale": False, "set_speed_ms": 25., "follow_personality": 1, **state}
    with patch.object(rivian_bridge.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(data).encode())) as get:
      self.bridge._poll_once()
    get.assert_called_once_with(f"{self.bridge.url}/state", timeout=1)

  def engage(self, enabled=True):
    self.parsers[Bus.cam].vl["ACM_Status"]["ACM_FeatureStatus"] = int(enabled)

  def test_follow_sync_without_gas(self):
    # Exercise the real CarState.update path with both cruise states and every
    # gap. This fails if the freshness/follow block is nested under gasPressed.
    for enabled in (False, True):
      self.engage(enabled)
      for personality in (0, 1, 2):
        with self.subTest(enabled=enabled, personality=personality):
          self.poll(follow_personality=personality)
          self.params.reset_mock()
          ret, _ = self.cs.update(self.parsers)
          self.assertFalse(ret.gasPressed)
          self.assertEqual(self.bridge._requested_personality, personality)
          self.params.put.assert_not_called()  # no I/O in the control loop
          worker = threading.Thread(target=self.bridge._sync_personality)
          worker.start()
          worker.join(timeout=2)
          self.assertFalse(worker.is_alive())
          self.params.put.assert_called_once_with("LongitudinalPersonality", personality)
          self.assertIs(type(self.params.put.call_args.args[1]), int)

  def test_personality_dedup_retry_and_validation(self):
    self.poll()
    self.cs.update(self.parsers)
    self.params.put.side_effect = OSError("temporary write failure")
    self.bridge._sync_personality()
    self.params.put.side_effect = None
    self.bridge._sync_personality()
    self.bridge._sync_personality()
    self.assertEqual(self.params.put.call_count, 2)
    for invalid in (-1, 3, "1", None, True, 1.0):
      self.poll(follow_personality=invalid)
      self.cs.update(self.parsers)
      self.bridge._sync_personality()
    self.assertEqual(self.params.put.call_count, 2)

  def test_stale_and_failed_http_do_not_update(self):
    self.engage()
    self.poll()
    self.cs.update(self.parsers)
    self.bridge._sync_personality()
    for stale in (True, "false", None):
      self.poll(stale=stale, set_speed_ms=30., follow_personality=2)
      ret, _ = self.cs.update(self.parsers)
      self.bridge._sync_personality()
      self.assertEqual(ret.cruiseState.speed, 25.)
    self.params.put.assert_called_once_with("LongitudinalPersonality", 1)
    self.poll()
    with patch.object(rivian_bridge.urllib.request, "urlopen", side_effect=TimeoutError):
      self.bridge._poll_once()
    self.assertTrue(self.bridge.stale)
    self.poll()
    self.bridge._received_at = time.monotonic() - rivian_bridge.STALE_AFTER - 1
    self.assertTrue(self.bridge.stale)

  def test_invalid_http_body(self):
    for payload in (b"[]", b"null", b"not json"):
      self.poll()
      with patch.object(rivian_bridge.urllib.request, "urlopen", return_value=io.BytesIO(payload)):
        self.bridge._poll_once()
      self.assertTrue(self.bridge.stale)

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

  def test_kit_speed_buttons_and_stalk_still_work(self):
    self.engage()
    self.poll()
    self.cs.update(self.parsers)
    buttons = self.parsers[Bus.alt].vl["WheelButtons_Fwd"]
    buttons["RightButton_RightClick"] = 2
    ret, _ = self.cs.update(self.parsers)
    self.assertAlmostEqual(ret.cruiseState.speed, 25. + 1 / 3.6, places=5)
    buttons["RightButton_RightClick"] = 0
    ret, _ = self.cs.update(self.parsers)
    self.assertAlmostEqual(ret.cruiseState.speed, 25. + 1 / 3.6, places=5)
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
    self.bridge._sync_personality()
    self.poll(follow_personality=2)
    self.cs.update(self.parsers)
    self.bridge._sync_personality()
    self.params.put.assert_called_once_with("LongitudinalPersonality", 2)

  def test_invalid_personality_recovery_reclaims_gap(self):
    self.poll(follow_personality=2)
    self.cs.update(self.parsers)
    self.bridge._sync_personality()
    # While the bridge gap is unavailable, a native CAN gap event can change
    # the param. Recovery must restore the absolute bridge value even if the
    # bridge returns the same value it reported before the outage.
    self.poll(follow_personality=None)
    self.parsers[Bus.alt].vl["WheelButtons_Fwd"]["RightButton_Scroll"] = 1
    ret, _ = self.cs.update(self.parsers)
    self.assertEqual(len(ret.buttonEvents), 1)
    self.bridge._sync_personality()
    self.params.reset_mock()
    self.poll(follow_personality=2)
    self.cs.update(self.parsers)
    self.bridge._sync_personality()
    self.params.put.assert_called_once_with("LongitudinalPersonality", 2)

  def test_stock_long_does_not_start_bridge(self):
    self.cp.openpilotLongitudinalControl = False
    with patch("opendbc.car.rivian.carstate.RivianBridge") as bridge:
      cs = CarState(self.cp, self.cp_sp)
    bridge.assert_not_called()
    self.assertIsNone(cs.bridge)

  def test_config_precedence(self):
    self.assertEqual(rivian_bridge.REPO_CONF.parent, Path(__file__).resolve().parents[5])
    with tempfile.TemporaryDirectory() as directory:
      repo, data = Path(directory) / "repo.conf", Path(directory) / "data.conf"
      with patch.object(rivian_bridge, "REPO_CONF", repo), patch.object(rivian_bridge, "DATA_CONF", data):
        self.assertEqual(rivian_bridge._read_bridge_url(), rivian_bridge.DEFAULT_URL)
        data.write_text("http://data:8082\n")
        self.assertEqual(rivian_bridge._read_bridge_url(), "http://data:8082")
        repo.write_text("http://repo:8082/\n")
        self.assertEqual(rivian_bridge._read_bridge_url(), "http://repo:8082")
        repo.write_text("\n")
        self.assertEqual(rivian_bridge._read_bridge_url(), "http://data:8082")

  def test_poll_thread_drops_realtime_before_io(self):
    order = []
    with patch.object(rivian_bridge, "_drop_rt_scheduling_for_this_thread", side_effect=lambda: order.append("scheduler")), \
         patch.object(self.bridge, "_poll_once", side_effect=lambda: order.append("http")), \
         patch.object(self.bridge, "_sync_personality", side_effect=lambda: order.append("params")), \
         patch.object(rivian_bridge.time, "sleep", side_effect=InterruptedError):
      with self.assertRaises(InterruptedError):
        self.bridge._poll_loop()
    self.assertEqual(order, ["scheduler", "http", "params"])

  def test_scheduling_syscalls_only_target_worker(self):
    with patch.object(rivian_bridge.os, "sched_setscheduler") as scheduler, \
         patch.object(rivian_bridge.os, "sched_setaffinity") as affinity, \
         patch.object(rivian_bridge.os, "cpu_count", return_value=8):
      rivian_bridge._drop_rt_scheduling_for_this_thread()
      scheduler.assert_called_once_with(0, rivian_bridge.os.SCHED_OTHER, rivian_bridge.os.sched_param(0))
      affinity.assert_called_once_with(0, {0, 1, 2, 3})
      scheduler.side_effect = PermissionError
      affinity.reset_mock()
      rivian_bridge._drop_rt_scheduling_for_this_thread()
      affinity.assert_called_once_with(0, {0, 1, 2, 3})
