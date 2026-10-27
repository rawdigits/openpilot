from opendbc.car import gen_empty_fingerprint
from opendbc.car.rivian.interface import CarInterface
from opendbc.car.rivian.values import CAR, RivianFlags
from openpilot.common.params import Params
from openpilot.common.test import OpenpilotTestCase
from openpilot.selfdrive.car.helpers import convert_to_capnp
from openpilot.selfdrive.controls.controlsd import Controls
from openpilot.selfdrive.controls.lib.latcontrol_angle import LatControlAngle
from openpilot.sunnypilot.modeld_v2.modeld_base import LAT_SMOOTH_MAX, get_lat_smooth_seconds, lat_smooth_scheduled


def rivian_params(angle_kit: bool):
  fingerprint = gen_empty_fingerprint()
  fingerprint[0][0x321] = 8
  if angle_kit:
    fingerprint[1][0x1310] = 8
  CP = CarInterface.get_params(CAR.RIVIAN_R1, fingerprint, [], False, False, False)
  CP_SP = CarInterface.get_params_sp(CP, CAR.RIVIAN_R1, fingerprint, [], False, False, False)
  return CP, CP_SP


class TestRivianAngleKitControls(OpenpilotTestCase):
  def _controls(self, angle_kit: bool) -> Controls:
    CP, CP_SP = rivian_params(angle_kit)
    params = Params()
    params.put("CarParams", CP.to_bytes(), block=True)
    params.put("CarParamsSP", convert_to_capnp(CP_SP).to_bytes(), block=True)
    return Controls()

  def test_angle_kit_present(self):
    controls = self._controls(angle_kit=True)
    self.assertTrue(controls.CP.flags & RivianFlags.ANGLE_KIT)
    self.assertEqual(controls.CP.lateralTuning.which(), 'torque')
    self.assertNotIsInstance(controls.LaC, LatControlAngle)
    self.assertIsInstance(controls.LaC_angle, LatControlAngle)
    self.assertTrue(controls.lat_smooth_scheduled)

  def test_angle_kit_absent(self):
    controls = self._controls(angle_kit=False)
    self.assertFalse(controls.CP.flags & RivianFlags.ANGLE_KIT)
    self.assertFalse(controls.CP.dashcamOnly)
    # plain torque control, no angle controller running alongside
    self.assertEqual(controls.CP.lateralTuning.which(), 'torque')
    self.assertNotIsInstance(controls.LaC, LatControlAngle)
    self.assertIsNone(controls.LaC_angle)
    self.assertFalse(controls.lat_smooth_scheduled)

  def test_lat_smooth(self):
    # the crawl-speed smoothing is for the angle EPAS limit cycle, torque only keeps the stock constant
    for angle_kit, expected in ((True, LAT_SMOOTH_MAX), (False, 0.1)):
      CP, _ = rivian_params(angle_kit)
      self.assertAlmostEqual(get_lat_smooth_seconds(0., 0.1, lat_smooth_scheduled(CP)), expected)
    self.assertAlmostEqual(get_lat_smooth_seconds(30., 0.1, True), 0.1)
