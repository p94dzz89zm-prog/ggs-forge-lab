# DragonMind v12: static-layer diagnostics and redundant-copy removal

2026-10-02. Local successor to v11.

## Result

| Seed | v11 control | v12 candidate | Winner / final logged turn |
|---|---:|---:|---|
| 20261011 | 25.509 s | 25.383 s | Jaymie / 45 |
| 20261012 | 49.104 s | 48.763 s | Destyn / 44 |
| Combined | 74.613 s | 74.146 s | |

The observed reduction was **0.63%**, only 0.467 seconds across two games.
One observation per seed/implementation does not establish a reliable speedup;
this result is consistent with ordinary timing noise. Games are still tens of
seconds, not instant. All **2,146 tracked events matched exactly**.

Identical settings: 1536 MiB heap, Parallel GC, non-tiered compiler with threshold
1000, stock AI, seat rotation zero, a warm two-seed process, and 180-second game
timeout. Control completed before candidate compilation/testing. No competing
games, tests, compilation, or profilers ran during the benchmark games.
Small source edits and patch/archive preparation occurred during the candidate
run. Traces compare Turn, Phase, Add To Stack, Resolve Stack, Damage, Life, Combat.

## What the deeper profile found

An isolated diagnostic overlay on v11 seed 20261012 completed in 55.435 seconds.
All 1,103 tracked events matched the reference. Selected nested timings:

| Operation | Calls | Inclusive seconds | Exclusive seconds |
|---|---:|---:|---:|
| Affected-card selection | 1,135,910 | 5.647 | 5.647 |
| Initial source collection | 77,162 | 3.527 | 3.527 |
| Live static-layer rebuild | 41,426 | 10.641 | 3.472 |
| Hypothetical static-layer rebuild | 35,776 | 9.912 | 2.988 |
| Continuous effect body | 861,543 | 2.740 | 2.629 |
| Clear prior effects | 77,162 | 0.778 | 0.778 |
| Apply before layers | 861,543 | 8.188 | 0.719 |
| Dependency ordering | 542,144 | 5.101 | 0.341 |
| Undo dependency trial | 165,462 | 0.341 | 0.341 |

Inclusive parent/child times and cross-thread roots overlap. Do not sum these
values into elapsed game time. Exclusive time excludes only timed child methods.
The affected-card count includes nested calls. Profiling adds overhead; this is
not a timing comparison with the candidate. The effect-body timer covers the
matching overload; an additional differently indented overload is not timed
separately. Static-apply-before and rebuild timers include its work.

## Change

Affected-card selection previously copied an assembled zone/defined list into a
second collection and then created its filtered result. When no eligible
hypothetical cards contribute, v12 filters that source list directly. This
removes redundant collection population without caching eligibility or results.

When hypothetical cards contribute, the original union-before-filter order stays
intact: even an invalid hypothetical card must retain priority over a same-id
live card. Results always own their membership, including when there is no
Affected restriction, so ignored-card removal and caller mutation cannot alter
the stack's live zone view or another source collection. Defined-card selection,
phasing filtering, Shaman's Trance's graveyard add-back, and ignored cards retain
their existing behavior.

No rebuild is skipped. Dependency ordering, granted traits, effect application,
static commands, control corrections, triggers and view updates still run.
No new cache or persistent references were introduced. This is not a renewed
heap/leak audit; v10's lifecycle checks remain the prior evidence on retention.

## Validation and packaging

- 41 optimization tests, 19 commander-pilot tests, 12 bridge tests, and 31 Python
  tests passed: **103 checks**.
- Four new tests cover owned result membership with/without filtering, ignored
  cards and live stack membership, invalid hypothetical precedence, defined-card
  hypothetical priority, and Shaman's Trance's opponent-graveyard access.
- 14 ordered patches reproduce 47 managed source files byte for byte from pinned
  upstream 4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676.
- Two source files changed in this patch, including tests. Three freshly compiled
  production class entries are packaged; test and diagnostic classes are excluded.
  Archive integrity passed.
- Changed classes compiled on Java 17. The full Maven source build was not rerun.
  These checks and sampled trace matches do not establish exhaustive correctness
  across all Magic cards.

- Packaged runner completed seed 20261011 in 26.119 engine seconds / 31.616
  wall seconds; all 1,043 tracked events matched. The stable dragonmind.jar
  was updated after this check. This is not another paired timing estimate.

## Next architectural target

This small allocation change does not remove the main bottleneck. The next
useful investigation is repeated collection of static sources during hypothetical
rebuilds: it accounts for 3.527 instrumented seconds here. Sharing immutable
source-discovery data within a verified read-only decision scope may avoid some
of that work, but must preserve hypothetical substitutions, granted/removed
traits, phasing, static commands, dependency ordering and triggers. Final effect
results must continue to use current state. Whole-layer memoization is not yet
justified by the evidence.

Reproduce diagnostics:
`python3 diagnostics/build_decision_profile.py SOURCE V11_JAR OUTPUT --static-internals`
Run from the engine's resource directory with the diagnostic classes before the
jar and `-Ddragonmind.decisionProfile=OUTPUT.csv`.
