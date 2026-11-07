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
levels map to 0 / 1 / 2 / 2; the TCM bridge owns that conversion. Since
yeet-angle-brake-levels the planner follows the truck's four levels directly
(`RivianFollowLevel`), see the end of this file.

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

## yeet-angle-brake-smooth: release slew on the accel request

Ryan, 2026-11-06 23:01Z: a car cut in at ~27 mph and radarState `leadOne` flipped every 1-3 frames between the cut-in
(~8.9-9.8 m, aLeadK ~ -3) and the old lead (~12.4-13.7 m, aLeadK ~ -0.3). The planner followed each flip, so the
request bounced (-1.82 -1.72 -1.75 -1.75 -1.73 -2.52 -2.81 -2.81 -3.60 -3.60 -3.21 -4.40 -4.40 -3.82), and right after
that the VDM raised `VDM_AdasFaultStatus=Imps_Cmd` and dropped ADAS. That's only a candidate cause: another Imps_Cmd
came at 62 mph with a smooth ~0 request. This change does not claim to fix the fault. It makes sure a flickering lead
can't release braking. A 79 mph hard stop on the same drive ramped -0.24 → -4.26 in ~0.7 s (up to ~76 m/s³) and the
truck accepted it, so onset stays unlimited.

`limit_release` in `longitudinal_planner.py` runs on the planner output (`output_a_target`) after the per-source floor
clip. That covers both MPCs, cruise, e2e and the switches into and out of the hard MPC.

- Onset (the output getting more negative) passes through unchanged, in one frame like before. A hard stop reaches the
  same decel at the same time as on ed39021a3.
- Release: once the previous output is below `ACCEL_RELEASE_BELOW` -1.0 m/s², it may get less negative by at most
  `ACCEL_RELEASE_RATE` 2.5 m/s³ (0.125 m/s² per 20 Hz frame). Above -1.0 nothing changes. Cruise and accel aren't
  touched, except that a release from below -1.0 keeps ramping at 2.5 m/s³ past -1.0 for the frames it started below
  it.
- Reset (not engaged, longControlState off, which covers disengage, longActive false and driver brake/gas override,
  and an uninitialized vCruise) skips the limit. The output goes straight to aEgo as before.
- While the limit holds the output, the plan source stays the previous one. That's the braking still being released,
  so `test_e2e_does_not_cap_lead_braking` still sees only MPC sources below -3.5.
- The MPCs start from the limited value (`set_cur_state(v, output_a_target)`), as does `v_desired_filter`. It's the
  accel actually requested. Starting from the unlimited value would make the MPC plan from an accel the car was never
  asked for, and its a-change cost would then pull the next plan toward a release that didn't happen.

The rate, from the maneuver plant with the Rivian CP (`test_hard_brake_parity` scenarios, all personalities):

| Release rate (m/s³) | normal scenarios (39) | worst hard-stop min gap vs ed39021a3 | flicker min gap (aggr., 6 random flicker patterns) |
|---|---|---|---|
| none (ed39021a3) | - | - | -0.86 .. -0.47 m |
| 1.5 | identical | +0.05 m or better, but holds braking long after the stop (output up to 2.7 m/s² off ed39021a3's) | 0.41 .. 0.63 m |
| 2.0 | identical | +0.003 m or better, output up to 2.1 m/s² off | 0.21 .. 0.41 m |
| **2.5** | identical | **never worse** (+0.009 to +1.13 m where it changes), output up to 1.3 m/s² off | -0.16 .. -0.02 m |
| 3.0 | identical | better or the same, only the aggressive stopped car changes | -0.42 .. -0.18 m |
| 4.0 | identical | the same, it barely binds | - |

The planner's own release while braking hard is 1.3-2.95 m/s³ in the cap-limited stops (4.7 m/s³ once, the aggressive
stopped car right after its -6.5 peak). At 2.5 the slew trims only the fastest of those (7 of 12 scenarios change, all
toward a larger gap), and the 23:01Z-style flicker
releases of 0.2-1.3 m/s² per frame (4-27 m/s³) are cut to 0.125. 1.5-2.0 would smooth the flicker more but hold
braking a long way into normal stops. 3.0+ lets most of a flickered frame through again. -1.0 is the release threshold
asked for. Starting it at 0 instead gives the same results in every scenario here (gentle braking above -1.0 never
releases faster than 2.5 m/s³ in the sims).

Results, ed39021a3 → now (`test_hard_brake_parity`; min gap below 0 is contact; max release step is the largest
per-frame rise from below -1.0; hard-MPC switch steps are per frame, entry / exit):

| Scenario | min gap (m) | min accel | time to min accel (s) | max release step (m/s²) | switch steps entry / exit |
|---|---|---|---|---|---|
| aggressive lead brakes -6 from 30, 30 m | 0.92 → 0.93 | -6.32 → -6.32 | 5.30 → 5.30 | 0.133 → 0.125 | -0.148 / 0.085 → same |
| aggressive 35 m/s, lead 25 at 24 m | 10.77 → 10.81 | -5.25 → -5.25 | 0.55 → 0.55 | 0.131 → 0.125 | -1.862 / 0.085 → -1.862 / 0.079 |
| aggressive lead brakes -4 from 25, 1s gap | 1.04 → 1.06 | -4.73 → -4.73 | 6.55 → 6.55 | 0.141 → 0.125 | -0.046 / 0.086 → -0.046 / 0.083 |
| aggressive stopped car at 30 m/s, 70 m | -1.04 → 0.09 | -6.50 → -6.50 | 0.05 → 0.05 | 0.234 → 0.125 | no switch (hard from the first frame) |
| standard lead brakes -6 from 30, 30 m | -3.93 → -3.46 | -6.49 → -6.49 | 5.20 → 5.20 | 0.147 → 0.125 | -0.103 / - → same |
| standard 35 m/s, lead 25 at 24 m | 8.51 → 8.51 | -4.31 → -4.31 | 0.85 → 0.85 | 0.090 → 0.090 | -0.728 / 0.090 → same |
| standard lead brakes -4 from 25, 1s gap | -2.47 → -2.47 | -4.71 → -4.71 | 6.55 → 6.55 | 0.109 → 0.109 | -0.029 / - → same |
| standard stopped car at 30 m/s, 70 m | -4.61 → -3.96 | -6.50 → -6.50 | 0.20 → 0.20 | 0.147 → 0.125 | no switch |
| relaxed lead brakes -6 from 30, 30 m | -0.75 → -0.75 | -5.57 → -5.57 | 5.30 → 5.30 | 0.102 → 0.102 | -0.119 / - → same |
| relaxed 35 m/s, lead 25 at 24 m | 11.29 → 11.29 | -5.09 → -5.09 | 0.80 → 0.80 | 0.100 → 0.100 | -0.805 / 0.071 → same |
| relaxed lead brakes -4 from 25, 1s gap | 0.45 → 0.45 | -3.72 → -3.72 | 6.55 → 6.55 | 0.066 → 0.066 | -0.019 / 0.061 → same |
| relaxed stopped car at 30 m/s, 70 m | -4.12 → -3.47 | -6.50 → -6.50 | 0.15 → 0.15 | 0.147 → 0.125 | no switch |
| aggressive 23:01Z flicker | 3.75 → 4.07 | -2.99 → -2.90 | 2.35 → 2.35 | 0.595 → 0.125 | no hard braking |
| standard 23:01Z flicker | 3.13 → 3.18 | -2.37 → -2.37 | 2.35 → 2.35 | 0.215 → 0.125 | no hard braking |
| relaxed 23:01Z flicker | 5.53 → 5.60 | -2.42 → -2.42 | 2.35 → 2.35 | 0.243 → 0.125 | no hard braking |

- Hard-MPC switches: entry (largest step -1.86 m/s² in one frame, aggressive 35 m/s, lead 25 at 24 m) always brakes
  harder, so it's onset and stays unlimited, as asked. Exit happens only once the output is above -3.5, and its step
  is at most 0.125 m/s² per frame now (0.090 before, under 2.5 m/s³ already, so only 0.085 → 0.079 and 0.086 → 0.083
  changed).
- Flicker (`test_flickering_lead_does_not_release`): ego at 12.9 m/s, the old lead at 13.7 m (aLeadK -0.3) and the
  cut-in at 9.8 m braking at -3 for 1.5 s, `leadOne` alternating in the logged 1-3 frame pattern for 2 s. Aggressive
  output, ed39021a3: -0.66 -0.81 -0.70 -1.19 -0.87 -0.99 -1.41 -1.57 -1.80 -1.54 -2.02 -1.60 ...; now: -0.66 -0.81 -0.70
  -1.19 -1.07 -0.94 -1.46 -1.55 -1.81 -1.69 -1.96 -1.84 ... While braking below -1.0 it rises by at most 0.125 m/s² per frame
  (2.5 m/s³). It isn't strictly monotonic: a flickered frame still releases by up to that much. The aggressive peak is
  0.09 m/s² lower (-2.90 vs -2.99) because it kept braking through the flicker. That ends 0.32 m further from the
  cut-in, at the same time to the peak.
- Normal scenarios (steady 15-35 m/s, lead decel, cut-in at a 1 s gap, closing 2-5 m/s, every personality,
  `test_normal_following_is_tuned_planner`) are bit for bit ed39021a3. That's also true of the yeet-angle-brake-tune
  report above: pull-away, re-close, steady gap and closing 5 / 8 m/s at 30 / 35 m/s for all personalities. Its hard
  stops only get better: aggressive stop 20@5 0.66 → 1.40 m, 30@4 0.01 → 0.38, 30@6 -0.27 → 0.93, 35@6.5 -1.96 → -0.81,
  standard 30@6 -2.19 → -2.18, 35@6.5 -3.33 → -3.14, peak decel identical. A stop and go behind a lead (15 m/s to 0
  and back to 10) is identical too.

Guard tests (`test_hard_brake_parity`): `test_release_slew_keeps_hard_braking` checks every cap-limited stop's min gap
≥ ed39021a3 - 0.05 m, the same min accel reached no later, and the release bounded. The ed39021a3 reference is in
`hard_brake_parity.json`, recorded from ed39021a3's planner, and the test also checks it against the same planner
without the slew. `test_hard_brake_switch_steps` checks entry steps equal ed39021a3's and exit steps are bounded.
`test_flickering_lead_does_not_release` covers the flicker, `test_release_is_immediate_on_reset` the reset, and
`test_limit_release` the function itself. `test_normal_following_is_tuned_planner` also checks bit for bit equality
with the planner without the slew. No vehicle validation yet.

Follow-up, not in this change: the flicker itself. Lead "stickiness" for cut-ins (holding the closer lead in radard or
the planner for a few frames instead of following each flip) would keep the plan from switching targets in the first
place. The slew only bounds the output while it does.

Which planner is in use is visible on the device: `longitudinalPlanSP.hardBrake` (`custom.capnp`, new field @8, set from
`LongitudinalPlanner.hard_brake` every cycle), and every switch logs `cloudlog.event("hard_brake_switch")` with
`prev_planner` / `planner` (`stock` or `hard`), `aTarget` (the output that cycle), `vEgo` and the plan `source`.
`test_hard_brake_published` checks the flag is True while the hard MPC is used in two hard stops, False all through
steady following, and that each switch logs one event.

## yeet-angle-brake-levels: four follow levels from the truck stalk

Ryan, 2026-11-07: the TCM bridge maps the truck's stalk levels 1-4 to personality 0 / 1 / 2 / 2, so levels 3 and 4 drove
the same. The planner now follows the level itself (the bridge's `follow_level`, unchanged bridge). Level 1 is the
aggressive personality and level 4 the relaxed one, bit for bit. Levels 2 and 3 are 1/3 and 2/3 of the way from aggressive to relaxed
in every per-personality value. Standard (personality 1) isn't one of the truck's levels any more, but personality 0 / 1 / 2 work
as before whenever there is no level (UI, no or stale bridge).

| Per-level value (`FollowLevel`, `long_mpc.follow_interp`) | level 1 (aggressive) | level 2 | level 3 | level 4 (relaxed) |
|---|---:|---:|---:|---:|
| T_FOLLOW (s) | 0.60 | 1.00 | 1.40 | 1.80 |
| comfort brake (m/s²) | 3.5 | 3.33 | 3.17 | 3.0 |
| jerk factor (a-change cost x) | 0.2 | 0.47 | 0.73 | 1.0 |
| MPC jerk cost (`J_EGO_COST` x jerk factor x factor) | 0.5 | 2.0 | 3.5 | 5.0 |
| A_CRUISE_MAX_VALS / J_CRUISE_VALS at 0 / 10 / 25 / 40 m/s | 2.0 / 1.8 / 1.4 / 1.1 | 1.87 / 1.6 / 1.2 / 0.93 | 1.73 / 1.4 / 1.0 / 0.77 | 1.6 / 1.2 / 0.8 / 0.6 |
| MPC costs while hard braking (`HARD_BRAKE_COST_LEVEL`) | level 1 | level 1 | level 1 | level 4 |

The jerk cost is interpolated as a cost (0.5 → 5.0), not as its two factors, so the MPC weights of levels 2 and 3 are
evenly between level 1's and level 4's (`test_between_is_evenly_interpolated`). Everything else in the planner and MPC
(`A_CHANGE_COST`, `DANGER_ZONE_COST`, `STOP_DISTANCE`, `ACCEL_MIN`/`MAX`, the -6.5 hard MPC, the release slew) has no
per-personality value and is the same for every level. Both MPCs get the level, so the hard planner's weights still match the
normal MPC's every cycle (`test_hard_mpc_uses_the_tune`, `test_hard_braking_costs`).

### Data flow

- `rivian_bridge.py` (poll thread, 3 Hz, already off the RT cores): `follow_level` is valid only as an int 1-4. Each poll,
  `_sync_follow_level` writes the new `RivianFollowLevel` param (INT, cleared on manager start and onroad) when it changes,
  from the poll thread only, as `_sync_personality` does: the level, or 0 when it's missing, 0, 5, another type, or the bridge is
  stale (stale flag, no answer for 2 s, failed HTTP). It retries a failed write on the next poll.
- `LongitudinalPersonality` is still written (same path, same dedup): with a valid level, the level's personality
  `FOLLOW_LEVEL_PERSONALITY` 1→0, 2→1, 3→2, 4→2, else the bridge's `follow_personality` as before. That's the bridge's own mapping. For
  level 3 (1.4 s) that's relaxed (1.8 s), not standard (1.1 s), so when the bridge goes stale mid-drive and the planner falls
  back to this personality, it never follows closer than the level did. The UI and the distance bars show the
  personality, so level 3 and 4 still look alike on the comma's screen (the truck's own HUD shows the level). The gap-button filter in
  `carstate.py` applies whenever the bridge supplies either a level or a personality.
- `selfdrived` reads `RivianFollowLevel` in its 10 Hz params thread, next to `LongitudinalPersonality`, and publishes it as
  `selfdriveStateSP.followLevel` (new field @4, 0 unless 1-4).
- The planner (`get_personality`) uses `FollowLevel(followLevel)` when it is 1-4, else `selfdriveState.personality` as before.
  Thumb-wheel change to planner: up to 0.33 s poll + 0.1 s params read + one planner cycle, about 0.5 s worst case, as for the
  personality today.

`FollowLevel` is a separate type passed where a personality goes (`get_T_FOLLOW`, `get_comfort_brake`, `get_jerk_factor`,
`get_j_ego_cost`, `get_max_accel`, `get_cruise_jerk`). Personality integers take the old code path, so non-Rivian cars, the
UI and stale-bridge driving are unchanged, and levels 1 and 4 return the personalities' own values, not computed from both
(`test_ends_are_the_personalities`). I didn't use a float "follow position" 0..2 on the personality path: standard is a
different tune (jerk factor 1.0 vs 0.73 at its T_FOLLOW), and making 1.0 mean anything other than standard would change it.

### Hard braking for levels 2 and 3

Plain interpolation also interpolates the costs that make level 1 react fast (jerk factor 0.2, jerk cost 0.5). With those
costs between level 1's and 4's, level 2 reacts more slowly than level 1 but follows much closer than level 4. In the hard stops
it ended closer to the lead than level 1 (plain interpolation, same plant):

| Scenario (min gap m, min a) | level 1 | level 2 | level 3 | level 4 |
|---|---|---|---|---|
| stop 20@3.0, settled (min gap m, min a) | 0.84, -3.62 | 0.77, -3.44 | 1.37, -3.00 | 1.90, -2.74 |
| stop 20@5.0, settled (min gap m, min a) | 1.40, -5.57 | 0.59, -4.86 | 1.17, -4.18 | 1.79, -3.80 |
| stop 30@4.0, settled (min gap m, min a) | 0.38, -4.80 | 0.02, -4.59 | 0.98, -3.95 | 1.76, -3.72 |
| stop 30@6.0, settled (min gap m, min a) | 0.93, -6.45 | -0.14, -6.18 | 0.78, -5.30 | 1.66, -4.94 |
| stop 35@6.5, settled (min gap m, min a) | -0.81, -6.50 | -0.55, -6.48 | 0.63, -5.86 | 1.63, -5.50 |
| lead brakes -6 from 30, 30 m (min gap m, min a) | 0.93, -6.32 | -0.50, -6.39 | -0.89, -5.97 | -0.75, -5.57 |
| 35 m/s, lead 25 at 24 m (min gap m, min a) | 10.81, -5.25 | 10.36, -4.90 | 10.81, -4.96 | 11.29, -5.09 |
| lead brakes -4 from 25, 1s gap (min gap m, min a) | 1.06, -4.73 | -0.01, -4.52 | 0.07, -4.11 | 0.45, -3.72 |
| stopped car at 30 m/s, 70 m (min gap m, min a) | 0.09, -6.50 | -1.16, -6.50 | -2.53, -6.50 | -3.47, -6.50 |

So while the planner is hard braking (`hard_brake`, the -6.5 hard MPC in use, a9920129c's switching), levels 2 and 3 plan with
level 1's cost weights (`HARD_BRAKE_COST_LEVEL`, `FollowLevel.hard`): the same jerk factor 0.2 and jerk cost 0.5 the aggressive tune brakes
with. T_FOLLOW, comfort brake and the cruise tables stay the level's. Both MPCs use them. On the cycle hard braking starts
both are solved again from the same state (previous plans and FCW count restored), so the plan used brakes with them from the
first hard braking cycle. On the cycle it ends the old ones still apply (decided after the solve). Levels 1 and 4 never take this path: their planner is
the personalities' code path exactly. Following, closing, pull-away and re-close of levels 2 and 3 never hard brake, so they're
the plain interpolation. I scanned the hard braking cost level from 1.0 to 2.0 (interpolated like a level, on an intermediate build
without the restored state for the re-solve, within 0.2 m of the final numbers). Level 2 stays at or past level 1's min gap in every stop at 1.0 and 1.1, not from 1.2 (stop 20@5.0: 1.34 m vs
level 1's 1.40). 1.0 has the most margin and is an existing tune (aggressive's braking) rather than a new blend.

### Per level

Maneuver plant, Rivian R1 CarParams (kit path), as in the tables above. Steady gap: 60 s behind a constant-speed lead. Pull-away:
settled at the level's gap, the lead accelerates at 2 m/s² by +10 m/s, mean accel over the next 6 s. Re-close: the lead +3 m/s
at 1.5 m/s², time until the gap is back within 0.05 s of the level's gap (the measure used above), and time until the gap error (m
past the level's gap) is half its peak. Hard stops "v@decel": settled at the level's gap, the lead brakes to 0. The other hard stops
are `test_hard_brake_parity`'s cap-limited scenarios with the same start for every level. Min gap below 0 is contact.
Generated by `python openpilot/selfdrive/controls/tests/test_follow_levels.py`.

| | level 1 | level 2 | level 3 | level 4 |
|---|---|---|---|---|
| T_FOLLOW (s) | 0.60 | 1.00 | 1.40 | 1.80 |
| steady gap 30 / 50 / 70 mph (m) | 11.1 / 16.4 / 21.8 | 16.4 / 25.4 / 34.3 | 21.8 / 34.3 / 46.8 | 27.1 / 43.2 / 59.4 |
| pull-away mean accel 10 / 20 / 30 m/s (m/s²) | 1.38 / 1.22 / 1.08 | 1.19 / 1.04 / 0.91 | 1.05 / 0.89 / 0.77 | 0.91 / 0.74 / 0.62 |
| re-close after lead +3, gap within 0.05 s, 10 / 20 / 30 m/s (s) | 11.3 / 10.7 / 8.95 | 14.1 / 13.85 / 12.5 | 14.9 / 14.1 / 12.15 | 14.85 / 12.9 / 10.35 |
| re-close after lead +3, gap error halved, 10 / 20 / 30 m/s (s) | 9.2 / 11.3 / 13.45 | 11.05 / 13.3 / 15.6 | 11.95 / 14.35 / 16.7 | 12.6 / 15.05 / 17.45 |
| stop 20@3.0, settled (min gap m, min a) | 0.84, -3.62 | 1.31, -3.75 | 1.37, -3.00 | 1.90, -2.74 |
| stop 20@5.0, settled (min gap m, min a) | 1.40, -5.57 | 1.54, -4.71 | 1.92, -4.72 | 1.79, -3.80 |
| stop 30@4.0, settled (min gap m, min a) | 0.38, -4.80 | 1.54, -4.38 | 1.92, -4.64 | 1.76, -3.72 |
| stop 30@6.0, settled (min gap m, min a) | 0.93, -6.45 | 1.48, -5.71 | 1.94, -5.63 | 1.66, -4.94 |
| stop 35@6.5, settled (min gap m, min a) | -0.81, -6.50 | 1.45, -6.25 | 1.94, -6.06 | 1.63, -5.50 |
| lead brakes -6 from 30, 30 m (min gap m, min a) | 0.93, -6.32 | 1.42, -5.78 | 1.95, -5.92 | -0.75, -5.57 |
| 35 m/s, lead 25 at 24 m (min gap m, min a) | 10.81, -5.25 | 13.66, -6.11 | 14.83, -6.45 | 11.29, -5.09 |
| lead brakes -4 from 25, 1s gap (min gap m, min a) | 1.06, -4.73 | 1.52, -4.38 | 1.79, -4.66 | 0.45, -3.72 |
| stopped car at 30 m/s, 70 m (min gap m, min a) | 0.09, -6.50 | 0.62, -6.50 | 0.66, -6.50 | -3.47, -6.50 |

- Level 1 and level 4 columns are the aggressive and relaxed numbers in the tables above (pull-away, re-close, steady and stops 1.38 /
  1.22 / 1.08, 11.3 / 10.7 / 8.95, the yeet-angle-brake-smooth stops). Bit for bit: `TestFollowLevelEnds` runs every
  `test_hard_brake_parity` scenario of the personality (39 following, 4 cap-limited each), the 23:01Z flicker, the
  `test_following_distance` scenario and pull-away / hard stops with the follow level and the personality set to standard, and
  compares the output arrays with `==`.
- Steady gap, pull-away and the halved gap error are evenly spaced and monotonic from level 1 to 4.
- Re-close to within 0.05 s isn't monotonic, and level 4 is faster than levels 2-3 at 20 and 30 m/s. That's the
  measure, not the planner: the gap error after the lead pulls away is about the same in metres for every level (peak 2.1-2.5 m,
  `reclose.py` traces), and 0.05 s is 1 m at 20 m/s at every level. Level 4's error decays slowest (the halved column) but starts
  smallest. Levels 1 / 4 match the earlier tables, which used the same measure.
- Hard stops: level 2 and 3 never end closer than level 1 in the same scenario (`test_hard_stop_never_closer_than_level_1`),
  and in the stops from a settled gap they're ordered level 1 ≤ 2 ≤ 3. With level 1's braking costs and a longer gap, levels 2 and 3 end
  further back than level 4 (relaxed's costs) in most stops. The stopped car at 30 m/s, 70 m is the closest: 0.62 / 0.66 m vs
  0.09 m (level 1) and -3.47 m (level 4, relaxed).

Tests (`test_follow_levels.py`, in the prebuilt CI): the per-level values and the hard braking costs, level 1 / 4 bit for bit,
monotonic levels and the level-1 min-gap guard (from the table's runs), both MPCs' weights every cycle, the re-solve on the first hard
braking cycle with one FCW count, a level change every cycle and while following. `test_rivian_bridge.py`: level sync 1-4
with the personality written alongside, fallback for missing / 0 / 5 / -1 / "2" / 2.0 / True / None and stale (flag, timeout,
failed HTTP), retry, written only from the poll thread and never from `CarState.update`. No vehicle validation yet.
