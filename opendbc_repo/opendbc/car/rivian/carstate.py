import copy
from opendbc.can import CANParser
from opendbc.car import Bus, structs
from opendbc.car.interfaces import CarStateBase
from opendbc.car.rivian.values import DBC, GEAR_MAP, RivianFlags
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.carlog import carlog
from opendbc.car.rivian.rivian_bridge import FOLLOW_LEVELS, PERSONALITY_FOLLOW_LEVEL, ButtonSource, RivianBridge
from opendbc.sunnypilot.car.rivian.carstate_ext import CarStateExt, MAX_SET_SPEED

GearShifter = structs.CarState.GearShifter


class CarState(CarStateBase, CarStateExt):
  def __init__(self, CP, CP_SP):
    CarStateBase.__init__(self, CP, CP_SP)
    CarStateExt.__init__(self, CP, CP_SP)
    self.last_speed = 30

    self.acm_lka_hba_cmd: dict | None = None
    self.sccm_wheel_touch: dict | None = None
    self.vdm_adas_status: list[dict] | None = None
    self.hands_on_level = 0
    self.eac_status = 0
    self.eac_error_code = 0
    self.long_cmd_rejected_counter = 0
    self.long_cmd_rejected_updated = False

    # yeet-angle-bridged: plain values from rivianbridged, set by card before each update (no I/O, no thread here)
    self.bridge = RivianBridge() if CP.openpilotLongitudinalControl else None
    self._last_bridge_speed_cluster = 0.
    self.sign_speed = 10.  # dash m/s, last valid traffic sign
    self._gas_override = False
    # yeet-angle-standalone: "comma" (the kit's forwarded wheel buttons) or "bridge" owns set speed and gap
    self.button_source = "bridge"
    self._button_source_log: tuple[str, str] | None = None

  def update(self, can_parsers) -> tuple[structs.CarState, structs.CarStateSP]:
    cp = can_parsers[Bus.pt]
    cp_cam = can_parsers[Bus.cam]
    cp_adas = can_parsers[Bus.adas]
    ret = structs.CarState()
    ret_sp = structs.CarStateSP()

    # Vehicle speed
    ret.vEgoRaw = cp.vl["ESP_Status"]["ESP_Vehicle_Speed"] * CV.KPH_TO_MS
    ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)
    ret.standstill = abs(ret.vEgoRaw) < 0.01
    conversion = CV.KPH_TO_MS if cp_adas.vl["Cluster"]["Cluster_Unit"] == 0 else CV.MPH_TO_MS
    ret.vEgoCluster = cp_adas.vl["Cluster"]["Cluster_VehicleSpeed"] * conversion

    # Gas pedal
    ret.gasPressed = cp.vl["VDM_PropStatus"]["VDM_AcceleratorPedalPosition"] > 0

    # Brake pedal
    ret.brakePressed = cp.vl["iBESP2"]["iBESP2_BrakePedalApplied"] == 1

    # Steering wheel
    ret.steeringAngleDeg = cp.vl["EPAS_AdasStatus"]["EPAS_InternalSas"]
    ret.steeringRateDeg = cp.vl["EPAS_AdasStatus"]["EPAS_SteeringAngleSpeed"]
    ret.steeringTorque = cp.vl["EPAS_SystemStatus"]["EPAS_TorsionBarTorque"]
    ret.steeringPressed = self.update_steering_pressed(abs(ret.steeringTorque) > 1.0, 5)

    ret.steerFaultTemporary = cp.vl["EPAS_AdasStatus"]["EPAS_EacErrorCode"] != 0

    eac_status = cp.vl["EPAS_AdasStatus"]["EPAS_EacStatus"]
    ret.steerFaultPermanent = eac_status == 4
    # stock ACM shows EAC errors when inactive, only fault when EAC is active
    ret.steerFaultTemporary = eac_status == 2 and ret.steerFaultTemporary
    # EPAS reports a dedicated error when the driver overrides the angle steering request
    ret.steeringDisengage = eac_status == 2 and cp.vl["EPAS_AdasStatus"]["EPAS_EacErrorCode"] == 12  # EPAS_Hands_On_Detn_Err

    # Cruise state
    speed = min(int(cp_adas.vl["ACM_tsrCmd"]["ACM_tsrSpdDisClsMain"]), 85)
    self.last_speed = speed if speed != 0 else self.last_speed
    ret.cruiseState.enabled = cp_cam.vl["ACM_Status"]["ACM_FeatureStatus"] == 1
    # TODO: find cruise set speed on CAN
    ret.cruiseState.speed = self.last_speed * CV.MPH_TO_MS  # detected speed limit
    if not self.CP.openpilotLongitudinalControl:
      ret.cruiseState.speed = -1
    ret.cruiseState.available = True  # cp.vl["VDM_AdasSts"]["VDM_AdasInterfaceStatus"] == 1
    ret.cruiseState.standstill = cp.vl["VDM_AdasSts"]["VDM_AdasVehicleHoldStatus"] == 1

    # ACM_Status->ACM_FaultSupervisorState normally 1, appears to go to 3 when either:
    # 1. car in park/not in drive (normal)
    # 2. something (message from another ECU) ACM relies on is faulty
    #  * ACM_FaultStatus will stay 0 since ACM itself isn't faulted
    # TODO: ACM_FaultStatus hasn't been seen high yet, but log anyway
    ret.accFaulted = (cp_cam.vl["ACM_Status"]["ACM_FaultStatus"] == 1 or
                      # VDM_AdasFaultStatus=Brk_Intv is the default for some reason
                      # VDM_AdasFaultStatus=Cntr_Fault isn't fully understood, but we've seen it in the wild
                      # VDM_AdasFaultStatus=Imps_Cmd was seen when sending it rapidly changing ACC enable commands, or when ACC command drops out
                      cp.vl["VDM_AdasSts"]["VDM_AdasFaultStatus"] in (2, 3))  # 2=Cntr_Fault, 3=Imps_Cmd

    # Gear
    ret.gearShifter = GEAR_MAP.get(int(cp.vl["VDM_PropStatus"]["VDM_Prndl_Status"]), GearShifter.unknown)

    # Doors and seatbelt
    # GEN2 has no CAN signal for these, but stock ACC already handles disengaging
    # door locks prevent opening while driving
    # on standstill, stock ACC disengages when a door is opened or seatbelt is unbuckled
    if not (self.CP.flags & RivianFlags.GEN2):
      ret.doorOpen = any(cp_adas.vl["IndicatorLights"][door] != 2 for door in ("RearDriverDoor", "FrontPassengerDoor", "DriverDoor", "RearPassengerDoor"))
      ret.seatbeltUnlatched = cp.vl["RCM_Status"]["RCM_Status_IND_WARN_BELT_DRIVER"] != 0

    # Blinkers
    ret.leftBlinker = cp_adas.vl["IndicatorLights"]["TurnLightLeft"] in (1, 2)
    ret.rightBlinker = cp_adas.vl["IndicatorLights"]["TurnLightRight"] in (1, 2)

    # Blindspot
    # ret.leftBlindspot = False
    # ret.rightBlindspot = False

    # AEB
    ret.stockAeb = cp_cam.vl["ACM_AebRequest"]["ACM_EnableRequest"] != 0

    # Messages needed by carcontroller
    self.acm_lka_hba_cmd = copy.copy(cp_cam.vl["ACM_lkaHbaCmd"])
    if not (self.CP.flags & RivianFlags.GEN2):
      self.sccm_wheel_touch = copy.copy(cp.vl["SCCM_WheelTouch"])
    # This message can lag and send two messages at once, make sure we forward all of them
    adas_status_msgs = cp.vl_all["VDM_AdasSts"]
    self.vdm_adas_status = [dict(zip(adas_status_msgs, vals, strict=True)) for vals in zip(*adas_status_msgs.values(), strict=True)]
    # our own longitudinal frames the panda rejected (bus 192 echo)
    rejected = can_parsers[Bus.loopback].vl_all["ACM_longitudinalRequest"]["ACM_longitudinalRequest_Counter"]
    self.long_cmd_rejected_updated = len(rejected) > 0
    if self.long_cmd_rejected_updated:
      self.long_cmd_rejected_counter = int(rejected[-1])

    self.eac_error_code = int(cp.vl["EPAS_AdasStatus"]["EPAS_EacErrorCode"])
    self.eac_status = int(cp.vl["EPAS_AdasStatus"]["EPAS_EacStatus"])
    self.hands_on_level = int(cp.vl["EPAS_SystemStatus"]["EPAS_HandsOnLevel"])

    self.update_forwarded_buttons(can_parsers)
    self.update_button_source()
    self.update_bridge(ret, int(cp_adas.vl["ACM_tsrCmd"]["ACM_tsrSpdDisClsMain"]))
    CarStateExt.update(self, ret, can_parsers)
    if self.comma_buttons:
      self.update_comma_follow_level(self.scroll_steps)
    if self.bridge is not None and not self.bridge.stale and self.bridge.bridge_personality >= 0:
      # The bridge supplies the absolute gap. Do not also cycle it from the
      # kit's forwarded scroll-wheel event; retain native buttons if offline.
      ret.buttonEvents = [b for b in ret.buttonEvents if b.type != structs.CarState.ButtonEvent.Type.gapAdjustCruise]
    if self.bridge is not None:
      # rivianbridged writes these to RivianFollowLevel / LongitudinalPersonality
      ret_sp.rivianCommaGap = self.bridge.comma_gap
      ret_sp.rivianCommaFollowLevel = self.bridge.comma_follow_level

    return ret, ret_sp

  def update_button_source(self) -> None:
    """RivianButtonSource (0 Auto, 1 Comma, 2 Bridge): who owns set speed and follow gap. Comma needs the kit's
    forwarded wheel buttons, Auto and Comma fall back to the bridge without them. Bridge falls back to the wheel
    buttons, as before, while it is stale."""
    if self.bridge is None:
      self.comma_buttons = self.suppress_button_speed = False
      return
    requested = self.bridge.button_source
    if requested == ButtonSource.BRIDGE:
      source, reason = "bridge", "selected" if not self.bridge.stale else "selected, stale: wheel buttons as before"
    elif self.forwarded_buttons:
      source, reason = "comma", "auto, forwarded buttons" if requested == ButtonSource.AUTO else "selected"
    elif requested == ButtonSource.COMMA:
      source, reason = "bridge", "comma selected but no forwarded buttons"
    else:
      source, reason = "bridge", "auto, no forwarded buttons"
    if (source, reason) != self._button_source_log:
      carlog.warning("rivian buttons: source=%s reason=%s", source, reason)
      self._button_source_log = (source, reason)

    if source != self.button_source and source == "bridge":
      self.bridge.comma_follow_level = 0  # back on the bridge's level; picked up again from there next time
    self.button_source = source
    self.comma_buttons = source == "comma"
    self.bridge.comma_gap = self.comma_buttons
    # no double handling: while the bridge has a target, the truck's own reaction to a press reaches us through it
    self.suppress_button_speed = source == "bridge" and not self.bridge.stale and self.bridge.set_speed_ms > 0

  def update_comma_follow_level(self, steps: int) -> None:
    """Comma: the scroll wheel moves the follow level 1-4 one per counter step, clamped. Published in carStateSP,
    rivianbridged writes it to RivianFollowLevel and its personality to LongitudinalPersonality, as for the bridge's level."""
    bridge = self.bridge
    if bridge is None:
      return
    level = bridge.comma_follow_level
    if level not in FOLLOW_LEVELS:
      # start where the gap is: the fresh bridge's level, else LongitudinalPersonality once rivianbridged read it
      if not bridge.stale and bridge.follow_level in FOLLOW_LEVELS:
        level = bridge.follow_level
      elif bridge.personality_param in PERSONALITY_FOLLOW_LEVEL:
        level = PERSONALITY_FOLLOW_LEVEL[bridge.personality_param]
      elif steps:
        level = 2
      else:
        return
      bridge.comma_follow_level = level
    if steps:
      # RivianScrollInvert False: counter up = farther
      new_level = max(FOLLOW_LEVELS[0], min(level + (-steps if bridge.scroll_invert else steps), FOLLOW_LEVELS[-1]))
      carlog.warning("rivian buttons: gap delta=%d invert=%s level=%d->%d", steps, bridge.scroll_invert, level, new_level)
      bridge.comma_follow_level = new_level

  def update_bridge(self, ret: structs.CarState, tsr_speed: int = 0) -> None:
    if self.bridge is None:
      return
    if not ret.cruiseState.enabled:
      self._last_bridge_speed_cluster = 0.
      self._gas_override = False

    # yeetfollow traffic sign detection: a newly detected sign within ~20 mph of the
    # set speed moves it to the sign + TrafficSignOffset. There the bridge rewrote the
    # set speed every frame, so this only took effect without a bridge target or
    # during an accelerator override.
    sign_speed = self.sign_speed
    if tsr_speed not in (0, 254, 255):  # 0=No Recognition, 254=Reserved, 255=Invalid
      sign_speed = min(tsr_speed * CV.MPH_TO_MS, MAX_SET_SPEED)  # 253=Unlimited_Speed
    # Comma ignores the bridge's set speed and follow level, sign offset and gas override stay
    bridge_target = not self.comma_buttons and not self.bridge.stale and self.bridge.set_speed_ms > 0
    if sign_speed != self.sign_speed and abs(self.set_speed_cluster - sign_speed) <= 9 and \
       self.bridge.sign_offset != 0 and (not bridge_target or self._gas_override):
      self.set_speed_cluster = sign_speed * (1 + 5 * self.bridge.sign_offset / 100)
    self.sign_speed = sign_speed

    # Follow sync is independent of gasPressed AND cruise engagement. Keep
    # this at the top level: nesting under gas override caused 06f98b3's bug.
    if not self.bridge.stale:
      target_cluster_ms = self.bridge.set_speed_ms
      if self.comma_buttons:
        # tracked, not applied: a later fallback to the bridge only applies its next change, no jump on the switch
        if ret.cruiseState.enabled and target_cluster_ms > 0:
          self._last_bridge_speed_cluster = target_cluster_ms
      else:
        # rivianbridged writes the bridge's personality itself while it is fresh and the comma does not own the gap
        # Accept single mph/kph steps while ignoring floating-point noise.
        if ret.cruiseState.enabled and target_cluster_ms > 0 and abs(target_cluster_ms - self._last_bridge_speed_cluster) > 0.01:
          self._last_bridge_speed_cluster = target_cluster_ms
          self.set_speed_cluster = target_cluster_ms
          self._gas_override = False

    # Hold an accelerator override until the bridge set speed changes. Applying
    # bridge changes only once also lets the kit's speed buttons keep working.
    # Compare and store dash speeds; CarStateExt converts only the planner output.
    if ret.cruiseState.enabled and ret.gasPressed and ret.vEgoCluster > self.set_speed_cluster:
      self.set_speed_cluster = ret.vEgoCluster
      self._gas_override = True

  @staticmethod
  def get_can_parsers(CP, CP_SP):
    return {
      Bus.pt: CANParser(DBC[CP.carFingerprint][Bus.pt], [], 0),
      Bus.adas: CANParser(DBC[CP.carFingerprint][Bus.pt], [], 1),
      Bus.cam: CANParser(DBC[CP.carFingerprint][Bus.pt], [], 2),
      # 192 = safety-rejected TX echo of bus 0
      Bus.loopback: CANParser(DBC[CP.carFingerprint][Bus.pt], [("ACM_longitudinalRequest", float('nan'))], 192),
      **CarStateExt.get_parser(CP, CP_SP),
    }
