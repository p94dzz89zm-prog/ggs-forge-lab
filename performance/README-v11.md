# DragonMind v11: damage forecast source discovery

2026-10-02. Local successor to v10. Single-worker fresh-pod comparison.

## Measured result

| Seed | v10 control | v11 candidate | Winner / final logged turn |
|---|---:|---:|---|
| 20261011 | 25.686 s | 26.334 s | Jaymie / 45 |
| 20261012 | 55.431 s | 49.995 s | Destyn / 44 |
| Combined | 81.117 s | 76.329 s | |

Combined engine-time reduction: **5.90%**. The
first game was 0.648 seconds slower; the longer game was 5.436 seconds faster.
Both complete ordered traces matched: 2,146 tracked events. One observation per
seed/implementation is a limited benchmark, not a universal speed guarantee.
These timings do not establish statistical significance or instant games.

Settings: 1536 MiB heap; Parallel GC; non-tiered compiler with threshold 1000;
stock AI profiles; rotation zero; warm two-seed process; 180-second game timeout.
The v10 control finished before candidate compilation/testing. No other games,
profilers or test processes ran during either measured pair. Events compared:
Turn, Phase, Add To Stack, Resolve Stack, Damage, Life, Combat.

## What the deeper profile found

Isolated nested instrumentation of v10 seed 20261012 took 59.599 engine seconds;
all 1,103 tracked events matched the reference game. Key timings:

| Instrumented operation | Calls | Inclusive seconds | Exclusive seconds |
|---|---:|---:|---:|
| Blocking search entry | 1,562 | 19.919 | 0.011 |
| Safe/good blocks | 1,921 | 8.426 | 0.308 |
| Group blocks | 1,965 | 4.916 | 2.587 |
| Blocker destruction forecast | 21,125 | 4.472 | 3.688 |
| Attacker destruction forecast | 21,390 | 4.180 | 3.407 |
| Damage forecast | 181,937 | 3.393 | 3.393 |
| Life-danger forecast | 5,459 | 3.647 | 2.851 |
| Creature evaluation | 38,484 | 2.008 | 2.008 |
| Live static-layer rebuild | 41,426 | 9.737 | 9.737 |
| Hypothetical static-layer rebuild | 35,776 | 8.792 | 8.792 |

Inclusive parent/child times overlap; cross-thread roots overlap too. Do not sum
this table into game wall time. Exclusive time excludes only instrumented children,
not all downstream work. Method counts include nested invocations. Profiling has
its own overhead and its elapsed time is not an optimization benchmark.

The survival forecasts repeatedly query combat damage rules. This justified
extending existing bounded source discovery rather than caching final survival
predictions. Block-cost lookup measured only 0.549 seconds here, so avoiding its
zero-cost allocations was not the priority for this change.

## Implementation and preservation of rules

- A complete ordered source snapshot is shared within the existing read-only
  forecast scope. It preserves zone/player order and current phasing membership.
- Toughness-based damage, reversed-power damage, and assignment as unblocked use
  the existing static-host discovery index; actual effects and conditions stay live.
- No-combat-damage and unpreventable-damage queries keep the complete source list
  before appending their explicit source. Filtering away a same-id real card could
  change LKI precedence; the full snapshot preserves the original deduplication.
- A replacement-host index includes hosts with **any** current replacement effect,
  so changing an existing effect's mode cannot remove a cached source. Prevention
  and fog queries reread current modes, active zones, validity, requirements,
  overriding abilities, and amounts on every query.
- Discovery that synthesizes traits and invalidates the scope falls back to the
  original full enumeration. Outside a valid scope, enumeration is unchanged.
- Existing mutation hooks invalidate parent/nested snapshots. Closing the bounded
  inspection restores/removes its thread-local state. No cross-action damage,
  legality, or survival result cache was introduced.

Replacement discovery opt-out:
`-Ddragonmind.disableCombatReplacementRuleIndex=true`.
The existing static-source opt-out remains available.

## Validation and packaging

- 37 engine optimization tests, 19 commander-pilot tests, 12 bridge tests, and
  31 Python tests passed: **99 checks**.
- New tests cover live modes/validity, original real-card/LKI precedence,
  replacement ordering, nested additions, phasing, departure, live prevention
  amounts/targets, opt-out enumeration, and fog combat flags/active zones.
- 13 ordered patches reproduce 47 source files
  byte for byte from the pinned upstream checkout.
- Eight source files changed in this patch, including tests. The v11 archive
  contains 11 newly compiled production class entries;
  test and diagnostic classes are excluded. Archive integrity passed.
- Packaged runner completed seed 20261011 in 24.884 engine seconds / 30.049
  wall seconds; all 1,043 tracked events matched. Stable dragonmind.jar was
  updated after this check. This is not another paired timing estimate.
- Changed Java classes compiled on Java 17. The full Maven source build was not
  rerun. Neither exact trace matches nor these targeted tests establish exhaustive
  conformance for all Magic cards.

Reproduce the expanded diagnostic overlay with:
`python3 diagnostics/build_decision_profile.py SOURCE V10_JAR OUTPUT --blocking --block-internals`.
Run from the engine resource working directory with that overlay before the jar
on the classpath and `-Ddragonmind.decisionProfile=OUTPUT.csv`.

## Next measured target

Static-layer rebuilding remains a large measured cost. It needs dependency and
mutation analysis before replacing full rebuilds. Group-block logic and repeated
life-danger forecasts are additional concrete targets. Faster batch throughput
continues to come from v10's measured two-worker configuration; this change does
not remeasure batch scaling.
