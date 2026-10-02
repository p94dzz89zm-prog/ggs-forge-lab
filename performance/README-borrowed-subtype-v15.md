# DragonMind: borrowed non-Assassin stack eligibility (v15)

October 2, 2026. This extends the accepted v14 eligibility inspection to borrowed
non-Assassin candidates. Borrowed Assassins still use full reconstruction. A
non-Assassin fails the recognized grant's required subtype regardless of who
would control its spell; the existing fresh dependency audit must still rule
out type changes, unknown grants, masked traits and other uncertainty. LKI and
extrinsic-keyword fallbacks remain. No controller-assignment assumption, new
state cache, search pruning or pilot change was introduced.

## Repeated unprofiled comparison

| Repetition | Seed | v14 seconds | v15 seconds |
|---|---:|---:|---:|
| 1 | 20261011 | 22.512 | 21.412 |
| 1 | 20261012 | 41.664 | 33.182 |
| 2 | 20261011 | 23.489 | 20.852 |
| 2 | 20261012 | 41.724 | 34.536 |

Control total: **129.389 seconds**. Candidate total: **109.982 seconds**.
Observed reduction: **15.00% (19.407 seconds)**. All four paired games were
faster. Both candidate runs matched all 2,146 tracked events: 4,292 events
across two repetitions. Two seeds remain limited evidence, not a statistical
claim or an engine-wide guarantee. These measurements are independent of the
previous v14/v13 comparison and should not be combined into a claimed gain.

ABBA order was control/candidate/candidate/control, two seeds per JVM. Java 17,
1536 MiB heap, Parallel GC, non-tiered compilation, threshold 1000, disabled
performance data, headless mode; Commander, Default AI, 180-second limit,
GGS_Layered_v1 / Jaymie_Ezio / Gabe_Food / Destyn_Turtles. No concurrent games,
profilers, compilation, regression suites or archive/source verification ran
during timed games. Light source reads and report preparation occurred.
Reproduce with diagnostics/benchmark_stack_eligibility.py using accepted v14
and v15 jars and a matching two-seed reference log.

## Selection and validation

The fresh v14 diagnostic profile's longer seed matched 1,103 tracked events.
It recorded 23,659 hypothetical static rebuilds, 6.351 seconds inclusive and
1.972 seconds exclusive; stack eligibility itself cost 1.501 seconds. Nested,
instrumented durations are attribution evidence, not unprofiled game timings.
The candidate-wait scope overlaps the worker and is not independent compute.
Raw observations: diagnostics/decision-profile-v14.csv.

The shadow overlay preserved v14's existing exclusions and observed the remaining
30,947 rebuilds across two seeds. It predicted **28,716 additional exclusions**;
all added zero alternative-cost options, with **zero productive misses and zero
incomplete observations**. All 2,146 tracked events matched. Its total inspection
cost was 2.988 instrumented seconds; net benefit was established separately by
the unprofiled comparison. The overlay builder now supports both pre-v14 and
v14 guards and uses a distinct diagnostic scope variable.

Checks: 24 shadow cases, 104 engine checks (26 eligibility, 43 performance,
19 pilot, 12 bridge, 4 lifecycle) and 31 Python checks. The new production case
compares borrowed non-Assassin options against the disabled full path, then
adds a stack-active Assassin type effect and verifies fallback/equality. The
existing controller/type differential matrix also covers a borrowed non-Assassin.

All 17 patches applied in order to the pinned upstream source and reproduced
51 managed source files. A fresh compile of the reconstructed helper produced
four class entries identical to the candidate jar; archive integrity passed,
with no diagnostic classes packaged. The full Maven reactor was not rerun.
There was no dedicated heap profile; the existing scope-release checks passed.
The runtime disable switch remains -Ddragonmind.disableStackCandidateEligibility=true.

The packaged-runner check and activation are recorded in
borrowed-subtype-measurements.json and borrowed-subtype-build-verification.json.
Accepted v14 remains available as dragonmind-v14-stack-eligibility.jar.
