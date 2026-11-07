#!/usr/bin/env python3
"""Closing / pull-away scenarios for the longitudinal tune (yeet-angle-tune).

Runs the maneuver plant with the Rivian R1 CarParams (0.35 s actuator delay) and
prints the metrics used to compare tunings: when braking starts, how hard it
gets, time spent below -1 m/s², 1 s jerk, the minimum time gap, FCW, and the
pull-away accel.
The scenarios mirror route 000000bd--5b41aadd11 (aggressive, closing at ~1 s
gap, lead pulling away around 30 mph). Synthetic: the plant tracks the command
exactly, as the drive's actual accel did.

  python3 tune_report.py [--personality aggressive|standard|relaxed] [--json]
"""
import argparse
import json

import numpy as np

from opendbc.car.rivian.interface import CarInterface
from opendbc.car.rivian.values import CAR
from openpilot.cereal import log
from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner
from openpilot.selfdrive.test.longitudinal_maneuvers.plant import Plant

BRAKE_START = -0.3  # m/s², "started braking"
HARD_BRAKE = -1.0   # m/s², the drive's hard-brake threshold

# name, ego speed, lead speed profile (t, v), initial gap, duration
CLOSING = [
  ("close 25->20 m/s, 60 m", 25., ([0., 30.], [20., 20.]), 60., 30.),
  ("close 25->15 m/s, 80 m", 25., ([0., 30.], [15., 15.]), 80., 30.),
  ("close 20->10 m/s, 50 m", 20., ([0., 30.], [10., 10.]), 50., 30.),
  ("close 30->22 m/s, 100 m", 30., ([0., 30.], [22., 22.]), 100., 30.),
  ("close 15->10 m/s, 25 m", 15., ([0., 30.], [10., 10.]), 25., 30.),
  # the drive's median closing case: ~2 m/s closing at a ~1 s gap
  ("close 22->20 m/s, 1.0 s gap", 22., ([0., 30.], [20., 20.]), 3. + 1.0 * 22., 30.),
  ("close 22->19 m/s, 1.2 s gap", 22., ([0., 30.], [19., 19.]), 3. + 1.2 * 22., 30.),
  ("lead brakes 1.5 m/s² 25->15", 25., ([0., 5., 11.67, 30.], [25., 25., 15., 15.]), 3. + 0.6 * 25., 30.),
]
PULL_AWAY = [
  ("lead 10->25 m/s at 1.5 m/s²", 10., ([0., 5., 15., 30.], [10., 10., 25., 25.])),
  ("lead 13.4->25 m/s at 2.0 m/s²", 13.4, ([0., 5., 10.8, 30.], [13.4, 13.4, 25., 25.])),
  ("lead 20->30 m/s at 1.0 m/s²", 20., ([0., 5., 15., 30.], [20., 20., 30., 30.])),
]


def make_plant(speed, gap, personality):
  plant = Plant(lead_relevancy=True, speed=speed, distance_lead=gap, personality=personality)
  CP = CarInterface.get_non_essential_params(CAR.RIVIAN_R1)
  CP_SP = CarInterface.get_non_essential_params_sp(CP, CAR.RIVIAN_R1)
  plant.planner = LongitudinalPlanner(CP, CP_SP, init_v=speed)
  return plant


def run(speed, lead_profile, gap, duration, personality, cruise=35.):
  plant = make_plant(speed, gap, personality)
  rows = []
  while plant.current_time < duration:
    t = plant.current_time
    v_lead = float(np.interp(t, *lead_profile))
    out = plant.step(v_lead, 1.0, cruise)
    d_rel = out['distance_lead'] - out['distance']
    rows.append((t, out['speed'], v_lead, out['acceleration'], d_rel, out['fcw']))
  return np.array(rows)


def jerk_1s(t, a):
  # ISO 15622 style: largest accel change over any 1 s window
  n = int(round(1. / (t[1] - t[0])))
  return round(float(np.abs(a[n:] - a[:-n]).max()), 2)


def closing_metrics(r):
  t, v, vl, a, d, fcw = r.T
  braking = np.nonzero(a < BRAKE_START)[0]
  i0 = braking[0] if len(braking) else None
  gap_s = (d - 3.) / np.maximum(v, 1.)
  return {
    "brake_start_s": None if i0 is None else round(float(t[i0]), 2),
    "brake_start_gap_s": None if i0 is None else round(float(gap_s[i0]), 2),
    "peak_decel": round(float(a.min()), 2),
    "hard_brake_s": round(float((a < HARD_BRAKE).sum() * (t[1] - t[0])), 2),
    "jerk_1s": jerk_1s(t, a),
    "min_gap_m": round(float(d.min()), 1),
    "min_gap_s": round(float(gap_s[v > 1.].min()), 2),
    "final_gap_s": round(float(gap_s[-1]), 2),
    "fcw": bool(fcw.any()),
  }


def pull_away_metrics(r):
  t, v, vl, a, d, fcw = r.T
  window = (t >= 5.) & (t < 10.)
  return {
    "accel_5_10s": round(float(a[window].mean()), 2),
    "peak_accel": round(float(a.max()), 2),
    "jerk_1s": jerk_1s(t, a),
    "gap_at_10s_m": round(float(d[np.searchsorted(t, 10.)]), 1),
    "final_gap_s": round(float((d[-1] - 3.) / max(v[-1], 1.)), 2),
  }


def report(personality):
  out = {}
  for name, speed, lead, gap, duration in CLOSING:
    out[name] = closing_metrics(run(speed, lead, gap, duration, personality))
  for name, speed, lead in PULL_AWAY:
    out[name] = pull_away_metrics(run(speed, lead, 3. + 0.6 * speed, 30., personality))
  return out


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--personality", default="aggressive", choices=["aggressive", "standard", "relaxed"])
  parser.add_argument("--json", action="store_true")
  args = parser.parse_args()
  res = report(getattr(log.LongitudinalPersonality, args.personality))
  if args.json:
    print(json.dumps(res, indent=1))
  else:
    for name, m in res.items():
      print(f"{name:32s} " + "  ".join(f"{k}={v}" for k, v in m.items()))
