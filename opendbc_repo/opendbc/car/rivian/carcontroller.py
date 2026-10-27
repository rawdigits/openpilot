import numpy as np
from opendbc.can import CANPacker
from opendbc.car import Bus
from opendbc.car.interfaces import CarControllerBase
from opendbc.car.lateral import apply_driver_steer_torque_limits
from opendbc.car.rivian.ext_controller import ExternalController, get_safety_CP  # noqa: F401
from opendbc.car.rivian.riviancan import create_angle_steering, create_lka_steering, create_longitudinal, create_wheel_touch, create_adas_status, create_acm_status
from opendbc.car.rivian.values import CarControllerParams, RivianFlags

from opendbc.sunnypilot.car.rivian.mads import MadsCarController

# torque-only (no angle kit): the EPAS faults on sustained torque at high angle
MAX_STEERING_ANGLE = 90.0


class CarController(CarControllerBase, MadsCarController):
  def __init__(self, dbc_names, CP, CP_SP):
    CarControllerBase.__init__(self, dbc_names, CP, CP_SP)
    MadsCarController.__init__(self)
    self.apply_torque_last = 0
    self.packer = CANPacker(dbc_names[Bus.pt])

    self.cancel_frames = 0
    self.long_cmd_counter = 0
    self.angle_kit = bool(CP.flags & RivianFlags.ANGLE_KIT)
    self.erc = ExternalController() if self.angle_kit else None

  def update(self, CC, CC_SP, CS, now_nanos):
    MadsCarController.update(self, CC, CC_SP, CS)
    actuators = CC.actuators
    can_sends = []

    apply_torque = 0
    steer_max = round(float(np.interp(CS.out.vEgoRaw, CarControllerParams.STEER_MAX_LOOKUP[0],
                                      CarControllerParams.STEER_MAX_LOOKUP[1])))

    if self.erc is not None:
      self.erc.update(CS, self.mads.lat_active, actuators)
      apply_torque = self.erc.apply_torque_last

      # send steering command, torque is 0 and toi_act_cmd low during a blip
      self.apply_torque_last = apply_torque
      can_sends.append(create_lka_steering(self.packer, self.frame, CS.acm_lka_hba_cmd, apply_torque, CC.enabled, self.erc.toi_act_cmd, self.mads))

      can_sends.append(create_angle_steering(self.packer, self.frame, self.erc.apply_angle_last, self.erc.angle_active))
      feature_status = (1 if self.erc.torque_active else 2) if self.mads.lat_active else 0
      can_sends.append(create_acm_status(self.packer, self.frame, feature_status))
    else:
      lat_active = self.mads.lat_active and abs(CS.out.steeringAngleDeg) < MAX_STEERING_ANGLE
      if lat_active:
        new_torque = int(round(actuators.torque * steer_max))
        apply_torque = apply_driver_steer_torque_limits(new_torque, self.apply_torque_last,
                                                        CS.out.steeringTorque, CarControllerParams, steer_max)

      self.apply_torque_last = apply_torque
      can_sends.append(create_lka_steering(self.packer, self.frame, CS.acm_lka_hba_cmd, apply_torque, CC.enabled, lat_active, self.mads))

    if self.frame % 5 == 0 and not (self.CP.flags & RivianFlags.GEN2):
      can_sends.append(create_wheel_touch(self.packer, CS.sccm_wheel_touch, self.mads.lat_active))

    # Longitudinal control
    if self.CP.openpilotLongitudinalControl:
      # CC.enabled lags the ACM clearing its feature status by the selfdrived/controlsd round trip
      long_enabled = CC.enabled and CS.out.cruiseState.enabled
      accel = float(np.clip(actuators.accel, CarControllerParams.ACCEL_MIN, CarControllerParams.ACCEL_MAX)) if long_enabled else 0.0
      # a rejected frame never reached the bus, resend its counter if nothing newer went out
      resend = CS.long_cmd_rejected_updated and CS.long_cmd_rejected_counter == self.long_cmd_counter % 15
      if not resend:
        self.long_cmd_counter += 1
      can_sends.append(create_longitudinal(self.packer, self.long_cmd_counter, accel, long_enabled))

      # keep the stock ACM from winding up its unactuated request
      # without the kit VDM_AdasSts is forwarded untouched, as on yeetfollow
      if self.angle_kit:
        for msg in CS.vdm_adas_status:
          can_sends.append(create_adas_status(self.packer, msg, None, 0 if CC.enabled else None))
    else:
      interface_status = None
      if CC.cruiseControl.cancel:
        # if there is a noEntry, we need to send a status of "available" before the ACM will accept "unavailable"
        # send "available" right away as the VDM itself takes a few frames to acknowledge
        interface_status = 1 if self.cancel_frames < 5 else 0
        self.cancel_frames += 1
      else:
        self.cancel_frames = 0

      for msg in CS.vdm_adas_status:
        can_sends.append(create_adas_status(self.packer, msg, interface_status))

    new_actuators = actuators.as_builder()
    new_actuators.torque = apply_torque / steer_max
    new_actuators.torqueOutputCan = apply_torque
    if self.erc is not None:
      new_actuators.steeringAngleDeg = self.erc.apply_angle_last

    self.frame += 1
    return new_actuators, can_sends
