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
| J_EGO_COST factor aggressive | 1.0 | 0.5 |
| A_CRUISE_MAX_VALS aggressive | [1.6, 1.2, 0.8, 0.6] | [2.0, 1.8, 1.4, 1.1] |
| J_CRUISE_VALS aggressive | [1.6, 1.2, 0.8, 0.6] | [2.0, 1.8, 1.4, 1.1] |

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

## Rivian hard braking for a lead (yeet-angle-brake)

Ryan, 2026-11-06 (route `000000bf--1167b1038a` seg 9): at 79 mph a slower lead cut the gap to 22-25 m, the planner sat
at the -3.5 m/s² cap for ~1 s, the truck delivered -3.17, and Ryan braked at -5.6 to -7.4. Rivian now brakes down to
-6.5 m/s² (~0.66 g), and only when the stock MPC is cap-limited for a present lead. Everything else is yeet-angle's
(b1da1d9c0) planner output, step for step.

| Limit | Before | Now |
|---|---:|---:|
| panda `RIVIAN_LONG_LIMITS.min_accel` (`safety/modes/rivian.h`) | -350 | -650 (1/100 m/s²) |
| `CarControllerParams.ACCEL_MIN` (`car/rivian/values.py`, carcontroller clip) | -3.5 | -6.5 |
| longcontrol PID clip (`get_pid_accel_limits`, Rivian override in `car/rivian/interface.py`) | -3.5 | -6.5 |
| stock MPC `a_min` and `min_x_lead` clip (`long_mpc.py`) | -3.5 | -3.5 (unchanged) |
| hard MPC `a_min` and `min_x_lead` clip, with a present lead, only used while cap-limited | - | -6.5 |
| planner output clip (`longitudinal_planner.py`), hard MPC lead source | -3.5 | -6.5 |
| excessive-actuation check (`selfdrived/helpers.py`) | -7.0 | -10.0 (same 3.5 margin past the car's limit) |

These stay as they were: `ACCEL_MIN` -3.5 in `opendbc/car/interfaces.py` (every other brand), `A_CRUISE_MIN` -1.2 and the
cruise jerk limit, `COMFORT_BRAKE` 3.0, all MPC costs and T_FOLLOW, and `ACCEL_MAX`.

### Why the first build (a44ab30a3) followed differently

Ryan (2026-11-06, `yeet-angle-brake-prebuilt` 46024f3): on aggressive it "leaves a wider gap now". a44ab30a3 ran the
one MPC with `a_min` -6.5 and `min_x_lead` from -6.5 whenever a lead was present. In steady following, gentle lead
decels and mild closing that changed almost nothing (max |Δa| < 1e-4), but in every faster closing it did, from the first
cycle, so the approach brakes harder and ends further back. The worst are closings whose plan touches -3.5 (closing 8 m/s at
30 m/s, aggressive at a 0.6 s gap: -2.92 min accel in b1da1d9c0, -3.59 in a44ab30a3, min gap 3.4 vs 5.6 m), and it reaches
closings that never get near the cap (5 m/s at 35 m/s, aggressive 0.6 s: -1.69 vs -1.78, Δa 0.12 m/s²). Both changes
do it, each on its own: only `a_min` -6.5 moves those cases up to 0.8 m/s², only `min_x_lead` from -6.5 up to 0.7 m/s²
(the clip lets the lead sit closer than -3.5 can brake for, which changes the MPC's obstacle). The longcontrol PID
limit and the excessive-actuation check don't change the plan.

### Design: the stock MPC always decides

- The planner runs the stock MPC exactly as b1da1d9c0 (`ACCEL_MIN` bound, `min_x_lead` from `ACCEL_MIN`), and a second
  "hard" MPC with `drive_helpers.get_lead_accel_min(CP)` (-6.5 for Rivian, only built for cars below `ACCEL_MIN`) from the
  same state. The hard MPC's bound is -6.5 only with a present lead (`leadOne`/`leadTwo.present`), and its `a_min` is
  -6.5 only if the lead it follows is present.
- The hard MPC's plan is used only while the stock plan is cap-limited (`LongitudinalPlanner.update_hard_brake`): its
  source is a lead, and its accel is within 0.05 of -3.5 in the first `HARD_BRAKE_T` 1 s, or it runs into a present lead
  at its real distance (`mpc.lead_crash`, before the `min_x_lead` clip). Hysteresis: hard braking ends only after the stock
  plan has not been cap-limited for `HARD_BRAKE_EXIT_T` 1 s and the output is back above -3.5. Engage reset ends it.
- Otherwise the stock plan is used and the output equals b1da1d9c0's. Running the hard MPC next to the stock one
  doesn't change the stock solver (separate acados instances), and both start from the same planner state.
- In the planner, each source is clipped to its own floor before the min: MPC `mpc.a_min` (of the plan in use), cruise and
  e2e (experimental-mode model accel) `ACCEL_MIN`. A cruise or set-speed drop, force decel, or the model alone can't go
  past -3.5. With the stock MPC every floor is -3.5, which is b1da1d9c0's single clip after the min.
- longcontrol and the carcontroller only clip to -6.5. They don't produce braking the planner didn't ask for.

Measured in the maneuver plant with the Rivian CP (`test_hard_brake_parity.py`; the min gap is the closest distance, below 0 is contact):

| Scenario (all personalities) | b1da1d9c0 | a44ab30a3 | now |
|---|---|---|---|
| steady lead 15-35 m/s, lead decel -0.5/-1.0, cut-in at a 1 s gap, closing 2-5 m/s (39 cases) | - | max \|Δa\| < 1e-4 | identical (Δa 0) |
| closing 5-15 m/s at 20-35 m/s, 0.6-2.5 s gaps, not cap-limited in b1da1d9c0 (79 of 180 cases) | - | up to 0.12 m/s² off | identical (Δa 0) |
| same sweep, cap-limited in b1da1d9c0 (101 cases, 39 end in contact there) | - | up to 3.0 m/s² harder | same as a44ab30a3 within 0.7 m min gap |
| aggressive, lead brakes -6 from 30 m/s at 30 m: min accel, min gap | -3.50, -39.0 m | -6.50, -2.9 m | -6.50, -2.9 m |
| standard, 35 m/s, lead 25 m/s at 24 m (the 000000bf case) | -3.49, 5.7 m | -4.31, 8.5 m | -4.31, 8.5 m |
| relaxed, lead brakes -4 from 25 m/s at a 1 s gap | -3.50, -0.9 m | -3.72, 0.4 m | -3.72, 0.4 m |
| standard, stopped car at 70 m from 30 m/s | -3.50, -59.7 m | -6.50, -4.6 m | -6.50, -4.6 m |

In cases that are cap-limited only later in the approach, the new planner starts hard braking a bit later than a44ab30a3
(when the stock plan hits -3.5, not from the first cycle), so the minimum gap there can be up to ~0.7 m shorter than
a44ab30a3's, and never shorter than b1da1d9c0's.

Guard tests: `test_hard_brake_parity` (every non-cap-limited scenario matches b1da1d9c0 within 0.02 m/s² and a 0.05 s gap,
aggressive the yeet-angle-brake-tune tune instead, see below; cap-limited ones at least as good as a44ab30a3, reference in
`hard_brake_parity.json`), `test_ryan_customizations.TestRivianHardBrake` (planner, both Rivian paths), `test_rivian_angle_kit.
test_hard_brake_reaches_can` (CarController → CAN → panda for -6.5) and `safety/tests/test_rivian.py` (`MIN_ACCEL = -6.5`,
`test_hard_brake_limit`).

CAN: `ACM_AccelerationRequest` is 11 bit, scale 0.01, offset -10.24, range [-10.24, 10.23] m/s², so -6.5 encodes
(raw 374). Nothing found shows whether the VDM honors a request below -3.5 or clips it: upstream Rivian (opendbc/panda)
uses -3.5 without a comment, `VDM_AdasDecelLimit` reads a constant 0.01 in the public Gen1/Gen2 CI routes, and the stock
ACM never asks for less than -1.4 m/s² there. Stock AEB brakes through the ESP with `ACM_AebRequest` (0x101,
`ACM_DecelRequest` 0-16 m/s²), not through this interface. xnor's long-kit firmware (`rivian_long_fw.bin.signed`, a black
panda image in gateway mode `RIVIAN_LONGITUDINAL`) contains the upstream Rivian safety mode, with `{max 200, min -350}`
checked on 0x160 in its tx hook. The binary doesn't show whether its gateway path applies that check to frames it forwards.
If it does, the kit path would still drop requests below -3.5. Only a drive shows what the truck delivers below -3.5.

## yeet-angle-tune: aggressive personality

Ryan's first xnor-kit drive with openpilot long (route `000000bd--5b41aadd11`, aggressive)
followed at the intended gap (median 0.84 s) but started braking early when closing on a
slower lead and pulled away gently (median 0.87 m/s² at 30 mph, tracked by the car). The four
`aggressive` rows above apply to the aggressive personality only; standard and relaxed keep
3.0 m/s², jerk factor 1.0 and the base cruise tables.

- `COMFORT_BRAKE` aggressive 3.5 m/s² (`get_comfort_brake()`, an MPC runtime parameter). The
  ego braking term and the lead's stopped-equivalence term both use it, so it cancels out when
  pace-matched: the steady-state gap stays `T_FOLLOW * v + STOP_DISTANCE`. When closing, the
  desired distance is shorter, so braking starts later. Kept at or below the 3.5 m/s² `ACCEL_MIN`,
  which is still the MPC's floor without a present lead, so the MPC can always command the
  braking it plans around. On yeet-angle-brake-tune the Rivian can brake to -6.5 for a present
  lead, but that doesn't make a higher comfort brake better: see the re-evaluation below.
- Jerk factor aggressive 0.2 (was 0.5): lets the MPC change accel sooner and spread braking
  out, which trims peak decel. With 3.5 alone the sims add 2 new lead-decel failures; 0.2
  instead clears the 4 known ones.
- `A_CRUISE_MAX_VALS` / `J_CRUISE_VALS` aggressive were [2.0, 1.6, 1.2, 0.9] on yeet-angle-tune (now [2.0, 1.8, 1.4, 1.1]): the cruise accel and
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

## yeet-angle-brake-tune: hard braking + aggressive tune, more pull-away

yeet-angle-brake (-6.5 m/s² for a present lead) with the yeet-angle-tune aggressive tune (`de7882112`). First built on
`a44ab30a3` (`7538ea628`), now on `a9920129c` (see "On a9920129c" below; the tables before that are from the
a44ab30a3 build).
Ryan (2026-11-06, on yeet-angle-brake-prebuilt): on aggressive it doesn't close the gap hard enough once it can
accelerate again. Aggressive only, standard and relaxed are unchanged (identical `tune_report.py` output and maneuver
results to yeet-angle-brake):

- `A_CRUISE_MAX_VALS` / `J_CRUISE_VALS` aggressive [2.0, 1.8, 1.4, 1.1] (yeet-angle-tune [2.0, 1.6, 1.2, 0.9]). Still
  within `ACCEL_MAX` 2.0 and the Rivian panda `max_accel = 200`, neither changed. Below 20 m/s the planner's 1.7 m/s²
  total-accel cap (`_A_TOTAL_MAX_V`) binds before the 1.8 at 10 m/s.
- MPC jerk cost (`J_EGO_COST`) aggressive x0.5 on top of the 0.2 jerk factor (`J_EGO_FACTOR_AGGRESSIVE`, 5 * 0.2 * 0.5
  = 0.5). `A_CHANGE_COST` and the MPC `a_max` (`ACCEL_MAX`) are unchanged.

What binds: when the lead pulls away hard (2 m/s² by +10 m/s) the cruise accel source is the min 50-100% of the time,
so the cruise table (and below 20 m/s the 1.7 total-accel cap) limits pull-away. When the lead speeds up by 3 m/s and
the gap has to re-close, the cruise source is never the min (0% of the time): the MPC's own plan is, at ~1.1 m/s² peak
against a cruise limit of 1.25-1.7 and an MPC `a_max` of 2.0. Its jerk and a-change costs are what hold it back, so
raising the table alone doesn't change re-closing at all (12.95 / 12.8 / 11.65 s, as yeet-angle-tune). Halving the
jerk cost re-closes 1.6-2.7 s sooner. Halving `A_CHANGE_COST` instead was slower (12.85 / 12.3 / 10.65 s) and stopped
worse; lowering the jerk factor to 0.1 (both costs) was faster still but is a bigger step than asked.

`COMFORT_BRAKE` aggressive stays 3.5 m/s². Raising it (sims at 4.0, 4.5, 5.0) re-closes slower at 30 m/s (9.7 / 10.1 /
10.3 s vs 8.95) and brakes later for a hard-stopping lead (min gap 30 m/s, lead -6: -0.81 / -1.37 / -1.88 m vs -0.27).
The -6.5 lead braking doesn't make the MPC plan with more comfort brake; it only lets it brake harder when it's late.
3.0 would stop better still, but takes back the later braking when closing that yeet-angle-tune is for.

Offline results, Rivian R1 CarParams, maneuver plant (tracks the command exactly), aggressive. Pull-away: settled at
0.6 s, lead accelerates at 2 m/s² by +10 m/s, mean accel over the next 6 s. Re-close: lead +3 m/s at 1.5 m/s², time
until the gap is back within 0.05 s of 0.6 s. Hard stop: settled at 0.6 s, lead brakes to 0 at the given rate, min
gap (negative is a collision in the plant). Steady gap at 10 / 20 / 30 m/s is the same as yeet-angle `b1da1d9c0` for
every personality (aggressive 9.0 / 15.0 / 21.0 m, standard 14.0 / 25.0 / 36.0 m, relaxed 21.0 / 39.0 / 57.0 m).

| Aggressive | b1da1d9c0 | a44ab30a3 (brake) | de7882112 (tune) | yeet-angle-brake-tune |
|---|---|---|---|---|
| pull-away mean accel 10 / 20 / 30 m/s (m/s²) | 0.96 / 0.77 / 0.64 | 0.96 / 0.77 / 0.64 | 1.26 / 1.09 / 0.94 | 1.38 / 1.22 / 1.08 |
| re-close after lead +3 m/s, 10 / 20 / 30 m/s (s) | 16.0 / 17.15 / 18.65 | 16.0 / 17.15 / 18.65 | 12.95 / 12.8 / 11.65 | 11.3 / 10.7 / 8.95 |
| stop 20 m/s, lead -3 (min gap m, FCW) | -2.39, FCW | -2.19, FCW | -0.04, FCW | 0.84 |
| stop 20 m/s, lead -5 | -12.12, FCW | -2.57, FCW | -9.72, FCW | 0.66 |
| stop 30 m/s, lead -4 | -20.43, FCW | -5.25, FCW | -16.41, FCW | 0.01, FCW |
| stop 30 m/s, lead -6 | -44.5, FCW | -6.09, FCW | -41.45, FCW | -0.27, FCW |
| stop 35 m/s, lead -6.5 | -69.57, FCW | -9.43, FCW | -66.23, FCW | -1.96, FCW |

No FCW in any pull-away, re-close, steady or `tune_report.py` scenario on any tree. Standard and relaxed hard stops
are the same as a44ab30a3. `tune_report.py` aggressive pull-away (accel 5-10 s, de7882112 → now): 1.07 → 1.11,
1.18 → 1.29, 0.71 → 0.73 m/s², final gap 0.74 → 0.67, 0.71 → 0.67, 0.67 → 0.65 s; the closing scenarios brake at
most 0.15 s later with the same min gap ±0.6 m. The maneuver suite passes with `KNOWN_FAILURES` empty, as on
yeet-angle-tune. `TestRivianHardBrake` now checks the -6.5 floor with an 8 m/s² lead stop: at 6 m/s² this tune brakes
early enough to peak at -6.32 (min gap +0.92 m vs -0.04 m on the plain merge). No vehicle validation yet.

### On a9920129c (hard MPC only while cap-limited)

`a9920129c` replaced a44ab30a3's single -6.5 MPC with the stock MPC deciding and a hard MPC used only while the stock plan
is cap-limited (above). The tune is rebased onto it unchanged: the personality values (comfort brake, jerk factor, jerk
cost factor) live in `LongitudinalMpc.set_weights` / `update`, and the planner passes the same personality to both MPCs,
so the hard plan is the tuned plan with the -6.5 bound. The cap-limited switching is a9920129c's, untouched.

`test_hard_brake_parity` now checks, for every non-cap-limited scenario, that the hard MPC is never used and the output
is the tuned planner without hard braking: aggressive the recorded `tune` reference (`de7882112` with 7538ea628's
`long_mpc.py` / `longitudinal_planner.py` changes), standard and relaxed `b1da1d9c0` (both within 0.02 m/s² sampled, and
bit for bit against the same planner without the hard MPC; measured: identical to the references). Cap-limited ones stay
at least as good as a44ab30a3 and are now also never closer than a9920129c and at most 0.7 m closer than 7538ea628
(measured: within 0.04 m of 7538ea628). `test_hard_mpc_uses_the_tune` checks both MPCs get the same cost weights and
t_follow / comfort brake every cycle. All references were regenerated from those trees with the test's `__main__`; the
b1da1d9c0 and a44ab30a3 ones came out identical to a9920129c's.

Maneuver plant, Rivian R1 CarParams (pull-away, re-close, steady and "stop" rows as in the table above, the other hard
stops are the `test_hard_brake_parity` cap-limited scenarios, closing ones start 80 m behind; min gap below 0 is contact):

| Scenario | b1da1d9c0 | a9920129c | 7538ea628 | now |
|---|---|---|---|---|
| aggressive pull-away mean accel 10/20/30 (m/s²) | 0.96 / 0.77 / 0.64 | 0.96 / 0.77 / 0.64 | 1.38 / 1.22 / 1.08 | 1.38 / 1.22 / 1.08 |
| aggressive re-close after lead +3, 10/20/30 (s) | 16.0 / 17.15 / 18.65 | 16.0 / 17.15 / 18.65 | 11.3 / 10.7 / 8.95 | 11.3 / 10.7 / 8.95 |
| aggressive steady gap 10/20/30 (m) | 9.0 / 15.0 / 21.0 | 9.0 / 15.0 / 21.0 | 9.0 / 15.0 / 21.0 | 9.0 / 15.0 / 21.0 |
| aggressive stop 20@3.0 (min gap m, peak decel) | -2.39, -3.47, FCW | -2.19, -3.81, FCW | 0.84, -3.62 | 0.84, -3.62 |
| aggressive stop 20@5.0 (min gap m, peak decel) | -12.12, -3.50, FCW | -2.57, -5.84, FCW | 0.66, -5.57 | 0.66, -5.57, FCW |
| aggressive stop 30@4.0 (min gap m, peak decel) | -20.43, -3.50, FCW | -5.25, -4.83, FCW | 0.01, -4.80, FCW | 0.01, -4.80, FCW |
| aggressive stop 30@6.0 (min gap m, peak decel) | -44.50, -3.50, FCW | -6.09, -6.50, FCW | -0.27, -6.45, FCW | -0.27, -6.45, FCW |
| aggressive stop 35@6.5 (min gap m, peak decel) | -69.57, -3.50, FCW | -9.43, -6.50, FCW | -1.96, -6.50, FCW | -1.96, -6.50, FCW |
| aggressive lead brakes -6 from 30, 30 m (min gap m, min a) | -39.01, -3.50 | -2.89, -6.50 | 0.92, -6.32 | 0.92, -6.32 |
| aggressive 35 m/s, lead 25 at 24 m (min gap m, min a) | 4.06, -3.42 | 7.52, -4.34 | 10.81, -5.23 | 10.77, -5.25 |
| aggressive lead brakes -4 from 25, 1s gap (min gap m, min a) | -11.13, -3.50 | -2.11, -5.14 | 1.04, -4.73 | 1.04, -4.73 |
| aggressive stopped car at 30 m/s, 70 m (min gap m, min a) | -59.23, -3.50 | -3.01, -6.50 | -1.04, -6.50 | -1.04, -6.50 |
| aggressive closing 5 m/s at 30 (min gap m, min a) | 18.07, -0.32 | 18.07, -0.32 | 18.03, -0.40 | 18.03, -0.40 |
| aggressive closing 8 m/s at 30 (min gap m, min a) | 16.22, -0.96 | 16.22, -0.96 | 16.21, -0.93 | 16.21, -0.93 |
| aggressive closing 5 m/s at 35 (min gap m, min a) | 21.19, -0.39 | 21.19, -0.39 | 21.09, -0.36 | 21.09, -0.36 |
| aggressive closing 8 m/s at 35 (min gap m, min a) | 19.28, -1.15 | 19.28, -1.15 | 19.24, -1.19 | 19.24, -1.19 |
| standard pull-away mean accel 10/20/30 (m/s²) | 0.92 / 0.75 / 0.62 | 0.92 / 0.75 / 0.62 | 0.92 / 0.75 / 0.62 | 0.92 / 0.75 / 0.62 |
| standard re-close after lead +3, 10/20/30 (s) | 17.2 / 17.95 / 18.2 | 17.2 / 17.95 / 18.2 | 17.2 / 17.95 / 18.2 | 17.2 / 17.95 / 18.2 |
| standard steady gap 10/20/30 (m) | 14.0 / 25.0 / 36.0 | 14.0 / 25.0 / 36.0 | 14.0 / 25.0 / 36.0 | 14.0 / 25.0 / 36.0 |
| standard stop 20@3.0 (min gap m, peak decel) | -0.57, -3.48, FCW | -0.54, -3.56, FCW | -0.54, -3.56, FCW | -0.54, -3.56, FCW |
| standard stop 20@5.0 (min gap m, peak decel) | -6.36, -3.50, FCW | -0.71, -4.95, FCW | -0.71, -4.95, FCW | -0.71, -4.95, FCW |
| standard stop 30@4.0 (min gap m, peak decel) | -12.93, -3.50, FCW | -2.06, -4.80, FCW | -2.06, -4.80, FCW | -2.06, -4.80, FCW |
| standard stop 30@6.0 (min gap m, peak decel) | -34.52, -3.50, FCW | -2.19, -6.40, FCW | -2.19, -6.40, FCW | -2.19, -6.40, FCW |
| standard stop 35@6.5 (min gap m, peak decel) | -57.45, -3.50, FCW | -3.33, -6.50, FCW | -3.33, -6.50, FCW | -3.33, -6.50, FCW |
| standard lead brakes -6 from 30, 30 m (min gap m, min a) | -36.97, -3.50 | -3.93, -6.49 | -3.93, -6.49 | -3.93, -6.49 |
| standard 35 m/s, lead 25 at 24 m (min gap m, min a) | 5.71, -3.49 | 8.51, -4.31 | 8.54, -4.31 | 8.51, -4.31 |
| standard lead brakes -4 from 25, 1s gap (min gap m, min a) | -8.63, -3.50 | -2.47, -4.71 | -2.47, -4.71 | -2.47, -4.71 |
| standard stopped car at 30 m/s, 70 m (min gap m, min a) | -59.75, -3.50 | -4.61, -6.50 | -4.61, -6.50 | -4.61, -6.50 |
| standard closing 5 m/s at 30 (min gap m, min a) | 30.56, -0.47 | 30.56, -0.47 | 30.56, -0.47 | 30.56, -0.47 |
| standard closing 8 m/s at 30 (min gap m, min a) | 27.22, -1.12 | 27.22, -1.12 | 27.22, -1.12 | 27.22, -1.12 |
| standard closing 5 m/s at 35 (min gap m, min a) | 36.14, -0.62 | 36.14, -0.62 | 36.14, -0.62 | 36.14, -0.62 |
| standard closing 8 m/s at 35 (min gap m, min a) | 32.75, -1.31 | 32.75, -1.31 | 32.75, -1.31 | 32.75, -1.31 |

Relaxed matches standard in the same way (identical across a9920129c, 7538ea628 and now). Steady following, pull-away,
re-close and closing are identical to 7538ea628; the hard stops are equal or within 0.04 m (35 m/s, lead 25 m/s at 24 m:
10.77 vs 10.81 m aggressive, 8.51 vs 8.54 standard, as a9920129c vs a44ab30a3). FCW comes from the stock MPC since
a9920129c, which still plans to -3.5, so it can show in hard stops where 7538ea628 had none (aggressive stop 20 m/s,
lead -5, min gap +0.66 m on both).
