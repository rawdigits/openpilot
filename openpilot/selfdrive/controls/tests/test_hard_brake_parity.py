"""yeet-angle-brake-tune: following and closing must be exactly the tuned planner without hard braking (aggressive:
yeet-angle-tune de7882112 plus 7538ea628's tune, standard and relaxed: yeet-angle b1da1d9c0), only cap-limited braking for
a lead goes past -3.5 (down to -6.5). yeet-angle-brake-smooth: the release slew keeps that braking as strong and as early as
ed39021a3 and bounds the release, also for a flickering lead (the 23:01Z cut-in). See MPC_TUNING.md.

hard_brake_parity.json holds the planner output (Rivian, kit path) of the trees in REFS, sampled every REF_DECIMATION
steps, and the hard-stop results of the -6.5 builds. Regenerate a part by copying this file into that tree and running
`python test_hard_brake_parity.py KEY` there (see REFS; "tune" is de7882112 with 7538ea628's long_mpc.py and
longitudinal_planner.py changes applied).
"""
import json
import sys
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from opendbc.car import gen_empty_fingerprint
from opendbc.car.interfaces import ACCEL_MIN
from opendbc.car.rivian.interface import CarInterface
from opendbc.car.rivian.values import CAR
from openpilot.cereal import log as capnp_log, messaging
from openpilot.common.parameterized import parameterized
from openpilot.common.test import OpenpilotTestCase
from openpilot.selfdrive.controls.lib import longitudinal_planner
from openpilot.selfdrive.controls.lib.longcontrol import LongCtrlState
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import LongitudinalMpc
from openpilot.selfdrive.controls.radard import _LEAD_ACCEL_TAU
from openpilot.selfdrive.test.longitudinal_maneuvers.plant import Plant

REF_FILE = Path(__file__).with_name("hard_brake_parity.json")
REF_DECIMATION = 5  # 0.25 s
ACCEL_TOL = 0.02
GAP_TOL = 0.05  # s
STEADY_T = 10.  # steady gap: mean time gap over the last STEADY_T s

PERSONALITIES = {"aggressive": 0, "standard": 1, "relaxed": 2}
T_FOLLOW = {0: 0.6, 1: 1.1, 2: 1.8}


def scenarios():
  """name -> (personality, secs, ego speed, lead distance, lead speed breakpoints, lead speeds, cap-limited)"""
  out = {}
  for pn, p in PERSONALITIES.items():
    for v in (15., 20., 25., 30., 35.):
      out[f"{pn} steady {v:.0f}"] = (p, 60., v, v * T_FOLLOW[p] + 8., [0., 60.], [v, v], False)
    for a in (0.5, 1.0):
      dur = 15. / a
      out[f"{pn} lead decel -{a} 25->10"] = (p, 40. + dur, 25., 25. * T_FOLLOW[p] + 3., [0., 30., 30. + dur], [25., 25., 10.], False)
    out[f"{pn} cut-in 1s gap 25"] = (p, 40., 25., 25., [0., 40.], [25., 25.], False)
    out[f"{pn} cut-in 1s gap 25, lead 22"] = (p, 40., 25., 25., [0., 40.], [22., 22.], False)
    for dv in (2., 3., 4., 5.):
      out[f"{pn} closing {dv:.0f} m/s at 30"] = (p, 60., 30., 80., [0., 60.], [30. - dv, 30. - dv], False)
    # cap-limited: b1da1d9c0 sits at -3.5 and runs into the lead
    out[f"{pn} lead brakes -6 from 30, 30 m"] = (p, 10., 30., 30., [0., 1., 6.], [30., 30., 0.], True)
    out[f"{pn} 35 m/s, lead 25 at 24 m"] = (p, 15., 35., 24., [0., 15.], [25., 25.], True)
    out[f"{pn} lead brakes -4 from 25, 1s gap"] = (p, 12., 25., 25., [0., 1., 7.25], [25., 25., 0.], True)
    out[f"{pn} stopped car at 30 m/s, 70 m"] = (p, 12., 30., 70., [0., 12.], [0., 0.], True)
  return out


SCENARIOS = scenarios()
NORMAL = [(k,) for k, s in SCENARIOS.items() if not s[6]]
CAP_LIMITED = [(k,) for k, s in SCENARIOS.items() if s[6]]
AGGRESSIVE = [k for k, s in SCENARIOS.items() if s[0] == PERSONALITIES["aggressive"]]

# key -> (tree, scenarios, planner output or hard-stop results)
REFS = {
  "b1da1d9c0": ("yeet-angle", list(SCENARIOS), "output"),
  "tune": ("de7882112 + 7538ea628's tune, no hard braking", AGGRESSIVE, "output"),
  "a44ab30a3": ("first -6.5 build", [k for k, in CAP_LIMITED], "hard"),
  "a9920129c": ("yeet-angle-brake, -6.5 only when cap-limited", [k for k, in CAP_LIMITED], "hard"),
  "7538ea628": ("yeet-angle-brake-tune on a44ab30a3", [k for k, in CAP_LIMITED], "hard"),
  "ed39021a3": ("yeet-angle-brake-tune, before the release slew", [k for k, in CAP_LIMITED], "stop"),
}
TUNE_STOP_TOL = 0.7  # m, hard-stop min gap vs 7538ea628 (hard braking starts when the stock plan is cap-limited, not on the first cycle)
SMOOTH_STOP_TOL = 0.05  # m, hard-stop min gap vs ed39021a3 (yeet-angle-brake-smooth only slows the release of braking)
DT = 0.05
RELEASE_BELOW = -1.0  # longitudinal_planner.ACCEL_RELEASE_BELOW, here too for recording trees without it


def normal_ref(ref, name):
  """The tuned planner without hard braking: the aggressive tune, b1da1d9c0 for standard and relaxed."""
  return ref["tune"][name] if name in ref["tune"] else ref["b1da1d9c0"][name]


def rivian_params():
  fingerprint = gen_empty_fingerprint()
  fingerprint[0][0x321] = 8  # Gen1
  fingerprint[1].update({0x1310: 8, 0x131a: 8})  # angle kit with the long harness
  CP = CarInterface.get_params(CAR.RIVIAN_R1, fingerprint, [], True, False, False)
  CP_SP = CarInterface.get_params_sp(CP, CAR.RIVIAN_R1, fingerprint, [], True, False, False)
  return CP, CP_SP


def simulate(name, hard_brake=True, release_slew=True):
  """Drive the real planner in the maneuver plant. hard_brake=False runs the same planner without the hard MPC,
  release_slew=False without the release slew (ed39021a3's planner)."""
  p, secs, speed, dist, bp, lead_v, _ = SCENARIOS[name]
  CP, CP_SP = rivian_params()
  plant = Plant(lead_relevancy=True, speed=speed, distance_lead=dist, personality=p)
  plant.planner = planner = longitudinal_planner.LongitudinalPlanner(CP, CP_SP, init_v=speed)
  if not hard_brake:
    planner.mpc_hard = None
  accel, speeds, gaps, hard = [], [], [], []
  no_slew = patch.object(longitudinal_planner, "ACCEL_RELEASE_RATE", np.inf) if hasattr(longitudinal_planner, "ACCEL_RELEASE_RATE") else nullcontext()
  with nullcontext() if release_slew else no_slew:
    while plant.current_time < secs:
      log = plant.step(float(np.interp(plant.current_time, bp, lead_v)), 1.0, 50.)
      accel.append(float(planner.output_a_target))
      speeds.append(log["speed"])
      gaps.append(log["distance_lead"] - log["distance"])
      hard.append(getattr(planner, "hard_brake", False))
  accel, speeds, gaps = map(np.array, (accel, speeds, gaps))
  steady = slice(-int(STEADY_T / plant.ts), None)
  steady_gap = float(np.mean(gaps[steady] / np.maximum(speeds[steady], 0.1)))
  return accel, steady_gap, float(gaps.min()), hard


# 2026-11-06 23:01Z: a car cut in at ~27 mph and radarState leadOne flipped every 1-3 frames between it (~9.8 m,
# aLeadK -3) and the old lead (~13.7 m, aLeadK -0.3). 1 = cut-in, from FLICKER_T s, then the cut-in stays.
FLICKER = [1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0]
FLICKER_T = 1.0


def radar_lead(d_rel, v_lead, a_lead, v_ego):
  lead = capnp_log.RadarState.LeadData.new_message()
  lead.dRel, lead.vRel, lead.vLead, lead.vLeadK = float(d_rel), float(v_lead - v_ego), float(v_lead), float(v_lead)
  lead.aLeadK, lead.aLeadTau = float(a_lead), float(_LEAD_ACCEL_TAU)
  lead.present, lead.modelProb, lead.radar = True, 1.0, True
  return lead


def planner_sm(lead, v_ego, personality, long_active=True):
  services = ('radarState', 'carState', 'carControl', 'controlsState', 'selfdriveState', 'vehicleParameters', 'modelV2',
              'carStateSP', 'liveMapDataSP', 'gpsLocation')
  sm = {s: getattr(messaging.new_message(s), s) for s in services}
  sm['radarState'].leadOne = lead
  sm['radarState'].leadTwo = lead
  sm['carState'].vEgo = float(v_ego)
  sm['carState'].vCruise = 30. * 3.6
  sm['controlsState'].longControlState = LongCtrlState.pid if long_active else LongCtrlState.off
  sm['selfdriveState'].personality = personality
  return sm


def simulate_flicker(personality, release_slew=True, secs=8.):
  """Ego at 12.9 m/s behind a lead at 13.7 m, the cut-in at 9.8 m brakes at -3 from FLICKER_T for 1.5 s while the
  planner's lead flickers. Returns the output accel and the min gap to the cut-in."""
  CP, CP_SP = rivian_params()
  planner = longitudinal_planner.LongitudinalPlanner(CP, CP_SP, init_v=12.9)
  v_ego, cut_in, old = 12.9, [9.8, 12.0], [13.7, 12.6]
  accel, gaps = [], []
  with nullcontext() if release_slew else patch.object(longitudinal_planner, "ACCEL_RELEASE_RATE", np.inf):
    for k in range(int(secs / DT)):
      t, k_flicker = k * DT, k - int(FLICKER_T / DT)
      a_cut_in, a_old = (-3. if FLICKER_T <= t < FLICKER_T + 1.5 else 0.), (-0.3 if t < 3. else 0.)
      use_cut_in = k_flicker >= 0 and (FLICKER[k_flicker] if k_flicker < len(FLICKER) else 1)
      lead = radar_lead(*cut_in, a_cut_in, v_ego) if use_cut_in else radar_lead(*old, a_old, v_ego)
      planner.update(planner_sm(lead, v_ego, personality))
      accel.append(float(planner.output_a_target))
      v_ego = max(v_ego + accel[-1] * DT, 0.)
      cut_in[1] = max(cut_in[1] + a_cut_in * DT, 0.)
      cut_in[0] += (cut_in[1] - v_ego) * DT
      old[1] = max(old[1] + a_old * DT, 0.)
      old[0] += (old[1] - v_ego) * DT
      gaps.append(cut_in[0])
  return np.array(accel), min(gaps)


def first_reached(accel, a):
  """Time the output first gets to a (rounded to 0.1 mm/s²)."""
  return round(float(np.argmax(accel <= a + 1e-4) * DT), 2)


def switch_steps(accel, hard):
  """Output step per frame at each switch into (entry) and out of (exit) hard braking."""
  steps = {True: [], False: []}
  for i in np.nonzero(np.diff(np.array(hard, int)))[0]:
    steps[bool(hard[i + 1])].append(float(accel[i + 1] - accel[i]))
  return steps[True], steps[False]


def max_release_step(accel):
  """Largest per-frame rise of the output from below ACCEL_RELEASE_BELOW (the frames the release slew covers)."""
  rises = np.diff(accel)[accel[:-1] < RELEASE_BELOW]
  return float(max(rises.max(initial=0.), 0.))


def stop_result(accel, min_gap, hard):
  entry, exit_ = switch_steps(accel, hard)
  return {"min_gap": round(min_gap, 3), "min_accel": round(float(accel.min()), 4),
          "t_min_accel": round(first_reached(accel, float(accel.min())), 2), "entry_steps": [round(d, 4) for d in entry],
          "exit_steps": [round(d, 4) for d in exit_], "max_release_step": round(max_release_step(accel), 4)}


class TestHardBrakeParity(OpenpilotTestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.ref = json.loads(REF_FILE.read_text())

  def test_scenarios_recorded(self):
    self.assertEqual(set(self.ref), set(REFS))
    for key, (_, names, _) in REFS.items():
      self.assertEqual(set(self.ref[key]), set(names), key)

  @parameterized.expand(NORMAL)
  def test_normal_following_is_tuned_planner(self, name):
    ref = normal_ref(self.ref, name)
    accel, steady_gap, _, hard = simulate(name)
    # the hard MPC is never used and the output equals the tuned planner's without hard braking
    self.assertFalse(any(hard))
    np.testing.assert_allclose(accel[::REF_DECIMATION], ref["accel"], rtol=0, atol=ACCEL_TOL)
    self.assertAlmostEqual(steady_gap, ref["steady_gap"], delta=GAP_TOL)
    # every step: the same planner without the hard MPC, bit for bit
    accel_stock, steady_gap_stock, _, _ = simulate(name, hard_brake=False)
    np.testing.assert_array_equal(accel, accel_stock)
    self.assertEqual(steady_gap, steady_gap_stock)
    # yeet-angle-brake-smooth: the release slew never binds when following, bit for bit ed39021a3's planner
    accel_ed39, steady_gap_ed39, _, _ = simulate(name, release_slew=False)
    np.testing.assert_array_equal(accel, accel_ed39)
    self.assertEqual(steady_gap, steady_gap_ed39)

  @parameterized.expand([(pn,) for pn in PERSONALITIES])
  def test_hard_mpc_uses_the_tune(self, pn):
    # the hard plan is the tuned plan with the -6.5 bound: both MPCs get the same personality cost weights
    # (jerk factor, jerk cost) and t_follow / comfort brake every cycle
    p, secs, speed, dist, bp, lead_v, _ = SCENARIOS[f"{pn} lead brakes -6 from 30, 30 m"]
    CP, CP_SP = rivian_params()
    plant = Plant(lead_relevancy=True, speed=speed, distance_lead=dist, personality=p)
    plant.planner = planner = longitudinal_planner.LongitudinalPlanner(CP, CP_SP, init_v=speed)
    weights = {id(planner.mpc): [], id(planner.mpc_hard): []}
    set_cost_weights = LongitudinalMpc.set_cost_weights
    def record(mpc, cost_weights, constraint_cost_weights):
      weights[id(mpc)].append((list(cost_weights), list(constraint_cost_weights)))
      return set_cost_weights(mpc, cost_weights, constraint_cost_weights)
    with patch.object(LongitudinalMpc, "set_cost_weights", autospec=True, side_effect=record):
      while plant.current_time < secs:
        plant.step(float(np.interp(plant.current_time, bp, lead_v)), 1.0, 50.)
        np.testing.assert_array_equal(planner.mpc_hard.params[:, 4:7], planner.mpc.params[:, 4:7])
    self.assertTrue(len(weights[id(planner.mpc)]) > 100)
    self.assertEqual(weights[id(planner.mpc_hard)], weights[id(planner.mpc)])

  @parameterized.expand(CAP_LIMITED)
  def test_cap_limited_brakes_harder(self, name):
    ref, ref_hard = normal_ref(self.ref, name), self.ref["a44ab30a3"][name]
    accel, _, min_gap, hard = simulate(name)
    self.assertLessEqual(min(ref["accel"]), ACCEL_MIN + 0.1)  # the planner without hard braking is at the cap here
    self.assertTrue(any(hard))
    self.assertGreaterEqual(accel.min(), -6.5 - 1e-6)
    self.assertLess(accel.min(), ACCEL_MIN)
    # at least as good as a44ab30a3: no closer to the lead, and much better than b1da1d9c0
    self.assertGreaterEqual(min_gap, ref_hard["min_gap"] - 0.1)
    self.assertGreater(min_gap, ref["min_gap"])
    # never closer than yeet-angle-brake a9920129c (min gaps are recorded to 1 mm), at most TUNE_STOP_TOL closer than 7538ea628
    self.assertGreaterEqual(min_gap, self.ref["a9920129c"][name]["min_gap"] - 1e-3)
    self.assertGreaterEqual(min_gap, self.ref["7538ea628"][name]["min_gap"] - TUNE_STOP_TOL)
    # at most two switches (into hard braking and back), no chatter
    self.assertLessEqual(int(np.sum(np.diff(np.array(hard, int)) != 0)), 2)

  @parameterized.expand(CAP_LIMITED)
  def test_release_slew_keeps_hard_braking(self, name):
    # yeet-angle-brake-smooth: braking as strong and as early as ed39021a3, never closer to the lead
    ref = self.ref["ed39021a3"][name]
    accel, _, min_gap, hard = simulate(name)
    self.assertGreaterEqual(min_gap, ref["min_gap"] - SMOOTH_STOP_TOL)
    self.assertLessEqual(accel.min(), ref["min_accel"] + 1e-4)
    self.assertLessEqual(first_reached(accel, ref["min_accel"]), ref["t_min_accel"])
    # ed39021a3's planner is what the reference recorded
    accel_ed39, _, min_gap_ed39, hard_ed39 = simulate(name, release_slew=False)
    self.assertEqual(stop_result(accel_ed39, min_gap_ed39, hard_ed39), ref)
    # the release is bounded, onset is untouched: braking harder only ever comes from the planner
    self.assertEqual(longitudinal_planner.ACCEL_RELEASE_BELOW, RELEASE_BELOW)
    self.assertLessEqual(max_release_step(accel), longitudinal_planner.ACCEL_RELEASE_RATE * DT + 1e-9)

  @parameterized.expand(CAP_LIMITED)
  def test_hard_brake_switch_steps(self, name):
    # output step at the switch into the hard MPC (no blend there, it brakes harder: onset, not limited) and out of it
    # (back to the stock plan: a release while braking, bounded by the slew)
    ref = self.ref["ed39021a3"][name]
    accel, _, _, hard = simulate(name)
    entry, exit_ = switch_steps(accel, hard)
    self.assertEqual(len(entry), len(ref["entry_steps"]))
    np.testing.assert_allclose(entry, ref["entry_steps"], rtol=0, atol=1e-4)
    self.assertTrue(all(d <= 0. for d in entry))
    for i in np.nonzero(np.diff(np.array(hard, int)) < 0)[0]:
      if accel[i] < RELEASE_BELOW:
        self.assertLessEqual(accel[i + 1] - accel[i], longitudinal_planner.ACCEL_RELEASE_RATE * DT + 1e-9)


  @parameterized.expand([(pn,) for pn in PERSONALITIES])
  def test_flickering_lead_does_not_release(self, pn):
    # the 23:01Z cut-in: while the lead flickers the output only gets less negative by the slew (ed39021a3 bounced back
    # up to 0.6 m/s² in a frame), and it ends no closer to the cut-in than ed39021a3
    p = PERSONALITIES[pn]
    accel, min_gap = simulate_flicker(p)
    accel_ed39, min_gap_ed39 = simulate_flicker(p, release_slew=False)
    flicker = slice(int(FLICKER_T / DT) - 1, int(FLICKER_T / DT) + len(FLICKER))
    self.assertLessEqual(max_release_step(accel[flicker]), longitudinal_planner.ACCEL_RELEASE_RATE * DT + 1e-9)
    self.assertGreaterEqual(min_gap, min_gap_ed39)
    self.assertLessEqual(accel.min(), accel_ed39.min() + 0.1)
    if p == PERSONALITIES["aggressive"]:
      self.assertGreater(max_release_step(accel_ed39[flicker]), 0.5)  # the bounce this is for

  def test_release_is_immediate_on_reset(self):
    # disengage, longActive false and driver override (longControlState off) reset the planner to aEgo as before:
    # the frame after hard braking for a lead that is gone, the output is ed39021a3's, the slew doesn't hold the braking
    def run(release_slew):
      CP, CP_SP = rivian_params()
      planner = longitudinal_planner.LongitudinalPlanner(CP, CP_SP, init_v=20.)
      with nullcontext() if release_slew else patch.object(longitudinal_planner, "ACCEL_RELEASE_RATE", np.inf):
        for _ in range(20):
          planner.update(planner_sm(radar_lead(10., 10., -3., 20.), 20., PERSONALITIES["standard"]))
        braking = planner.output_a_target
        sm = planner_sm(capnp_log.RadarState.LeadData.new_message(), 20., PERSONALITIES["standard"], long_active=False)
        sm['carState'].aEgo = 0.3
        planner.update(sm)
      return braking, planner.output_a_target
    braking, after_reset = run(True)
    self.assertLess(braking, ACCEL_MIN)
    self.assertEqual((braking, after_reset), run(False))
    self.assertGreater(after_reset - braking, longitudinal_planner.ACCEL_RELEASE_RATE * DT)

  def test_limit_release(self):
    rate_dt = longitudinal_planner.ACCEL_RELEASE_RATE * DT
    # onset (braking harder) passes through, also as a step
    self.assertEqual(longitudinal_planner.limit_release(-6.5, -1.5, DT), -6.5)
    self.assertEqual(longitudinal_planner.limit_release(-1.5, -0.2, DT), -1.5)
    # release from below ACCEL_RELEASE_BELOW is rate limited, also into positive accel
    self.assertAlmostEqual(longitudinal_planner.limit_release(-1.0, -3.0, DT), -3.0 + rate_dt)
    self.assertAlmostEqual(longitudinal_planner.limit_release(1.0, -1.01, DT), -1.01 + rate_dt)
    # above it nothing changes, cruise and accel side included
    self.assertEqual(longitudinal_planner.limit_release(0.5, -0.9, DT), 0.5)
    self.assertEqual(longitudinal_planner.limit_release(1.2, 0.3, DT), 1.2)


  @parameterized.expand([("aggressive lead brakes -6 from 30, 30 m", True), ("standard 35 m/s, lead 25 at 24 m", True),
                         ("aggressive steady 30", False), ("standard steady 25", False)])
  def test_hard_brake_published(self, name, hard_expected):
    # longitudinalPlanSP.hardBrake shows on the device which planner is in use, and every switch logs a
    # hard_brake_switch event with the old and new planner, aTarget and vEgo
    p, secs, speed, dist, bp, lead_v, _ = SCENARIOS[name]
    CP, CP_SP = rivian_params()
    plant = Plant(lead_relevancy=True, speed=speed, distance_lead=dist, personality=p)
    plant.planner = planner = longitudinal_planner.LongitudinalPlanner(CP, CP_SP, init_v=speed)
    pm, sm = MagicMock(), MagicMock()
    sm.all_checks.return_value = True
    flags, hard = [], []
    with patch.object(longitudinal_planner.cloudlog, "event") as event:
      while plant.current_time < secs:
        plant.step(float(np.interp(plant.current_time, bp, lead_v)), 1.0, 50.)
        planner.publish_longitudinal_plan_sp(sm, pm)
        flags.append(pm.send.call_args.args[1].longitudinalPlanSP.hardBrake)
        hard.append(planner.mpc_hard is not None and planner.hard_brake)
    self.assertEqual(flags, hard)
    self.assertEqual(any(flags), hard_expected)
    switches = [c.kwargs for c in event.call_args_list if c.args == ("hard_brake_switch",)]
    self.assertEqual(len(switches), int(np.sum(np.diff(np.array([False] + hard, int)) != 0)))
    for sw, i in zip(switches, np.nonzero(np.diff(np.array([False] + hard, int)))[0], strict=True):
      self.assertEqual((sw["prev_planner"], sw["planner"]), ("stock", "hard") if hard[i] else ("hard", "stock"))
      self.assertEqual(set(sw), {"planner", "prev_planner", "aTarget", "vEgo", "source"})


if __name__ == "__main__":
  # record a reference from the tree this runs in, KEY from REFS
  key = sys.argv[1]
  _, names, kind = REFS[key]
  data = json.loads(REF_FILE.read_text()) if REF_FILE.exists() else {}
  data[key] = {}
  for n in names:
    accel, steady_gap, min_gap, hard = simulate(n)
    if kind == "output":
      data[key][n] = {"accel": [round(float(a), 4) for a in accel[::REF_DECIMATION]], "steady_gap": round(steady_gap, 4),
                      "min_gap": round(min_gap, 3)}
    elif kind == "stop":
      data[key][n] = stop_result(accel, min_gap, hard)
    else:
      data[key][n] = {"min_gap": round(min_gap, 3), "min_accel": round(float(accel.min()), 4)}
  REF_FILE.write_text(json.dumps({k: data[k] for k in REFS if k in data}, indent=1) + "\n")
