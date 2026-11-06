from opendbc.car import get_safety_config, structs
from opendbc.car.interfaces import CarInterfaceBase
from opendbc.car.rivian.carcontroller import CarController
from opendbc.car.rivian.carstate import CarState
from opendbc.car.rivian.radar_interface import RadarInterface
from opendbc.car.rivian.values import RivianFlags, RivianSafetyFlags, set_model_line_specs
from opendbc.sunnypilot.car.rivian.values import RivianFlagsSP


class CarInterface(CarInterfaceBase):
  CarState = CarState
  CarController = CarController
  RadarInterface = RadarInterface

  @staticmethod
  def _get_params(ret: structs.CarParams, candidate, fingerprint, car_fw, alpha_long, is_release, docs) -> structs.CarParams:
    ret.brand = "rivian"

    ret.safetyConfigs = [get_safety_config(structs.CarParams.SafetyModel.rivian)]

    # GEN2 (2025+) doesn't have SCCM_WheelTouch on the bus
    if 0x321 not in fingerprint[0]:
      ret.flags |= RivianFlags.GEN2.value

    # angle upgrade installed, decided once at startup from the fingerprint
    if 0x1310 in fingerprint[1]:
      ret.flags |= RivianFlags.ANGLE_KIT.value
      ret.safetyConfigs[0].safetyParam |= RivianSafetyFlags.ANGLE_KIT.value

    ret.steerLimitTimer = 0.4
    CarInterfaceBase.configure_torque_tune(candidate, ret.lateralTuning)

    # torque is the primary channel, the angle command comes in via actuators.steeringAngleDeg
    ret.steerControlType = structs.CarParams.SteerControlType.torque
    ret.radarUnavailable = True

    if ret.flags & RivianFlags.ANGLE_KIT:
      ret.steerActuatorDelay = 0.1
      ret.steerAtStandstill = True

      # TODO is GEN2 the same?
      ret.alphaLongitudinalAvailable = docs or not (ret.flags & RivianFlags.GEN2)
      if alpha_long and ret.alphaLongitudinalAvailable:
        ret.openpilotLongitudinalControl = True
        ret.safetyConfigs[0].safetyParam |= RivianSafetyFlags.LONG_CONTROL.value
    else:
      # no angle kit: torque steering only, as on yeetfollow
      ret.steerActuatorDelay = 0.15

      # yeetfollow runs openpilot longitudinal on the stock harness, the Rivian bridge supplies set speed and gap
      ret.alphaLongitudinalAvailable = True
      ret.openpilotLongitudinalControl = True
      ret.safetyConfigs[0].safetyParam |= RivianSafetyFlags.LONG_CONTROL.value
      ret.radarUnavailable = False

    # yeetfollow's longitudinal tune in both paths, the long actuator (ACM_longitudinalRequest) is the same with and without the kit
    ret.longitudinalActuatorDelay = 0.35
    # yeetfollow's vEgoStopping 0.25 is a deprecated CarParam here, see drive_helpers.STOP_SPEED_BRAND
    ret.stopAccel = 0

    return ret

  @staticmethod
  def _get_params_sp(stock_cp: structs.CarParams, ret: structs.CarParamsSP, candidate, fingerprint: dict[int, dict[int, int]],
                     car_fw: list[structs.CarParams.CarFw], alpha_long: bool, is_release_sp: bool, docs: bool) -> structs.CarParamsSP:
    # get_car assigns the VIN before this stage, and constructs the controller afterwards.
    set_model_line_specs(stock_cp)

    if 0x131a in fingerprint[1]:
      ret.flags |= RivianFlagsSP.LONGITUDINAL_HARNESS_UPGRADE.value
      stock_cp.radarUnavailable = False
      stock_cp.alphaLongitudinalAvailable = True

    if alpha_long and stock_cp.alphaLongitudinalAvailable:
      stock_cp.openpilotLongitudinalControl = True
      stock_cp.safetyConfigs[0].safetyParam |= RivianSafetyFlags.LONG_CONTROL.value

    return ret
