"""yeet-angle-brake-levels: the Rivian truck's four follow levels (RivianFollowLevel, from the TCM bridge's follow_level).
Level 1 is the aggressive personality and level 4 the relaxed one, bit for bit, levels 2 and 3 are 1/3 and 2/3 of the way
from aggressive to relaxed in every per-personality value. See MPC_TUNING.md.

`python test_follow_levels.py` prints the per-level table in MPC_TUNING.md.
"""
import itertools
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from openpilot.cereal import log
from openpilot.common.parameterized import parameterized
from openpilot.common.test import OpenpilotTestCase
from openpilot.selfdrive.controls.lib import longitudinal_planner
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib import long_mpc
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import FollowLevel
from openpilot.selfdrive.controls.tests import test_hard_brake_parity as parity
from openpilot.selfdrive.test.longitudinal_maneuvers.plant import Plant

Personality = log.LongitudinalPersonality
LEVELS = (1, 2, 3, 4)
ENDS = {1: Personality.aggressive, 4: Personality.relaxed}
MPH = 0.44704


def run(speed, gap, bp, lead_v, secs, cruise=50., follow_level=0, personality=Personality.standard):
  """Drive the real planner (Rivian, kit path) in the maneuver plant. Returns time, ego speed, accel output, gap, fcw."""
  CP, CP_SP = parity.rivian_params()
  plant = Plant(lead_relevancy=True, speed=speed, distance_lead=gap, personality=personality, follow_level=follow_level)
  plant.planner = planner = longitudinal_planner.LongitudinalPlanner(CP, CP_SP, init_v=speed)
  rows = []
  while plant.current_time < secs:
    t = plant.current_time
    out = plant.step(float(np.interp(t, bp, lead_v)), 1.0, cruise)
    rows.append((t, out["speed"], float(planner.output_a_target), out["distance_lead"] - out["distance"], out["fcw"]))
  return np.array(rows).T


def desired_gap(level, v):
  return long_mpc.get_T_FOLLOW(FollowLevel(level)) * v + long_mpc.STOP_DISTANCE


def steady_gap(level, mph):
  """Gap (m) after 60 s behind a lead at a constant mph, starting 5 m past the desired gap."""
  v = mph * MPH
  _, _, _, d, _ = run(v, desired_gap(level, v) + 5., [0., 60.], [v, v], 60., cruise=v + 5., follow_level=level)
  return round(float(d[-1]), 2)


def pull_away(level, v):
  """Settled at v, the lead accelerates at 2 m/s² by +10 m/s at 20 s: mean accel over the next 6 s (m/s²)."""
  t, _, a, _, _ = run(v, desired_gap(level, v), [0., 20., 25., 80.], [v, v, v + 10., v + 10.], 26., cruise=v + 15., follow_level=level)
  return round(float(a[(t >= 20.) & (t < 26.)].mean()), 3)


def reclose(level, v):
  """Settled at v, the lead +3 m/s at 1.5 m/s² at 20 s. Returns the time until the gap is back within 0.05 s of the
  level's (s, as in the tables above) and the time until the gap error (m past the level's gap) is half its peak (s)."""
  t, ve, _, d, _ = run(v, desired_gap(level, v), [0., 20., 22., 120.], [v, v, v + 3., v + 3.], 90., cruise=v + 15., follow_level=level)
  t_follow = long_mpc.get_T_FOLLOW(FollowLevel(level))
  g = (d - long_mpc.STOP_DISTANCE) / np.maximum(ve, 1.)
  widest = int(np.argmax(np.where(t >= 20., g, -1.)))
  back = np.nonzero((t > t[widest]) & (g <= t_follow + 0.05))[0]
  err = d - (t_follow * ve + long_mpc.STOP_DISTANCE)
  peak = int(np.argmax(np.where(t >= 20., err, -np.inf)))
  half = np.nonzero((t > t[peak]) & (err <= err[peak] / 2))[0]
  return (round(float(t[back[0]] - 20.), 2) if len(back) else None), (round(float(t[half[0]] - 20.), 2) if len(half) else None)


STOPS = ((20., 3.), (20., 5.), (30., 4.), (30., 6.), (35., 6.5))


def hard_stop(level, key):
  """Min gap (m, below 0 is contact) and min accel. key "v@decel": settled at the level's gap, the lead brakes to 0 at decel
  from 10 s. Else a test_hard_brake_parity cap-limited scenario (the same start for every level)."""
  if "@" in key:
    v, dec = map(float, key.split("@"))
    t, _, a, d, _ = run(v, desired_gap(level, v), [0., 10., 10. + v / dec, 60.], [v, v, 0., 0.], 10. + v / dec + 15., follow_level=level)
  else:
    _, secs, speed, dist, bp, lead_v, _ = parity.SCENARIOS[f"aggressive {key}"]
    t, _, a, d, _ = run(speed, dist, bp, lead_v, secs, follow_level=level)
  return round(float(d.min()), 3), round(float(a.min()), 3)


CAP_LIMITED_KEYS = [k.removeprefix("aggressive ") for k, s in parity.SCENARIOS.items() if s[6] and k.startswith("aggressive ")]
METRICS = {"steady gap": steady_gap, "pull-away": pull_away, "re-close": reclose, "hard stop": hard_stop}
METRIC_KEYS = {"steady gap": (30, 50, 70), "pull-away": (10., 20., 30.), "re-close": (10., 20., 30.),
               "hard stop": [f"{v:.0f}@{dec}" for v, dec in STOPS] + CAP_LIMITED_KEYS}


def _metric(args):
  kind, key, level = args
  return METRICS[kind](level, key)


def all_metrics():
  """{kind: {key: [level 1, 2, 3, 4]}}"""
  jobs = [(kind, key, level) for kind, keys in METRIC_KEYS.items() for key in keys for level in LEVELS]
  with ProcessPoolExecutor() as ex:
    values = iter(ex.map(_metric, jobs))
  return {kind: {key: [next(values) for _ in LEVELS] for key in keys} for kind, keys in METRIC_KEYS.items()}


def assert_monotonic(test, values, msg):
  # levels 2 and 3 in order between level 1 and level 4 (either direction)
  sign = np.sign(values[-1] - values[0])
  test.assertTrue(all(sign * (b - a) >= 0 for a, b in itertools.pairwise(values)), f"{msg}: {values}")


class TestFollowLevelValues(OpenpilotTestCase):
  def test_t_follow(self):
    self.assertEqual([long_mpc.get_T_FOLLOW(FollowLevel(lv)) for lv in (1, 4)], [0.60, 1.80])
    np.testing.assert_allclose([long_mpc.get_T_FOLLOW(FollowLevel(lv)) for lv in LEVELS], [0.6, 1.0, 1.4, 1.8], rtol=0, atol=1e-12)

  @parameterized.expand([(1,), (4,)])
  def test_ends_are_the_personalities(self, level):
    # the same values (==, not approximately) for every per-personality getter
    p = ENDS[level]
    for get in (long_mpc.get_T_FOLLOW, long_mpc.get_comfort_brake, long_mpc.get_jerk_factor, long_mpc.get_j_ego_factor,
                long_mpc.get_j_ego_cost):
      self.assertEqual(get(FollowLevel(level)), get(p), get.__name__)
      self.assertEqual(get(FollowLevel(level, hard=True)), get(p), get.__name__)
    for v in (0., 5., 10., 17.5, 25., 33., 40., 50.):
      self.assertEqual(longitudinal_planner.get_max_accel(v, FollowLevel(level)), longitudinal_planner.get_max_accel(v, p))
      self.assertEqual(longitudinal_planner.get_cruise_jerk(v, FollowLevel(level)), longitudinal_planner.get_cruise_jerk(v, p))
    for prev_accel_constraint in (True, False):
      self.assertEqual(self._weights(FollowLevel(level), prev_accel_constraint), self._weights(p, prev_accel_constraint))

  @staticmethod
  def _weights(personality, prev_accel_constraint):
    mpc = long_mpc.LongitudinalMpc()
    weights = []
    mpc.set_cost_weights = lambda w, c: weights.append((list(w), list(c)))
    mpc.set_weights(prev_accel_constraint, personality=personality)
    return weights

  @parameterized.expand([(2,), (3,)])
  def test_between_is_evenly_interpolated(self, level):
    w = (level - 1) / 3
    def lerp(a, r):
      return (1 - w) * a + w * r
    A, R = Personality.aggressive, Personality.relaxed
    self.assertAlmostEqual(long_mpc.get_T_FOLLOW(FollowLevel(level)), lerp(0.6, 1.8))
    self.assertAlmostEqual(long_mpc.get_comfort_brake(FollowLevel(level)), lerp(3.5, 3.0))
    self.assertAlmostEqual(long_mpc.get_jerk_factor(FollowLevel(level)), lerp(0.2, 1.0))
    # the MPC costs themselves are interpolated: a-change jerk_factor * A_CHANGE_COST, jerk 0.2 * 0.5 * 5 .. 5
    (cost, constraint), = self._weights(FollowLevel(level), True)
    (cost_a, constraint_a), = self._weights(A, True)
    (cost_r, constraint_r), = self._weights(R, True)
    np.testing.assert_allclose(cost, [lerp(a, r) for a, r in zip(cost_a, cost_r, strict=True)], rtol=1e-12)
    self.assertAlmostEqual(cost[5], lerp(0.5, 5.))
    self.assertEqual(constraint, constraint_a)
    self.assertEqual(constraint, constraint_r)
    # hard braking: level 1's cost weights, the rest stays the level's
    self.assertEqual(long_mpc.HARD_BRAKE_COST_LEVEL, {1: 1, 2: 1, 3: 1, 4: 4})
    self.assertEqual(self._weights(FollowLevel(level, hard=True), True), self._weights(A, True))
    self.assertEqual(long_mpc.get_T_FOLLOW(FollowLevel(level, hard=True)), long_mpc.get_T_FOLLOW(FollowLevel(level)))
    self.assertEqual(long_mpc.get_comfort_brake(FollowLevel(level, hard=True)), long_mpc.get_comfort_brake(FollowLevel(level)))
    self.assertEqual(longitudinal_planner.get_max_accel(20., FollowLevel(level, hard=True)),
                     longitudinal_planner.get_max_accel(20., FollowLevel(level)))
    for v in (0., 10., 17.5, 25., 40.):
      self.assertAlmostEqual(longitudinal_planner.get_max_accel(v, FollowLevel(level)),
                             lerp(longitudinal_planner.get_max_accel(v, A), longitudinal_planner.get_max_accel(v, R)))
      self.assertAlmostEqual(longitudinal_planner.get_cruise_jerk(v, FollowLevel(level)),
                             lerp(longitudinal_planner.get_cruise_jerk(v, A), longitudinal_planner.get_cruise_jerk(v, R)))
    # the cruise tables at the breakpoints: [2.0, 1.8, 1.4, 1.1] .. [1.6, 1.2, 0.8, 0.6]
    expected = {2: [1.8667, 1.6, 1.2, 0.9333], 3: [1.7333, 1.4, 1.0, 0.7667]}[level]
    for v, a in zip(longitudinal_planner.A_CRUISE_MAX_BP, expected, strict=True):
      self.assertAlmostEqual(longitudinal_planner.get_max_accel(v, FollowLevel(level)), a, places=4)

  def test_planner_selection(self):
    # the follow level wins over the personality when it is 1-4, 0 (no level) and anything else uses the personality
    sm = parity.planner_sm(parity.radar_lead(30., 20., 0., 20.), 20., Personality.standard)
    for level, expected in ((1, FollowLevel(1)), (2, FollowLevel(2)), (3, FollowLevel(3)), (4, FollowLevel(4)),
                            (0, Personality.standard), (5, Personality.standard), (255, Personality.standard)):
      sm['selfdriveStateSP'].followLevel = level
      self.assertEqual(longitudinal_planner.get_personality(sm), expected)
    with self.assertRaises(NotImplementedError):
      long_mpc.get_T_FOLLOW(FollowLevel(5))


class TestFollowLevelHardBraking(OpenpilotTestCase):
  """Levels 2 and 3 plan with level 1's MPC costs while the planner is hard braking, both MPCs, from the cycle it starts."""

  @parameterized.expand([(lv,) for lv in (2, 3)])
  def test_hard_braking_costs(self, level):
    _, secs, speed, dist, bp, lead_v, _ = parity.SCENARIOS["aggressive lead brakes -6 from 30, 30 m"]
    CP, CP_SP = parity.rivian_params()
    plant = Plant(lead_relevancy=True, speed=speed, distance_lead=dist, follow_level=level)
    plant.planner = planner = longitudinal_planner.LongitudinalPlanner(CP, CP_SP, init_v=speed)
    hard, used = [], []
    weights = {id(planner.mpc): [], id(planner.mpc_hard): []}
    set_cost_weights = long_mpc.LongitudinalMpc.set_cost_weights
    def record(mpc, cost_weights, constraint_cost_weights):
      weights[id(mpc)].append(list(cost_weights))
      return set_cost_weights(mpc, cost_weights, constraint_cost_weights)
    long_mpc.LongitudinalMpc.set_cost_weights = record
    try:
      while plant.current_time < secs:
        plant.step(float(np.interp(plant.current_time, bp, lead_v)), 1.0, 50.)
        hard.append(planner.hard_brake)
        used.append(planner.mpc_personality)
        self._check_params(planner, level)
    finally:
      long_mpc.LongitudinalMpc.set_cost_weights = set_cost_weights
    self.assertEqual(weights[id(planner.mpc_hard)], weights[id(planner.mpc)])
    self.assertIn(self._level_1_weights(), weights[id(planner.mpc)])
    self.assertTrue(any(hard))
    # hard braking costs on every cycle that hard brakes, from the first one, and on the cycle it ends (solved before)
    self.assertEqual(used, [FollowLevel(level, hard=h or h_prev) for h, h_prev in zip(hard, [False] + hard[:-1], strict=True)])

  @staticmethod
  def _level_1_weights():
    mpc = long_mpc.LongitudinalMpc()
    out = []
    mpc.set_cost_weights = lambda w, c: out.append(list(w))
    mpc.set_weights(True, personality=Personality.aggressive)
    return out[0]

  def _check_params(self, planner, level):
    # both MPCs plan with the same personality and costs, T_FOLLOW and comfort brake stay the level's
    np.testing.assert_array_equal(planner.mpc_hard.params[:, 4:7], planner.mpc.params[:, 4:7])
    self.assertEqual(planner.mpc.params[0, 4], long_mpc.get_T_FOLLOW(FollowLevel(level)))
    self.assertEqual(planner.mpc.params[0, 6], long_mpc.get_comfort_brake(FollowLevel(level)))

  def test_hard_brake_switch_and_fcw(self):
    # the cycle hard braking starts is solved again with the hard braking costs: one hard_brake_switch, FCW counted once
    _, secs, speed, dist, bp, lead_v, _ = parity.SCENARIOS["aggressive stopped car at 30 m/s, 70 m"]
    CP, CP_SP = parity.rivian_params()
    plant = Plant(lead_relevancy=True, speed=speed, distance_lead=dist, follow_level=2)
    plant.planner = planner = longitudinal_planner.LongitudinalPlanner(CP, CP_SP, init_v=speed)
    crash_cnt, solves = [], []
    update = long_mpc.LongitudinalMpc.update
    def count(mpc, *args, **kwargs):
      solves.append(mpc is planner.mpc)
      return update(mpc, *args, **kwargs)
    long_mpc.LongitudinalMpc.update = count
    try:
      for _ in range(10):
        solves.clear()
        plant.step(0., 1.0, 50.)
        crash_cnt.append(planner.mpc.crash_cnt)
        if planner.hard_brake and len(crash_cnt) == 1:
          self.assertEqual(solves, [True, False, True, False])  # solved again on the first cycle
    finally:
      long_mpc.LongitudinalMpc.update = update
    self.assertTrue(planner.hard_brake)
    self.assertEqual(np.diff(crash_cnt).max(), 1)


class TestFollowLevelChange(OpenpilotTestCase):
  def test_level_change_takes_effect_next_cycle(self):
    # the planner reads selfdriveStateSP.followLevel every cycle (the bridge polls at 3 Hz and selfdrived reads the param
    # at 10 Hz, so a thumb-wheel change reaches the planner in ~0.5 s)
    CP, CP_SP = parity.rivian_params()
    planner = longitudinal_planner.LongitudinalPlanner(CP, CP_SP, init_v=25.)
    sm = parity.planner_sm(parity.radar_lead(40., 25., 0., 25.), 25., Personality.standard)
    for level in (1, 4, 2, 3, 0):
      sm['selfdriveStateSP'].followLevel = level
      planner.update(sm)
      expected = FollowLevel(level) if level else Personality.standard
      self.assertEqual(planner.personality, expected)
      self.assertEqual(planner.mpc.params[0, 4], long_mpc.get_T_FOLLOW(expected))

  def test_level_change_while_following(self):
    # 1 -> 4 -> 2 behind a steady lead: the gap moves to each level's, no hard braking
    v = 25.
    CP, CP_SP = parity.rivian_params()
    plant = Plant(lead_relevancy=True, speed=v, distance_lead=desired_gap(1, v), follow_level=1)
    plant.planner = planner = longitudinal_planner.LongitudinalPlanner(CP, CP_SP, init_v=v)
    for level in (1, 4, 2):
      plant.follow_level = level
      t0 = plant.current_time
      while plant.current_time < t0 + 60.:
        out = plant.step(v, 1.0, 50.)
        self.assertFalse(planner.hard_brake)
        self.assertGreater(planner.output_a_target, -2.0)
      self.assertAlmostEqual(out["distance_lead"] - out["distance"], desired_gap(level, v), delta=0.5)


def parity_scenarios():
  return [(k, lv) for k, s in parity.SCENARIOS.items() for lv, p in ENDS.items() if s[0] == p]


class TestFollowLevelEnds(OpenpilotTestCase):
  """Level 1 is aggressive and level 4 relaxed bit for bit, with the personality set to something else."""

  @staticmethod
  def _parity_run(name, follow_level, personality):
    _, secs, speed, dist, bp, lead_v, _ = parity.SCENARIOS[name]
    return run(speed, dist, bp, lead_v, secs, follow_level=follow_level, personality=personality)

  @parameterized.expand(parity_scenarios())
  def test_parity_scenarios(self, name, level):
    p = parity.SCENARIOS[name][0]
    other = Personality.standard
    ref = self._parity_run(name, 0, p)
    np.testing.assert_array_equal(self._parity_run(name, level, other), ref)
    # and the same as test_hard_brake_parity's run of the personality (the recorded references)
    accel, _, _, _ = parity.simulate(name)
    np.testing.assert_array_equal(ref[2], accel)

  @parameterized.expand([(lv,) for lv in ENDS])
  def test_flicker(self, level):
    # the 23:01Z flicker (test_hard_brake_parity.simulate_flicker), driven with the follow level instead
    ref = parity.simulate_flicker(ENDS[level])
    planner_sm = parity.planner_sm
    def with_level(lead, v_ego, personality, long_active=True):
      sm = planner_sm(lead, v_ego, Personality.standard, long_active)
      sm['selfdriveStateSP'].followLevel = level
      return sm
    parity.planner_sm = with_level
    try:
      accel, min_gap = parity.simulate_flicker(ENDS[level])
    finally:
      parity.planner_sm = planner_sm
    np.testing.assert_array_equal(accel, ref[0])
    self.assertEqual(min_gap, ref[1])

  @parameterized.expand([(lv, v) for lv in ENDS for v in (0., 10., 35.)])
  def test_following_distance(self, level, v):
    # test_following_distance's scenario: lead at constant speed, 100 m ahead
    args = (v, 100., [0.], [v], 100.)
    np.testing.assert_array_equal(run(*args, follow_level=level, personality=Personality.standard),
                                  run(*args, personality=ENDS[level]))

  @parameterized.expand([(lv, key) for lv in ENDS for key in ("30@4.0", "35@6.5")])
  def test_stops_and_pull_away(self, level, key):
    v, dec = map(float, key.split("@"))
    for args in (((v, 25., [0., 10., 10. + v / dec, 60.], [v, v, 0., 0.], 25. + v / dec)),
                 ((v, 25., [0., 20., 25., 80.], [v, v, v + 10., v + 10.], 30., v + 15.))):
      np.testing.assert_array_equal(run(*args, follow_level=level, personality=Personality.standard),
                                    run(*args, personality=ENDS[level]))


class TestFollowLevelSpacing(OpenpilotTestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.metrics = all_metrics()

  def test_levels_are_monotonic(self):
    for kind in ("steady gap", "pull-away"):
      for key, values in self.metrics[kind].items():
        assert_monotonic(self, values, f"{kind} {key}")
    # re-close: the time to halve the gap error. The time to within 0.05 s isn't monotonic (MPC_TUNING.md)
    for key, values in self.metrics["re-close"].items():
      self.assertNotIn(None, [h for _, h in values], f"re-close {key}")
      assert_monotonic(self, [h for _, h in values], f"re-close half {key}")
    # hard stops settled at the level's own gap: a longer gap from level 1 to 3 ends no closer. Level 4 is relaxed's planner,
    # levels 2 and 3 brake with level 1's costs (MPC_TUNING.md), so they can end further back than level 4.
    for key, values in self.metrics["hard stop"].items():
      if "@" in key:
        gaps = [g for g, _ in values]
        self.assertTrue(gaps[0] <= gaps[1] <= gaps[2], f"hard stop {key}: {gaps}")

  def test_steady_gap_is_the_level_gap(self):
    for mph, values in self.metrics["steady gap"].items():
      for level, gap in zip(LEVELS, values, strict=True):
        self.assertAlmostEqual(gap, desired_gap(level, mph * MPH), delta=0.5)
      # evenly spaced, as T_FOLLOW is
      np.testing.assert_allclose(np.diff(values), np.diff(values)[0], rtol=0, atol=0.5)

  def test_hard_stop_never_closer_than_level_1(self):
    for key, values in self.metrics["hard stop"].items():
      for level, (min_gap, _) in zip(LEVELS[1:3], values[1:3], strict=True):
        self.assertGreaterEqual(min_gap, values[0][0], f"level {level}, {key}: {values}")

  def test_ends_match_the_personalities(self):
    # the table's level 1 / 4 columns are the aggressive / relaxed personality's numbers
    for v in (10., 20.):
      t, _, a, _, _ = run(v, 0.6 * v + 3., [0., 20., 25., 80.], [v, v, v + 10., v + 10.], 26., cruise=v + 15.,
                          personality=Personality.aggressive)
      self.assertEqual(self.metrics["pull-away"][v][0], round(float(a[(t >= 20.) & (t < 26.)].mean()), 3))


def table(metrics):
  rows = [("steady gap at 30 / 50 / 70 mph (m)", " / ".join(f"{metrics['steady gap'][m][i]:.1f}" for m in (30, 50, 70)))
          for i in range(4)]
  out = ["| | " + " | ".join(f"level {lv}" for lv in LEVELS) + " |", "|---" * 5 + "|"]
  out.append("| T_FOLLOW (s) | " + " | ".join(f"{long_mpc.get_T_FOLLOW(FollowLevel(lv)):.2f}" for lv in LEVELS) + " |")
  out.append("| steady gap 30 / 50 / 70 mph (m) | " + " | ".join(r[1] for r in rows) + " |")
  out.append("| pull-away mean accel 10 / 20 / 30 m/s (m/s²) | " + " | ".join(
    " / ".join(f"{metrics['pull-away'][v][i]:.2f}" for v in (10., 20., 30.)) for i in range(4)) + " |")
  out.append("| re-close after lead +3, gap within 0.05 s, 10 / 20 / 30 m/s (s) | " + " | ".join(
    " / ".join(f"{metrics['re-close'][v][i][0]}" for v in (10., 20., 30.)) for i in range(4)) + " |")
  out.append("| re-close after lead +3, gap error halved, 10 / 20 / 30 m/s (s) | " + " | ".join(
    " / ".join(f"{metrics['re-close'][v][i][1]}" for v in (10., 20., 30.)) for i in range(4)) + " |")
  for key, values in metrics["hard stop"].items():
    label = f"stop {key}, settled (min gap m, min a)" if "@" in key else f"{key} (min gap m, min a)"
    out.append(f"| {label} | " + " | ".join(f"{g:.2f}, {a:.2f}" for g, a in values) + " |")
  return "\n".join(out)


if __name__ == "__main__":
  print(table(all_metrics()))
  sys.exit(0)
