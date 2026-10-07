"""TCM bridge polling and personality persistence, outside the 100 Hz control loop."""

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
DEFAULT_URL = "http://172.28.1.64:8082"
POLL_INTERVAL = 0.3
STALE_AFTER = 2.0
BACKGROUND_CORES = {0, 1, 2, 3}
RT_CORES = {4, 5, 7}


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


def _read_bridge_url():
  for path in (REPO_CONF, DATA_CONF):
    try:
      url = Path(path).read_text().strip()
      if url:
        return url.rstrip("/")
    except OSError:
      continue
  return DEFAULT_URL


class RivianBridge:
  def __init__(self, url=None, *, params=None, start=True):
    self.url = _read_bridge_url() if url is None else url.rstrip("/")
    self.state = {}
    self._received_at = -math.inf
    self._lock = threading.Lock()
    self._params = params
    self._requested_personality = None
    self._last_written_personality = None
    self._thread = threading.Thread(target=self._poll_loop, name="rivian_bridge", daemon=True)
    if start:
      self._thread.start()

  def _poll_once(self):
    try:
      with urllib.request.urlopen(f"{self.url}/state", timeout=1) as response:
        data = json.loads(response.read())
      if not isinstance(data, dict):
        raise ValueError("Bridge state must be an object")
    except Exception:
      # A lost HTTP connection must not leave the last response fresh forever.
      data = {}
    with self._lock:
      self.state = data
      self._received_at = time.monotonic()

  def _poll_loop(self):
    _drop_rt_scheduling_for_this_thread()
    while True:
      self._poll_once()
      self._sync_personality()
      time.sleep(POLL_INTERVAL)

  def request_personality(self, personality):
    # Only an in-memory handoff from carstate: no Params, filesystem or network
    # access on the realtime thread, even when the driver changes the gap.
    if type(personality) is int and personality in (0, 1, 2):
      self._requested_personality = personality

  def _sync_personality(self):
    personality = self._requested_personality
    if self.stale or self.follow_personality < 0:
      self._last_written_personality = None
      self._requested_personality = None
      return
    if personality is None or personality != self.follow_personality or personality == self._last_written_personality:
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

  @property
  def set_speed_ms(self):
    with self._lock:
      speed = self.state.get("set_speed_ms", 0)
    return speed if type(speed) in (int, float) and math.isfinite(speed) and speed > 0 else 0

  @property
  def follow_personality(self):
    with self._lock:
      personality = self.state.get("follow_personality", -1)
    return personality if type(personality) is int and personality in (0, 1, 2) else -1

  @property
  def stale(self):
    with self._lock:
      return self.state.get("stale", True) is not False or time.monotonic() - self._received_at > STALE_AFTER
