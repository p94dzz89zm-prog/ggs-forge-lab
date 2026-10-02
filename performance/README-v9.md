# DragonMind v9: shared combat-rule discovery

October 2, 2026. This pass reduces repeated source-list construction inside combat searches, adds phasing invalidation and retires the ineffective v8 stack filter.

| Complete four-player game | v8 control | v9 candidate |
| --- | ---: | ---: |
| Seed 20261011 | 26.952 s | 26.659 s |
| Seed 20261012 | 61.281 s | 54.756 s |
| Combined engine time | 88.233 s | 81.415 s |

The observed combined reduction is **7.73%**. All **2,146** compared turn, phase, stack, damage, life and combat events match in order. Jaymie/Ezio won the first game; Destyn/Turtles won the second. This is one paired observation per seed, not a statistically established general speedup. The first-game difference is small enough to include runtime noise. Changes were measured together, so the result cannot be attributed separately to the new lookup and the v8 rollback. Fresh games still take tens of seconds.

## Diagnosis

A separate, instrumented v8 run of seed 20261012 completed in 64.071 seconds. All 1,103 tracked events match the slower control game. It recorded 580,139 canBlock invocations across nested overloads, 425,407 block-cost queries and 71,004 block-requirement queries. Block-cost queries took approximately 2.321 seconds inside their instrumented bodies. Block-search timing included approximately 17.638 seconds outside the other instrumented child stages.

These are diagnostic wall timings with instrumentation overhead. Inclusive timings overlap; waiting for the candidate-evaluation worker overlaps its computation. The recording covers the process, including setup, and is not a CPU-time budget or an independent paired speed measurement.

The v8 run also retained exactly the same stack-keyword simulation and restoration counts as the earlier v7 diagnostic: 34,671 and 34,811 respectively. That did not support attributing the earlier small observed timing difference to reduced rebuilding. v9 removes v8's controller-specific stack filter, its extra world scan and its six dedicated tests. The original broad, full-rule stack calculation is restored. The v8 report remains historical, with a retirement note in the source project.

## Architecture change

Combat rule queries repeatedly aggregate source cards from battlefield, graveyard, exile, command and stack zones. Inside an existing bounded read-only combat-inspection scope, v9 lazily discovers cards with static traits once and reuses their ordered host list.

Attack/block costs, attack/block prohibitions, blocker restrictions and mandatory blocking use this list. Every query rereads current traits, modes, conditions, validity, costs and combat state. Explicit attacker/blocker hosts remain prepended by the original query code, preserving hypothetical and last-known-information creatures and their priority over real-card duplicates.

The lookup uses the original aggregate's exact zone/player ordering and phasing behavior. Existing trait, state and zone mutation hooks invalidate it through nested scopes. Invalidation during source discovery falls back to the original full list. Outside a valid scope, queries also use the original list. The diagnostic property `dragonmind.disableCombatRuleIndex=true` disables this additional host filtering.

Direct Card.setPhasedOut changes now invalidate combat/source inspection, covering phased-in hosts previously absent from cached lists. This also protects the existing v6 trait-host lookup. The new code stores source membership within a single search; rule applicability and completed combat decisions remain live. Rules checks and stock AI strategy remain enabled.

## Verification

**86 targeted checks passed:** 32 rules/performance checks, 19 Commander-pilot checks, 12 bridge checks and 23 Python checks. The performance suite comprises the prior 28 checks plus four new cases; the six retired v8 filter checks were removed with that code.

New cases cover exact source ordering, empty-host filtering, nested additions, direct zone departures, live validity and cost changes, live mode changes, explicit hypothetical attacker/blocker traits, the opt-out path, and direct phasing changes across both source indexes.

Tests and matching traces are targeted regression evidence, not universal rules-conformance certification. The lookup relies on bounded read-only usage and its known invalidation hooks.

The eleven ordered patches reproduce **39 checked source files** byte-for-byte. The v9 delta changes ReplacementHandler, CombatUtil, StaticAbilityCantAttackBlock, StaticAbilityBlockRestrict, StaticAbilityMustBlock, Card, GameAction, GameActionUtil and performance tests. The archive passed integrity verification and overlays **25 production classes** onto v8. Tests and profiling classes are excluded. Changed Java classes were compiled against the accepted runtime; a full Maven rebuild was not run. The source build script applies all eleven patches and runs designated engine tests. Upstream attribution remains intact.

## Reproduction

The new source patch is `forge-fork/dragonmind-blocking-v9.patch`, after v8. Build from pinned upstream with `forge-fork/build_bridge.py`.

Benchmarks used Java 17, 1536 MB heap, Parallel GC, `-XX:-TieredCompilation`, `-XX:CompileThreshold=1000`, headless mode, stock Default AI, unchanged GGS/Jaymie/Gabe/Destyn deck order, sequential seeds 20261011 and 20261012 and explicit 120-second game limits. Games ran sequentially without concurrent simulations, tests or profilers. Raw logs are `blocking-control.log` and `blocking-candidate.log`; `blocking-measurements.json` retains times and trace equality.

For finer blocking diagnostics, `diagnostics/build_decision_profile.py` now supports `--blocking`, adding legality, costs, requirements and attacker-blockability timers. Use the matching runtime jar and overlay classpath; analyze the CSV with `diagnostics/summarize_decision_profile.py`. Diagnostic files are `blocking-profile-v8.csv` and `blocking-profile-v8.log`.

The next measured targets are the remaining work inside blocker search, repeated damage/trade evaluation and unnecessary cost-object construction on queries with no additional cost. Full board rebuilding also remains substantial. No instant-game claim or deck-strength conclusion follows from this pass.

The packaged v9 executable passed the end-to-end runner check in 27.078 seconds of engine time, with all 1,043 tracked events matching the first control game. Metadata retains executable/deck hashes and the command. This separate packaging check is not another paired speed estimate. The stable `dragonmind.jar` now uses v9, with earlier executables retained. Changes and this report are checkpointed locally; no GitHub upload was performed.
