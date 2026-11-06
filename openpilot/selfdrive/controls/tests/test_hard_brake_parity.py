"""yeet-angle-brake: following and closing must be exactly yeet-angle's (b1da1d9c0), only cap-limited braking for a lead
goes past -3.5 (down to -6.5). See MPC_TUNING.md.

hard_brake_parity.json holds b1da1d9c0's planner output (Rivian, kit path) for every scenario below, sampled every
REF_DECIMATION steps, and a44ab30a3's hard-stop results (the first -6.5 build). Regenerate the b1da1d9c0 part by copying
this file into a b1da1d9c0 tree and running `python test_hard_brake_parity.py ref`, the a44ab30a3 part with `hard` there.
"""
import json
import sys
from pathlib import Path

import numpy as np

from opendbc.car import gen_empty_fingerprint
from opendbc.car.interfaces import ACCEL_MIN
from opendbc.car.rivian.interface import CarInterface
from opendbc.car.rivian.values import CAR
from openpilot.common.parameterized import parameterized
from openpilot.common.test import OpenpilotTestCase
from openpilot.selfdrive.controls.lib import longitudinal_planner
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


def rivian_params():
  fingerprint = gen_empty_fingerprint()
  fingerprint[0][0x321] = 8  # Gen1
  fingerprint[1].update({0x1310: 8, 0x131a: 8})  # angle kit with the long harness
  CP = CarInterface.get_params(CAR.RIVIAN_R1, fingerprint, [], True, False, False)
  CP_SP = CarInterface.get_params_sp(CP, CAR.RIVIAN_R1, fingerprint, [], True, False, False)
  return CP, CP_SP


def simulate(name, hard_brake=True):
  """Drive the real planner in the maneuver plant. hard_brake=False runs the same planner without the hard MPC."""
  p, secs, speed, dist, bp, lead_v, _ = SCENARIOS[name]
  CP, CP_SP = rivian_params()
  plant = Plant(lead_relevancy=True, speed=speed, distance_lead=dist, personality=p)
  plant.planner = planner = longitudinal_planner.LongitudinalPlanner(CP, CP_SP, init_v=speed)
  if not hard_brake:
    planner.mpc_hard = None
  accel, speeds, gaps, hard = [], [], [], []
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


class TestHardBrakeParity(OpenpilotTestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.ref = json.loads(REF_FILE.read_text())

  def test_scenarios_recorded(self):
    self.assertEqual(set(self.ref["b1da1d9c0"]), set(SCENARIOS))
    self.assertEqual(set(self.ref["a44ab30a3"]), {k for k, in CAP_LIMITED})

  @parameterized.expand(NORMAL)
  def test_normal_following_is_yeet_angle(self, name):
    ref = self.ref["b1da1d9c0"][name]
    accel, steady_gap, _, hard = simulate(name)
    # the hard MPC is never used and the output equals b1da1d9c0's
    self.assertFalse(any(hard))
    np.testing.assert_allclose(accel[::REF_DECIMATION], ref["accel"], rtol=0, atol=ACCEL_TOL)
    self.assertAlmostEqual(steady_gap, ref["steady_gap"], delta=GAP_TOL)
    # every step: the same planner without the hard MPC (b1da1d9c0's planner)
    accel_stock, steady_gap_stock, _, _ = simulate(name, hard_brake=False)
    np.testing.assert_allclose(accel, accel_stock, rtol=0, atol=ACCEL_TOL)
    self.assertAlmostEqual(steady_gap, steady_gap_stock, delta=GAP_TOL)

  @parameterized.expand(CAP_LIMITED)
  def test_cap_limited_brakes_harder(self, name):
    ref, ref_hard = self.ref["b1da1d9c0"][name], self.ref["a44ab30a3"][name]
    accel, _, min_gap, hard = simulate(name)
    self.assertLessEqual(min(ref["accel"]), ACCEL_MIN + 0.1)  # b1da1d9c0 is at the cap here
    self.assertTrue(any(hard))
    self.assertGreaterEqual(accel.min(), -6.5 - 1e-6)
    self.assertLess(accel.min(), ACCEL_MIN)
    # at least as good as a44ab30a3: no closer to the lead, and much better than b1da1d9c0
    self.assertGreaterEqual(min_gap, ref_hard["min_gap"] - 0.1)
    self.assertGreater(min_gap, ref["min_gap"])
    # at most two switches (into hard braking and back), no chatter
    self.assertLessEqual(int(np.sum(np.diff(np.array(hard, int)) != 0)), 2)


if __name__ == "__main__":
  # record a reference from the tree this runs in: `ref` for b1da1d9c0, `hard` for a44ab30a3
  key, names = {"ref": ("b1da1d9c0", SCENARIOS), "hard": ("a44ab30a3", [k for k, in CAP_LIMITED])}[sys.argv[1]]
  data = json.loads(REF_FILE.read_text()) if REF_FILE.exists() else {}
  data[key] = {}
  for n in names:
    accel, steady_gap, min_gap, _ = simulate(n)
    data[key][n] = ({"accel": [round(float(a), 4) for a in accel[::REF_DECIMATION]], "steady_gap": round(steady_gap, 4),
                     "min_gap": round(min_gap, 3)} if key == "b1da1d9c0" else {"min_gap": round(min_gap, 3), "min_accel": round(float(accel.min()), 4)})
  REF_FILE.write_text(json.dumps(data, indent=1) + "\n")
