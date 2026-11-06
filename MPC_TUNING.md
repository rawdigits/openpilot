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
cap-limited ones at least as good as a44ab30a3, reference in `hard_brake_parity.json`), `test_ryan_customizations.TestRivianHardBrake` (planner, both Rivian paths), `test_rivian_angle_kit.
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
