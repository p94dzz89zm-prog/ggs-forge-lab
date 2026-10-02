# DragonMind: reduce repeated discovery and collection work

October 1, 2026 (America/New_York). This change targets allocation and collection assembly found in the live profile of ability discovery and hypothetical combat. Magic rules checks remain enabled.

## Measured result

| Complete four-player game | Current v4 control | v5 candidate | Observed reduction |
| --- | ---: | ---: | ---: |
| Seed 20261011, first game in process | 34.373 s | 31.324 s | 8.9% |
| Seed 20261012, second game in process | 72.533 s | 65.980 s | 9.0% |
| Both game times combined | 106.906 s | 97.304 s | 9.0% |

These are two sequential games per executable, one paired trial for each seed, not a statistically established general speedup. The three changes were measured together; this table does not attribute a separate gain to each change. Machine load and JVM variability remain practical limits. Earlier passes' numbers are not used as the control.

All 2,146 compared turn, phase, stack-addition, stack-resolution, damage, life and combat events matched exactly. Jaymie/Ezio won the first game on global turn 45; Destyn/Turtles won the second on global turn 44. Neither a different strategy nor a shortened game accounts for the observed reduction in these traces. Trace matching is targeted evidence, not exhaustive rules certification or a deck win-rate estimate.

## What changed

1. **One snapshot for alternative-cost sources.** The old path constructed an aggregate collection across source zones, then copied it into another collection with the prospective spell's source at the front. The new path builds that source-first snapshot directly from the same zones, players and stack. It preserves order, identity deduplication, phased-card filtering and LKI/alternate-host precedence. Static abilities and their conditions are still evaluated fresh on every query; nothing persists across queries.
2. **Direct copies into empty unique collections.** When an empty FCollection receives another FCollection, the source already guarantees uniqueness. The new path copies its backing list rather than checking each incoming element for duplicates. Destination membership storage remains independent and is populated when required. Nonempty destinations and arbitrary iterable sources retain the original deduplicating path. This shared operation serves rules discovery, static-trait assembly, and combat-related collection work.
3. **Skip empty name-effect iteration.** Card.getName returns the current state's name immediately when there are no changed-name effects. This avoids allocating/iterating an empty table view in repeated name checks, including combat forecasts. Changed-name effects still run in their existing timestamp order, and each call reads the current table and state; this is not a name cache.

No hypothetical combat result, legal-action list, damage amount, targeting choice or static-layer result is cached. This pass reduces repeated collection overhead underneath the two hotspots. It does not replace the hypothetical-combat search architecture itself. That remains further work.

## Verification

75 targeted checks passed: 21 performance/rules checks, 19 Commander-pilot checks, 12 bridge checks, and 23 Python checks. New checks cover empty/small/large bulk copies, source/destination independence, self-addition, duplicate suppression, removal and reuse after clearing; source-first discovery against the original reference snapshot, alternative-cost host departure; and name-effect addition, ordering, removal and clearing.

An initial test fixture used Omniscience for a static AlternativeCost assertion. Forge scripts Omniscience through a Continuous MayPlay permission, so that assertion was inappropriate. The fixture was corrected to Fist of Suns, which uses the intended AlternativeCost path. This was a test correction, not a rules-engine change.

The seven ordered patches reproduce all 29 checked source files exactly. The v5 patch changes FCollection, Card, StaticAbilityAlternativeCost, and the performance regression test. The executable archive passed integrity checking and overlays 15 production classes onto v4. Test classes and the JFR diagnostic reader are excluded from the playing executable. The source retains Forge's pinned upstream version and GPL attribution.

The candidate's changed classes and tests were compiled with Java 17 against the accepted runtime, and the targeted Java tests were run directly. A full Maven rebuild was not run in this workspace. The build script applies all seven patches and runs the designated tests for a full source build.

The packaged executable also passed the end-to-end Python runner check: seed 20261011 completed in 33.407 seconds with Jaymie/Ezio winning, and all 1,043 tracked events matched the first control game. Runner metadata records the executable/deck hashes and exact command. This separate packaging check is not an additional paired speed estimate.

## Reproduce

Build from source with forge-fork/build_bridge.py. The new patch is forge-fork/dragonmind-discovery-v5.patch; it applies after dragonmind-decision-architecture-v4.patch. The packaged executable is dragonmind-v5.jar.

The paired comparison used Java 17, a 1536 MB heap, Parallel GC, -XX:-TieredCompilation, -XX:CompileThreshold=1000, headless mode, stock Default AI, unchanged deck order GGS/Jaymie/Gabe/Destyn, sequential seeds 20261011 and 20261012 in one process, and explicit 120-second game limits. Controls and candidates ran sequentially; profilers and other game simulations were not run concurrently with these benchmarks.

Raw comparison logs are discovery-control.log and discovery-candidate.log in the working workspace. The source patch, build integration, and this report are checkpointed locally; no GitHub upload was performed.

## Remaining goal

The observed improvement is useful but full games still take tens of seconds. Instant fresh games have not been achieved. Repeated hypothetical-combat/blocker evaluation and rules-sensitive static recalculation remain major targets. Further changes need fresh measurements and stable query boundaries rather than reuse of stale game state or bypassing Magic rules.
