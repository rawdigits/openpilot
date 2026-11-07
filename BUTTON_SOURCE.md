# Rivian wheel buttons: comma or bridge (yeet-angle-standalone)

Who owns set speed and follow gap. Param `RivianButtonSource` (Settings > Vehicle > Rivian > Wheel Buttons):

| Value | Name | Set speed | Follow gap |
|---|---|---|---|
| 0 | Auto (default) | Comma when the xnor kit forwards `WheelButtons_Fwd` (valid scroll counter within ~1 s), else Bridge | |
| 1 | Comma | wheel buttons only (tap ±1, hold 0.66 s → next 5 mph / 10 kph), engage = current speed, stalk down = max(set, speed) | scroll wheel, directional, level 1-4 clamped |
| 2 | Bridge | bridge `set_speed_ms`; the wheel buttons are ignored while the bridge is fresh with a target, used as before when it is stale or has none | bridge `follow_level`, `gapAdjustCruise` cycling only while stale |

- Comma ignores the bridge's `set_speed_ms` and `follow_level` completely. Bridge `TrafficSignOffset` sign logic still applies.
- Comma without forwarded buttons falls back to Bridge (logged once).
- Comma gap: each `RightButton_Scroll` counter step (8-bit, wraps, 255 and the first sample ignored) moves the level by
  one, no wrap at 1 / 4. Written by rivianbridged (from carStateSP) as `RivianFollowLevel` plus `LongitudinalPersonality`
  through `FOLLOW_LEVEL_PERSONALITY {1:0, 2:1, 3:2, 4:2}`, the same path as the bridge's levels. Start level: the fresh
  bridge's level, else `LongitudinalPersonality` (0→1, 1→2, 2→4).
- `RivianScrollInvert` (bool, default off = counter up is farther). Unverified which way is which: every step is logged
  as `rivian buttons: gap delta=<d> invert=<b> level=<a>-><b>`; flip the toggle if the logs show it backwards.
- Source changes are logged as `rivian buttons: source=comma|bridge reason=...`.

Code: `opendbc_repo/opendbc/car/rivian/carstate.py` (`update_button_source`, `update_comma_follow_level`),
`opendbc_repo/opendbc/sunnypilot/car/rivian/carstate_ext.py`, `rivian_bridge.py`, `rivianbridged.py` (BRIDGED.md). Tests:
`opendbc_repo/opendbc/car/rivian/tests/test_rivian_button_source.py`.
