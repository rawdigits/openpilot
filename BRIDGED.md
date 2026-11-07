# Rivian TCM bridge out of card (yeet-angle-bridged)

Why: automotive/openpilot#9 comment 80759. On 2026-11-07 at 04:59:18Z the VDM latched an Imps_Cmd cruise fault 50 ms
after card stalled for 37 ms (every sendcan address and carState gapped). Suspect, unproven: the bridge poll thread
inside card (urllib, json, Params) sharing card's GIL and a lock with the 100 Hz loop.

## What runs where

| | before | now |
|---|---|---|
| bridge HTTP, URL list / rotation, stale rules | thread in card | `rivianbridged` process (`openpilot/sunnypilot/selfdrive/car/rivianbridged.py`), normal priority, cores 0-3, started by manager only onroad with a Rivian and openpilot longitudinal |
| Params reads (`TrafficSignOffset`, `RivianButtonSource`, `RivianScrollInvert`, `LongitudinalPersonality`) | that thread | `rivianbridged`, every 0.3 s |
| `RivianFollowLevel` / `LongitudinalPersonality` writes (bridge level, comma wheel level) | that thread | `rivianbridged`, on change only, same mapping `{1:0, 2:1, 3:2, 4:2}` |
| card | read the thread's state under a lock | reads the latest `rivianBridgeSP` without blocking (conflated socket), hands plain values to `RivianBridge` before `CarState.update`. No network, files, Params or shared locks. Publishes the comma wheel level in `carStateSP.rivianCommaGap` / `rivianCommaFollowLevel` |

Bridge source: `GET /stream` (SSE, one `data:` line per event, full `/state` JSON, heartbeat at least every 250 ms).
One connection; stale after 1 s with no event (the read times out), reconnect backoff 0.25, 0.5, 1, 2 then 5 s, with
`GET /state` polled every 0.1 s in between. A bridge that answers 404 (or isn't an event stream) is polled and asked
for `/stream` again every 30 s. Polled state is stale after 2 s, as before. A failed connection moves to the next URL
(`/data/rivian-bridge.conf`, else the repo `rivian-bridge.conf`, else Nebula then truck LAN); a switch is logged once.

`rivianBridgeSP` (cereal custom slot `customReserved10` → `RivianBridgeSP`): `stale`, `setSpeedMs`, `followLevel`,
`followPersonality`, `signOffset`, `buttonSource`, `scrollInvert`, `personalityParam`, `url`, `streaming`, `ageMs`.
Published on every bridge event (coalesced to 50 Hz) and at least at 10 Hz. card treats it as stale when the latest
message is older than 2 s (rivianbridged gone or hung), keeping the last Params values.

## card lateness

`cloudlog.event("card_late", kind="cycle"|"sendcan", ms=..., prev_step_ms=..., suppressed=N[, can_strs=...])` when a
cycle starts more than 15 ms late (gap between cycle starts minus 10 ms), or sendcan publishes are more than 25 ms
apart while controlling. At most one per second; `suppressed` counts the ones dropped since the last.
