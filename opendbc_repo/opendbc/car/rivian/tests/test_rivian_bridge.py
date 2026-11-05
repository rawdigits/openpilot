import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from opendbc.car.rivian import rivian_bridge

NEBULA, LAN = "http://192.168.4.34:8082", "http://172.28.1.64:8082"


class TestRivianBridgeUrls:
  @pytest.fixture(autouse=True)
  def setup(self, mocker):
    self.mocker = mocker
    self.params = mocker.Mock(spec=["put_nonblocking"])
    mocker.patch.object(rivian_bridge, "Params", return_value=self.params)
    mocker.patch.object(rivian_bridge.threading.Thread, "start")

  def poll(self, bridge, up):
    """One poll; hosts in `up` answer, the rest time out. Returns the URLs requested."""
    calls = []
    def urlopen(url, timeout):
      assert timeout == 1
      calls.append(url)
      if url.removesuffix("/state") not in up:
        raise TimeoutError
      return io.BytesIO(json.dumps({"stale": False, "set_speed_ms": 25.}).encode())
    with patch.object(rivian_bridge.urllib.request, "urlopen", side_effect=urlopen):
      bridge._poll_once()
    return calls

  def test_defaults(self):
    assert rivian_bridge.DEFAULT_URLS == (NEBULA, LAN)

  def test_config_precedence(self):
    with tempfile.TemporaryDirectory() as d:
      repo, data = Path(d) / "repo.conf", Path(d) / "data.conf"
      self.mocker.patch.object(rivian_bridge, "REPO_CONF", str(repo))
      self.mocker.patch.object(rivian_bridge, "DATA_CONF", str(data))
      assert rivian_bridge._read_bridge_urls() == [NEBULA, LAN]
      repo.write_text("http://repo:2/\n")
      assert rivian_bridge._read_bridge_urls() == ["http://repo:2"]
      # the device override wins over the shipped repo conf
      data.write_text("http://data:1\n")
      assert rivian_bridge._read_bridge_urls() == ["http://data:1"]
      data.write_text("\n")
      assert rivian_bridge._read_bridge_urls() == ["http://repo:2"]

  def test_config_multi_line(self):
    assert rivian_bridge._parse_bridge_urls(" http://a:1/ \n\n# comment\nhttp://b:2\nhttp://a:1\n") == ["http://a:1", "http://b:2"]
    with tempfile.TemporaryDirectory() as d:
      data = Path(d) / "data.conf"
      data.write_text("http://data-nebula:8082\nhttp://data-lan:8082\n")
      self.mocker.patch.object(rivian_bridge, "REPO_CONF", str(Path(d) / "missing.conf"))
      self.mocker.patch.object(rivian_bridge, "DATA_CONF", str(data))
      assert rivian_bridge.RivianBridge().urls == ["http://data-nebula:8082", "http://data-lan:8082"]

  def test_failover_to_lan_and_back(self):
    bridge = rivian_bridge.RivianBridge(f"{NEBULA}\n{LAN}")
    log = self.mocker.patch.object(rivian_bridge.carlog, "warning")
    assert self.poll(bridge, {NEBULA, LAN}) == [f"{NEBULA}/state"]
    assert bridge.stale is False
    # Nebula goes down: one 1 s request per poll, the LAN on the following poll
    assert self.poll(bridge, {LAN}) == [f"{NEBULA}/state"]
    assert self.poll(bridge, {LAN}) == [f"{LAN}/state"]
    # sticks to the LAN while it answers, even when Nebula is back
    for _ in range(5):
      assert self.poll(bridge, {NEBULA, LAN}) == [f"{LAN}/state"]
    # LAN goes down: back to Nebula on the following poll
    assert self.poll(bridge, {NEBULA}) == [f"{LAN}/state"]
    assert self.poll(bridge, {NEBULA}) == [f"{NEBULA}/state"]
    # both down: alternate, one request per poll
    for expected in (NEBULA, LAN, NEBULA):
      assert self.poll(bridge, set()) == [f"{expected}/state"]
    assert self.poll(bridge, {NEBULA, LAN}) == [f"{LAN}/state"]
    # one log line per switch, none for repeated polls or outages
    assert [c.args[1] for c in log.call_args_list] == [NEBULA, LAN, NEBULA, LAN]

  def test_single_url_config(self):
    bridge = rivian_bridge.RivianBridge("http://only:8082/")
    assert bridge.urls == ["http://only:8082"]
    for up in (set(), set(), {"http://only:8082"}):
      assert self.poll(bridge, up) == ["http://only:8082/state"]
    assert bridge.stale is False
