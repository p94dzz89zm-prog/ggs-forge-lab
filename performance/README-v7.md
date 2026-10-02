# DragonMind: defensive ability discovery optimization

October 1, 2026 (America/New_York).

The v7 candidate reduces repeated discovery work inside combat forecasts. Magic rule checks and stock Commander AI remain enabled.

| Complete four-player game | v6 control | v7 candidate |
| --- | ---: | ---: |
| Seed 20261011 | 33.946 s | 31.716 s |
| Seed 20261012 | 74.053 s | 68.459 s |
| Combined engine time | 107.999 s | 100.175 s |

The observed combined reduction is **7.24%**. All **2,146** compared turn, phase, stack, damage, life and combat events match in order. Jaymie/Ezio won the first game and Destyn/Turtles the second. This is one paired observation per seed, not a statistically established general speedup. Fresh games still take tens of seconds; instant simulation has not been achieved.

## Why this change

A separate diagnostic run measured 3,755 attacker-destruction and 3,192 blocker-destruction calls. Of these, 735 attacker calls repeated the diagnostic's observed state within the enclosing search, accounting for approximately 0.160 seconds of measured call-body time. No blocker repeats survived that observed-state filter. Both methods together accounted for approximately 2.199 seconds of measured body time. Diagnostic instrumentation affects timing, and its state key does not establish semantic equivalence for every Magic interaction. These measurements do not justify introducing a whole-combat outcome cache. The diagnostic game's 1,043 tracked events match the first control game.

Instead, v7 shares discovery of potential regeneration and damage-prevention source cards. Those two checks previously traversed the controller's battlefield repeatedly during hypothetical combat searches.

## Architecture

The first defensive query in a valid, bounded combat-inspection scope scans the controller's battlefield and indexes hosts by ability type. Later queries reuse these ordered host lists. Consumers still reread abilities and check activation eligibility, targets, costs, available mana, tapped state and prevention amounts on every call. No final combat outcome, affordability result or target result is cached.

The index is thread-local and discarded when the enclosing scope ends. Existing state, trait and zone mutation hooks invalidate it. New guards cover intrinsic and keyword-provided spell ability additions and changes to an ability's API type. Invalidation causes fallback to the original full battlefield scan, including when trait discovery itself changes the state. Queries outside a valid scope also use the original scan. The diagnostic flag `dragonmind.disableCombatDefenseIndex=true` disables host filtering while retaining all rule checks.

## Verification

**82 targeted checks passed:** 28 rules/performance checks, 19 Commander-pilot checks, 12 bridge checks and 23 Python checks. The new cases verify fresh tap availability and prevention amounts, mana availability, ability type changes, nested keyword additions and direct battlefield departures. These checks and matching traces are regression evidence, not universal rules-conformance certification.

The nine ordered source patches reproduce **34 checked source files** byte-for-byte. The v7 delta changes ReplacementHandler, ComputerUtil, CardState, KeywordInstance, SpellAbility and the performance tests. The archive passed integrity verification and overlays **13 production classes** onto v6; test and profiler classes are excluded. Changed Java classes were compiled against the accepted runtime. A full Maven rebuild was not run; the source build script applies all nine patches and runs the designated engine tests. Upstream attribution remains intact.

## Reproduction

The new patch is `forge-fork/dragonmind-defense-v7.patch`, following the v6 combat patch. Build from the pinned upstream source using `forge-fork/build_bridge.py`.

Benchmarks used Java 17, a 1536 MB heap, Parallel GC, `-XX:-TieredCompilation`, `-XX:CompileThreshold=1000`, headless mode, stock Default AI, unchanged GGS/Jaymie/Gabe/Destyn deck order, sequential seeds 20261011 and 20261012, and explicit 120-second game limits. Benchmarks ran sequentially without concurrent game simulations or profilers. Raw logs are `defense-control.log` and `defense-candidate.log`; `defense-measurements.json` records the times and trace comparison.

The diagnostic tools are checkpointed under `diagnostics/CombatWorkProfiler.java` and `diagnostics/build_combat_profile.py`. Their state-repeat counters are investigative metrics, not a safe persistent cache key.

The packaged v7 executable completed an end-to-end runner check in 32.890 seconds of engine time. All 1,043 tracked events matched the first control game; runner metadata retains executable and deck hashes. This is a packaging check, not another paired speed estimate. The stable `dragonmind.jar` now uses v7, with earlier executables retained. No GitHub upload was performed.
