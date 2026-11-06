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
