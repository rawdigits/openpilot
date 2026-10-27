# yeetfollow → yeet-angle parity audit (automotive/openpilot#4)

Source: Forgejo `yeetfollow` tip `254a18943`, audited as `git log 1490a2437..yeetfollow` (53 commits), plus the pinned
opendbc `rawdigits/opendbc` `807ce9ff4..1545aa41` (28 commits) and the panda pin `4fab184d..7723bbca` (1 commit).
Destination: `yeet-angle` `3543cc78e` (xnor rx-master / sunnypilot base, opendbc flattened into `opendbc_repo/`).

Status before this change → after:
- **exact**: already identical on yeet-angle.
- **different → ported**: was different, now matches yeetfollow (same numbers) in both kit-present and torque-fallback paths.
- **missing → ported**: was absent, now ported.
- **closest equivalent**: the base has no direct equivalent, so the nearest mechanism was used. Documented below.
- **n/a**: not applicable on the new base. Reason given.

"Both paths" means the angle kit present (`0x1310`) and the torque fallback without the kit. Everything in the MPC, planner,
DM and cruise code is car-agnostic. In the Rivian interface/carstate code it applies to both kit branches.

## Longitudinal / follow-distance tuning

| # | Item (source commit) | yeetfollow | yeet-angle before | Status | Where now |
|---|---|---|---|---|---|
| 1 | `COMFORT_BRAKE` (`40955a998`) | 3.0 | 2.5 | different → ported | `long_mpc.py` |
| 2 | `STOP_DISTANCE` (`40955a998`) | 3.0 | 6.0 | different → ported | `long_mpc.py` (the maneuver tests' "resume from a stop" start gap follows it) |
| 3 | `CRUISE_MAX_ACCEL` (`40955a998`) | 1.8 (MPC cruise-obstacle clip) | none | n/a | Base removed the MPC cruise obstacle; cruise is now `get_cruise_accel()` with `A_CRUISE_MAX_VALS` [1.6, 1.2, 0.8, 0.6], the same as yeetfollow's planner clip. Both bases already shared that limit, so nothing was changed. |
| 4 | `CRUISE_MIN_ACCEL` | -1.2 (unchanged from base) | `A_CRUISE_MIN = -1.2` | exact | `longitudinal_planner.py` |
| 5 | `A_CHANGE_COST` (`5428fb812`) | 100 | 100 | exact | `long_mpc.py` |
| 6 | `DANGER_ZONE_COST` (`40955a998`, `3ad41b16e`) | 60 | 60 | exact | `long_mpc.py` |
| 7 | `LEAD_DANGER_FACTOR` (`40955a998`, `3ad41b16e`, `3e6c978b8`) | 0.85 | 0.85 | exact | `long_mpc.py` |
| 8 | T_FOLLOW aggressive / standard / relaxed (`40955a998`, `3ad41b16e`, `75c4959b9`) | 0.60 / 1.10 / 1.80 s | same | exact | `long_mpc.get_T_FOLLOW` |
| 9 | Jerk factors, J_EGO_COST, other MPC costs | base values | base values | exact | Not customized on yeetfollow |
| 10 | Personality mapping (aggressive 0, standard 1, relaxed 2, default standard) | same | same | exact | Native `LongitudinalPersonality` param, bridge writes absolute 0/1/2 |
| 11 | Rivian `vEgoStopping` (opendbc `200ad276`) | 0.25 m/s (planner `should_stop`) | `should_stop` hard-coded 0.3, `CarParams.vEgoStopping` deprecated | closest equivalent | `drive_helpers.STOP_SPEED_BRAND = {"rivian": 0.25}` → `get_stop_speed(CP)`, used by the planner's MPC and cruise stop checks and by both modeld e2e `shouldStop` paths. Other brands keep 0.3. |
| 12 | Rivian `longitudinalActuatorDelay` (opendbc `200ad276`) | 0.35 | kit 0.25, fallback 0.35 | different → ported | `rivian/interface.py`, both paths 0.35 |
| 13 | Rivian `stopAccel` (opendbc `200ad276`) | 0 | kit -0.2, fallback 0 | different → ported | both paths 0 |
| 14 | Rivian long ki | std default `kiV [0.]` | kit `[0.2]`, fallback `[0.]` | different → ported | both paths base default `[0.]` |
| 15 | `stoppingDecelRate` / `vEgoStarting` | base defaults (0.8 / 0.5), not customized | base hard-codes 1.0 m/s²/s, no starting state | n/a | Not Ryan customizations. The new base's longcontrol has no per-car value, and changing the generic stop ramp would be new tuning, not parity. |
| 16 | Rivian openpilot longitudinal enabled (opendbc `200ad276`) | always, on the old harness | fallback: always. Kit: needs the long harness (`0x131a`) + alpha toggle | exact (fallback) / n/a (kit) | With the kit the base's ACM handling (`VDM_AdasSts` wind-up, long harness) decides. Forcing long without the long harness on the kit would bypass xnor's kit detection, so it stays the base's decision. |
| 17 | Rivian radar (`radarUnavailable = False`) | always | fallback False; kit True unless long harness | exact (fallback) / n/a (kit) | Kit radar tracks come via the long harness (`0x131a`). Same reasoning as 16. |

## Rivian bridge (TCM HTTP), cruise and set speed

| # | Item (source commit) | Status | Where now / notes |
|---|---|---|---|
| 18 | HTTP `/state` poll at 0.3 s, 1 s timeout (opendbc `73b52d12`) | exact | `rivian_bridge.py` |
| 19 | URL precedence repo root → `/data/rivian-bridge.conf` → `http://172.28.1.64:8082` (opendbc `0461cae2`, `bbc32445`; `57f98cd18`, `e1816b0b1`, `4e224e910`) | exact | `rivian_bridge.py`, root `rivian-bridge.conf` same URL |
| 20 | Set speed from bridge, gas override held until stalk change (opendbc `73b52d12`; `e479033d0`) | exact (behavior) | `carstate.update_bridge`. Dash-speed frame and 0.01 m/s change threshold are Ryan's later yeet-angle fix `ec7776dea`, kept. |
| 21 | Follow-distance sync every frame, independent of gas (opendbc `06f98b3b`; `2dbd4211c`) | exact | `carstate.update_bridge` |
| 22 | Personality write off the 100 Hz path, dedup (opendbc `ccfd6b02`; `47f35174a`, `ecc563106`) | exact | bridge worker `_sync_personality` |
| 23 | Poll thread off the RT cores, SCHED_OTHER (opendbc `ac45b65b`/`1545aa41`; `61bff41f7`) | exact | `_drop_rt_scheduling_for_this_thread` |
| 24 | `MAX_SET_SPEED` 50 m/s (`5820e4547`) | exact | `carstate_ext.py` |
| 25 | `MIN_SET_SPEED` 1 m/s (opendbc `390b77e8`) | different → ported | `carstate_ext.py` was 20 mph, now 1.0 m/s (dash) in both paths |
| 26 | `V_CRUISE_MAX` 180 kph (`2acc7693c`, `0bdb1d183`) | exact | `cruise.py`, `cruise_ext.py`, opendbc `interfaces.py` |
| 27 | Traffic-sign set speed + `TrafficSignOffset` param, Off/+5/+10/+15 %, default +5 % (opendbc `390b77e8`..`5c4cd29d`, `747fda7f6`, `d18e9633e`) | missing → ported | `carstate.update_bridge` (same ±9 m/s window, 0/254/255 invalid, 253 capped). Param in `params_keys.h` (default 1). Read in the bridge worker, never in the 100 Hz loop. Settings → Toggles "Traffic Sign Detection" below Driving Personality (`toggles.py`). On yeetfollow the bridge rewrote the set speed every frame, so the sign only took effect while the bridge was stale or during a gas override. The port keeps that precedence. |
| 28 | Rivian gap without CAN `gapAdjustCruise` (`44960f4a0`) | exact | bridge personality; kit scroll-wheel events are suppressed while the bridge owns the gap |
| 29 | `uiSetSpeed` on-screen +/- buttons (`354921629`, `a32d3628d`, `6ae9a1636`; opendbc `200ad276`) | n/a | Removed on yeetfollow itself by opendbc `73b52d12`: carstate no longer subscribes, so the buttons there are inert. New base also has no Qt UI (raylib). Nothing to port. |
| 30 | `UiSetSpeed.targetSpeed`, `setSpeed` param, Wi-Fi TCP script (`64b59c1f4`, `ec9b6eae9`, `1f8fba403`; removed by `b20debe87`) | n/a | Replaced on yeetfollow by the HTTP bridge, unused. |
| 31 | Max steering angle 90° (opendbc `3add98c1`) | exact (fallback) / closest equivalent (kit) | Fallback `MAX_STEERING_ANGLE = 90`. Kit: `ExternalController` TOI blip at 90° (`TOI_MAX_ANGLE_DEG`). |
| 32 | Torque steering limits / safety | exact (fallback) | `RIVIAN_TORQUE_ONLY_STEERING_LIMITS`, from `3543cc78e` (#3) |

## Driver monitoring

| # | Item (`3ad41b16e`) | Status | Where now |
|---|---|---|---|
| 33 | Wheel-touch timeout 130 s (alerts at 115/124/130 s) | exact (equivalent mapping) | `monitoring/policy.py`, from `b2b775df7` |
| 34 | Vision timeout 111 s (alerts at 103/105/111 s) | exact (equivalent mapping) | same |
| 35 | Pose pitch 0.7133 / 0.7237, yaw 0.7020 / 0.8042 | exact | same |

## MADS (Jason Wen's `mads-tesla` merge in the yeetfollow base)

| # | Item | Status | Notes |
|---|---|---|---|
| 36 | `MadsSteeringMode` (remain/pause/disengage) replaces `MadsPauseLateralOnBrake`, pandad `ALT_EXP_MADS_DISENGAGE_LATERAL_ON_BRAKE` (`b31fbad3c`, opendbc `748d9623`) | exact | Upstreamed into sunnypilot. Present in base `mads/helpers.py`, `params_keys.h`, pandad. |
| 37 | Rivian/Tesla MADS: force disengage-on-brake + unified engagement, no main cruise (`7b047f14e`, `e0f7063b2`, `b8809740f`, `bd55ce794`) | exact | Base `get_mads_limited_brands` / `MADS_NO_ACC_MAIN_BUTTON` |
| 38 | MADS requests lateral on op engage (opendbc `a11e1ed8`) | exact | `safety/sunnypilot/mads.h` `op_controls_allowed` |
| 39 | Tesla-only MADS / teslacan changes | n/a | Not the R1S |

## Boot, build, firmware, repo

| # | Item | Status | Notes |
|---|---|---|---|
| 40 | Boot recovery from unclean-shutdown build corruption (`ecd93ea02`) | exact (broader) | `launch_chffrplus.sh`: also skips `.venv` and `.git` on this base |
| 41 | Panda CAN ignition prev counter scoping (panda `7723bbca`, `bbef572fd`) | exact | Per-brand `prev_counter_rivian` in `opendbc/safety/ignition.h` |
| 42 | Submodule URLs to rawdigits/opendbc, lukasloetkolben/panda (`7ec5672e4`, `ba5a784b4`, `efd17efe2`) | n/a | opendbc is in-tree, panda changes upstreamed |
| 43 | `MPC_TUNING.md` (`411fbc2f9`) | different → updated | Current values |
| 44 | Forgejo prebuilt CI (`2d44ca9da`) | exact | `.forgejo/` (`d2a2a3d39`) |
| 45 | xfail the known tuning failures (`254a18943`) | ported (different case set) | See below |
| 46 | opendbc `TASK.md` (`a772cd9b`) | n/a | Administrative |

## Tests (#4)

With items 1–2 and 11–14 the following-distance suite still passes (18/18). The same maneuver tests fail as on
yeetfollow's harder-braking cases. These 4 are marked strict xfail ("known: yeetfollow tuning, see automotive/openpilot#4"):

| mode | force_decel | maneuver |
|---|---|---|
| e2e | no | steady state following a car at 20m/s, then lead decel to 0mph at 2m/s^2 |
| e2e | no | steady state following a car at 20m/s, then lead decel to 0mph at 3m/s^2 |
| acc | no | steady state following a car at 20m/s, then lead decel to 0mph at 2m/s^2 |
| acc | no | steady state following a car at 20m/s, then lead decel to 0mph at 3m/s^2 |

yeetfollow fails 19 (4 standstill follow-distance + 15 maneuvers). yeet-angle fails fewer with identical constants because the
base's planner differs. It has no MPC cruise obstacle or `CRUISE_MAX_ACCEL`, and the MPC runs leads-only. Cruise, MPC and
e2e accelerations are combined by taking the minimum, and `should_stop` is ORed across sources. The xfail set was measured on
this branch, not copied. The xfails use subtests, which can't carry a marker, so strict is emulated as on
yeetfollow: a known case that passes fails the test.


## Guard tests

`openpilot/selfdrive/controls/tests/test_ryan_customizations.py` pins every row above that has code on this base (all but
the n/a rows 15, 29, 30, 39, 42, 46). Each test names its row. The Rivian rows run with the angle kit (plus the long harness)
and on the torque fallback. The file runs in the Forgejo prebuilt CI, so a rebase that drops one of these customizations fails CI.
