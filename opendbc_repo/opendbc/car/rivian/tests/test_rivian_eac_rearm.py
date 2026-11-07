"""EPAS angle control re-arm after a drop (automotive/openpilot#10).

2026-11-06 route 000000c7--4693ee51c3: EacStatus 2 -> 0 with EacErrorCode 11 (EPAS_Vehspd_Max_Thd_Err) at 101 mph,
then EacStatus 0 err 0 for the rest of the drive while ext_controller sat in torque with ACM_EacEnabled 0. A simulated
EPAS runs against the real CarController, every frame passes panda safety with the simulated speed and wheel angle.
"""
import unittest

from opendbc.can import CANParser
from opendbc.car import Bus, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.rivian import ext_controller as ec
from opendbc.car.rivian.tests.test_rivian_angle_kit import startup
from opendbc.safety.tests.common import CANPackerSafety
from opendbc.safety.tests.libsafety import libsafety_py
from opendbc.safety.tests.test_rivian import checksum

WHEEL = -2.1  # steady wheel angle at the drop


class SimEPAS:
  """EAC states from the drive: 2 active, 0 inhibited. Overspeed drops 2 -> 0 with err 11, err clears below the
  threshold, the EPAS then stays inhibited until angle is requested again (answers 1 then 2 if responsive)."""
  DROP_SPEED = 100.5 * CV.MPH_TO_MS  # dropped as speed crossed ~101 mph

  def __init__(self, responsive=True, answer_frames=3):
    self.status = 1
    self.err = 0
    self.responsive = responsive
    self.answer_frames = answer_frames
    self.request_frames = 0

  def update(self, v_ego, eac_enabled):
    if v_ego > self.DROP_SPEED:
      if self.status == 2:
        self.status = 0
      self.err = 11 if self.status == 0 else 0
      self.request_frames = 0
      return
    self.err = 0
    self.request_frames = self.request_frames + 1 if eac_enabled else 0
    if self.status == 2 and not eac_enabled:
      self.status = 0
    elif eac_enabled and self.responsive and self.status in (0, 1):
      if self.request_frames >= 2 * self.answer_frames:
        self.status = 2
      elif self.request_frames >= self.answer_frames:
        self.status = 1


class TestRivianEacRearm(unittest.TestCase):
  def setUp(self):
    self.CI = startup(angle_kit=True)
    self.erc = self.CI.CC.erc
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(structs.CarParams.SafetyModel.rivian, self.CI.CP.safetyConfigs[0].safetyParam)
    self.safety.init_tests()
    self.safety.set_controls_allowed(True)
    self.safety_packer = CANPackerSafety("rivian_primary_actuator")
    self.parser = CANParser("rivian_primary_actuator", [("ACM_SteeringControl", float("nan")), ("ACM_Status", float("nan"))], 0)

    CS = self.CI.CS
    CS.acm_lka_hba_cmd = self.CI.can_parsers[Bus.cam].vl["ACM_lkaHbaCmd"]
    CS.sccm_wheel_touch = self.CI.can_parsers[Bus.pt].vl["SCCM_WheelTouch"]
    CS.vdm_adas_status = []
    CS.hands_on_level = 0

    self.frame = 0
    self.cnt = 0
    self.wheel = WHEEL
    self.epas = SimEPAS()
    self.log = []

  def _rx(self, v_ego, wheel):
    self.cnt += 1
    msgs = [
      self.safety_packer.make_can_msg_safety("ESP_Status", 0, {"ESP_Vehicle_Speed": v_ego * CV.MS_TO_KPH, "ESP_Status_Counter": self.cnt % 15,
                                                               "ESP_Vehicle_Speed_Q": 1}, fix_checksum=checksum),
      self.safety_packer.make_can_msg_safety("VDM_PropStatus", 0, {"VDM_VehicleSpeed": v_ego * CV.MS_TO_KPH, "VDM_PropStatus_Counter": self.cnt % 15,
                                                                   "VDM_VehicleSpeedQ": 1}, fix_checksum=checksum),
      self.safety_packer.make_can_msg_safety("EPAS_AdasStatus", 0, {"EPAS_InternalSas": wheel}),
    ]
    for msg in msgs:
      self.assertTrue(self.safety.safety_rx_hook(msg))

  def _step(self, v_ego, desired=WHEEL, hands_on=False, lat_active=True):
    CS = self.CI.CS
    CS.out.vEgoRaw = CS.out.vEgo = v_ego
    CS.out.aEgo = 0.
    CS.out.steeringAngleDeg = self.wheel
    CS.out.steeringRateDeg = 0.
    CS.out.steeringTorque = 0.
    CS.out.steeringPressed = False
    CS.hands_on_level = 2 if hands_on else 0
    CS.eac_status = self.epas.status
    CS.eac_error_code = self.epas.err

    self._rx(v_ego, self.wheel)
    self.frame += 1
    self.safety.set_timer(self.frame * 10000)  # 100 Hz

    CC = structs.CarControl(enabled=lat_active, latActive=lat_active)
    CC.actuators.steeringAngleDeg = desired
    CC.actuators.torque = -0.2
    _, can_sends = self.CI.apply(CC.as_reader(), structs.CarControlSP(), 0)
    for addr, dat, bus in can_sends:
      if bus in (0, 2):
        self.assertTrue(self.safety.safety_tx_hook(libsafety_py.make_CANPacket(addr, bus, dat)), (hex(addr), self.frame))
    self.parser.update([(self.frame * 10_000_000, [(addr, dat, 0) for addr, dat, bus in can_sends if addr in (0x100, 0x110) and bus == 0])])
    enabled = bool(self.parser.vl["ACM_SteeringControl"]["ACM_EacEnabled"])
    angle = self.parser.vl["ACM_SteeringControl"]["ACM_SteeringAngleRequest"]
    feature = int(self.parser.vl["ACM_Status"]["ACM_FeatureStatus"])
    self.log.append({"enabled": enabled, "angle": angle, "feature": feature, "wheel": self.wheel, "status": CS.eac_status,
                     "err": CS.eac_error_code, "angle_active": self.erc.angle_active, "torque_active": self.erc.torque_active,
                     "v": v_ego})

    # the EPAS answers next frame, on angle the wheel follows the sent angle
    self.epas.update(v_ego, enabled)
    if self.epas.status == 2 and enabled:
      self.wheel = angle

  def _run(self, frames, v_ego, **kwargs):
    start = len(self.log)
    for _ in range(frames):
      self._step(v_ego, **kwargs)
    return self.log[start:]

  def _retries(self, log):
    # (start, length) of each EacEnabled window while ext_controller is in torque
    windows, start = [], None
    for i, f in enumerate(log):
      probing = f["enabled"] and f["torque_active"]
      if probing and start is None:
        start = i
      elif not probing and start is not None:
        windows.append((start, i - start))
        start = None
    if start is not None:
      windows.append((start, len(log) - start))
    return windows

  def _drop_at_101(self):
    # steady on angle at 98 mph, then 101 mph: overspeed handoff and the EPAS drop with err 11, back to 85 mph
    self._run(200, 98. * CV.MPH_TO_MS)
    self.assertTrue(self.erc.angle_active)
    self.assertEqual(self.epas.status, 2)
    over = self._run(300, 101. * CV.MPH_TO_MS)
    self.assertEqual((self.epas.status, self.epas.err), (0, 11))
    self.assertTrue(self.erc.torque_active)
    # no angle request while over the EPAS speed threshold
    self.assertFalse(any(f["enabled"] for f in over[1:]))

  def test_rearm_after_overspeed_drop(self):
    self._drop_at_101()
    back = self._run(400, 85. * CV.MPH_TO_MS)
    # inhibited without an error from the EPAS's first frame below the threshold
    self.assertEqual((back[1]["status"], back[1]["err"]), (0, 0))
    self.assertTrue(self.erc.angle_active)
    self.assertEqual(self.epas.status, 2)
    retries = self._retries(back)
    self.assertEqual(len(retries), 1)
    start = retries[0][0]
    # retry from the settled torque state at the wheel angle, FeatureStatus 2 with it
    self.assertAlmostEqual(back[start]["angle"], back[start]["wheel"], delta=0.1)
    self.assertEqual(back[start]["feature"], 2)
    self.assertFalse(back[start - 1]["enabled"])
    self.assertEqual(back[start - 1]["feature"], 1)
    # stays on angle once the EPAS answered 1 -> 2
    first_angle = next(i for i, f in enumerate(back) if f["angle_active"])
    self.assertTrue(all(f["angle_active"] and f["enabled"] for f in back[first_angle:]))
    self.assertTrue(all(f["feature"] == 2 for f in back[first_angle:]))

  def test_never_a_step(self):
    self._drop_at_101()
    # the plan wants 3 deg more than the wheel has: the retry starts at the wheel, angle then ramps at the jerk limit
    back = self._run(600, 85. * CV.MPH_TO_MS, desired=WHEEL - 3.)
    self.assertTrue(self.erc.angle_active)
    step = ec.get_max_angle_delta_vm(85. * CV.MPH_TO_MS, self.erc.VM_safety, ec.CCP)
    first = next(i for i, f in enumerate(back) if f["enabled"])
    self.assertAlmostEqual(back[first]["angle"], back[first]["wheel"], delta=0.1)
    for prev, f in zip(back[first:], back[first + 1:], strict=False):
      self.assertTrue(f["enabled"])
      self.assertLessEqual(abs(f["angle"] - prev["angle"]), step + 0.1 + 1e-6)
    self.assertAlmostEqual(back[-1]["angle"], WHEEL - 3., delta=0.1)

  def test_retry_rate_bounded_when_epas_never_answers(self):
    self._drop_at_101()
    self.epas.responsive = False
    back = self._run(6000, 85. * CV.MPH_TO_MS)  # 60 s
    self.assertTrue(all(f["torque_active"] for f in back))
    retries = self._retries(back)
    self.assertGreaterEqual(len(retries), 3)
    self.assertTrue(all(length <= ec.EAC_PROBE_FRAMES for _, length in retries))
    gaps = [b[0] - (a[0] + a[1]) for a, b in zip(retries, retries[1:], strict=False)]
    self.assertTrue(all(g >= ec.EAC_RETRY_INTERVAL_FRAMES for g in gaps))
    # backs off up to the max interval
    self.assertGreaterEqual(gaps[-1], ec.EAC_RETRY_MAX_INTERVAL_FRAMES)
    self.assertLessEqual(len(retries), 2 + 6000 // ec.EAC_RETRY_MAX_INTERVAL_FRAMES)
    # FeatureStatus 2 only while requesting angle
    self.assertTrue(all((f["feature"] == 2) == f["enabled"] for f in back))

  def test_flapping_epas_stays_rate_limited(self):
    # the EPAS takes angle and drops it again 0.2 s later, long enough for the torque fallback, every time.
    # re-arms count against the backoff
    self._drop_at_101()
    back, deaf = [], 0
    for _ in range(6000):
      self._step(85. * CV.MPH_TO_MS)
      deaf = max(deaf - 1, 0)
      if self.epas.status == 2 and self.erc.angle_active and self.erc.eac_stable_frames >= 20:
        self.epas.status, deaf = 0, 2 * ec.EAC_RECOVER_FRAMES
      self.epas.responsive = deaf == 0
      back.append(self.log[-1])
    starts = [i for i, (a, b) in enumerate(zip(back, back[1:], strict=False)) if not a["enabled"] and b["enabled"]]
    self.assertGreaterEqual(len(starts), 2)
    gaps = [b - a for a, b in zip(starts, starts[1:], strict=False)]
    self.assertTrue(all(g >= ec.EAC_RETRY_INTERVAL_FRAMES for g in gaps))
    self.assertLessEqual(len(starts), 2 + 6000 // ec.EAC_RETRY_MAX_INTERVAL_FRAMES)

  def test_engage_within_epas_limits(self):
    # 2026-11-07 route 000000c9--d0dbc1edaa: EacStatus 2 -> 1 err 0 1.4 s after an engage at 64 mph. The engage request
    # itself starts at the wheel and stays inside the EPAS rate window and panda's jerk limit, whatever the plan wants
    v = 64. * CV.MPH_TO_MS
    step = ec.get_max_angle_delta_vm(v, self.erc.VM_safety, ec.CCP)
    window = float(ec.np.interp(v, ec.EPAS_FW_RATE_BP, ec.EPAS_FW_RATE_V)) * 100. * ec._RateBudget.WINDOW_TIME_S
    for desired in (WHEEL, 0., 5., -10.):
      with self.subTest(desired=desired):
        self.setUp()
        self._run(100, v, desired=desired, lat_active=False)  # disengaged, the controller tracks the wheel
        log = self._run(300, v, desired=desired)
        self.assertTrue(log[0]["enabled"])
        self.assertEqual(log[0]["feature"], 2)
        self.assertLessEqual(abs(log[0]["angle"] - WHEEL), step + 0.1)
        self.assertTrue(all(f["angle_active"] for f in log))
        for a, b in zip(log, log[1:], strict=False):
          self.assertLessEqual(abs(b["angle"] - a["angle"]), step + 0.1 + 1e-6)
        for i in range(len(log) - ec._RateBudget.WINDOW_USER_FRAMES):
          self.assertLess(abs(log[i + ec._RateBudget.WINDOW_USER_FRAMES]["angle"] - log[i]["angle"]), window)

  def test_no_retry_hands_on(self):
    self._drop_at_101()
    back = self._run(1000, 85. * CV.MPH_TO_MS, hands_on=True)
    self.assertFalse(any(f["enabled"] for f in back))
    self.assertTrue(all(f["torque_active"] for f in back))
    # hands off again, re-arms
    back = self._run(400, 85. * CV.MPH_TO_MS)
    self.assertTrue(self.erc.angle_active)

  def test_no_retry_with_eac_error(self):
    self._drop_at_101()
    self.epas.err = 11
    self.CI.CS.eac_error_code = 11
    for _ in range(600):
      self.epas.update = lambda v, en: None  # holds the error
      self._step(85. * CV.MPH_TO_MS)
    self.assertFalse(any(f["enabled"] for f in self.log[-600:]))

  def test_no_retry_while_wheel_moving_or_off_target(self):
    self._drop_at_101()
    # desired far from the wheel: no handback, no retry
    back = self._run(600, 85. * CV.MPH_TO_MS, desired=WHEEL + ec.HANDOFF_EXIT_DEG + 1)
    self.assertFalse(any(f["enabled"] for f in back))

  def test_overspeed_handoff_before_the_epas_drops(self):
    # ramp 95 -> 103 mph: torque before 101 mph, so the EPAS never drops EAC on its own
    self._run(200, 95. * CV.MPH_TO_MS)
    self.assertTrue(self.erc.angle_active)
    for i in range(800):
      v = (95. + 8. * i / 800) * CV.MPH_TO_MS
      self._step(v)
      if v > ec.EAC_MAX_SPEED:
        self.assertTrue(self.erc.torque_active)
    self.assertFalse(any(f["status"] == 2 and f["v"] > SimEPAS.DROP_SPEED for f in self.log))
    # hysteresis: no re-arm between the re-arm speed and the threshold
    back = self._run(1000, (ec.EAC_REARM_SPEED + ec.EAC_MAX_SPEED) / 2)
    self.assertFalse(any(f["enabled"] for f in back))
    back = self._run(400, ec.EAC_REARM_SPEED - 1.)
    self.assertTrue(self.erc.angle_active)

  def test_backoff_resets_after_angle_holds(self):
    self._drop_at_101()
    self.epas.responsive = False
    self._run(2500, 85. * CV.MPH_TO_MS)
    self.assertGreater(self.erc.eac_retry_interval, ec.EAC_RETRY_INTERVAL_FRAMES)
    self.epas.responsive = True
    self._run(ec.EAC_RETRY_MAX_INTERVAL_FRAMES + 200, 85. * CV.MPH_TO_MS)
    self.assertTrue(self.erc.angle_active)
    self._run(ec.EAC_STABLE_FRAMES + 10, 85. * CV.MPH_TO_MS)
    self.assertEqual(self.erc.eac_retry_interval, ec.EAC_RETRY_INTERVAL_FRAMES)
    self.assertEqual(self.erc.eac_retries, 0)


if __name__ == "__main__":
  unittest.main()
