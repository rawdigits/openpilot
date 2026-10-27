"""Guards for Ryan's customizations on yeetfollow (automotive/openpilot#4).

One test per row of PARITY.md (on yeet-angle) that applies to this base, pinning the
exact value or behavior, so an upstream rebase that silently drops a customization
fails CI. Each test names its row. yeetfollow has no angle kit, so the Rivian rows
cover the torque-only path. Rows 15, 29, 30, 39, 42, 43, 46 have no code to pin, and
row 44 is this CI itself.
"""
import io
import json
import os
import re
import subprocess
import tempfile
import threading
from pathlib import Path

import pytest
from parameterized import parameterized

from cereal import log
from opendbc.car import Bus, gen_empty_fingerprint
from opendbc.car import interfaces as car_interfaces
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.rivian import carstate as rivian_carstate
from opendbc.car.rivian import rivian_bridge
from opendbc.car.rivian.carcontroller import MAX_STEERING_ANGLE
from opendbc.car.rivian.interface import CarInterface
from opendbc.car.rivian.values import CAR, CarControllerParams
from opendbc.car.structs import CarParams
from opendbc.safety.tests.common import CANPackerPanda
from opendbc.safety.tests.libsafety import libsafety_py
from openpilot.common.basedir import BASEDIR
from openpilot.common.params import Params
from openpilot.selfdrive.car import cruise
from openpilot.selfdrive.controls.lib import longitudinal_planner
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib import long_mpc
from openpilot.selfdrive.controls.tests import test_following_distance
from openpilot.selfdrive.monitoring.helpers import DRIVER_MONITOR_SETTINGS
from openpilot.selfdrive.test.longitudinal_maneuvers import test_longitudinal
from openpilot.sunnypilot.mads import helpers as mads_helpers

ROOT = Path(BASEDIR)
Personality = log.LongitudinalPersonality


def rivian_params():
  fingerprint = gen_empty_fingerprint()
  CP = CarInterface.get_params(CAR.RIVIAN_R1_GEN1, fingerprint, [], False, False)
  CP_SP = CarInterface.get_params_sp(CP, CAR.RIVIAN_R1_GEN1, fingerprint, [], False, False)
  return CP, CP_SP


class TestLongitudinalTuning:
  # rows 1, 2
  def test_comfort_brake_and_stop_distance(self):
    assert long_mpc.COMFORT_BRAKE == 3.0
    assert long_mpc.STOP_DISTANCE == 3.0
    assert long_mpc.get_safe_obstacle_distance(0., 0.85) == pytest.approx(3.0)
    assert long_mpc.get_stopped_equivalence_factor(6.) == pytest.approx(6.)
    # 20 m/s standard: 400/6 + 22 + 3
    assert long_mpc.get_safe_obstacle_distance(20., 1.10) == pytest.approx(400 / 6 + 25)
    # the maneuver tests' "resume from a stop" start gap follows STOP_DISTANCE
    assert test_longitudinal.STOP_DISTANCE is long_mpc.STOP_DISTANCE

  # rows 3, 4
  def test_cruise_accel_limits(self):
    assert long_mpc.CRUISE_MAX_ACCEL == 1.8
    assert long_mpc.CRUISE_MIN_ACCEL == -1.2
    assert longitudinal_planner.A_CRUISE_MAX_VALS == [1.6, 1.2, 0.8, 0.6]
    assert longitudinal_planner.A_CRUISE_MAX_BP == [0., 10.0, 25., 40.]

  # rows 5, 6, 7
  def test_mpc_costs(self):
    assert long_mpc.A_CHANGE_COST == 100.
    assert long_mpc.DANGER_ZONE_COST == 60.
    assert long_mpc.LEAD_DANGER_FACTOR == 0.85

  # row 8
  @parameterized.expand([(Personality.aggressive, 0.60), (Personality.standard, 1.10), (Personality.relaxed, 1.80)])
  def test_t_follow(self, personality, t_follow):
    assert long_mpc.get_T_FOLLOW(personality) == t_follow

  # row 9
  def test_uncustomized_mpc_costs(self):
    assert long_mpc.J_EGO_COST == 5.
    assert [long_mpc.get_jerk_factor(p) for p in (Personality.aggressive, Personality.standard, Personality.relaxed)] == [0.5, 1.0, 1.0]

  # row 10
  def test_personality_mapping(self):
    assert (Personality.aggressive, Personality.standard, Personality.relaxed) == (0, 1, 2)
    assert long_mpc.get_T_FOLLOW() == 1.10
    assert '("LongitudinalPersonality", str(log.LongitudinalPersonality.standard))' in (ROOT / "system/manager/manager.py").read_text()

  # row 45
  def test_known_failures(self):
    assert test_following_distance.KNOWN_FAILURES == {(e2e, p, 0) for e2e in (True, False) for p in (Personality.standard, Personality.aggressive)}
    decel = 'steady state following a car at 20m/s, then lead decel to 0mph at '
    assert test_longitudinal.KNOWN_FAILURES == {
      *((True, False, t) for t in ('approach stopped car at 25m/s, initial distance: 120m',
                                   'approach stopped car at 20m/s, initial distance 90m',
                                   decel + '1m/s^2', decel + '2m/s^2', decel + '3m/s^2', decel + '3+m/s^2',
                                   'approach stopped car at 20m/s, with prob_lead_values',
                                   'approach stopped car at 20m/s, with prob_throttle_values and pitch = -0.1',
                                   'approach stopped car at 20m/s, with prob_throttle_values and pitch = +0.1',
                                   'NaN recovery')),
      (True, True, decel + '3+m/s^2'),
      *((False, False, t) for t in (decel + '2m/s^2', decel + '3m/s^2', decel + '3+m/s^2', 'NaN recovery')),
    }


class TestRivianLongitudinalTune:
  def setup_method(self):
    self.CP, self.CP_SP = rivian_params()

  # row 11: the planner's should_stop uses CarParams.vEgoStopping
  def test_stop_speed(self):
    assert self.CP.vEgoStopping == pytest.approx(0.25)
    speeds = [0.27] * longitudinal_planner.CONTROL_N
    assert not longitudinal_planner.get_accel_from_plan(speeds, [0.] * len(speeds), vEgoStopping=self.CP.vEgoStopping)[1]
    speeds = [0.24] * longitudinal_planner.CONTROL_N
    assert longitudinal_planner.get_accel_from_plan(speeds, [0.] * len(speeds), vEgoStopping=self.CP.vEgoStopping)[1]
    assert "vEgoStopping=self.CP.vEgoStopping" in Path(longitudinal_planner.__file__).read_text()

  # rows 12, 13, 14
  def test_long_tune(self):
    assert self.CP.longitudinalActuatorDelay == pytest.approx(0.35)
    assert self.CP.stopAccel == 0.
    assert list(self.CP.longitudinalTuning.kiV) == [0.]

  # rows 16, 17
  def test_openpilot_long_and_radar(self):
    assert self.CP.openpilotLongitudinalControl
    assert not self.CP.radarUnavailable


class TestRivianBridge:
  @pytest.fixture(autouse=True)
  def setup(self, mocker):
    self.mocker = mocker
    self.params = mocker.Mock(spec=["put_nonblocking"])
    mocker.patch.object(rivian_bridge, "Params", return_value=self.params)
    start = mocker.patch.object(rivian_bridge.threading.Thread, "start")
    self.bridge = rivian_bridge.RivianBridge(url="http://bridge")
    mocker.stop(start)
    self.CP, self.CP_SP = rivian_params()
    mocker.patch.object(rivian_bridge, "RivianBridge", return_value=self.bridge)
    self.cs = rivian_carstate.CarState(self.CP, self.CP_SP)
    assert self.cs.bridge is self.bridge
    self.parsers = self.cs.get_can_parsers(self.CP, self.CP_SP)
    self.set_speed(24.)
    Params().put("TrafficSignOffset", "1")

  def poll(self, **state):
    self.bridge.state = {"stale": False, "set_speed_ms": 25., "follow_personality": 1, **state}

  def engage(self, enabled=True):
    self.parsers[Bus.cam].vl["ACM_Status"]["ACM_FeatureStatus"] = int(enabled)

  def set_speed(self, speed):
    self.parsers[Bus.pt].vl["ESP_Status"]["ESP_Vehicle_Speed"] = speed * CV.MS_TO_KPH

  def gas(self, pressed):
    self.parsers[Bus.pt].vl["VDM_PropStatus"]["VDM_AcceleratorPedalPosition"] = 10 if pressed else 0

  def update(self, tsr=0):
    self.parsers[Bus.adas].vl["ACM_tsrCmd"]["ACM_tsrSpdDisClsMain"] = tsr
    return self.cs.update(self.parsers)

  # rows 18, 22, 23: RT scheduling dropped first, /state polled every 0.3 s with a 1 s timeout, personality synced off-thread
  def test_poll_loop(self):
    order = []
    data = {"stale": False, "set_speed_ms": 25., "follow_personality": 2}
    def urlopen(*args, **kwargs):
      order.append("http")
      return io.BytesIO(json.dumps(data).encode())
    self.mocker.patch.object(rivian_bridge, "_drop_rt_scheduling_for_this_thread", side_effect=lambda: order.append("sched"))
    get = self.mocker.patch.object(rivian_bridge.urllib.request, "urlopen", side_effect=urlopen)
    sleep = self.mocker.patch.object(rivian_bridge.time, "sleep", side_effect=InterruptedError)
    with pytest.raises(InterruptedError):
      self.bridge._poll_loop()
    assert order == ["sched", "http"]
    get.assert_called_once_with("http://bridge/state", timeout=1)
    sleep.assert_called_once_with(0.3)
    self.params.put_nonblocking.assert_called_once_with("LongitudinalPersonality", "2")

  # row 19
  def test_url_precedence(self):
    assert rivian_bridge.DEFAULT_URL == "http://172.28.1.64:8082"
    assert rivian_bridge.REPO_CONF == "/data/openpilot/rivian-bridge.conf"
    assert rivian_bridge.DATA_CONF == "/data/rivian-bridge.conf"
    assert (ROOT / "rivian-bridge.conf").read_text().strip() == rivian_bridge.DEFAULT_URL
    with tempfile.TemporaryDirectory() as d:
      repo, data = Path(d) / "repo.conf", Path(d) / "data.conf"
      self.mocker.patch.object(rivian_bridge, "REPO_CONF", str(repo))
      self.mocker.patch.object(rivian_bridge, "DATA_CONF", str(data))
      assert rivian_bridge._read_bridge_url() == rivian_bridge.DEFAULT_URL
      data.write_text("http://data:1\n")
      assert rivian_bridge._read_bridge_url() == "http://data:1"
      repo.write_text("http://repo:2\n")
      assert rivian_bridge._read_bridge_url() == "http://repo:2"

  # row 20: bridge set speed, gas override held until the stalk changes it by more than 0.5 m/s
  def test_set_speed_and_gas_override(self):
    self.engage()
    self.poll(set_speed_ms=30.)
    assert self.update().cruiseState.speed == 30.
    self.gas(True)
    self.set_speed(33.)
    assert self.update().cruiseState.speed == pytest.approx(33.)
    self.gas(False)
    self.set_speed(30.)
    assert self.update().cruiseState.speed == pytest.approx(33.)
    self.poll(set_speed_ms=30.4)
    assert self.update().cruiseState.speed == pytest.approx(33.)
    self.poll(set_speed_ms=31.)
    assert self.update().cruiseState.speed == 31.
    # disengaged: follows ego speed
    self.engage(False)
    self.poll(stale=True)
    assert self.update().cruiseState.speed == pytest.approx(30.)

  # rows 10, 21, 22: bridge follow levels 1-4 arrive as personality 0/1/2/2 and are written
  # from the poll thread regardless of gas, deduplicated, never from the 100 Hz update
  def test_follow_sync(self):
    for level, personality in ((1, 0), (2, 1), (3, 2), (4, 2)):
      self.bridge._last_written_personality = None
      self.params.put_nonblocking.reset_mock()
      data = {"stale": False, "follow_level": level, "follow_personality": personality}
      self.bridge.state = data
      self.update()
      self.params.put_nonblocking.assert_not_called()
      worker = threading.Thread(target=self.bridge._sync_personality, args=(data,))
      worker.start()
      worker.join(timeout=2)
      self.params.put_nonblocking.assert_called_once_with("LongitudinalPersonality", str(personality))
      self.bridge._sync_personality(data)
      self.params.put_nonblocking.assert_called_once()
    self.params.put_nonblocking.reset_mock()
    for data in ({"stale": True, "follow_personality": 0}, {"stale": False, "follow_personality": -1}, {"follow_personality": 0}):
      self.bridge._sync_personality(data)
    self.params.put_nonblocking.assert_not_called()
    assert "LongitudinalPersonality" not in Path(rivian_carstate.__file__).read_text().split("NOTE: follow-distance")[0]

  # row 23
  def test_poll_thread_off_rt_cores(self):
    assert rivian_bridge.BACKGROUND_CORES == {0, 1, 2, 3}
    assert rivian_bridge.RT_CORES == {4, 5, 7}
    scheduler = self.mocker.patch.object(rivian_bridge.os, "sched_setscheduler")
    affinity = self.mocker.patch.object(rivian_bridge.os, "sched_setaffinity")
    self.mocker.patch.object(rivian_bridge.os, "cpu_count", return_value=8)
    rivian_bridge._drop_rt_scheduling_for_this_thread()
    scheduler.assert_called_once_with(0, os.SCHED_OTHER, os.sched_param(0))
    affinity.assert_called_once_with(0, {0, 1, 2, 3})

  # rows 24, 25
  def test_set_speed_bounds(self):
    assert rivian_carstate.MAX_SET_SPEED == 50
    assert rivian_carstate.MIN_SET_SPEED == 1
    self.engage()
    self.poll(set_speed_ms=100.)
    assert self.update().cruiseState.speed == 50
    self.engage(False)
    self.poll(stale=True)
    self.set_speed(0.)
    assert self.update().cruiseState.speed == 1

  # row 27
  def test_traffic_sign_offset(self):
    assert '("TrafficSignOffset", "1")' in (ROOT / "system/manager/manager.py").read_text()
    sign = 60 * CV.MPH_TO_MS
    self.poll(stale=True)
    self.engage()
    self.set_speed(25.)
    for offset in (0, 1, 2, 3):
      Params().put("TrafficSignOffset", str(offset))
      self.cs.set_speed = 25.
      self.cs.sign_speed = 10.
      assert self.update(tsr=60).cruiseState.speed == pytest.approx(sign * (1 + 0.05 * offset) if offset else 25.)
    Params().put("TrafficSignOffset", "1")
    # invalid signs and signs more than 9 m/s away are ignored
    for tsr in (0, 254, 255, 85):
      self.cs.set_speed = 25.
      self.cs.sign_speed = 10.
      assert self.update(tsr=tsr).cruiseState.speed == pytest.approx(25.)
    # the bridge rewrites the set speed every frame, so a sign only matters while it is stale or overridden
    self.poll(set_speed_ms=25.)
    self.cs.sign_speed = 10.
    assert self.update(tsr=60).cruiseState.speed == 25.
    # 253 = unlimited, capped at MAX_SET_SPEED
    self.update(tsr=253)
    assert self.cs.sign_speed == 50

  # row 28: the Rivian gap comes only from the bridge, no CAN gapAdjustCruise
  def test_no_can_gap_events(self):
    self.poll(follow_personality=2)
    assert len(self.update().buttonEvents) == 0


class TestCruiseAndSteering:
  # row 26
  def test_v_cruise_max(self):
    assert cruise.V_CRUISE_MAX == 180
    assert car_interfaces.V_CRUISE_MAX == 180

  # row 31
  def test_max_steering_angle(self):
    assert MAX_STEERING_ANGLE == 90.0

  # row 32
  def test_torque_steering_limits(self):
    assert CarControllerParams.STEER_MAX_LOOKUP == ([9, 17], [350, 250])
    src = (ROOT / "opendbc_repo/opendbc/safety/safety/safety_rivian.h").read_text()
    limits = re.search(r"RIVIAN_STEERING_LIMITS = \{(.*?)\n  \};", src, re.S).group(1)
    for field in (".max_torque = 350,", "{9., 17., 17.},", "{350, 250, 250},", ".max_rate_up = 3,", ".max_rate_down = 5,",
                  ".max_rt_delta = 125,", ".driver_torque_multiplier = 2,", ".driver_torque_allowance = 100,"):
      assert field in limits


class TestDriverMonitoring:
  # rows 33, 34
  def test_timeouts(self):
    s = DRIVER_MONITOR_SETTINGS()
    assert (s._AWARENESS_TIME, s._AWARENESS_PRE_TIME_TILL_TERMINAL, s._AWARENESS_PROMPT_TIME_TILL_TERMINAL) == (130., 15., 6.)
    assert (s._DISTRACTED_TIME, s._DISTRACTED_PRE_TIME_TILL_TERMINAL, s._DISTRACTED_PROMPT_TIME_TILL_TERMINAL) == (111., 8., 6.)

  # row 35
  def test_pose_thresholds(self):
    s = DRIVER_MONITOR_SETTINGS()
    assert (s._POSE_PITCH_THRESHOLD, s._POSE_PITCH_THRESHOLD_SLACK) == (0.7133, 0.7237)
    assert (s._POSE_YAW_THRESHOLD, s._POSE_YAW_THRESHOLD_SLACK) == (0.7020, 0.8042)


class TestMads:
  # row 36
  def test_steering_mode(self):
    assert (mads_helpers.MadsSteeringModeOnBrake.REMAIN_ACTIVE, mads_helpers.MadsSteeringModeOnBrake.PAUSE,
            mads_helpers.MadsSteeringModeOnBrake.DISENGAGE) == (0, 1, 2)
    assert "#define ALT_EXP_MADS_DISENGAGE_LATERAL_ON_BRAKE 2048" in (ROOT / "selfdrive/pandad/pandad.cc").read_text()
    params = Params()
    params.put_bool("Mads", True)
    params.put("MadsSteeringMode", "2")
    CP, _ = rivian_params()
    mads_helpers.set_alternative_experience(CP, params)
    assert CP.alternativeExperience & 2048

  # row 37: on yeetfollow the Rivian (and Tesla) branch is nested under `if CP.brand == "hyundai":`
  # (merge bd55ce794), so it never runs. yeet-angle has it working. Strict: fixing it fails here.
  @pytest.mark.xfail(strict=True, reason="known: Rivian MADS block unreachable on yeetfollow, see automotive/openpilot#4")
  def test_rivian_disengage_on_brake(self):
    params = Params()
    params.put("MadsSteeringMode", "0")
    params.put_bool("MadsMainCruiseAllowed", True)
    CP, CP_SP = rivian_params()
    mads_helpers.set_car_specific_params(CP, CP_SP, params)
    assert params.get("MadsSteeringMode") == b"2"
    assert params.get_bool("MadsUnifiedEngagementMode")
    assert not params.get_bool("MadsMainCruiseAllowed")

  # row 38: the op engage rising edge alone turns lateral on
  def test_mads_requests_lateral_on_op_engage(self):
    safety = libsafety_py.libsafety
    safety.set_safety_hooks(CarParams.SafetyModel.rivian, 0)
    safety.init_tests()
    safety.set_mads_params(True, True, False)
    packer = CANPackerPanda("rivian_primary_actuator")
    brake = packer.make_can_msg_panda("iBESP2", 0, {"iBESP2_BrakePedalApplied": 0})
    safety.set_controls_allowed(False)
    safety.safety_rx_hook(brake)
    assert not safety.get_controls_allowed_lat()
    safety.set_controls_allowed(True)
    safety.safety_rx_hook(brake)
    assert safety.get_controls_allowed_lat()


class TestBootAndFirmware:
  # row 40: run the launcher's recovery block on a fake checkout and cache
  def test_build_corruption_cleanup(self):
    launcher = (ROOT / "launch_chffrplus.sh").read_text()
    block = re.search(r"\n(  rm -f /data/scons_cache/\*\.lock.*?)\n\n", launcher, re.S)
    assert block is not None, "boot recovery block missing from launch_chffrplus.sh"
    with tempfile.TemporaryDirectory() as d:
      tree, cache = Path(d) / "openpilot", Path(d) / "scons_cache"
      files = {
        "cache/a.lock": b"", "cache/empty": b"", "cache/good": b"x",
        "tree/x.o": b"", "tree/x.os": b"", "tree/x.so": b"", "tree/x.a": b"", "tree/ok.o": b"x",
        "tree/y.o.tmp": b"x", "tree/y.os.tmp": b"x", "tree/third_party/z.so": b"", "tree/third_party/z.o.tmp": b"x",
      }
      for name, data in files.items():
        path = (cache if name.startswith("cache/") else tree) / name.split("/", 1)[1]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
      script = block.group(1).replace("/data/scons_cache", str(cache))
      subprocess.run(["bash", "-c", script], env={**os.environ, "DIR": str(tree)}, check=True)
      kept = {f"cache/{p.relative_to(cache)}" for p in cache.rglob("*") if p.is_file()} | \
             {f"tree/{p.relative_to(tree)}" for p in tree.rglob("*") if p.is_file()}
    assert kept == {"cache/good", "tree/ok.o", "tree/third_party/z.so", "tree/third_party/z.o.tmp"}

  # row 41: panda pin 7723bbca scopes the CAN ignition counter per brand
  def test_ignition_counter_scoping(self):
    src = (ROOT / "panda/board/drivers/can_common.h").read_text()
    hook = re.search(r"void ignition_can_hook\(.*?\n}\n", src, re.S).group(0)
    gm = hook.index("// GM exception")
    assert "prev_counter" not in hook[:gm], "shared prev_counter is back at function scope"
    rivian = hook[hook.index("// Rivian"):hook.index("// Tesla")]
    tesla = hook[hook.index("// Tesla"):]
    assert "static int prev_counter = -1;" in rivian
    assert "static int prev_counter = -1;" in tesla
