# Rivian EPAS angle control re-arm (automotive/openpilot#10)

Drive 2026-11-06, route `000000c7--4693ee51c3`, build `yeet-angle-brake-smooth` `0e368b6ad`. Numbers below are from the
issue, the raw logs are on the device only. No rlogs or fixtures for this route exist in the repo (process replay
only lists the remote Gen1 route `bc095dc92e101734|000000db--ee9fe46e57--1`).

## What the codes mean

From `opendbc_repo/opendbc/dbc/rivian_primary_actuator.dbc` (`EPAS_AdasStatus`, 0x390), the only source found:

| Signal | Value | DBC name |
|---|---|---|
| `EPAS_EacStatus` | 0 | `EPAS_EacStatus_Eac_Inhibited` |
| | 1 | `Eac_Available` |
| | 2 | `Eac_Active` |
| | 3 / 4 / 5 | `Eac_Standby` / `Eac_Fault` / `Sna` |
| `EPAS_EacErrorCode` | 11 | `EPAS_Vehspd_Max_Thd_Err` (vehicle speed above max threshold) |
| | 10 | `EPAS_Vehspd_Corrln_Failr_Err` (speed correlation failure) |

No upstream sunnypilot / commaai issue or doc names these codes; a web search for the signal names finds nothing
beyond the DBC.

- Confirmed: err 11 is the EPAS's own "vehicle speed above threshold" error (DBC name), and it showed up both times the
  speed crossed ~101 mph (seg 10) and 104 mph (seg 18).
- Unconfirmed: the exact threshold (somewhere just under ~101 mph by the EPAS's own speed, 160 km/h = 99.4 mph is a
  guess), whether it has its own hysteresis, and what the 78 mph drop in seg 7 was (it recovered by itself, its error
  code is not in the issue).
- Unconfirmed: that the EPAS leaves Inhibited when angle is requested again. The drive only shows it stays at 0 while
  `ACM_EacEnabled` is 0.

## The deadlock

After the drop `eac_dead_frames >= EAC_RECOVER_FRAMES` put `ExternalController` in torque. In torque
`create_angle_steering` sent `ACM_EacEnabled=0` and `ACM_FeatureStatus=1`. The handback to angle needs
`EacStatus == 1 and EacErrorCode == 0`, the EPAS sat at 0 (Inhibited, err 0) for segs 11-24. Neither side moved.

## The fix (`ext_controller.py`)

**Retry.** While in torque, lat active, hands off, not steeringPressed, and all handback checks pass (torque at least
0.5 s, hands off 0.75 s, wheel inside the EPAS / ISO / 25 deg envelope, inside the EPAS rate budget, within 15 deg of the
plan), with the wheel still (`|steeringRateDeg| < 2`), the last sent angle within 0.5 deg of the wheel, and
`EacStatus 0, EacErrorCode 0`:

- request angle (`ACM_EacEnabled=1`, `ACM_FeatureStatus=2`) for up to 50 frames (0.5 s), angle = measured wheel angle,
  torque keeps holding the wheel meanwhile
- EPAS answers 1 (Available): the existing handback runs, then 2 has to follow within `EAC_RECOVER_FRAMES` as before
- EPAS goes straight to 2: handback too
- otherwise (window over, hands on, any EacErrorCode, EacStatus 4, wheel moves): stop requesting, stay on torque

**Rate.** After a failed retry wait 3 s, doubling per failure up to 12 s. A successful re-arm also starts the backoff, so
an EPAS that takes angle and drops it again cycles at most every 3/6/12 s. The backoff resets after 10 s on angle or on
disengage. Worst case with an EPAS that never answers: 0.5 s of EacEnabled every 12 s.

**Overspeed (goal 3).** Above 160 km/h (99.4 mph, `vEgoRaw`) hand to torque before the EPAS drops, no angle request or
retry until below 155 km/h (96.3 mph). The evidence is the DBC name plus two drops at 101/104 mph and none below that
with err 11. Without it the EPAS drops on its own anyway (and the retry then re-arms below the threshold), so a wrong
threshold only costs angle control between 99.4 and ~101 mph.

**Logs.** carlog (cloudlog) warnings: `rivian eac: above/below ...`, `rivian eac: retry N failed, EacStatus S err E
after F frames, next in W frames`, `rivian eac: angle re-armed after N retries`.

## EacStatus 2 -> 1 (err 0) shortly after engage

2026-11-07, after a vehicle reset, route `000000c9--d0dbc1edaa` seg 0: engage at 64 mph t=24.0 s -> 2, then 2 -> 1 err 0
at 25.4 s with no driver press, torque fallback, handback at 57.8 s. Again 2 -> 1 at 63.6 s, back to 2 at 65.2 s.

What the code does at engage (checked in `test_engage_within_epas_limits`, real CarController + libsafety, 64 mph, plan
equal to the wheel and 2 / 5 / 8 deg off it):
- `ACM_EacEnabled` 1 and `ACM_FeatureStatus` 2 go out together on the first lat-active frame, angle within one jerk
  step (0.27 deg at 64 mph) of the measured wheel. Disengaged, the sent angle is the measured angle.
- Afterwards every frame stays inside panda's jerk limit and the sent angle never moves more than the EPAS's own rate
  window (0.18 deg/frame x 16 frames at >= 37 mph, 0.94 margin) allows.

So no step, rate or sequencing problem shows up in our command. The EPAS reports err 0, so it names no reason, and
1 (Available) means it gave control back and would take it again. Not explained by the code; candidates that need the
rlog: the hands-on level (`EPAS_HandsOnLevel`) or torsion bar torque around 25.4 s, a `ACM_SteeringAngleRequest` vs
`EPAS_InternalSas` gap the EPAS counts as a steady-state error without publishing it, or something in the bus traffic
from the kit at that moment.

Debounce: not changed. With EacStatus 1 the EPAS does not steer, so waiting longer than `EAC_RECOVER_FRAMES` (0.15 s)
before torque means no steering at all for that time at highway speed. The second drop shows the cost is small (back on
angle 1.6 s later). The 32 s until the first handback is the bigger problem, but it needs the handback conditions from the
log (most likely hands-on via the capacitive sensor or presence latch, or the wheel outside 15 deg of the plan).

Every drop while on angle now logs `rivian eac: drop 2 -> S err E after N frames active, v, wheel, rate, sent, desired,
torque, hands_on_level`, so the next drive shows what the EPAS saw.

## Panda safety

Unchanged. `rivian.h` checks 0x110 with `steer_angle_cmd_checks_vm(desired_angle, ACM_EacEnabled)`:
- EacEnabled 0: the angle must be within 0.1 deg of the measured angle. Torque mode sends the measured angle, as before.
- EacEnabled 1: jerk limit from the last sent angle, which is the measured angle while inactive, and the ISO lat-accel
  limit. The retry starts at the measured angle (<= 0.5 deg away from the last sent) and stays there, the wheel is
  inside the handback envelope.
- EacEnabled toggles freely while controls are allowed, there is no rule on the bit itself.
- ACM_Status (0x100) has no tx check. Torque (0x120) keeps going through `steer_torque_cmd_checks` during the retry.

`test_rivian_eac_rearm.py` runs the real CarController against libsafety with simulated speed and wheel angle on every
frame.

## Unverified, check on the next drive

- that the EPAS goes 0 -> 1/2 when `ACM_EacEnabled` comes back (the whole fix depends on it)
- that a retry does not fault the EPAS (`EacStatus 4`) or show a cluster warning
- the overspeed threshold: whether angle drops between 99.4 and 101 mph would have happened anyway
- how torque and angle mix during the 0.5 s window if the EPAS goes active while torque is still applied (the handback
  zeroes torque the frame it sees 1 or 2)

Signals: `EPAS_AdasStatus.EPAS_EacStatus` / `EPAS_EacErrorCode`, `ACM_SteeringControl.ACM_EacEnabled` /
`ACM_SteeringAngleRequest`, `ACM_Status.ACM_FeatureStatus`, `EPAS_InternalSas`, vEgo, carControl.latActive,
`carOutput.actuatorsOutput.torqueOutputCan`, and the `rivian eac:` cloudlog lines.
