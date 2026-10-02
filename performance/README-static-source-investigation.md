# DragonMind: static-source collection investigation

2026-10-02. Experimental candidate tested against v12, then set aside.
The active engine remains v12.

## Benchmark

| Seed | v12 control | Candidate | Winner / final logged turn |
|---|---:|---:|---|
| 20261011 | 26.962 s | 25.012 s | Jaymie / 45 |
| 20261012 | 48.127 s | 49.895 s | Destyn / 44 |
| Combined | 75.089 s | 74.907 s | |

The observed combined reduction is **0.24%** (0.182 seconds). The first game is
faster and the second slower. This does not establish a reliable overall speedup;
one observation per seed/implementation is consistent with timing noise. All
2,146 tracked events matched exactly. Games remain tens of seconds.

Identical settings: 1536 MiB heap, Parallel GC, non-tiered compilation with
threshold 1000, stock AI profiles, seat rotation zero, two seeds per warmed
process, 180-second game timeout. Control finished before compilation. Benchmarks
ran without competing games, profilers, compilation or test workloads. Small
source edits and patch/archive preparation occurred during the candidate run.
Tracked events: Turn, Phase, Add To Stack, Resolve Stack, Damage, Life, Combat.

## Implementation

The existing source-discovery snapshots are invalidated by static rebuilds and
trait changes. Extending their lifetime would require a broader correctness
argument. This change instead avoids building effective-trait collections for
cards whose current state has only intrinsic static abilities.

A CardState collector reads intrinsic static abilities directly when there are
no combined split traits, changed trait effects, removed intrinsic abilities,
or static abilities contributed by cached keywords. It checks continuous mode
and current active zones on every invocation and adds matching abilities to the
rebuild's independently owned result collection. Otherwise it uses the original
effective-trait getter. No intrinsic membership is exposed or retained, and no
source, condition or effect result is memoized.

GameAction still substitutes hypothetical cards before source inspection. It
still visits the complete original zones, sideboards, inbound tokens and stack
in the original order. Hidden static abilities and static commands are collected
by their original paths. Effect ordering, layers, dependency trials, granted
traits, commands, control corrections, triggers and view updates are unchanged.

## Diagnostic result and decision

The candidate's isolated diagnostic game completed in 55.817 seconds and matched
all 1,103 tracked events. For the same seed, the preceding v11 diagnostic profile
measured source collection at 3.527144 seconds across 77,162 calls. The candidate
measured **3.525742 seconds across the same 77,162 calls**. This is no meaningful
change. The reference profile was v11, not a fresh v12 diagnostic run; v12's
change was in affected-card selection rather than source collection. These
instrumented measurements overlap enclosing rebuild time and are not ordinary
elapsed-game benchmarks.

Other candidate profile costs remain substantial: affected-card selection
1,135,910 calls / 5.510 seconds; live rebuilds 41,426 calls / 10.730 inclusive
seconds; hypothetical rebuilds 35,776 calls / 9.928 inclusive seconds. Parent and
child timings and cross-thread roots overlap and must not be summed.

**Decision: do not install the candidate.** Its paired game timings and targeted
profile provide no convincing improvement for this workload. Restore the three
candidate source files to the accepted v12 checkpoint and leave the active jar
unchanged. Preserve the experimental patch and measurements for reproducibility
and future investigations. No new production architecture or cache was adopted.

## Validation

- 46 engine optimization tests, 19 commander-pilot tests, 12 bridge tests and
  31 Python tests passed: **108 checks**.
- Five new tests check collection membership ownership; active zones, phasing and
  modes; granted/removed traits; keyword and split-state traits; land-type effects
  that remove intrinsic abilities; and an actual hypothetical rebuild followed
  by live-board restoration.
- The 14 accepted patches plus this experimental patch reproduce 47 managed
  source files byte for byte from pinned
  upstream 4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676.
- Three candidate source files changed, including tests. Five freshly compiled
  production class entries were packaged in the experimental jar. Archive
  integrity passed; tests and profilers are excluded. It was not installed.
- Restored source bytes match the pre-experiment v12 checkpoint exactly. The
  active jar still matches the accepted v12 jar exactly.
- Java 17 compiled the changed classes; the full Maven source build was not rerun.
  Tests and sampled trace matches do not establish exhaustive Magic rules
  conformance. No new retained cache was introduced; this turn did not repeat
  v10's heap-retention audit.
- One concurrent test JVM failed at startup inside JVM PerfMemory allocation
  (native SIGBUS), before engine checks. An isolated rerun with JVM performance
  data disabled passed all 19 commander tests. This is not an observed rules
  engine failure; the exact external cause was not established.

The candidate was exercised through the Java game entry point and diagnostic
overlay. A further packaged Python-runner game was not run after rejecting the
candidate; v12 remains the previously verified active runtime.

## What to investigate next

Avoiding intrinsic-source collection allocation is ruled out as a useful
optimization for these two games. Affected-card selection remains the largest
measured static-internal leaf. The next focused profile should distinguish zone
assembly, validity predicates, hypothetical-list merging and Shaman's Trance
handling before choosing another edit. Reducing the number of hypothetical
rebuilds may offer a larger architectural gain, but preserving dependencies,
granted traits and triggers requires proof; this experiment did not justify
skipping them.

The experimental patch is at
`diagnostics/experiments/static-source-collector-candidate.patch`.
Apply it after the accepted 14-patch chain. Its tests were compiled and run with
the same test runners as the accepted checkpoint. Expanded profiler commands
remain documented in the v12 report.
