"""TCM bridge polling and personality / follow level persistence, outside the 100 Hz control loop."""

import json
import math
import os
import threading
import time
import urllib.request
from pathlib import Path

from opendbc.car.carlog import carlog

REPO_CONF = Path(__file__).resolve().parents[4] / "rivian-bridge.conf"
DATA_CONF = Path("/data/rivian-bridge.conf")
# Tried in order: Nebula first, then the truck LAN.
DEFAULT_URLS = ("http://192.168.4.34:8082", "http://172.28.1.64:8082")
POLL_INTERVAL = 0.3
STALE_AFTER = 2.0
BACKGROUND_CORES = {0, 1, 2, 3}
RT_CORES = {4, 5, 7}
# truck stalk follow levels, RivianFollowLevel (0 = none, the planner uses LongitudinalPersonality then)
FOLLOW_LEVELS = (1, 2, 3, 4)
# the LongitudinalPersonality written for a follow level, for the UI and distance bars, and what the planner falls back
# to once the bridge is stale: the bridge's own mapping, the nearest personality with a gap at least as long as the
# level's (T_FOLLOW 0.6 / 1.1 / 1.8 s vs the levels' 0.6 / 1.0 / 1.4 / 1.8 s), so a fallback never follows closer
FOLLOW_LEVEL_PERSONALITY = {1: 0, 2: 1, 3: 2, 4: 2}


def _drop_rt_scheduling_for_this_thread():
  # card creates us after pinning itself to core 4 with SCHED_FIFO. pthreads
  # inherit both settings; pid=0 changes ONLY the calling (poll) thread.
  try:
    os.sched_setscheduler(0, os.SCHED_OTHER, os.sched_param(0))
  except OSError:
    carlog.exception("Unable to drop Rivian bridge realtime scheduling")
  try:
    cpus = set(range(os.cpu_count() or 1))
    allowed = (cpus & BACKGROUND_CORES) or (cpus - RT_CORES)
    if allowed:
      os.sched_setaffinity(0, allowed)
  except OSError:
    carlog.exception("Unable to move Rivian bridge to background CPUs")


def _parse_bridge_urls(text):
  urls = []
  for line in text.splitlines():
    url = line.strip().rstrip("/")
    if url and not url.startswith("#") and url not in urls:
      urls.append(url)
  return urls


def _read_bridge_urls():
  # The device override wins over the shipped repo conf. One URL per line.
  for path in (DATA_CONF, REPO_CONF):
    try:
      urls = _parse_bridge_urls(Path(path).read_text())
    except OSError:
      continue
    if urls:
      return urls
  return list(DEFAULT_URLS)


class RivianBridge:
  def __init__(self, url=None, *, params=None, start=True):
    if url is None:
      self.urls = _read_bridge_urls()
    else:
      self.urls = _parse_bridge_urls(url if isinstance(url, str) else "\n".join(url)) or list(DEFAULT_URLS)
    self._url_index = 0
    self._last_ok_url = None
    self.state = {}
    self._received_at = -math.inf
    self._lock = threading.Lock()
    self._params = params
    self._requested_personality = None
    self._last_written_personality = None
    self._last_written_follow_level = None
    # TrafficSignOffset: 0=off, 1/2/3 = sign speed +5/10/15 %, read here so carstate never touches Params
    self.sign_offset = 1
    self._thread = threading.Thread(target=self._poll_loop, name="rivian_bridge", daemon=True)
    if start:
      self._thread.start()

  @property
  def url(self):
    return self.urls[self._url_index]

  def _poll_once(self):
    url = self.url
    try:
      with urllib.request.urlopen(f"{url}/state", timeout=1) as response:
        data = json.loads(response.read())
      if not isinstance(data, dict):
        raise ValueError("Bridge state must be an object")
    except Exception:
      # A lost HTTP connection must not leave the last response fresh forever.
      data = {}
      # One URL per poll, so a dead link costs at most one timeout. The next poll tries the next URL.
      self._url_index = (self._url_index + 1) % len(self.urls)
    else:
      # Stick to the URL that answered. Logged once per switch, not per poll.
      if url != self._last_ok_url:
        carlog.warning("Rivian bridge switched to %s (was %s)", url, self._last_ok_url)
        self._last_ok_url = url
    with self._lock:
      self.state = data
      self._received_at = time.monotonic()

  def _poll_loop(self):
    _drop_rt_scheduling_for_this_thread()
    while True:
      self._poll_once()
      self._sync_personality()
      self._sync_follow_level()
      self._read_sign_offset()
      time.sleep(POLL_INTERVAL)

  def request_personality(self, personality):
    # Only an in-memory handoff from carstate: no Params, filesystem or network
    # access on the realtime thread, even when the driver changes the gap.
    if type(personality) is int and personality in (0, 1, 2):
      self._requested_personality = personality

  def _sync_personality(self):
    personality = self._requested_personality
    if self.stale or self.bridge_personality < 0:
      self._last_written_personality = None
      self._requested_personality = None
      return
    if personality is None or personality != self.bridge_personality or personality == self._last_written_personality:
      return
    try:
      if self._params is None:
        from openpilot.common.params import Params
        self._params = Params()
      # rx-master's typed Params.put is asynchronous by default and takes an int.
      self._params.put("LongitudinalPersonality", personality)
      self._last_written_personality = personality
    except Exception:
      carlog.exception("Unable to sync Rivian bridge personality")

  def _sync_follow_level(self):
    # yeet-angle-brake-levels: the truck's follow level 1-4 for the planner, 0 while the bridge is stale or has no valid
    # level, so it falls back to LongitudinalPersonality. Written on change, from this (poll) thread only.
    level = 0 if self.stale else max(self.follow_level, 0)
    if level == self._last_written_follow_level:
      return
    try:
      if self._params is None:
        from openpilot.common.params import Params
        self._params = Params()
      self._params.put("RivianFollowLevel", level)
      self._last_written_follow_level = level
    except Exception:
      carlog.exception("Unable to sync Rivian bridge follow level")

  def _read_sign_offset(self):
    try:
      if self._params is None:
        from openpilot.common.params import Params
        self._params = Params()
      offset = self._params.get("TrafficSignOffset", return_default=True)
      if type(offset) is int and offset in (0, 1, 2, 3):
        self.sign_offset = offset
    except Exception:
      pass

  @property
  def set_speed_ms(self):
    """TCM ACM_AccHmi_SetSpeed in dash m/s, not true wheel speed."""
    with self._lock:
      speed = self.state.get("set_speed_ms", 0)
    return speed if type(speed) in (int, float) and math.isfinite(speed) and speed > 0 else 0

  @property
  def follow_personality(self):
    with self._lock:
      personality = self.state.get("follow_personality", -1)
    return personality if type(personality) is int and personality in (0, 1, 2) else -1

  @property
  def bridge_personality(self):
    """The personality to write: the follow level's nearest one, or the bridge's follow_personality without a level."""
    level = self.follow_level
    return FOLLOW_LEVEL_PERSONALITY[level] if level > 0 else self.follow_personality

  @property
  def follow_level(self):
    with self._lock:
      level = self.state.get("follow_level", -1)
    return level if type(level) is int and level in FOLLOW_LEVELS else -1

  @property
  def stale(self):
    with self._lock:
      return self.state.get("stale", True) is not False or time.monotonic() - self._received_at > STALE_AFTER
