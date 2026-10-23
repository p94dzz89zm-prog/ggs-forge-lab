# Stage57: integrated native mulligan service

The unreserved native chain was restored from eight hash-bound preserved
archives. Nine executable versions verified; latest base SHA256
`c43ce68ab06b7fa6e5aabeca11a6f7960beb416c899917a0c74e4df8b65186df`
includes the house profile, execution evidence, stack notification repair and
stale-payment guard. No original archive, historical log or Stage47/48 artifact
was edited. An initial legacy-manifest format rejection was preserved, then
the legacy archive's exact inventory, hashes, sizes and CRC were verified.

The Stage56 declaration barrier is integrated into this chain. Only the actual
round method is replaced; initialization, house policy selection and post-round
processing remain unchanged. A second independently reproduced defect offers
standard London mulligans after the player's opening hand reaches zero cards.
The optional `--london-limit` overlay changes only London's permission predicate
from a non-strict to a strict hand-size boundary. This is separate from the
declaration-order defect.

The frozen September25,2026 Comprehensive Rules,103.5 and103.5c, require London
bottoming as part of each mulligan, before the next decision. Existing bottoming
timing is therefore retained. For four players, the first mulligan is free;
after two, the opening hand has six cards; after eight, zero, and no further
mulligan is permitted. House `ggs-house-v1` instead explicitly caps at three
free full-seven reshuffles with no bottoming. This is the deterministic
three-free profile, not a claim that every playgroup uses the same cap.

Six native JVM controls exercised actual `MulliganService.perform()` with the
real policy factory, rotated starting seat2, and no injected policy list:

| Runtime/control | Required observation |
|---|---|
| Original/standard | Expected declaration-order assertion failure |
| Round-only/standard | Two redraws, seven then six cards; legal bottom order |
| Round-only/zero-card boundary | Expected assertion: another decision offered at zero cards |
| Integrated/standard | Same two-redraw assertions pass |
| Integrated/zero-card boundary | Eight redraws, zero-card final hand, automatic keep |
| Integrated/house | Three full sevens, no bottoming, automatic keep |

Every declaration checks all player counts/hand sizes and keep states; every
final state checks physical card conservation and exact chosen library-bottom
order. Controls also retain commander damage history, apply the house loss
exception only when enabled, and retain ordinary zero-life loss. These are
constructed service integrations, not natural games or strategic evaluations.

Reproduction requires the preserved latest base and runtime resources:

```
python3 forge-fork/build_mulligan_round.py --base /runtime/latest.jar --expected-base-sha256 c43ce68ab06b7fa6e5aabeca11a6f7960beb416c899917a0c74e4df8b65186df --output /fresh/integrated.jar --london-limit
python3 forge-fork/run_mulligan_service.py --runtime /runtime/resources --patched /fresh/integrated.jar --logs /fresh/controls
```

The initial six JVMs used the equivalent preserved invocations before the
reusable runner was added. The runner is syntax-checked, not an additional
executed batch. Exact output hashes, inputs and failed controls remain private.
All other JAR entries and normalized unrelated class methods remain identical.

407 baseline Python tests pass; hosted CI and final checkpoint status are in
the authoritative ledger. Three historical games remain unapproved; original
2026202029 retains its illegal mulligan order. Approved historical events0,
complete approvals0, new natural games0, training0. Replay466choices and
1790/1985conditional support remain reserved and unchanged.

Next stage: prospective evidence protocol and opening-state instrumentation,
including authentic shuffle permutations, starting-player selection and exact
canonical deck/card-data bindings. Do not start a prospective certification
game until that opening evidence passes independent controls.
