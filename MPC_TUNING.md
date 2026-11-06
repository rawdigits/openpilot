# yeet-angle longitudinal tuning

Implementation: `openpilot/selfdrive/controls/lib/longitudinal_mpc_lib/long_mpc.py`.

| Parameter | xnor `5d22bdad0` | yeet-angle |
|---|---:|---:|
| A_CHANGE_COST | 200 | 100 |
| DANGER_ZONE_COST | 100 | 60 |
| LEAD_DANGER_FACTOR | 0.75 | 0.85 |
| T_FOLLOW aggressive (personality 0) | 1.25 s | 0.60 s |
| T_FOLLOW standard (personality 1) | 1.45 s | 1.10 s |
| T_FOLLOW relaxed (personality 2) | 1.75 s | 1.80 s |
| COMFORT_BRAKE | 2.5 m/s² | 3.0 m/s² |
| STOP_DISTANCE | 6.0 m | 3.0 m |
| Rivian stop speed (yeetfollow `vEgoStopping`) | 0.3 m/s | 0.25 m/s |
| COMFORT_BRAKE aggressive | 2.5 m/s² | 3.5 m/s² |
| Jerk factor aggressive | 0.5 | 0.2 |
| A_CRUISE_MAX_VALS aggressive | [1.6, 1.2, 0.8, 0.6] | [2.0, 1.6, 1.2, 0.9] |
| J_CRUISE_VALS aggressive | [1.6, 1.2, 0.8, 0.6] | [2.0, 1.6, 1.2, 0.9] |

The bridge supplies absolute personality values through the existing
`LongitudinalPersonality` param. Standard is the base's default. Legacy Rivian
levels map to 0 / 1 / 2 / 2; the TCM bridge owns that conversion.

These are the yeetfollow source-tip values, including the inherited `40955a998`
3 m stop distance and 3 m/s² comfortable braking (automotive/openpilot#4). The
1.8 m/s² `CRUISE_MAX_ACCEL` has no equivalent: this base has no MPC cruise
obstacle, and the cruise acceleration limit table (`A_CRUISE_MAX_VALS`) is the
same as yeetfollow's. See `PARITY.md`. Lower acceleration-change cost permits faster acceleration changes;
these constants alone do not establish driving behavior. See `ANGLE_PORT_NOTES.md`
for source commits, verification and the remaining vehicle validation.

## yeet-angle-tune: aggressive personality

Ryan's first xnor-kit drive with openpilot long (route `000000bd--5b41aadd11`, aggressive)
followed at the intended gap (median 0.84 s) but started braking early when closing on a
slower lead and pulled away gently (median 0.87 m/s² at 30 mph, tracked by the car). The four
`aggressive` rows above apply to the aggressive personality only; standard and relaxed keep
3.0 m/s², jerk factor 1.0 and the base cruise tables.

- `COMFORT_BRAKE` aggressive 3.5 m/s² (`get_comfort_brake()`, an MPC runtime parameter). The
  ego braking term and the lead's stopped-equivalence term both use it, so it cancels out when
  pace-matched: the steady-state gap stays `T_FOLLOW * v + STOP_DISTANCE`. When closing, the
  desired distance is shorter, so braking starts later. Capped at the 3.5 m/s² `ACCEL_MIN`
  (and Rivian panda `min_accel = -350`) so the MPC can always command the braking it plans
  around. 4.5 braked later still in the sims but plans beyond that limit.
- Jerk factor aggressive 0.2 (was 0.5): lets the MPC change accel sooner and spread braking
  out, which trims peak decel. With 3.5 alone the sims add 2 new lead-decel failures; 0.2
  instead clears the 4 known ones.
- `A_CRUISE_MAX_VALS` / `J_CRUISE_VALS` aggressive [2.0, 1.6, 1.2, 0.9]: the cruise accel and
  jerk limits that cap pull-away. 2.0 m/s² is `ACCEL_MAX` (ISO 15622) and the Rivian panda
  limit (`rivian.h` `max_accel = 200`).

Offline results from `openpilot/selfdrive/test/longitudinal_maneuvers/tune_report.py` (the
maneuver plant with Rivian R1 CarParams), yeet-angle `b1da1d9c0` → yeet-angle-tune. The plant
tracks the command exactly. No FCW in any scenario before or after; standard and relaxed
output is identical to yeet-angle. Gap is (dRel - 3 m) / vEgo, as in the drive analysis.

| Scenario (aggressive) | Braking starts (s / time gap) | Peak decel (m/s²) | Time < -1 m/s² (s) | Min gap (m / s) |
|---|---|---|---|---|
| close 25->20 m/s, 60 m | 1.0 s / 2.08 s → 1.4 s / 2.01 s | -0.45 → -0.43 | 0.0 → 0.0 | 15.6 / 0.63 → 15.4 / 0.62 |
| close 25->15 m/s, 80 m | 0.25 s / 2.97 s → 0.3 s / 2.95 s | -1.21 → -1.13 | 2.8 → 2.5 | 12.2 / 0.61 → 12.1 / 0.6 |
| close 20->10 m/s, 50 m | 0.05 s / 2.3 s → 0.05 s / 2.3 s | -1.91 → -1.79 | 4.0 → 4.2 | 8.6 / 0.56 → 8.8 / 0.58 |
| close 30->22 m/s, 100 m | 0.8 s / 3.02 s → 1.4 s / 2.86 s | -0.6 → -0.6 | 0.0 → 0.0 | 18.2 / 0.68 → 17.4 / 0.65 |
| close 15->10 m/s, 25 m | 0.1 s / 1.42 s → 0.05 s / 1.43 s | -1.09 → -1.09 | 1.15 → 1.25 | 8.3 / 0.53 → 8.6 / 0.56 |
| close 22->20 m/s, 1.0 s gap | 1.0 s / 0.91 s → 0.8 s / 0.93 s | -0.37 → -0.38 | 0.0 → 0.0 | 15.0 / 0.6 → 15.0 / 0.6 |
| close 22->19 m/s, 1.2 s gap | 0.6 s / 1.12 s → 0.5 s / 1.13 s | -0.54 → -0.56 | 0.0 → 0.0 | 14.5 / 0.6 → 14.4 / 0.6 |
| lead brakes 1.5 m/s² 25->15 | 5.6 s / 0.59 s → 5.45 s / 0.59 s | -1.75 → -1.72 | 5.4 → 5.45 | 5.3 / 0.15 → 6.8 / 0.25 |

| Scenario (aggressive) | Mean accel 5–10 s (m/s²) | Peak accel (m/s²) | Final gap (s) |
|---|---|---|---|
| lead 10->25 m/s at 1.5 m/s² | 0.87 → 1.07 | 1.15 → 1.49 | 1.36 → 0.74 |
| lead 13.4->25 m/s at 2.0 m/s² | 0.88 → 1.18 | 1.09 → 1.47 | 1.08 → 0.71 |
| lead 20->30 m/s at 1.0 m/s² | 0.62 → 0.71 | 0.88 → 1.05 | 0.84 → 0.67 |

The maneuver suite also passes the 4 known #4 failures (20 m/s lead decel to 0 at 2 and 3 m/s²,
acc and e2e) with min gap 0.96 m and 0.51 m, against collisions before. No vehicle validation yet.
