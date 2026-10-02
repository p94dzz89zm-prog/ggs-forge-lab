# DragonMind v2: rules baseline and performance

October 1, 2026

Wizards of the Coast's Comprehensive Rules and current Oracle text are the authority for simulation behavior. Forge is the implementation, and its authors retain GPL attribution. DragonMind is our customized simulation and AI layer. Recording a rules baseline does not certify that every card script implements it correctly.

## Official baseline

The official rules text checked this iteration is effective September 25, 2026, including Commander section 903. Rule 108.1 identifies Oracle as the authoritative card wording source. The source URL and SHA-256 are pinned in `rules-baseline.json` and included in run metadata.

Official text: https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt
Oracle: https://gatherer.wizards.com/

The simulator now explicitly disables Forge's inherited performance mode, which otherwise permits skipping some checks. Discrepancies must be treated as engine bugs. There is no exhaustive rules-conformance certification yet, and pinning this document does not automatically update older card scripts.

## Measurements

Four-player Commander pod: layered GGS, Jaymie/Ezio, Gabe/Food, Destyn/Turtles. Same seat order, stock AI, seed 20261011, unprofiled.

| Configuration | First game engine time | Loaded-engine repeat |
| --- | ---: | ---: |
| Original baseline | 46.199 s | — |
| Previous DragonMind v1 | 39.499 s | 34.787 s |
| v2 empty-trait paths + Parallel GC | 32.445 s | 28.582 s |
| Final v2, including scoped mana inspection | 33.057 s | 29.317 s |

The final v2 first game was 28.4% faster than baseline; its loaded-engine repeat was 36.5% faster. The best intermediate repeat was 38.1% faster. These are single-seed observations, not a general performance guarantee. The final additional optimizations did not beat the best intermediate time; isolated timings are noisy and do not establish their independent benefit.

Both final repeats matched all 1,043 compared turn, phase, stack-addition, resolution, damage, life and combat log entries from baseline. Winner remained Jaymie/Ezio, final global turn 45. This is targeted behavioral evidence, not a proof of every internal rules decision.

Difficult seeds remain unfinished: seed 20261013 reached the 45-second limit at global turn 48, and a profiled seed 20261012 reached its 35-second limit at turn 29. They have no assigned winner and are excluded from completed-game timing comparisons. Instant games have not been achieved.

## Changes

- Fast paths avoid allocating empty static and replacement trait lists, with checks for changed traits, keyword traits, counters, split cards and special card types.
- Cache bounded parsed validity syntax, while evaluating card properties and controller state afresh.
- Filter already-unique collections without repeatedly rebuilding membership indexes; preserve order and duplicate handling for other inputs.
- Scope mana replacement-source candidate reuse to read-only AI inspection. Reevaluate applicability for each query; invalidate on actual replacement resolution, static-effect recalculation and hooked trait/state changes. Exit the scope before payment/actions. Future mutation paths require care.
- Record the garbage collector choice and default to Parallel GC based on the initial throughput checks.
- Preserve commander-aware ninjutsu behavior, fresh game creation, RNG reset, timeout classification and explicit failure reporting.

## Validation

65 targeted checks passed: 19 commander pilot, 12 bridge, 14 performance/rules regressions and 20 Python runner/comparison tests. New coverage includes intrinsic/changed/keyword trait additions, shield/stun/finality counters, planeswalker/battle/saga/adventure replacements, split cards, mutable validity properties, filtered membership, replacement flags, zone changes and scoped invalidation when an effect is added.

The four ordered patches recreate the changed source files exactly. The final executable ZIP integrity check passed. The packaged executable completed an end-to-end commander-aware runner game: seed 20261011, Jaymie/Ezio winner, global turn 45, 32.953 seconds engine time and 37.769 seconds runner wall time including loading. This verifies packaging and policy integration; it is separate from the stock-policy equivalence comparison.

## Reproduce

```sh
python3 forge-fork/build_bridge.py /absolute/path/new-dragonmind-source
python3 dragonmind.py --engine /absolute/path/new-dragonmind-source/forge-gui --jar /absolute/path/new-dragonmind-source/forge-gui-desktop/target/dragonmind.jar --seeds 4 --batch-size 4 --workers 1 --gc parallel
```

Build order: `forge.patch`, `commander-identity-followup.patch`, `dragonmind-performance.patch`, `dragonmind-rules-performance-v2.patch`. Upstream pinned to `4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676`. Java 17+, Maven, Python and Forge resources are required. The artifact produced in this workspace is `dragonmind-v2.jar`; the reproducible builder names its final output `dragonmind.jar`.

The default runner uses commander-aware ninjutsu. Add `--stock` for the timing comparison above. Use a new output directory for every run. Independent workers improve aggregate throughput when resources permit, rather than guaranteeing faster individual games.

## Remaining work

Games still take tens of seconds. Repeated effect evaluation and AI mana/decision work remain significant costs. Difficult seed profiles need targeted investigation, and further caching needs proven invalidation rather than assuming game state is unchanged. Broad commander inference remains incomplete: the current pilot is a narrow enhancement of Forge's AI, not four general language-model agents. Card-addition comparisons need multiple independent games and seat rotations after these reliability and throughput issues are addressed.

Executable SHA-256: `78ca4d9d45f800638a6c438faa11aaddbf752a7473c2743522d149ffb3510cdf`
