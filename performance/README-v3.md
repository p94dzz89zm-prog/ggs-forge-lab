# DragonMind v3: performance checkpoint

October 1, 2026

## Outcome

Fresh four-player Commander games are not instant. The best completed loaded-engine benchmark in this iteration was 28.264 seconds. The packaged commander-aware game completed in 37.704 seconds, and the difficult independent seed remained unfinished at its 60-second limit. These measurements do not establish a general win rate, general speedup, or exhaustive rules correctness.

Wizards' Comprehensive Rules and current Oracle wording remain the authority. The simulator explicitly keeps Forge's approximation/performance mode disabled. GPL attribution remains intact. No rules resolution, AI candidate search, or recorded game event was removed to manufacture a faster result.

## Fresh paired measurements

The execution environment was slower than the previous session, so this round reran the previous executable instead of comparing directly to historical times. Same deck files, stock AI, seed 20261011, seat order, heap and collector:

| Engine and compiler configuration | First game engine time | Loaded-engine repeat |
| --- | ---: | ---: |
| v2, standard tiered compiler | 50.315 s | 45.221 s |
| Tracked-view candidate, standard compiler | 52.374 s | 33.554 s |
| v2, throughput compiler settings | 49.854 s | 35.139 s |
| Accepted v3, throughput compiler settings | 38.561 s | 28.264 s |

With the same throughput compiler settings, v3 improved the first game by about 22.7% and the loaded-engine repeat by 19.6%. Against v2 with its previous compiler configuration, the repeat was about 37.5% faster. These are individual measurements from one completed seed, not population estimates. Simulations also incur resource-loading and process overhead outside the reported engine times.

Each completed benchmark above matched all 1,043 compared turn, phase, stack-addition, resolution, damage, life and combat events from the original baseline, with Jaymie/Ezio winning on global turn 45. Matching these log categories is targeted evidence rather than a proof of every internal rules decision.

## Accepted changes

1. Replaced raw live keyword collection exposure with tracked live views. Retained views remain live, and iterator, removal, clearing, adding and bulk operations invalidate membership caching. Ordinary text rendering can now read these collections without permanently disabling the cache. Mutable trait contents are still read fresh.
2. Return the shared empty collection when a card has neither a relevant hidden counter ability nor an active suspected ability. Keyword-counter and suspected behavior remain evaluated normally when present.
3. Added a recorded `--jit throughput|default` setting to the runner. The default throughput setting uses `-XX:-TieredCompilation -XX:CompileThreshold=1000` on Java 17, paired with the existing Parallel GC default. It favors this measured workload and may not help every configuration. `--jit default` restores the ordinary compiler policy. Metadata retains both settings and the complete command.

## Experiments discarded

A mode-specific effect prefilter passed its targeted trait tests but did not finish the benchmark within its 50-second limit; its tracked prefix still matched baseline. Broader aggregate-trait snapshots, global revision invalidation, observer-based local invalidation and whole-card trait snapshots failed to consistently beat the simpler tracked-view approach. Those production changes were removed. Their logs are retained for investigation, and their timing is excluded from the accepted v3 result.

## Verification

69 targeted checks passed: 19 commander pilot, 12 bridge, 17 performance/rules regressions and 21 Python runner/comparison checks. New coverage includes retained live views edited through bulk operations and iterators, mutable keyword trait lists edited through sublists/list iterators/copies, hidden suspected abilities and keyword counters, and explicit runtime flag selection.

The five ordered source patches reproduce the checked source files exactly. The v3 delta touches Card, KeywordCollection and the performance regression test. The runner and build script syntax checks passed, and the packaged executable passed archive integrity validation.

End-to-end packaged runner, commander-aware policy, default throughput settings:

| Seed | Result | Engine time | Final logged global turn |
| --- | --- | ---: | ---: |
| 20261011 | Completed; Jaymie/Ezio won | 37.704 s | 45 |
| 20261012 | Timeout; no winner | 60.001 s | 37 |

Total runner wall time for these two attempts was 104.146 seconds. The timeout is excluded from completed-game timing summaries. This run checks packaging and policy integration; its commander-aware first game is separate from stock-policy benchmark equivalence.

## Reproduce

```sh
python3 forge-fork/build_bridge.py /absolute/path/new-dragonmind-source
python3 dragonmind.py --engine /absolute/path/new-dragonmind-source/forge-gui --jar /absolute/path/new-dragonmind-source/forge-gui-desktop/target/dragonmind.jar --seeds 4 --batch-size 4 --workers 1 --gc parallel --jit throughput
```

Build requirements: Java 17+, Maven, Python, network access for build dependencies, and Forge resources. The executable alone does not include the resource database. Upstream remains pinned to `4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676`.

Patch order: `forge.patch`, `commander-identity-followup.patch`, `dragonmind-performance.patch`, `dragonmind-rules-performance-v2.patch`, `dragonmind-performance-v3.patch`.

This workspace's executable is named `dragonmind-v3.jar`; the reproducible builder names its output `dragonmind.jar`. Use `--stock` for comparisons to the benchmark table, `--jit default` for the ordinary compiler, and a fresh output directory for each run. Additional workers improve aggregate throughput when CPU and memory permit; they do not make each individual game instant.

## Unresolved target

Instant fresh games have not been achieved. The v2 profile identified repeated static and replacement trait assembly, world scans, card filtering and AI evaluation as substantial costs; this iteration addressed part of that workload. The remaining goal requires a larger change to indexing and evaluation, validated against state changes, copies, counter effects, zone changes and current rules. Skipping legal checks, declaring a timeout a win, or replaying cached old games would not satisfy the deck-comparison goal.

Broad commander inference also remains unfinished. The commander-aware pilot is still a narrow enhancement to Forge's AI. The current timings and tests do not certify four general strategic agents or reliable card-addition rankings.

Executable SHA-256: `761a50b746226e3ce4687d28ac6a992294e13f4a1cb359562ec60ac293a46baf`

## Additional optimization trials after this checkpoint

The following candidates were tested and removed; the accepted executable remains v3. All completed equivalent trials matched the original 1,043 tracked events per game. Times below are individual trials and are not proof of general performance.

| Candidate | First game | Loaded repeat | Decision |
| --- | ---: | ---: | --- |
| Direct property checks | 41.572 s | 30.444 s | Removed; no demonstrated improvement over v3 |
| Direct special-type membership | 46.380 s | 36.718 s | Removed |
| Compact collection copies | 48.579 s | 33.939 s | Removed |
| Skip headless ability-text formatting | 54.199 s | 35.677 s | Removed |
| Defer redundant base-paired alternative costs, corrected | 46.108 s | 32.011 s | Removed |

The first alternative-cost candidate failed a graveyard/flashback regression and changed the full game's outcome. It was stopped. The corrected candidate retained standalone alternatives when the base ability was filtered out; it passed the 18-check candidate suite and matched all 2,086 tracked events across two complete replays. It still did not beat the best accepted warm result, so it was removed. The retained suite remains 17 performance checks (69 targeted checks across all suites).

The final source was compared byte-for-byte with the five accepted ordered patches after removing these trials. The packaged v3 executable remains unchanged. Instant fresh simulation is still unresolved; no replay cache, shortened game, artificial winner or rules-skipping mode is presented as completion.
