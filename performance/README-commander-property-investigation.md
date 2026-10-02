# DragonMind: exact commander-property dispatch

2026-10-02. Comparison against accepted v12.

## Change under test

The original CardProperty dispatcher checks IsCommander near the end of a long
property chain. The candidate handles this exact property immediately after the
existing phasing gate and removes the old branch. It still reads the live card’s
commander marker. Game/LKI/controller setup remains in its original position.
Prepared-spell exclusion continues to run in Card.isValid before property checks.
No new state, cached result, source index, or decision shortcut is introduced.

The candidate is isolated from the working engine source and stable jar during
benchmarking. Two focused tests cover live commander changes, negation, ordinary
and explicitly requested phased-out properties, live versus LKI markers,
controller changes, and prepared-spell exile/command-zone behavior.

## Validation

43 optimization tests, 19 commander-pilot tests, 12 bridge tests and 31 Python
tests passed: 105 checks. The existing runtime-lifecycle test passed its four
checks as well. Java 17 compiled the two changed source files, including tests.
The full Maven build was not rerun. Candidate packaging contains the two freshly
compiled production entries for CardProperty; test and diagnostic classes are
excluded. The sampled trace comparisons and these tests do not establish
exhaustive Magic rules conformance. No new retained cache was introduced and
no fresh heap-retention audit was required or performed for this stateless edit.

An initial Python-created archive passed its immediate ZIP check but was later
unreadable by Java and Python. That candidate startup attempt failed before the
engine ran and supplies no game timing. The cause of the archive becoming
unreadable was not established. Repackaging by copying the accepted jar and
updating its production entries with Java’s jar tool passed integrity and class
byte checks and successfully launched all recorded candidate games.

## Benchmark protocol

Control/candidate/candidate/control order, two seeds per JVM, 20261011 followed
by 20261012. Java 17, 1536 MiB heap, Parallel GC, non-tiered compilation,
compile threshold 1000, disabled JVM performance data and headless mode.
Commander, GGS_Layered_v1/Jaymie_Ezio/Gabe_Food/Destyn_Turtles seat order,
stock Default AI, 180-second game limit. No concurrent games, profiling,
compilation, regression tests or archive/source verification runs occurred during
benchmark games. Lightweight source reads and report/patch writing took place.

## Assessment of optimization headroom

Recent source-collection and per-query syntax-preparation experiments did not
establish useful whole-game gains. That is evidence of diminishing returns for
those local changes, not a measured lower bound for the engine.

The corrected v12 diagnostic recorded about 14.566 instrumented seconds in
blocking search, and 41,426 live plus 35,776 hypothetical static rebuilds.
Inclusive parent/child timings overlap, and this is diagnostic data rather than
unprofiled elapsed time. It does identify much larger repeated-work targets than
individual property dispatches. Future work should first measure duplicate
forecast requests or repeated candidate reconstruction within one decision and
establish a safe reuse boundary. Reducing search effort changes policy behavior
and requires separate play-quality validation. No such architecture or policy
change is adopted here.

## Repeated unprofiled result

| Repetition | Seed | v12 seconds | Candidate seconds |
|---|---:|---:|---:|
| 1 | 20261011 | 25.549 | 25.209 |
| 1 | 20261012 | 50.243 | 46.875 |
| 2 | 20261011 | 26.360 | 24.352 |
| 2 | 20261012 | 48.369 | 49.010 |

Combined v12 time: 150.521 seconds. Candidate: 145.446 seconds. Observed
reduction: **3.37% (5.075 seconds)**. Three paired games were faster and one was
slower. Both paired repetitions matched all 2,146 tracked events, 4,292 total;
Jaymie won the first seed at logged turn 45 and Destyn the second at turn 44.
Two seeds with two repetitions each are a limited sample; this does not establish
statistical significance or general speedups across decks, boards or seeds.
Games still take tens of seconds.

**Decision: retain the small stateless change as v13, after packaged-runner
verification.** It removes proven dispatch work without storing or skipping
live game-state results. The 15-patch chain reproduces all 48 managed source
files. The old rejected static-source experiment’s v13 archive is preserved;
the new runtime is named dragonmind-v13-commander-property.jar.

This is additional small headroom, not evidence that property dispatch can make
full games instant. After this checkpoint, measure repeated blocking forecasts
and hypothetical candidate reconstruction to select a broader target. The
present change introduces neither architectural reuse nor search pruning.

## Activation

The packaged Python runner completed seed 20261011 with stock policy in 26.135
engine seconds / 31.666 runner wall seconds. All 1,043 tracked events matched
the v12 control. This is a packaging/integration check, not another paired
benchmark. Only after that check was dragonmind.jar replaced with the verified
v13 commander-property jar. Its bytes and SHA-256 match that archive exactly;
the v12 jar and rejected experimental jars remain preserved.
