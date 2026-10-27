import os
import time
import unittest
from unittest.mock import patch

import numpy as np

from opendbc.car import Bus, structs
from opendbc.car.can_definitions import CanData
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.car_helpers import get_car
from opendbc.car.rivian.carcontroller import MAX_STEERING_ANGLE
from opendbc.car.rivian.rivian_bridge import RivianBridge
from opendbc.car.rivian.values import CAR, RivianFlags, RivianSafetyFlags
from opendbc.safety.tests.libsafety import libsafety_py

ANGLE_KIT_ADDR = 0x1310
LONG_KIT_ADDR = 0x131a


def fake_can(angle_kit: bool, long_kit: bool = False):
  # Gen1 R1S traffic on the bus as seen by card during fingerprinting
  bus0 = [CanData(addr, b"\x00" * 8, 0) for addr in (0x150, 0x208, 0x321, 0x380, 0x38f, 0x390)]
  bus1 = [CanData(addr, b"\x00" * 8, 1) for addr in (0x500, 0x51f)]
  if angle_kit:
    bus1.append(CanData(ANGLE_KIT_ADDR, b"\x00" * 8, 1))
  if long_kit:
    bus1.append(CanData(LONG_KIT_ADDR, b"\x00" * 8, 1))
  bus2 = [CanData(addr, b"\x00" * 8, 2) for addr in (0x100, 0x110, 0x120)]
  return [bus0 + bus1 + bus2]


def startup(angle_kit: bool, long_kit: bool = False, alpha_long: bool = False):
  """Fingerprint and build the interface the way card does at startup, from fake CAN."""
  packets = fake_can(angle_kit, long_kit)
  bridge = RivianBridge(start=False)
  with patch.dict(os.environ, {"SKIP_FW_QUERY": "1"}), patch("opendbc.car.rivian.carstate.RivianBridge", return_value=bridge):
    CI = get_car(lambda wait_for_one=False: packets, lambda msgs: None, lambda obd: None, alpha_long, False,
                 fixed_fingerprint=CAR.RIVIAN_R1)
  return CI


class TestRivianAngleKitDetection(unittest.TestCase):
  def test_angle_kit_present(self):
    CI = startup(angle_kit=True)
    CP = CI.CP
    self.assertTrue(CP.flags & RivianFlags.ANGLE_KIT)
    self.assertFalse(CP.dashcamOnly)
    self.assertTrue(CP.safetyConfigs[0].safetyParam & RivianSafetyFlags.ANGLE_KIT)
    self.assertFalse(CP.openpilotLongitudinalControl)
    self.assertFalse(CP.alphaLongitudinalAvailable)
    self.assertTrue(CP.steerAtStandstill)
    self.assertAlmostEqual(CP.steerActuatorDelay, 0.1, places=5)
    self.assertIsNotNone(CI.CC.erc)

  def test_angle_kit_present_with_long_kit(self):
    CI = startup(angle_kit=True, long_kit=True, alpha_long=True)
    self.assertTrue(CI.CP.flags & RivianFlags.ANGLE_KIT)
    self.assertTrue(CI.CP.openpilotLongitudinalControl)
    self.assertEqual(CI.CP.safetyConfigs[0].safetyParam, RivianSafetyFlags.ANGLE_KIT | RivianSafetyFlags.LONG_CONTROL)

  def test_angle_kit_absent(self):
    for alpha_long in (False, True):
      with self.subTest(alpha_long=alpha_long):
        CI = startup(angle_kit=False, alpha_long=alpha_long)
        CP = CI.CP
        self.assertFalse(CP.flags & RivianFlags.ANGLE_KIT)
        # torque steering instead of dashcam-only
        self.assertFalse(CP.dashcamOnly)
        self.assertEqual(CP.steerControlType, structs.CarParams.SteerControlType.torque)
        self.assertEqual(CP.lateralTuning.which(), "torque")
        self.assertFalse(CP.steerAtStandstill)
        self.assertAlmostEqual(CP.steerActuatorDelay, 0.15, places=5)
        # yeetfollow: openpilot longitudinal with the Rivian bridge, on the stock harness
        self.assertTrue(CP.openpilotLongitudinalControl)
        self.assertEqual(CP.safetyConfigs[0].safetyParam, RivianSafetyFlags.LONG_CONTROL)
        self.assertIsNotNone(CI.CS.bridge)
        self.assertIsNone(CI.CC.erc)
        self.assertAlmostEqual(CP.longitudinalActuatorDelay, 0.35, places=5)
        self.assertEqual(list(CP.longitudinalTuning.kiV), [0.])

  def test_bridge_set_speed_without_kit(self):
    # set speed and follow distance come from the Rivian bridge, there are no forwarded kit buttons
    CI = startup(angle_kit=False)
    bridge = CI.CS.bridge
    bridge.state = {"stale": False, "set_speed_ms": 30., "follow_personality": 2}
    bridge._received_at = time.monotonic()
    self.assertNotIn(Bus.alt, CI.can_parsers)
    CI.can_parsers[Bus.pt].vl["ESP_Status"]["ESP_Vehicle_Speed"] = 24. * CV.MS_TO_KPH
    CI.can_parsers[Bus.adas].vl["Cluster"].update({"Cluster_Unit": 0, "Cluster_VehicleSpeed": 25. * CV.MS_TO_KPH})
    CI.can_parsers[Bus.cam].vl["ACM_Status"]["ACM_FeatureStatus"] = 1
    cs, _ = CI.update([])
    self.assertAlmostEqual(cs.cruiseState.speedCluster, 30., places=5)
    self.assertAlmostEqual(cs.cruiseState.speed, 30. * 0.96, places=5)
    self.assertEqual(bridge._requested_personality, 2)

  def test_decided_at_startup(self):
    # the kit appearing on the bus mid-drive does not switch the controller
    CI = startup(angle_kit=False)
    CI.update([(0, [CanData(ANGLE_KIT_ADDR, b"\x00" * 8, 1)])])
    self.assertFalse(CI.CP.flags & RivianFlags.ANGLE_KIT)
    self.assertIsNone(CI.CC.erc)


class TestRivianControllerSafety(unittest.TestCase):
  """Runs the real CarController for each path and checks every frame against panda safety."""

  def setUp(self):
    self.safety = libsafety_py.libsafety
    self.frame = 0

  def _setup(self, angle_kit: bool):
    CI = startup(angle_kit=angle_kit)
    self.safety.set_safety_hooks(structs.CarParams.SafetyModel.rivian, CI.CP.safetyConfigs[0].safetyParam)
    self.safety.init_tests()
    self.safety.set_controls_allowed(True)
    CI.CS.out.vEgoRaw = 20.
    CI.CS.out.vEgo = 20.
    CI.CS.acm_lka_hba_cmd = CI.can_parsers[Bus.cam].vl["ACM_lkaHbaCmd"]
    CI.CS.sccm_wheel_touch = CI.can_parsers[Bus.pt].vl["SCCM_WheelTouch"]
    CI.CS.vdm_adas_status = [dict(CI.can_parsers[Bus.pt].vl["VDM_AdasSts"])]
    return CI

  def _run(self, CI, torque: float, frames: int, steering_angle: float = 0.):
    CC = structs.CarControl(enabled=True, latActive=True)
    CC.actuators.torque = torque
    CC = CC.as_reader()
    CC_SP = structs.CarControlSP()
    CI.CS.out.steeringAngleDeg = steering_angle
    sent = []
    for _ in range(frames):
      self.frame += 1
      self.safety.set_timer(self.frame * 10000)  # 100 Hz
      actuators, can_sends = CI.apply(CC, CC_SP, 0)
      for addr, dat, bus in can_sends:
        if bus in (0, 2):
          self.assertTrue(self.safety.safety_tx_hook(libsafety_py.make_CANPacket(addr, bus, dat)), hex(addr))
      sent.append((actuators, can_sends))
    return sent

  def test_torque_only_without_kit(self):
    CI = self._setup(angle_kit=False)
    sent = self._run(CI, 1.0, 200)
    addrs = {addr for _, msgs in sent for addr, _, _ in msgs}
    # no angle command or ACM_Status replacement without the kit
    self.assertNotIn(0x110, addrs)
    self.assertNotIn(0x100, addrs)
    self.assertIn(0x120, addrs)
    self.assertIn(0x160, addrs)
    # ramps up to the torque limit at the rate limit, as on yeetfollow
    torques = [a.torqueOutputCan for a, _ in sent]
    self.assertEqual(torques[0], 3)
    self.assertTrue(np.all(np.diff(torques) >= 0))
    self.assertEqual(torques[-1], 250)

  def test_torque_only_high_angle_cutoff(self):
    CI = self._setup(angle_kit=False)
    sent = self._run(CI, 1.0, 10, steering_angle=MAX_STEERING_ANGLE + 1)
    self.assertTrue(all(a.torqueOutputCan == 0 for a, _ in sent))

  def test_angle_path_with_kit(self):
    CI = self._setup(angle_kit=True)
    # EPAS ready for angle control on engage, then steering on angle
    CI.CS.eac_status = 1
    sent = self._run(CI, 1.0, 1)
    CI.CS.eac_status = 2
    sent += self._run(CI, 1.0, 100)
    addrs = {addr for _, msgs in sent for addr, _, _ in msgs}
    self.assertTrue({0x100, 0x110, 0x120}.issubset(addrs))
    self.assertTrue(CI.CC.erc.angle_active)
    self.assertTrue(all(a.torqueOutputCan == 0 for a, _ in sent))

  def test_torque_only_blocks_angle_msgs(self):
    # safety without the kit rejects the kit's messages even if the controller sent them
    self._setup(angle_kit=False)
    for addr in (0x100, 0x110):
      self.assertFalse(self.safety.safety_tx_hook(libsafety_py.make_CANPacket(addr, 0, b"\x00" * 8)))


if __name__ == "__main__":
  unittest.main()
