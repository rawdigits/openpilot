# MPC Tuning Reference (yeetfollow branch)

## Parameter Comparison

| Parameter | Sunnypilot (base) | Dan's yeetfollow | Ryan's tweak |
|---|---|---|---|
| DANGER_ZONE_COST | 100 | 50 | 60 |
| LEAD_DANGER_FACTOR | 0.75 | 0.55 | 0.65 |
| COMFORT_BRAKE | 2.5 | 3.0 | 3.0 |
| STOP_DISTANCE | 6.0 | 3.0 | 3.0 |
| CRUISE_MAX_ACCEL | 1.6 | 1.8 | 1.8 |
| T_FOLLOW relaxed | 1.75s | 1.25s | 1.25s |
| T_FOLLOW standard | 1.45s | 0.85s | 0.85s |
| T_FOLLOW aggressive | 1.25s | 0.60s | 0.60s |

## What These Mean

- **DANGER_ZONE_COST** — MPC penalty for being in the danger zone behind a lead car. Higher = more cautious.
- **LEAD_DANGER_FACTOR** — How aggressively it reacts to lead car proximity. Higher = reacts sooner.
- **COMFORT_BRAKE** — Max comfortable braking decel in m/s². Higher = allows harder braking.
- **STOP_DISTANCE** — Distance to stop behind lead car in meters.
- **CRUISE_MAX_ACCEL** — Max acceleration in m/s².
- **T_FOLLOW** — Time gap to lead car in seconds, per personality level.

## Summary

Dan made the fork significantly more aggressive than sunnypilot — shorter follow distances, less danger zone caution, harder braking allowed, closer stops. Ryan's tweak bumped DANGER_ZONE_COST (50→60) and LEAD_DANGER_FACTOR (0.55→0.65) back toward sunnypilot values slightly — a safety correction on Dan's aggressive tune.

## LongitudinalPersonality (Follow Distance Selector)

| Value | Name | T_FOLLOW | Jerk Factor |
|---|---|---|---|
| 0 | aggressive | 0.60s | 0.5 |
| 1 | standard | 0.85s | 1.0 |
| 2 | relaxed | 1.25s | 1.0 |

Default is **standard** (1).

## Rivian Follow Distance Mapping (cruise_sync)

| Rivian Level | OpenPilot Personality |
|---|---|
| Level 1 (closest) | aggressive (0) |
| Level 2 | standard (1) |
| Level 3 | relaxed (2) |
| Level 4 (farthest) | relaxed (2) |

Set via `Params('LongitudinalPersonality')` — no rebuild needed.

## File

`selfdrive/controls/lib/longitudinal_mpc_lib/long_mpc.py`

## Branch History

- Fork base: sunnypilot (`a6780e835`)
- Dan's Rivian commits: `bbef572fd` through `40955a998` (15 commits)
- Ryan's tuning: commit `3ad41b16e`
- Cruise sync (targetSpeed + follow distance): commits `64b59c1f4` through `44960f4a0`
