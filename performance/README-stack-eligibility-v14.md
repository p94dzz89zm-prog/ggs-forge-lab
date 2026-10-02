# DragonMind: scoped stack-grant eligibility (v14)

October 2, 2026. An isolated shadow prototype followed by an actual-skipping
candidate compared with accepted v13. The shadow result selected a real
reconstruction target; unprofiled games then measured the net effect of excluding
those rebuilds, including the new inspection overhead.

## Result

| Repetition | Seed | v13 seconds | v14 seconds |
|---|---:|---:|---:|
| 1 | 20261011 | 25.733 | 24.771 |
| 1 | 20261012 | 51.303 | 43.538 |
| 2 | 20261011 | 25.382 | 25.828 |
| 2 | 20261012 | 48.081 | 45.810 |

Combined control: **150.499 seconds**. Candidate: **139.947 seconds**.
Observed reduction: **7.01% (10.552 seconds)**. Three paired games were faster
and one was slower. Improvement was concentrated in the longer seed. Both paired
repetitions matched all 2,146 tracked events: 4,292 matching candidate events.
Two seeds and two repetitions are limited evidence, not statistical significance
or an engine-wide speed guarantee. Games still take tens of seconds.

The Java 17 benchmark ran control/candidate/candidate/control, with seeds
20261011 then 20261012 per JVM. Commander, GGS_Layered_v1 / Jaymie_Ezio /
Gabe_Food / Destyn_Turtles, Default AI, 180-second limits, 1536 MiB heap,
Parallel GC, non-tiered compilation, threshold 1000, disabled JVM performance
data and headless mode. No concurrent games, diagnostic counters, compilation,
regression suites or archive/source verification ran during these eight games.
Light source reads and report/test preparation occurred.

## What changed

Ezio's freerunning effect makes the existing broad stack-zone guard true for
many spell candidates. The new eligibility inspection recognizes the exact
literal grant script (Card.Assassin+YouCtrl+wasCast, stack zone, Freerunning:B B).
It excludes a rebuild only when all recognized grants reject the candidate by
controller or subtype, and the fresh source inspection finds no relevant
uncertainty. Other grant shapes retain the original full reconstruction.

The source walk includes visible and hidden static traits across the world.
Only the candidate moves to the stack in this hypothetical operation: a different
source in a fixed inactive zone cannot become battlefield-active through that
zone move. Candidate sources that may activate on the stack are retained.
Suppression and activation conditions are not used to exclude sources.

The inspection distinguishes simple local Self/Equipped/Enchanted effects from
potential stack grants. It checks the actual current recipient on every query.
Only whitelisted local changes and passive generated triggers qualify; unknown
scripts, ability rewrites, copy/control/text effects, uncertain type changes,
unknown generated statics/variables/keywords, static commands, and masked or
removed source traits retain the original path. Compound characteristic effects
cannot hide generated abilities behind a self-only type classification.

A compact parsed-metadata index lives only inside the outer spell-discovery
scope. Each lookup rereads the world, source zones, controller/type/attachment
state, parameter maps and layers. Metadata reuse requires matching maps and
layers; definitions referenced through generated SVars are inspected again.
There is no persistent source membership or final spell-option cache. Nested
scopes share the index; ordinary and exceptional outer exits remove it. Direct
queries outside a discovery scope do not retain metadata. No search pruning or
pilot policy change is introduced. Disable the exclusion with
-Ddragonmind.disableStackCandidateEligibility=true.

This is a first structural exclusion, not a long-lived event-driven dependency
index. It deliberately pays for fresh membership inspection to avoid relying on
incomplete global invalidation hooks. The observed timings include that cost.

## Shadow and regression validation

The final shadow overlay still ran every original rebuild. Across the two seeds
it predicted 17,633 exclusions out of 48,580 rebuilds (**36.3%**). Every predicted
exclusion added zero spell options; no productive rebuild was missed, and no
query was incomplete. Both shadow games matched all 2,146 tracked events.
The aggregate time fields include shadow inspection overhead and are not saved
wall time. The shadow counters are excluded from the packaged candidate.

23 focused shadow checks passed. The actual-skipping candidate passed 25 focused
checks, 43 existing performance checks, 19 pilot checks, 12 bridge checks and
four lifecycle checks: **103 engine checks**, plus **31 Python checks**. Additional
cases compare exclusion-enabled options directly with disabled full rebuilding
across controllers and type changes, and verify reference cleanup on nested and
exceptional scope exits. These tests and sampled traces do not establish
exhaustive Magic rules conformance. A full Maven build was not rerun.

The sixteen ordered patches reproduce all **51 managed source files** from
pinned upstream. Fresh Java compilation matches the eight packaged production
class entries byte-for-byte. The archive passed integrity checks; it contains
no new diagnostic or test classes. The existing v13 archive is preserved.

## Reproduction and evidence

forge-fork/build_bridge.py applies dragonmind-stack-eligibility-v14.patch last
and includes StackCandidateEligibilityTest in its Maven test selection.
Use diagnostics/build_stack_eligibility_profile.py with SOURCE, accepted v13 JAR
and OUTPUT arguments for the shadow overlay, classes before the jar on the
classpath, and -Ddragonmind.stackEligibilityProfile=OUTPUT.csv.

Use diagnostics/benchmark_stack_eligibility.py with accepted JAR, candidate JAR,
deck directory, Forge resource directory, a trace-matched two-seed v13 reference
log, and output directory. It runs the ABBA sequence and stops on a trace mismatch.
Tracked categories are Turn, Phase, Add To Stack, Resolve Stack, Damage, Combat
and Life. Full engine-state equivalence is not claimed from those categories.

CSV counters, source examples, measurement/log hashes and build metadata are
retained with this checkpoint. The v14 change demonstrates additional modest
headroom in this pod; it does not establish that micro-optimizations or repeated
reconstruction can make arbitrary Commander games instantaneous.

## Activation

The packaged Python runner completed stock seed 20261011 in 23.506 engine seconds
/ 28.72 runner wall seconds. All 1,043 tracked events matched the accepted control.
This is an integration check, not another paired performance observation. Only
after that check was dragonmind.jar atomically replaced with the verified v14
archive. Its SHA-256 matches dragonmind-v14-stack-eligibility.jar; the v13 archive
remains preserved. All 51 managed working-source files match the reconstructed
sixteen-patch chain. No dedicated heap profile was run; targeted scope lifecycle
checks verify metadata references are removed on ordinary, nested and exceptional
outer-scope exits.

**Decision: retain v14.** The measured benefit is modest and workload-dependent.
Future changes should be selected from fresh profiling rather than assuming this
eligibility check removes all hypothetical reconstruction cost.
