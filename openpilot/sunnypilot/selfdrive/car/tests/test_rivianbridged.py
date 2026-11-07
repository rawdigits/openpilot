"""yeet-angle-bridged: rivianbridged (the Rivian TCM bridge out of card) and card's side of it."""
import builtins
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch

from openpilot.cereal import custom, messaging
from opendbc.car.structs import car
from openpilot.common.basedir import BASEDIR
from openpilot.selfdrive.car import card
from openpilot.sunnypilot.selfdrive.car import rivianbridged
from openpilot.sunnypilot.selfdrive.car.rivian_bridge_reader import RivianBridgeReader
from openpilot.sunnypilot.selfdrive.car.rivianbridged import (BridgeConnection, BridgeState, RivianBridged, SSEParser,
                                                               STREAM_STALE_AFTER)
from openpilot.system.manager.process_config import managed_processes
from opendbc.car.rivian.rivian_bridge import STALE_AFTER, ButtonSource, RivianBridge

NEBULA, LAN = rivianbridged.DEFAULT_URLS


class StopMain(Exception):
  pass


class Clock:
  def __init__(self, t=1000.):
    self.t = t

  def __call__(self):
    return self.t

  def sleep(self, dt):
    self.t += dt


class FakeResponse(io.BytesIO):
  def __init__(self, body=b"", content_type="application/json", lines=None, clock=None, gaps=None):
    super().__init__(body)
    self.headers = {"Content-Type": content_type}
    self._lines = lines
    self._clock = clock
    self._gaps = gaps or {}

  def __iter__(self):
    if self._lines is None:
      return super().__iter__()
    return self._iter_lines()

  def _iter_lines(self):
    for i, line in enumerate(self._lines):
      if i in self._gaps:
        self._clock.sleep(self._gaps[i])
      if isinstance(line, BaseException):
        raise line
      yield line


def sse(*states, heartbeat_comment=False):
  lines = []
  for state in states:
    if heartbeat_comment:
      lines.append(b": ping\n")
    lines += [f"data: {json.dumps(state)}\n".encode(), b"\n"]
  return lines


class FakeBridge:
  """urlopen for a set of bridge hosts. hosts[url] = "stream" | "poll" (no /stream, 404) | None (down)."""
  def __init__(self, hosts, clock, state=None, stream_lines=None):
    self.hosts = hosts
    self.clock = clock
    self.state = state or {"stale": False, "set_speed_ms": 25., "follow_level": 2}
    self.stream_lines = stream_lines
    self.calls = []

  def __call__(self, url, timeout):
    self.calls.append(url)
    host, _, path = url.rpartition("/")
    kind = self.hosts.get(host)
    if kind is None:
      self.clock.sleep(timeout)
      raise TimeoutError
    if path == "stream":
      if kind != "stream":
        raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
      lines = self.stream_lines if self.stream_lines is not None else sse(self.state) + [TimeoutError()]
      return FakeResponse(content_type="text/event-stream", lines=lines, clock=self.clock)
    return FakeResponse(json.dumps(self.state).encode())


def record(state):
  """The data of every state.set call."""
  seen = []
  orig = state.set
  def set_and_record(data, *args, **kwargs):
    seen.append(data)
    orig(data, *args, **kwargs)
  state.set = set_and_record
  return seen


def connection(hosts, urls=(NEBULA, LAN), **kwargs):
  clock = Clock()
  bridge = FakeBridge(hosts, clock, **kwargs)
  state = BridgeState()
  conn = BridgeConnection(state, list(urls), urlopen=bridge, clock=clock, sleep=clock.sleep)
  # BridgeState stamps with time.monotonic: use the fake clock
  state_set = state.set
  def set_now(data, url, streaming, now=None):
    state_set(data, url, streaming, clock())
  state.set = set_now
  return conn, state, bridge, clock


class TestSSEParser(unittest.TestCase):
  def test_events_comments_and_multiline(self):
    p = SSEParser()
    out = [p.feed_line(line) for line in (": heartbeat", "event: state", "data: {\"a\":", "data:1}", "id: 7", "", "", "data: x", "")]
    self.assertEqual([o for o in out if o is not None], ['{"a":\n1}', "x"])

  def test_stream_events_set_state(self):
    states = [{"stale": False, "set_speed_ms": 25.}, {"stale": False, "set_speed_ms": 26., "follow_level": 3}]
    conn, state, bridge, clock = connection({NEBULA: "stream"}, stream_lines=sse(*states, heartbeat_comment=True) + [TimeoutError()])
    seen = record(state)
    conn.stream_once()
    self.assertEqual(seen[:2], states)
    self.assertEqual(seen[-1], {})  # the read timed out: stale until the next event
    self.assertEqual(bridge.calls, [f"{NEBULA}/stream"])

  def test_invalid_event_is_stale(self):
    for payload in (b"[]", b"null", b"not json"):
      with self.subTest(payload=payload):
        conn, state, _, _ = connection({NEBULA: "stream"}, stream_lines=[b"data: " + payload + b"\n", b"\n"])
        seen = record(state)
        conn.stream_once()
        self.assertEqual(seen[0], {})


class TestBridgeConnection(unittest.TestCase):
  def test_stream_primary(self):
    conn, state, bridge, clock = connection({NEBULA: "stream", LAN: "stream"})
    conn.step()
    self.assertEqual(bridge.calls, [f"{NEBULA}/stream"])
    # ended (timeout): poll the same URL during the backoff, then reconnect the stream
    conn.step()
    self.assertEqual(bridge.calls[-1], f"{NEBULA}/state")
    clock.sleep(rivianbridged.STREAM_BACKOFF[0])
    conn.step()
    self.assertEqual(bridge.calls[-1], f"{NEBULA}/stream")

  def test_reconnect_backoff_grows_and_resets(self):
    # connects, but never sends an event (hung bridge): the backoff grows
    conn, state, bridge, clock = connection({NEBULA: "stream"}, urls=[NEBULA], stream_lines=[TimeoutError()])
    starts = []
    for _ in range(40):
      before = len(bridge.calls)
      conn.step()
      if bridge.calls[before:] == [f"{NEBULA}/stream"]:
        starts.append(clock())
    gaps = [round(b - a, 2) for a, b in zip(starts, starts[1:], strict=False)]
    self.assertEqual(gaps[:3], sorted(gaps[:3]))
    self.assertLess(gaps[0], gaps[2])
    # an event resets it
    bridge.stream_lines = sse({"stale": False}) + [TimeoutError()]
    clock.sleep(10)
    conn.step()
    self.assertEqual(conn._stream_fails, 1)

  def test_heartbeat_staleness(self):
    clock = Clock()
    state = BridgeState()
    bridged = RivianBridged(state, Mock(), clock=clock)
    state.set({"stale": False, "set_speed_ms": 25.}, NEBULA, True, now=clock())
    for dt, stale in ((0.25, False), (0.5, False), (STREAM_STALE_AFTER - 0.01, False), (STREAM_STALE_AFTER + 0.01, True)):
      with self.subTest(dt=dt):
        clock.t = state.received_at + dt
        bridged.update_bridge()
        self.assertEqual(bridged.stale, stale)
    # polled state keeps the 2 s rule
    state.set({"stale": False, "set_speed_ms": 25.}, NEBULA, False, now=clock())
    for dt, stale in ((STREAM_STALE_AFTER + 0.5, False), (STALE_AFTER + 0.01, True)):
      clock.t = state.received_at + dt
      bridged.update_bridge()
      self.assertEqual(bridged.stale, stale)

  def test_heartbeat_gap_ends_stream(self):
    # a 1 s gap between events is the socket timeout: the read raises, state is cleared, the next step polls
    lines = sse({"stale": False}, {"stale": False}) + [TimeoutError()]
    conn, state, bridge, clock = connection({NEBULA: "stream"}, stream_lines=lines)
    conn.stream_once()
    self.assertEqual(state.data, {})
    self.assertTrue(state.streaming)

  def test_fallback_to_polling_without_stream(self):
    conn, state, bridge, clock = connection({NEBULA: "poll"}, urls=[NEBULA])
    conn.step()
    self.assertEqual(bridge.calls, [f"{NEBULA}/stream"])
    for _ in range(10):
      conn.step()
    self.assertEqual(bridge.calls[1:], [f"{NEBULA}/state"] * 10)
    self.assertFalse(state.streaming)
    self.assertEqual(state.data["set_speed_ms"], 25.)
    # every 0.1 s
    self.assertAlmostEqual(clock() - 1000., 0.9, places=5)
    # asked again for /stream after a while
    clock.sleep(rivianbridged.STREAM_RETRY_NO_STREAM)
    conn.step()
    self.assertEqual(bridge.calls[-1], f"{NEBULA}/stream")

  def test_not_an_event_stream_is_no_stream(self):
    conn, state, bridge, clock = connection({NEBULA: "poll"}, urls=[NEBULA])
    bridge.hosts[NEBULA] = "stream"
    bridge.__class__ = type("JsonStream", (FakeBridge,), {
      "__call__": lambda self, url, timeout: (self.calls.append(url), FakeResponse(json.dumps(self.state).encode()))[1]})
    conn.step()
    conn.step()
    self.assertEqual(bridge.calls, [f"{NEBULA}/stream", f"{NEBULA}/state"])
    self.assertGreaterEqual(conn._next_stream - clock(), rivianbridged.STREAM_RETRY_NO_STREAM - 1)

  def test_failover_rotation(self):
    conn, state, bridge, clock = connection({NEBULA: "poll", LAN: "poll"})
    with patch.object(rivianbridged.cloudlog, "warning") as warning:
      conn.step()  # /stream 404
      conn.step()
      self.assertEqual(bridge.calls[-1], f"{NEBULA}/state")
      # Nebula goes down: one timeout, then the LAN, stream first
      bridge.hosts[NEBULA] = None
      conn.step()
      self.assertEqual(bridge.calls[-1], f"{NEBULA}/state")
      self.assertEqual(state.data, {})
      conn.step()
      self.assertEqual(bridge.calls[-1], f"{LAN}/stream")
      conn.step()
      self.assertEqual(bridge.calls[-1], f"{LAN}/state")
      self.assertEqual(state.url, LAN)
      # sticks to the LAN while it answers, even with Nebula back
      bridge.hosts[NEBULA] = "poll"
      for _ in range(5):
        conn.step()
        self.assertEqual(bridge.calls[-1], f"{LAN}/state")
      # both down: alternate, stays stale
      bridge.hosts = {}
      for _ in range(4):
        conn.step()
        self.assertEqual(state.data, {})
    # one log line per switch, none for repeated polls or outages
    switches = [c.args[0] for c in warning.call_args_list if "switched" in c.args[0]]
    self.assertEqual(len(switches), 2)
    self.assertIn(LAN, switches[1])

  def test_dead_stream_host_falls_back_to_poll_then_rotates(self):
    conn, state, bridge, clock = connection({LAN: "stream"})
    conn.step()  # Nebula /stream: connect fails, poll it
    conn.step()  # Nebula /state: fails, rotate
    conn.step()
    self.assertEqual(bridge.calls, [f"{NEBULA}/stream", f"{NEBULA}/state", f"{LAN}/stream"])
    self.assertTrue(state.streaming)

  def test_config_precedence(self):
    self.assertEqual(rivianbridged.REPO_CONF, Path(BASEDIR) / "rivian-bridge.conf")
    self.assertEqual(rivianbridged.DATA_CONF, Path("/data/rivian-bridge.conf"))
    self.assertEqual(rivianbridged.parse_bridge_urls(rivianbridged.REPO_CONF.read_text()), [NEBULA, LAN])
    self.assertEqual((NEBULA, LAN), ("http://192.168.4.34:8082", "http://172.28.1.64:8082"))
    with tempfile.TemporaryDirectory() as d:
      repo, data = Path(d) / "repo.conf", Path(d) / "data.conf"
      with patch.object(rivianbridged, "REPO_CONF", repo), patch.object(rivianbridged, "DATA_CONF", data):
        self.assertEqual(rivianbridged.read_bridge_urls(), [NEBULA, LAN])
        repo.write_text("http://repo:8082/\n")
        self.assertEqual(rivianbridged.read_bridge_urls(), ["http://repo:8082"])
        data.write_text("http://data:1\n# c\n\nhttp://data:2/\nhttp://data:1\n")
        self.assertEqual(rivianbridged.read_bridge_urls(), ["http://data:1", "http://data:2"])
        data.write_text("\n")
        self.assertEqual(rivianbridged.read_bridge_urls(), ["http://repo:8082"])


class TestRivianBridgedParams(unittest.TestCase):
  def setUp(self):
    self.clock = Clock()
    self.state = BridgeState()
    self.params = Mock(spec=["put", "get", "get_bool"])
    self.param_values = {"TrafficSignOffset": 2, "RivianButtonSource": 2, "LongitudinalPersonality": 0}
    self.params.get.side_effect = lambda key, return_default=False: self.param_values[key]
    self.params.get_bool.side_effect = lambda key: key == "RivianScrollInvert"
    self.bridged = RivianBridged(self.state, self.params, clock=self.clock)

  def bridge(self, **data):
    self.state.set({"stale": False, "set_speed_ms": 25., "follow_personality": 1, **data}, NEBULA, True, now=self.clock())
    self.bridged.update_bridge()
    self.bridged.sync_params()

  def comma(self, gap, level):
    cs = custom.CarStateSP.new_message(rivianCommaGap=gap, rivianCommaFollowLevel=level)
    self.bridged.update_comma(cs)
    self.bridged.sync_params()

  def writes(self, key):
    return [c.args[1] for c in self.params.put.call_args_list if c.args[0] == key]

  def test_reads_params(self):
    self.bridged.read_params()
    b = self.bridged
    self.assertEqual((b.sign_offset, b.button_source, b.scroll_invert, b.personality_param), (2, ButtonSource.BRIDGE, True, 0))
    # invalid values keep the last good ones
    self.param_values.update({"TrafficSignOffset": 7, "RivianButtonSource": 7, "LongitudinalPersonality": None})
    self.bridged.read_params()
    self.assertEqual((b.sign_offset, b.button_source, b.personality_param), (2, ButtonSource.BRIDGE, 0))
    self.params.get.side_effect = OSError
    self.bridged.read_params()  # no crash

  def test_level_and_personality_written_on_change_only(self):
    for level, personality in ((1, 0), (2, 1), (3, 2), (4, 2)):
      with self.subTest(level=level):
        self.params.reset_mock()
        self.bridge(follow_level=level, follow_personality=min(level - 1, 2))
        self.bridge(follow_level=level, follow_personality=min(level - 1, 2))
        self.assertEqual(self.writes("RivianFollowLevel"), [level])
        self.assertIs(type(self.writes("RivianFollowLevel")[0]), int)
        self.assertEqual(self.writes("LongitudinalPersonality"), [] if level == 4 else [personality])

  def test_follow_personality_without_level(self):
    for personality in (0, 1, 2):
      self.bridge(follow_personality=personality)
    self.assertEqual(self.writes("LongitudinalPersonality"), [0, 1, 2])
    self.assertEqual(self.writes("RivianFollowLevel"), [0])
    for invalid in (-1, 3, "1", None, True, 1.0):
      self.bridge(follow_personality=invalid)
    self.assertEqual(self.writes("LongitudinalPersonality"), [0, 1, 2])

  def test_stale_writes_level_zero_and_recovery_rewrites(self):
    self.bridge(follow_level=3)
    for stale in ({"stale": True}, {"stale": "false"}, {"stale": None}):
      self.params.reset_mock()
      self.bridge(follow_level=3, **stale)
      self.assertEqual(self.writes("RivianFollowLevel"), [0])
      self.assertEqual(self.writes("LongitudinalPersonality"), [])
      self.params.reset_mock()
      # recovery restores the bridge's value even when it is the one written before the outage
      self.bridge(follow_level=3)
      self.assertEqual(self.writes("RivianFollowLevel"), [3])
      self.assertEqual(self.writes("LongitudinalPersonality"), [2])
    # no state for too long
    self.params.reset_mock()
    self.clock.sleep(STREAM_STALE_AFTER + 0.1)
    self.bridged.update_bridge()
    self.bridged.sync_params()
    self.assertEqual(self.writes("RivianFollowLevel"), [0])

  def test_write_retry(self):
    self.params.put.side_effect = OSError("temporary write failure")
    self.bridge(follow_level=2)
    self.params.put.side_effect = None
    self.bridge(follow_level=2)
    self.bridge(follow_level=2)
    self.assertEqual(self.writes("RivianFollowLevel"), [2, 2])
    self.assertEqual(self.writes("LongitudinalPersonality"), [1, 1])

  def test_comma_level_written_like_the_bridge(self):
    self.bridge(follow_level=2)
    self.params.reset_mock()
    # LongitudinalPersonality on change only: levels 3 and 4 share personality 2
    for level, personalities in ((3, [2]), (4, []), (3, []), (2, [1]), (1, [0])):
      with self.subTest(level=level):
        self.params.reset_mock()
        self.comma(True, level)
        self.assertEqual(self.writes("RivianFollowLevel"), [level])
        self.assertEqual(self.writes("LongitudinalPersonality"), personalities)
        self.assertEqual(self.bridged.personality_param, {1: 0, 2: 1, 3: 2, 4: 2}[level])
    # the bridge's own level and personality are ignored while the comma owns the gap, stale or not
    self.params.reset_mock()
    self.bridge(follow_level=4, follow_personality=2)
    self.bridge(stale=True)
    self.assertEqual(self.params.put.call_count, 0)
    # level not set yet: RivianFollowLevel 0, no personality
    self.comma(True, 0)
    self.assertEqual(self.writes("RivianFollowLevel"), [0])
    self.assertEqual(self.writes("LongitudinalPersonality"), [])
    # back to the bridge: its level
    self.params.reset_mock()
    self.comma(False, 0)
    self.bridge(follow_level=2)
    self.assertEqual(self.writes("RivianFollowLevel"), [2])

  def test_message(self):
    self.bridged.read_params()
    self.bridge(follow_level=3, set_speed_ms=27.5)
    m = self.bridged.message().rivianBridgeSP
    self.assertEqual((m.stale, m.setSpeedMs, m.followLevel, m.followPersonality), (False, 27.5, 3, 1))
    self.assertEqual((m.signOffset, m.buttonSource, m.scrollInvert, m.personalityParam), (2, 2, True, 0))
    self.assertEqual((m.url, m.streaming), (NEBULA, True))
    for invalid in (None, "30", -1., float("nan"), float("inf"), True):
      self.bridge(set_speed_ms=invalid)
      self.assertEqual(self.bridged.message().rivianBridgeSP.setSpeedMs, 0.)
    fresh = RivianBridged(BridgeState(), self.params).message().rivianBridgeSP
    self.assertTrue(fresh.stale)
    self.assertEqual((fresh.followLevel, fresh.followPersonality, fresh.personalityParam), (-1, -1, -1))


class FakeSock:
  def __init__(self):
    self.msgs = []

  def receive(self, non_blocking=False):
    assert non_blocking, "card must never block on rivianBridgeSP"
    return self.msgs.pop(0) if self.msgs else None


class TestCardBridgeReader(unittest.TestCase):
  def setUp(self):
    self.clock = Clock()
    self.sock = FakeSock()
    self.bridge = RivianBridge()
    self.reader = RivianBridgeReader(self.bridge, self.sock, clock=self.clock)

  def send(self, **fields):
    msg = messaging.new_message("rivianBridgeSP")
    for k, v in {"stale": False, "setSpeedMs": 25., "followLevel": 2, "followPersonality": 1, "signOffset": 3,
                 "buttonSource": 1, "scrollInvert": True, "personalityParam": 2, **fields}.items():
      setattr(msg.rivianBridgeSP, k, v)
    self.sock.msgs.append(msg.to_bytes())

  def test_fresh_message(self):
    self.reader.update()
    self.assertTrue(self.bridge.stale)  # nothing received yet
    self.send()
    self.reader.update()
    b = self.bridge
    self.assertFalse(b.stale)
    self.assertEqual((b.set_speed_ms, b.follow_level, b.follow_personality, b.bridge_personality), (25., 2, 1, 1))
    self.assertEqual((b.sign_offset, b.button_source, b.scroll_invert, b.personality_param), (3, 1, True, 2))
    self.send(personalityParam=-1, followLevel=-1)
    self.reader.update()
    self.assertIsNone(b.personality_param)
    self.assertEqual(b.follow_level, -1)

  def test_stale_flag_and_old_message(self):
    self.send(stale=True)
    self.reader.update()
    self.assertTrue(self.bridge.stale)
    self.send()
    self.reader.update()
    # no new message: fresh for 2 s, then stale, keeping the Params values
    self.clock.sleep(STALE_AFTER - 0.01)
    self.reader.update()
    self.assertFalse(self.bridge.stale)
    self.clock.sleep(0.02)
    self.reader.update()
    self.assertTrue(self.bridge.stale)
    self.assertEqual((self.bridge.sign_offset, self.bridge.button_source), (3, 1))
    self.send()
    self.reader.update()
    self.assertFalse(self.bridge.stale)

  def test_comma_level_survives_messages(self):
    self.bridge.comma_gap, self.bridge.comma_follow_level = True, 3
    self.send()
    self.reader.update()
    self.assertEqual((self.bridge.comma_gap, self.bridge.comma_follow_level), (True, 3))

  def test_no_params_or_network_on_the_card_path(self):
    # card's per-cycle bridge path: no Params, urllib, socket or file access
    def fail(*args, **kwargs):
      raise AssertionError("I/O on the card path")
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
      if name.startswith(("urllib", "http", "openpilot.common.params", "socket", "json")):
        raise AssertionError(f"card path imported {name}")
      return real_import(name, *args, **kwargs)
    with patch("builtins.open", fail), patch("urllib.request.urlopen", fail), patch("socket.socket", fail), \
         patch("openpilot.common.params.Params", fail), patch.object(builtins, "__import__", guarded_import):
      for _ in range(50):
        self.send()
        self.reader.update()
    import openpilot.sunnypilot.selfdrive.car.rivian_bridge_reader as reader_module
    for name in ("Params", "urllib", "threading", "json"):
      self.assertFalse(hasattr(reader_module, name), name)
    self.assertNotIn("rivianbridged", card.__dict__)


class TestCardLateness(unittest.TestCase):
  def setUp(self):
    self.clock = Clock()
    self.log = Mock()
    self.late = card.LatenessLog(clock=self.clock, log=self.log)

  def cycle(self, dt=0.01, sent=True, work=0.002):
    self.clock.sleep(dt - work)
    self.late.start_cycle(1)
    self.clock.sleep(work)
    self.late.sendcan(sent)
    self.late.end_cycle()

  def events(self):
    return [c.kwargs for c in self.log.event.call_args_list if c.args == ("card_late",)]

  def test_on_time_is_quiet(self):
    for _ in range(500):
      self.cycle(0.01 + 0.004)  # 4 ms jitter, under both thresholds
    self.assertEqual(self.events(), [])

  def test_late_cycle_and_sendcan_gap(self):
    for _ in range(10):
      self.cycle()
    self.cycle(0.047)  # the 37 ms stall from #9
    events = self.events()
    self.assertEqual([e["kind"] for e in events], ["cycle"])
    self.assertAlmostEqual(events[0]["ms"], 37., places=0)
    self.assertEqual(events[0]["suppressed"], 0)
    self.assertAlmostEqual(events[0]["prev_step_ms"], 2., places=0)
    # the sendcan gap of the same stall falls inside the 1 s rate limit
    self.assertEqual(self.late.suppressed, 1)

  def test_sendcan_gap_alone(self):
    for _ in range(10):
      self.cycle()
    # a 30 ms sendcan gap where cycles stay on time (sendcan skipped twice, not a startup gap)
    self.clock.sleep(0.03)
    self.late.sendcan(True)
    self.assertEqual([e["kind"] for e in self.events()], ["sendcan"])
    self.assertAlmostEqual(self.events()[0]["ms"], 30., places=0)

  def test_not_sending_resets_the_gap(self):
    self.cycle()
    for _ in range(100):
      self.cycle(sent=False)
    self.cycle()
    self.assertEqual(self.events(), [])

  def test_rate_limit_with_suppressed_count(self):
    self.cycle()
    for _ in range(5):
      self.cycle(0.05)  # within 1 s: one event, the rest counted
    self.assertEqual(len(self.events()), 1)
    self.clock.sleep(1.)
    self.cycle(0.05)
    events = self.events()
    self.assertEqual(len(events), 2)
    self.assertGreaterEqual(events[1]["suppressed"], 4)
    self.assertEqual(self.late.suppressed, 1)  # this stall's sendcan gap


class TestProcessConfig(unittest.TestCase):
  def test_rivianbridged_runs_for_rivian_openpilot_long_only(self):
    proc = managed_processes["rivianbridged"]
    self.assertEqual(proc.module, "openpilot.sunnypilot.selfdrive.car.rivianbridged")
    for brand, long, started, want in (("rivian", True, True, True), ("rivian", True, False, False),
                                       ("rivian", False, True, False), ("toyota", True, True, False)):
      with self.subTest(brand=brand, long=long, started=started):
        CP = car.CarParams.new_message(brand=brand, openpilotLongitudinalControl=long)
        self.assertEqual(bool(proc.should_run(started, None, CP)), want)

  def test_not_realtime(self):
    # normal priority, background cores; nothing in it sets SCHED_FIFO
    source = Path(rivianbridged.__file__).read_text()
    self.assertNotIn("config_realtime_process", source)
    self.assertNotIn("SCHED_FIFO", source)
    self.assertEqual(rivianbridged.BACKGROUND_CORES, [0, 1, 2, 3])
    with patch.object(rivianbridged, "set_core_affinity", side_effect=StopMain) as affinity:
      with self.assertRaises(StopMain):
        rivianbridged.main()
    affinity.assert_called_once_with([0, 1, 2, 3])


if __name__ == "__main__":
  unittest.main()
