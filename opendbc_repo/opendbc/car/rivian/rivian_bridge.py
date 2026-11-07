"""TCM bridge values for the Rivian CarState.

yeet-angle-bridged: the HTTP polling / streaming and every Params read and write live in their own process,
rivianbridged (openpilot/sunnypilot/selfdrive/car/rivianbridged.py). card reads its latest rivianBridgeSP message
without blocking and hands the plain values to RivianBridge here before each CarState update, and publishes the comma
follow level back (rivianButtonsSP) for rivianbridged to persist. Nothing in here does network, file or Params access,
and nothing is shared with another thread: this module must stay importable without cereal.
"""

import math
from dataclasses import dataclass

STALE_AFTER = 2.0
# truck stalk follow levels, RivianFollowLevel (0 = none, the planner uses LongitudinalPersonality then)
FOLLOW_LEVELS = (1, 2, 3, 4)
# the LongitudinalPersonality written for a follow level, for the UI and distance bars, and what the planner falls back
# to once the bridge is stale: the bridge's own mapping, the nearest personality with a gap at least as long as the
# level's (T_FOLLOW 0.6 / 1.1 / 1.8 s vs the levels' 0.6 / 1.0 / 1.4 / 1.8 s), so a fallback never follows closer
FOLLOW_LEVEL_PERSONALITY = {1: 0, 2: 1, 3: 2, 4: 2}
# yeet-angle-standalone: the follow level a LongitudinalPersonality starts the wheel scroll at (T_FOLLOW 0.6 / 1.1 / 1.8 s)
PERSONALITY_FOLLOW_LEVEL = {0: 1, 1: 2, 2: 4}


class ButtonSource:
  """RivianButtonSource: who owns set speed and follow gap. Auto = Comma with the xnor kit's forwarded wheel buttons."""
  AUTO = 0
  COMMA = 1
  BRIDGE = 2


@dataclass
class BridgeValues:
  """One rivianBridgeSP message as plain values. The defaults are what card uses before the first message."""
  stale: bool = True
  set_speed_ms: float = 0.  # TCM ACM_AccHmi_SetSpeed in dash m/s, 0 = no target
  follow_level: int = -1  # 1-4, -1 = none
  follow_personality: int = -1  # 0-2, -1 = none
  # TrafficSignOffset: 0=off, 1/2/3 = sign speed +5/10/15 %
  sign_offset: int = 1
  # RivianButtonSource, RivianScrollInvert and LongitudinalPersonality (None = not read yet)
  button_source: int = ButtonSource.AUTO
  scroll_invert: bool = False
  personality_param: int | None = None


def valid_set_speed(speed) -> float:
  return speed if type(speed) in (int, float) and math.isfinite(speed) and speed > 0 else 0


def valid_follow_level(level) -> int:
  return level if type(level) is int and level in FOLLOW_LEVELS else -1


def valid_personality(personality) -> int:
  return personality if type(personality) is int and personality in (0, 1, 2) else -1


def bridge_personality(follow_level: int, follow_personality: int) -> int:
  """The personality to write: the follow level's nearest one, or the bridge's follow_personality without a level."""
  return FOLLOW_LEVEL_PERSONALITY[follow_level] if follow_level > 0 else follow_personality


class RivianBridge:
  """Plain value holder, set by card before each CarState update. comma_gap and comma_follow_level go the other way:
  card publishes them and rivianbridged writes RivianFollowLevel / LongitudinalPersonality."""

  def __init__(self):
    self.values = BridgeValues()
    # set by card each cycle: the last rivianBridgeSP message is older than STALE_AFTER (or there was none yet)
    self.message_stale = True
    # set by carstate while the wheel buttons own the gap: the bridge's follow level and personality are ignored and
    # comma_follow_level (0 = not set yet) is written instead
    self.comma_gap = False
    self.comma_follow_level = 0

  def apply(self, values: BridgeValues, message_stale: bool = False) -> None:
    self.values = values
    self.message_stale = message_stale

  @property
  def sign_offset(self) -> int:
    return self.values.sign_offset

  @sign_offset.setter
  def sign_offset(self, offset: int) -> None:
    self.values.sign_offset = offset

  @property
  def button_source(self) -> int:
    return self.values.button_source

  @button_source.setter
  def button_source(self, source: int) -> None:
    self.values.button_source = source

  @property
  def scroll_invert(self) -> bool:
    return self.values.scroll_invert

  @scroll_invert.setter
  def scroll_invert(self, invert: bool) -> None:
    self.values.scroll_invert = invert

  @property
  def personality_param(self) -> int | None:
    return self.values.personality_param

  @personality_param.setter
  def personality_param(self, personality: int | None) -> None:
    self.values.personality_param = personality

  @property
  def set_speed_ms(self) -> float:
    """TCM ACM_AccHmi_SetSpeed in dash m/s, not true wheel speed."""
    return valid_set_speed(self.values.set_speed_ms)

  @property
  def follow_personality(self) -> int:
    return valid_personality(self.values.follow_personality)

  @property
  def follow_level(self) -> int:
    return valid_follow_level(self.values.follow_level)

  @property
  def bridge_personality(self) -> int:
    return bridge_personality(self.follow_level, self.follow_personality)

  @property
  def stale(self) -> bool:
    return self.values.stale is not False or self.message_stale
