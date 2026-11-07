#!/usr/bin/env python3
"""yeet-angle-bridged: the Rivian TCM bridge, out of card's process (automotive/openpilot#9).

Owns everything card's in-process poll thread did: the bridge HTTP connection (GET /stream, SSE, falling back to polling
GET /state on older bridges), the URL list and rotation, the stale rules, every Params read the Rivian CarState needs
(TrafficSignOffset, RivianButtonSource, RivianScrollInvert, LongitudinalPersonality) and the RivianFollowLevel /
LongitudinalPersonality writes, the comma's wheel scroll level included (read back from carStateSP). Publishes
rivianBridgeSP on every bridge event (coalesced to 50 Hz) and at least at 10 Hz; card reads it without blocking.
"""
import json
import math
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import openpilot.cereal.messaging as messaging
from openpilot.common.basedir import BASEDIR
from openpilot.common.params import Params
from openpilot.common.realtime import set_core_affinity
from openpilot.common.swaglog import cloudlog
from opendbc.car.rivian.rivian_bridge import (FOLLOW_LEVEL_PERSONALITY, FOLLOW_LEVELS, STALE_AFTER, ButtonSource,
                                              bridge_personality, valid_follow_level, valid_personality, valid_set_speed)

REPO_CONF = Path(BASEDIR) / "rivian-bridge.conf"
DATA_CONF = Path("/data/rivian-bridge.conf")
# Tried in order: Nebula first, then the truck LAN.
DEFAULT_URLS = ("http://192.168.4.34:8082", "http://172.28.1.64:8082")
BACKGROUND_CORES = [0, 1, 2, 3]

HTTP_TIMEOUT = 1.0
POLL_INTERVAL = 0.1  # GET /state, older bridges without /stream
# /stream: heartbeat at least every 250 ms, so 1 s without an event is stale (and the read times out)
STREAM_STALE_AFTER = 1.0
STREAM_BACKOFF = (0.25, 0.5, 1., 2., 5.)  # s before the next /stream attempt after consecutive failures, polling meanwhile
STREAM_RETRY_NO_STREAM = 30.  # s, a bridge that answered 404 to /stream is asked again this often
PUBLISH_MIN_INTERVAL = 0.02  # 50 Hz max, bridge events are coalesced
PUBLISH_MAX_INTERVAL = 0.1  # 10 Hz min
PARAMS_INTERVAL = 0.3


def parse_bridge_urls(text):
  urls = []
  for line in text.splitlines():
    url = line.strip().rstrip("/")
    if url and not url.startswith("#") and url not in urls:
      urls.append(url)
  return urls


def read_bridge_urls():
  # The device override wins over the shipped repo conf. One URL per line.
  for path in (DATA_CONF, REPO_CONF):
    try:
      urls = parse_bridge_urls(Path(path).read_text())
    except OSError:
      continue
    if urls:
      return urls
  return list(DEFAULT_URLS)


def parse_state(raw):
  data = json.loads(raw)
  if not isinstance(data, dict):
    raise ValueError("Bridge state must be an object")
  return data


class NoStream(Exception):
  """The bridge answered, but has no /stream (404, or not an event stream)."""


class SSEParser:
  """text/event-stream: "data:" lines up to a blank line are one event; comments (":") and other fields are skipped."""
  def __init__(self):
    self._data = []

  def feed_line(self, line):
    """One line without its line ending. Returns the event's data when the line completes one, else None."""
    if line == "":
      if not self._data:
        return None
      data, self._data = "\n".join(self._data), []
      return data
    if line.startswith(":"):
      return None
    field, _, value = line.partition(":")
    if field == "data":
      self._data.append(value[1:] if value.startswith(" ") else value)
    return None


class BridgeState:
  """The latest bridge state, shared between the connection thread and the main loop of this process only."""
  def __init__(self):
    self._lock = threading.Lock()
    self._new = threading.Event()
    self.data = {}
    self.received_at = -math.inf
    self.streaming = False
    self.url = ""

  def set(self, data, url, streaming, now=None):
    with self._lock:
      self.data = data
      self.received_at = time.monotonic() if now is None else now
      self.url = url
      self.streaming = streaming
    self._new.set()

  def wait(self, timeout):
    """True when a new state arrived (since the last call), within timeout."""
    new = self._new.wait(timeout)
    self._new.clear()
    return new

  def snapshot(self):
    with self._lock:
      return self.data, self.received_at, self.url, self.streaming


class BridgeConnection:
  """GET /stream, else GET /state polling, over the URL list. step() is one connection attempt, stream or poll."""
  def __init__(self, state, urls=None, *, urlopen=None, clock=time.monotonic, sleep=time.sleep):
    self.state = state
    self.urls = urls if urls is not None else read_bridge_urls()
    if not self.urls:
      self.urls = list(DEFAULT_URLS)
    self._url_index = 0
    self._last_ok_url = None
    self._urlopen = urlopen or urllib.request.urlopen
    self._clock = clock
    self._sleep = sleep
    self._stream_fails = 0
    self._next_stream = 0.  # clock time of the next /stream attempt; polling until then
    self._next_poll = 0.

  @property
  def url(self):
    return self.urls[self._url_index]

  def _ok(self, url):
    # Stick to the URL that answered. Logged once per switch, not per poll.
    if url != self._last_ok_url:
      cloudlog.warning(f"Rivian bridge switched to {url} (was {self._last_ok_url})")
      self._last_ok_url = url

  def _rotate(self):
    # One URL per attempt, so a dead link costs at most one timeout. The next attempt tries the next URL, stream first.
    self._url_index = (self._url_index + 1) % len(self.urls)
    self._stream_fails = 0
    self._next_stream = 0.

  def _stream_failed(self, no_stream=False):
    if no_stream:
      delay = STREAM_RETRY_NO_STREAM
    else:
      delay = STREAM_BACKOFF[min(self._stream_fails, len(STREAM_BACKOFF) - 1)]
      self._stream_fails += 1
    self._next_stream = self._clock() + delay

  def step(self):
    if self._clock() >= self._next_stream:
      self.stream_once()
    else:
      self.poll_once()

  def stream_once(self):
    """Connect to /stream and read events until it stops. Fails over to polling (this URL) on any error."""
    url = self.url
    events = 0
    try:
      with self._urlopen(f"{url}/stream", timeout=HTTP_TIMEOUT) as response:
        if "text/event-stream" not in response.headers.get("Content-Type", ""):
          raise NoStream
        parser = SSEParser()
        # the socket timeout ends the read after 1 s without data, the heartbeat is 250 ms
        for raw in response:
          data = parser.feed_line(raw.decode("utf-8", "replace").rstrip("\r\n"))
          if data is None:
            continue
          try:
            state = parse_state(data)
          except ValueError:
            state = {}  # an invalid event must not leave the last one fresh
          if events == 0:
            self._ok(url)
            self._stream_fails = 0
          events += 1
          self.state.set(state, url, True)
    except (NoStream, urllib.error.HTTPError) as e:
      # older bridge without /stream: poll it, ask again now and then
      self._stream_failed(no_stream=isinstance(e, NoStream) or e.code == 404)
      return
    except Exception:
      pass
    # connection failed, timed out (no event for 1 s) or ended: stale until the next state, poll meanwhile
    self.state.set({}, url, events > 0)
    self._stream_failed()

  def poll_once(self):
    now = self._clock()
    if now < self._next_poll:
      self._sleep(self._next_poll - now)
    self._next_poll = max(now, self._next_poll) + POLL_INTERVAL
    url = self.url
    try:
      with self._urlopen(f"{url}/state", timeout=HTTP_TIMEOUT) as response:
        data = parse_state(response.read())
    except Exception:
      # A lost HTTP connection must not leave the last response fresh forever.
      data = {}
      self._rotate()
    else:
      self._ok(url)
    self.state.set(data, url, False)

  def run(self):
    while True:
      try:
        self.step()
      except Exception:
        cloudlog.exception("rivianbridged: connection step failed")
        self._sleep(POLL_INTERVAL)


class RivianBridged:
  """Params reads and writes and the rivianBridgeSP message, from the latest bridge state and carStateSP."""
  def __init__(self, state, params=None, *, clock=time.monotonic):
    self.state = state
    self.params = params
    self._clock = clock
    self._last_written_personality = None
    self._last_written_follow_level = None
    self.sign_offset = 1
    self.button_source = ButtonSource.AUTO
    self.scroll_invert = False
    self.personality_param = None
    # from card's carStateSP: the wheel buttons own the gap, and their level (0 = not set yet)
    self.comma_gap = False
    self.comma_follow_level = 0
    # the current bridge values, see update_bridge
    self.stale = True
    self.set_speed_ms = 0.
    self.follow_level = -1
    self.follow_personality = -1
    self.url = ""
    self.streaming = False
    self.age = math.inf

  def _params(self):
    if self.params is None:
      self.params = Params()
    return self.params

  def update_bridge(self):
    data, received_at, self.url, self.streaming = self.state.snapshot()
    self.age = self._clock() - received_at
    stale_after = STREAM_STALE_AFTER if self.streaming else STALE_AFTER
    self.stale = data.get("stale", True) is not False or self.age > stale_after
    self.set_speed_ms = valid_set_speed(data.get("set_speed_ms", 0))
    self.follow_level = valid_follow_level(data.get("follow_level", -1))
    self.follow_personality = valid_personality(data.get("follow_personality", -1))

  def update_comma(self, car_state_sp):
    self.comma_gap = bool(car_state_sp.rivianCommaGap)
    level = int(car_state_sp.rivianCommaFollowLevel)
    self.comma_follow_level = level if level in FOLLOW_LEVELS else 0

  def sync_params(self):
    self.sync_personality()
    self.sync_follow_level()

  def sync_personality(self):
    if self.comma_gap:
      self._sync_comma_personality()
      return
    personality = bridge_personality(self.follow_level, self.follow_personality)
    if self.stale or personality < 0:
      # recovery must restore the bridge's value even if it is the one written before the outage
      self._last_written_personality = None
      return
    if personality == self._last_written_personality:
      return
    try:
      # rx-master's typed Params.put is asynchronous by default and takes an int.
      self._params().put("LongitudinalPersonality", personality)
      self._last_written_personality = personality
    except Exception:
      cloudlog.exception("Unable to sync Rivian bridge personality")

  def _sync_comma_personality(self):
    # the wheel scroll's level through the same mapping as the bridge's, written on change
    level = self.comma_follow_level
    if level not in FOLLOW_LEVELS:
      return
    personality = FOLLOW_LEVEL_PERSONALITY[level]
    if personality == self._last_written_personality:
      return
    try:
      self._params().put("LongitudinalPersonality", personality)
      self._last_written_personality = personality
      self.personality_param = personality
    except Exception:
      cloudlog.exception("Unable to sync Rivian wheel button personality")

  def sync_follow_level(self):
    # yeet-angle-brake-levels: the truck's follow level 1-4 for the planner, 0 while the bridge is stale or has no valid
    # level, so it falls back to LongitudinalPersonality. Written on change.
    # yeet-angle-standalone: the wheel scroll's level instead while the wheel buttons own the gap.
    if self.comma_gap:
      level = self.comma_follow_level if self.comma_follow_level in FOLLOW_LEVELS else 0
    else:
      level = 0 if self.stale else max(self.follow_level, 0)
    if level == self._last_written_follow_level:
      return
    try:
      self._params().put("RivianFollowLevel", level)
      self._last_written_follow_level = level
    except Exception:
      cloudlog.exception("Unable to sync Rivian bridge follow level")

  def read_params(self):
    try:
      params = self._params()
      # TrafficSignOffset: 0=off, 1/2/3 = sign speed +5/10/15 %
      offset = params.get("TrafficSignOffset", return_default=True)
      if type(offset) is int and offset in (0, 1, 2, 3):
        self.sign_offset = offset
      source = params.get("RivianButtonSource", return_default=True)
      if type(source) is int and source in (ButtonSource.AUTO, ButtonSource.COMMA, ButtonSource.BRIDGE):
        self.button_source = source
      self.scroll_invert = params.get_bool("RivianScrollInvert")
      personality = params.get("LongitudinalPersonality", return_default=True)
      if type(personality) is int and personality in (0, 1, 2):
        self.personality_param = personality
    except Exception:
      pass

  def message(self):
    msg = messaging.new_message("rivianBridgeSP")
    msg.valid = True
    bridge = msg.rivianBridgeSP
    bridge.stale = self.stale
    bridge.setSpeedMs = float(self.set_speed_ms)
    bridge.followLevel = self.follow_level
    bridge.followPersonality = self.follow_personality
    bridge.signOffset = self.sign_offset
    bridge.buttonSource = self.button_source
    bridge.scrollInvert = self.scroll_invert
    bridge.personalityParam = -1 if self.personality_param is None else self.personality_param
    bridge.url = self.url
    bridge.streaming = self.streaming
    bridge.ageMs = float(min(self.age, 1e6) * 1000.)
    return msg


def main():
  # normal priority (manager does not start us realtime), off card's and the other realtime cores
  try:
    set_core_affinity(BACKGROUND_CORES)
  except OSError:
    cloudlog.exception("rivianbridged: unable to move to background CPUs")

  state = BridgeState()
  connection = BridgeConnection(state)
  cloudlog.warning(f"rivianbridged: bridge URLs {connection.urls}")
  threading.Thread(target=connection.run, name="rivianbridged_http", daemon=True).start()

  bridged = RivianBridged(state)
  pm = messaging.PubMaster(["rivianBridgeSP"])
  sm = messaging.SubMaster(["carStateSP"])
  last_publish = last_params = -math.inf
  while True:
    state.wait(PUBLISH_MAX_INTERVAL)
    sm.update(0)
    if sm.updated["carStateSP"]:
      bridged.update_comma(sm["carStateSP"])
    now = time.monotonic()
    if now - last_params >= PARAMS_INTERVAL:
      bridged.read_params()
      last_params = now
    bridged.update_bridge()
    bridged.sync_params()
    pm.send("rivianBridgeSP", bridged.message())
    last_publish = time.monotonic()
    # coalesce bursts of bridge events
    time.sleep(max(0., last_publish + PUBLISH_MIN_INTERVAL - time.monotonic()))


if __name__ == "__main__":
  main()
