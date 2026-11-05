"""Background poller for Rivian bridge HTTP API on TCM."""

import json
import os
import threading
import time
import urllib.request

from openpilot.common.params import Params
from opendbc.car.carlog import carlog

REPO_CONF = "/data/openpilot/rivian-bridge.conf"
DATA_CONF = "/data/rivian-bridge.conf"
# Tried in order: Nebula first, then the truck LAN.
DEFAULT_URLS = ("http://192.168.4.34:8082", "http://172.28.1.64:8082")

# openpilot's realtime cores: card + controlsd on 4 (SCHED_FIFO 53), radard +
# plannerd on 5 (SCHED_FIFO 51), modeld on 7 (SCHED_FIFO 54).
RT_CORES = {4, 5, 7}
# Where openpilot already puts its background/network threads: athenad, uploader
# and sunnylinkd all call set_core_affinity([0, 1, 2, 3]). This poll thread is the
# same kind of work (periodic HTTP), so it gets the same home.
BACKGROUND_CORES = {0, 1, 2, 3}


def _drop_rt_scheduling_for_this_thread():
    """Take the calling thread off the realtime class and off the RT cores.

    DO NOT REMOVE. This is not defensive boilerplate, it is load-bearing.

    card's main() calls config_realtime_process(4, Priority.CTRL_HIGH) BEFORE it
    constructs Car() -> CarState -> RivianBridge, so the main thread is already
    SCHED_FIFO 53 pinned to core 4 when we spawn the poll thread. Linux
    pthread_create defaults to PTHREAD_INHERIT_SCHED, and CPython sets only the
    stack size on the pthread attr, so this poll thread is BORN as SCHED_FIFO 53
    on core 4 - the same core and priority as the 100Hz card loop and controlsd.

    SCHED_FIFO does not timeslice between equal priorities: a runnable thread runs
    until it blocks. Every urlopen/json.loads/param-write here holds the GIL and
    competes directly with the control loop, so a slow TCM link (more socket
    wakeups, more GIL-holding) shows up as longitudinal actuation jitter.

    Both syscalls act on the CALLING THREAD only (pid=0 means "this thread" for
    scheduling), so card's main thread keeps its realtime settings.
    """
    # Separate try blocks on purpose: on a dev PC, or anywhere the process was
    # never made realtime, the policy call can fail while the affinity call still
    # needs to run. Neither may ever kill the poll thread - a dead poll thread
    # means a frozen set speed in a moving car.
    try:
        os.sched_setscheduler(0, os.SCHED_OTHER, os.sched_param(0))
    except Exception:
        pass
    try:
        cpus = set(range(os.cpu_count() or 1))
        # Prefer openpilot's background cores, but never hand sched_setaffinity an
        # empty set (it would raise) or a core that does not exist on this machine:
        # a dev PC with fewer cores falls back to "anything that is not an RT core",
        # and failing that, leaves affinity alone.
        allowed = (cpus & BACKGROUND_CORES) or (cpus - RT_CORES)
        if allowed:
            os.sched_setaffinity(0, allowed)
    except Exception:
        pass


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
            with open(path) as f:
                urls = _parse_bridge_urls(f.read())
        except OSError:
            continue
        if urls:
            return urls
    return list(DEFAULT_URLS)


class RivianBridge:
    def __init__(self, url=None):
        if url is None:
            self.urls = _read_bridge_urls()
        else:
            self.urls = _parse_bridge_urls(url if isinstance(url, str) else "\n".join(url)) or list(DEFAULT_URLS)
        self._url_index = 0
        self._last_ok_url = None
        self.state = {}
        self._lock = threading.Lock()
        self._params = Params()
        self._last_written_personality = None
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def _poll_loop(self):
        # First thing the thread does: shed the SCHED_FIFO priority and the core-4
        # affinity it inherited from card's main thread. See the function docstring.
        _drop_rt_scheduling_for_this_thread()
        while True:
            self._poll_once()
            time.sleep(0.3)  # Poll at ~3Hz

    @property
    def url(self):
        return self.urls[self._url_index]

    def _poll_once(self):
        url = self.url
        try:
            req = urllib.request.urlopen(f"{url}/state", timeout=1)
            data = json.loads(req.read())
        except Exception:
            # One URL per poll, so a dead link costs at most one 1 s timeout.
            # The next poll tries the next URL.
            self._url_index = (self._url_index + 1) % len(self.urls)
            return
        # Stick to the URL that answered. Logged once per switch, not per poll.
        if url != self._last_ok_url:
            carlog.warning("Rivian bridge switched to %s (was %s)", url, self._last_ok_url)
            self._last_ok_url = url
        try:
            with self._lock:
                self.state = data
            # Sync follow distance here, OFF the control hot path. This poll
            # thread runs at ~3Hz and already does I/O, so a param write is
            # safe here. NEVER write params from carstate.update() (100Hz).
            self._sync_personality(data)
        except Exception:
            pass

    def _sync_personality(self, data):
        # Only write LongitudinalPersonality when the bridge reports fresh,
        # valid data AND the value actually changed since our last write.
        if data.get("stale", True):
            return
        personality = data.get("follow_personality", -1)
        if personality < 0 or personality == self._last_written_personality:
            return
        try:
            self._params.put_nonblocking("LongitudinalPersonality", str(personality))
            self._last_written_personality = personality
        except Exception:
            pass

    @property
    def set_speed_ms(self):
        with self._lock:
            return self.state.get("set_speed_ms", 0)

    @property
    def follow_personality(self):
        with self._lock:
            return self.state.get("follow_personality", -1)

    @property
    def stale(self):
        with self._lock:
            return self.state.get("stale", True)
