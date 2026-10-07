"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import math
from enum import StrEnum

from opendbc.car import Bus, DT_CTRL, structs
from opendbc.can.parser import CANParser
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.common.filter_simple import FirstOrderFilter
from opendbc.car.rivian.values import DBC
from opendbc.sunnypilot.car.rivian.values import RivianFlagsSP

ButtonType = structs.CarState.ButtonEvent.Type

MAX_SET_SPEED = 50.0  # dash m/s (180 kph)
MIN_SET_SPEED = 20 * CV.MPH_TO_MS
MIN_SPEED_FOR_RATIO = 5.0  # m/s, avoid cluster quantization near standstill
SPEED_RATIO_TAU = 5.0  # seconds


class CarStateExt:
  def __init__(self, CP: structs.CarParams, CP_SP: structs.CarParamsSP):
    self.CP = CP
    self.CP_SP = CP_SP

    # All driver inputs (bridge, kit buttons, stalk and gas override) use dash m/s.
    self.set_speed_cluster = 10.
    # True / dash speed. Use unity until the first valid sample, then filter.
    self.cluster_speed_ratio = FirstOrderFilter(1.0, SPEED_RATIO_TAU, DT_CTRL, initialized=False)
    self.increase_button = False
    self.decrease_button = False
    self.distance_button = 0
    self.increase_counter = 0
    self.decrease_counter = 0

  def update_longitudinal_upgrade(self, ret: structs.CarState, can_parsers: dict[StrEnum, CANParser]) -> None:
    cp_park = can_parsers[Bus.alt]
    cp_adas = can_parsers[Bus.adas]
    cp = can_parsers[Bus.pt]

    prev_increase_button = self.increase_button
    prev_decrease_button = self.decrease_button

    if self.CP.openpilotLongitudinalControl:
      # distance scroll wheel
      right_scroll = cp_park.vl["WheelButtons_Fwd"]["RightButton_Scroll"]
      if right_scroll != 255:
        if self.distance_button != right_scroll:
          ret.buttonEvents = [structs.CarState.ButtonEvent(pressed=False, type=ButtonType.gapAdjustCruise)]
        self.distance_button = right_scroll

      # button logic for set-speed
      self.increase_button = cp_park.vl["WheelButtons_Fwd"]["RightButton_RightClick"] == 2
      self.decrease_button = cp_park.vl["WheelButtons_Fwd"]["RightButton_LeftClick"] == 2

      self.increase_counter = self.increase_counter + 1 if self.increase_button else 0
      self.decrease_counter = self.decrease_counter + 1 if self.decrease_button else 0

      metric = cp_adas.vl["Cluster"]["Cluster_Unit"] == 0
      conversion = CV.KPH_TO_MS if metric else CV.MPH_TO_MS
      long_press_step = 10.0 if metric else 5.0
      set_speed_converted = self.set_speed_cluster * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH)

      if self.increase_button:
        if self.increase_counter % 66 == 0:
          self.set_speed_cluster = (int(math.ceil((set_speed_converted + 1) / long_press_step)) * long_press_step) * conversion
        elif not prev_increase_button:
          self.set_speed_cluster += conversion

      if self.decrease_button:
        if self.decrease_counter % 66 == 0:
          self.set_speed_cluster = (int(math.floor((set_speed_converted - 1) / long_press_step)) * long_press_step) * conversion
        elif not prev_decrease_button:
          self.set_speed_cluster -= conversion

      if not ret.cruiseState.enabled:
        self.set_speed_cluster = ret.vEgoCluster

      # VDM_UserAdasRequest: 0=IDLE, 1=UP_1, 2=UP_2, 3=DOWN_1, 4=DOWN_2
      stalk_down = int(cp.vl["VDM_AdasSts"]["VDM_UserAdasRequest"]) in (3, 4)
      if stalk_down:
        # Mimic Rivian ACC: stalk down sets speed to current speed (never decreases)
        self.set_speed_cluster = max(self.set_speed_cluster, ret.vEgoCluster)

      self.set_speed_cluster = max(MIN_SET_SPEED, min(self.set_speed_cluster, MAX_SET_SPEED))

      # Learn from the raw CAN speeds before interface/UI cluster processing.
      # Hold the last good ratio at low speed or with missing/invalid signals.
      if (math.isfinite(ret.vEgoRaw) and math.isfinite(ret.vEgoCluster) and
          ret.vEgoRaw > MIN_SPEED_FOR_RATIO and ret.vEgoCluster > MIN_SPEED_FOR_RATIO):
        self.cluster_speed_ratio.update(max(0.90, min(ret.vEgoRaw / ret.vEgoCluster, 1.0)))

      # Reuse the existing planner/display split; ego speed and control stay true.
      ret.cruiseState.speedCluster = self.set_speed_cluster
      ret.cruiseState.speed = self.set_speed_cluster * self.cluster_speed_ratio.x

    if self.CP.enableBsm:
      ret.leftBlindspot = cp_park.vl["BSM_BlindSpotIndicator_Fwd"]["BSM_BlindSpotIndicator_Left"] != 0
      ret.rightBlindspot = cp_park.vl["BSM_BlindSpotIndicator_Fwd"]["BSM_BlindSpotIndicator_Right"] != 0

  def update(self, ret: structs.CarState, can_parsers: dict[StrEnum, CANParser]) -> None:
    if self.CP_SP.flags & RivianFlagsSP.LONGITUDINAL_HARNESS_UPGRADE:
      self.update_longitudinal_upgrade(ret, can_parsers)

  @staticmethod
  def get_parser(CP, CP_SP) -> dict[StrEnum, CANParser]:
    messages = {}

    if CP_SP.flags & RivianFlagsSP.LONGITUDINAL_HARNESS_UPGRADE:
      messages[Bus.alt] = CANParser(DBC[CP.carFingerprint][Bus.alt], [], 1)

    return messages
