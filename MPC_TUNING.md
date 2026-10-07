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
| COMFORT_BRAKE | 2.5 m/s² | 2.5 m/s² |
| STOP_DISTANCE | 6.0 m | 6.0 m |

The bridge supplies absolute personality values through the existing
`LongitudinalPersonality` param. Standard is the base's default. Legacy Rivian
levels map to 0 / 1 / 2 / 2; the TCM bridge owns that conversion.

These are Ryan's final source-tip MPC changes, with xnor's stopping and
acceleration-limit implementation retained. The inherited Dan tune's 3 m stop
distance, 3 m/s² comfortable braking and 1.8 m/s² cruise acceleration were not
replayed. Lower acceleration-change cost permits faster acceleration changes;
these constants alone do not establish driving behavior. See `ANGLE_PORT_NOTES.md`
for source commits, verification and the remaining vehicle validation.
