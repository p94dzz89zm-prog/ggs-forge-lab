# DragonMind: validity preparation and live property investigation

2026-10-02. Accepted production baseline is v12.

## Source isolation and attribution correction

The pre-existing source tree contained three unfinished candidate files: Card,
CardLists, and DragonMindPerformanceTest. They prepared cached syntax once per
list query. The stable jar continued to match accepted v12 exactly.

The earlier affected-selection overlay recompiled candidate Card and CardLists
against the v12 jar. Its 4.790395-second validity figure belongs to that candidate,
not accepted v12. Its report and machine-readable summary now carry this correction.

This investigation reconstructed all 47 managed source files from pinned upstream
4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676 and the accepted 14-patch chain. Only the
three candidate files differed from the pre-existing source tree. Baseline and
candidate overlays were built separately. Both diagnostic games matched all
1,103 tracked events of the accepted reference game.

## Corrected baseline profile

Seed 20261012 completed in 58.700 instrumented engine seconds, Destyn winning at
logged turn 44. These are diagnostic costs, not ordinary game timing estimates.

| Stage | Calls | Inclusive instrumented seconds |
|---|---:|---:|
| Affected validity | 981,973 | 5.686071 |
| Query preparation, all string queries | 983,190 | 0.065164 |
| Query filtering, all string queries | 983,190 | 4.927740 |
| Affected zone assembly | 981,973 | 0.666224 |

Individual card checks were sampled within 15,309 affected queries, selected
by an independent deterministic sequence with approximately 1/64 probability.
The sampler never uses the engine RNG. The following call counts and durations
are sampled work only, not whole-game totals:

| Sampled leaf | Calls | Instrumented seconds |
|---|---:|---:|
| Syntax-cache lookup | 326,277 | 0.025675 |
| Self property | 96,685 | 0.019088 |
| Type/initial eligibility | 326,277 | 0.017488 |
| IsCommander property | 9,681 | 0.014826 |
| Assassin property | 1,843 | 0.003709 |
| YouOwn property | 9,681 | 0.003046 |
| YouCtrl property | 10,856 | 0.001627 |

Preparing syntax once per query removes repeated cache lookups during candidate
filtering. It increases preparation work: the candidate diagnostic measured
0.380151 seconds preparing and 3.795961 seconds filtering. Its complete diagnostic
game took 60.741 seconds, so the profiles alone establish no whole-game speedup.
Profiler overhead, nested timings and cross-thread roots prevent summing these
values into elapsed game time. The summarizer checked root/exclusive accounting
and nonnegative exclusive durations for both profiles.

## Candidate behavior

The candidate retains the existing bounded syntax-only cache and prepares each
comma-separated alternative once per list query. Card evaluation still checks
current types, controller, phasing, keywords, commander status, counters, prepared
spell zones and last-known information on every invocation. Alternatives,
negation, empty clauses, null-card handling and independently owned result
membership remain unchanged. There is no new retained cache of cards, game state,
legality or eligibility results.

## Checks

46 optimization tests, 19 commander-pilot tests, 12 bridge tests and 31 Python
tests passed: 108 checks. The existing runtime-lifecycle test also passed all
four of its checks. Five focused validity tests include changes to live state,
phasing, prepared-spell zones, last-known controller information and owned
result membership. Changed Java classes compiled with Java 17; the full Maven
source build was not rerun. Test and diagnostic classes are excluded from the
isolated candidate jar, whose ZIP integrity check passed.

The first regression process passed all 77 engine/pilot/bridge methods and then
failed to load the uncompiled runtime-lifecycle test class. After compiling that
class, its isolated run passed; already-passing groups were not rerun. A Python
comparison-test invocation used the resource directory and failed import; the
same four tests passed when invoked from the repository.

## Reproduction

Build the isolated overlay from the accepted source checkpoint:

```bash
python3 diagnostics/build_decision_profile.py SOURCE V12_JAR OUTPUT --validity-internals
```

Run from the resource directory with OUTPUT/classes before V12_JAR on the
classpath, entry point forge.view.Main and dragonmind.decisionProfile set to a
CSV output path. Use Commander, GGS_Layered_v1/Jaymie_Ezio/Gabe_Food/Destyn_Turtles
seat order, stock Default profiles, seed 20261012 and 180-second game timeout.
JVM: Java 17, 1536 MiB heap, Parallel GC, non-tiered compilation, threshold 1000,
disabled JVM performance data and headless mode.

Raw CSV/logs and isolated source checkpoints remain in the diagnostic workspace.
Committed summaries: diagnostics/validity-internals-v12-summary.json and
diagnostics/validity-internals-candidate-summary.json. The experimental patch is
diagnostics/experiments/prepared-validity-candidate.patch.

## Unprofiled comparison and decision

Two repetitions per implementation and seed ran in control/candidate/candidate/
control order. Each JVM ran seed 20261011 followed by 20261012 with the same
settings described above. Both paired repetitions matched all 2,146 tracked
events: 4,292 comparisons in total. Winners and logged turns were unchanged.

| Repetition | Seed | v12 seconds | Candidate seconds |
|---|---:|---:|---:|
| 1 | 20261011 | 28.618 | 27.770 |
| 1 | 20261012 | 48.788 | 49.741 |
| 2 | 20261011 | 26.192 | 25.879 |
| 2 | 20261012 | 49.315 | 48.884 |

Combined v12 time: 152.913 seconds. Candidate: 152.274 seconds. The observed
reduction is only **0.42% (0.639 seconds)**. Repetition one is slightly slower;
repetition two is slightly faster. There is no convincing whole-game speedup.
In addition, a patch/source comparison and archive-verification step took about
0.62 seconds during the second control run; this could bias such a small
combined difference. No concurrent games, profiles, compilation or Java/Python
regression workloads ran during the benchmark games. These timings are not a
statistically established general throughput result.

**Decision: keep v12 active and set the candidate aside.** The three working
candidate files have been restored to the accepted checkpoint; all 47 managed
source files match the original 14-patch chain. The stable jar remains byte for
byte equal to dragonmind-v12.jar. The complete experimental patch, five tests,
profiles, build verification and measurements are preserved. The candidate was
not installed. No new heap-retention audit was performed for this discarded
candidate. There was no additional Python-runner game after rejection; the
packaged candidate itself completed all four unprofiled Java-entry-point games.

## Next target

The syntax-only preparation change did not establish a useful whole-game gain.
The sampled IsCommander property is costly per invocation relative to simple
controller checks; its original dispatcher sits near the end of a long property
chain. A focused next experiment can test early dispatch of a few exact common
properties while preserving prepared-spell exclusion, phasing and last-known
controller semantics. Another option is returning to the larger block-search
cost. Neither optimization is adopted by this investigation.
