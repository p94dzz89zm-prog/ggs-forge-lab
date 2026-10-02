# DragonMind v15: broader seeds, fresh profile and worker throughput

October 2, 2026. Accepted v15 was compared with v14 on six new seeds, followed
by an isolated v15 profile and a packaged-runner one/two-worker comparison.
No engine optimization or runtime default was changed in this investigation.

## Broader seed result

| Seed | v14 seconds | v15 seconds | Exact legacy trace match |
|---|---:|---:|---|
| 20261013 | 34.614 | 33.104 | no: combat ordering |
| 20261014 | 41.155 | 40.236 | yes |
| 20261015 | 7.037 | 8.387 | yes |
| 20261016 | 14.189 | 15.958 | yes |
| 20261017 | 27.033 | 27.350 | yes |
| 20261018 | 42.946 | 39.853 | yes |

Total: **166.974 seconds v14, 164.888 seconds v15**: a **1.25% reduction**
(2.086 seconds). Three of six pairs were faster; three were slower. This is
much smaller than the previous 15.00% observation on two repeated seeds.
The earlier result remains a result for those seeds, not a general estimate.
These six new pairs were observed once each. No significance or universal gain
is claimed, and results were not pooled with the earlier repeated sample.

Order: control then candidate on seeds 20261013–15, candidate then control
on 20261016–18; three seeds per JVM. Same fixed seats/decks and stock AI,
Java 17, 1536 MiB heap, Parallel GC, non-tiered compilation, threshold 1000,
disabled JVM performance data, headless mode and 180-second per-game limit.
All 12 games completed with matching winner and last logged turn per pair.
No simultaneous games, compilation, regression suites or profilers ran during
these timing comparisons. Light file reads and diagnostic script preparation
occurred. The diagnostic control replay is excluded from timed totals.

### Trace investigation and limits

Five pairs matched the legacy ordered trace exactly. Seed 20261013 did not:
attacker display order, the first printed blocker line and damage record order
varied. The unchanged v14 replay itself varied attacker ordering for that seed.
Inspection of the multiline blocker log showed identical full assignments in
both versions, rather than the different first lines suggesting different blocks.

The new supplemental comparison includes combat continuation lines that the
legacy prefix-only extractor omits. It preserves turn/phase boundaries and the
order of non-combat/damage tracked records. It compares combat and damage
record multisets within each phase, and compares combat participants by card IDs
rather than display order. All six pairs passed this comparison: **6,566 full
tracked records**. The control replay passed it as well. The exact-match failure
is retained in the measurements; normalization is a supplementary log audit,
not a proof that damage ordering is irrelevant or a complete rules-state check.
Three parser regression tests verify inclusion of multiline blockers, rejection
of changed blocking targets/damage amounts, and preservation of phase/stack order.

## Fresh v15 profile

The isolated seed 20261012 profile completed in 40.807 seconds and matched all
1,103 legacy events exactly, and all 1,138 full tracked records under the
supplemental comparison. Nested exclusive sums were nonnegative and matched
the sum of per-thread roots. Instrumentation adds overhead; roots overlap across
threads, and candidate-wait overlaps the worker. Profile durations below are
attribution evidence, not an unprofiled speed comparison.

| Scope | Calls | Exclusive seconds |
|---|---:|---:|
| Card ability discovery | 115,289 | 3.301 |
| Stack eligibility inspection | 34,671 | 3.168 |
| Destroy-blocker prediction | 21,125 | 3.165 |
| Destroy-attacker prediction | 21,390 | 2.955 |
| Life danger prediction | 5,459 | 2.286 |
| Combat forecast body | 1,231 | 2.151 |
| Gang-block selection body | 1,965 | 2.081 |
| Damage prediction | 181,937 | 1.831 |

Hypothetical static rebuilds fell from **23,659 in the prior v14 profile to
2,817**, with the same traced game. Their current inclusive duration was
1.003 seconds, exclusive body 0.260 seconds. Eligibility inspection increased
from 1.501 to 3.168 instrumented seconds as it inspected more borrowed candidates.
Fresh inspection remains necessary for the conservative exclusions.

The next selected investigation is the computation inside attacker/blocker
survival predictions: 42,515 calls, 6.120 exclusive instrumented seconds here.
Inspect transformation, first-strike and power/toughness bonus prediction work
for repeated work within a single call. Prior duplicate-result audits found
little benefit from broader answer caching; no cache or shortcut is proposed
without new evidence. Ability discovery and eligibility inspection are secondary
targets. No v16 candidate has been built or accepted in this measurement step.

## Reproducibility

Use diagnostics/benchmark_seed_expansion.py for new-seed jar comparisons;
--resume reads existing logs without retiming completed groups. It retains exact
trace results and stops on outcome or phase-inventory mismatches. Use
build_decision_profile.py with --block-internals --static-internals --blocking
--stack-eligibility, then summarize_decision_profile.py. The committed profile
summary retains scope counts and nested root/static boundaries. Full scratch
profile logs are not required for rebuilding the instrumentation.

Worker measurements and limitations are recorded below and in
v15-worker-throughput-measurements.json. The simulation jars were unchanged;
accepted v15 SHA256 is
9389e96f9190e051f1b739460e61e0b407b087aa7fb3f5f423d6169bc5eeab68.

## Worker throughput

| Workers | Four-game wall seconds | Completed games/minute |
|---|---:|---:|
| 2 | 84.406 | 2.843 |
| 1 | 106.887 | 2.245 |

Two workers delivered **26.64% higher throughput** in this sample.
The existing two-worker default remains supported; it was not changed. Seeds
20261013–16 ran with batch size 2 and stock AI, in order two workers then one.
All four outcomes matched; three legacy traces matched exactly, and seed 16
varied combat ordering. All four phase-inventory comparisons matched, covering
4,161 full tracked records per worker configuration. Timing includes startup
and runner overhead. No concurrent profiling, compilation, testing or other
games ran alongside these worker configurations.

Host limits: eight CPU quota cores and 8 GiB cgroup memory. This was one short
four-game run per worker count, not a long-run capacity study. Four workers,
peak memory and sustained memory pressure were not measured. The practical
recommendation is to retain two workers on this host, not a claim of globally
optimal concurrency. Existing host-capacity guards remain in effect.

Validation: 34 Python tests passed, including the three new trace-parser cases.
No Java production source, active jar, runtime defaults or pilot behavior changed.
