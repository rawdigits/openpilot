"""yeet-angle-bridged: card's side of rivianbridged. Reads the latest rivianBridgeSP without blocking and hands plain
values to the Rivian CarState's RivianBridge before each update. No network, file or Params access, no locks."""
import math
import time

import openpilot.cereal.messaging as messaging
from opendbc.car.rivian.rivian_bridge import STALE_AFTER, BridgeValues


def bridge_values(msg) -> BridgeValues:
  return BridgeValues(
    stale=bool(msg.stale),
    set_speed_ms=float(msg.setSpeedMs),
    follow_level=int(msg.followLevel),
    follow_personality=int(msg.followPersonality),
    sign_offset=int(msg.signOffset),
    button_source=int(msg.buttonSource),
    scroll_invert=bool(msg.scrollInvert),
    personality_param=int(msg.personalityParam) if msg.personalityParam >= 0 else None,
  )


class RivianBridgeReader:
  def __init__(self, bridge, sock=None, clock=time.monotonic):
    self.bridge = bridge
    self.sock = sock if sock is not None else messaging.sub_sock("rivianBridgeSP", conflate=True)
    self._clock = clock
    self.received_at = -math.inf

  def update(self) -> None:
    now = self._clock()
    msg = messaging.recv_one_or_none(self.sock)
    if msg is not None:
      self.received_at = now
      self.bridge.apply(bridge_values(msg.rivianBridgeSP))
    # no message for 2 s (rivianbridged gone or hung): stale, as a bridge without a response was before.
    # The last values (Params among them) are kept.
    self.bridge.message_stale = now - self.received_at > STALE_AFTER
