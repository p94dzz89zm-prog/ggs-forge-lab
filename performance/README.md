# DragonMind performance update

October 1, 2026

DragonMind is the name of our Commander simulation and AI layer. It remains a Forge 2.0.15 fork using Forge's full rules engine; GPL attribution and licensing are preserved. Source package names and the existing repository directory remain compatible.

## Measured performance

Same layered GGS deck, opponents, seed 20261011, and seat order:

| Configuration | Engine game time |
| --- | ---: |
| Previous executable, unprofiled | 46.199 seconds |
| Optimized executable, first game | 39.499 seconds |
| Optimized executable, loaded engine | 34.787 seconds |
| Optimized executable, commander-aware policy | 38.107 seconds |

The first three games had the same winner (Jaymie/Ezio), final global turn (45), and 1,043 identical compared turn, phase, cast, resolution, damage, life, and combat events. The commander-aware run verifies that policy and the new runner execute together; it is not included in the stock-policy equivalence comparison. Its full process took 44.046 seconds, including loading.

The optimized cold run is about 14.5% faster; the warm run about 24.7% faster than the unprofiled baseline. These are individual observations from one completed seed, not statistically established general speedups. Profiling itself added overhead: the profiled baseline took 51.858 seconds and is excluded from percentage comparisons. The prior 37-minute guided game included hundreds of external decision waits and was not a throughput benchmark.

Seed 20261012 remained incomplete after 90 seconds under unattended stock play. It is recorded as a timeout with no winner. We have not achieved seconds-to-instant full games across this pod.

## Changes

1. Added an unattended batch entry point, `dragonmind.py`, and the `dragonmind.jar` executable name. Multiple independent seeds run in one loaded JVM, with a fresh match and reset RNG for each game. Additional JVM workers isolate Forge's global RNG.
2. Avoided expensive turn-direction/static-source scans when a continuous effect's inclusive restrictions cannot possibly match a player. Player, Opponent, You, and Any restrictions retain their existing behavior.
3. Cached keyword membership during repeated trait application. Mutable keyword traits are read fresh. Membership changes invalidate the cache; exposing a live collection view disables caching so later edits through that view stay visible.
4. Removed the 100 ms presentation sleep for mulligans in games marked as having no GUI user. Interactive GUI games keep the delay.
5. Added structured per-seed results, explicit timeout/error classifications, and batch abortion after failure. Failed games do not receive forced game-over results that could fabricate winners. Unattempted remaining seeds are labeled not run.
6. Kept expensive private audit recording opt-in. Full game logs remain available; no card resolution or strategic search was dropped to manufacture faster numbers.

## Validation

- 19 commander-aware pilot tests passed on the optimized classpath.
- 12 bridge engine tests passed on the optimized classpath.
- Four new performance regressions passed, covering membership changes, mutable traits, retained collection views, iterator removal, and player targeting.
- 20 Python runner/comparison tests passed, including duplicate/missing results, timeout false winners, and swallowed AI exceptions.
- All three ordered patches recreate the exact modified source: 18 files checked.
- Final executable archive integrity passed.
- End-to-end commander-aware runner completed one game.
- Forced one-second timeout emitted one timeout and left the next seed not run, with no fabricated Game Outcome or Game Result.

An initial packaging smoke attempt failed with a corrupt archive and produced no game; it is retained as a process error and excluded. The rebuilt, integrity-checked executable passed the later runner check. The final timeout-output correction was verified separately; it does not change completed-game timing.

## Reproduce

From the existing project:

```sh
python3 forge-fork/build_bridge.py /absolute/path/new-dragonmind-source
python3 dragonmind.py --engine /absolute/path/new-dragonmind-source/forge-gui --jar /absolute/path/new-dragonmind-source/forge-gui-desktop/target/dragonmind.jar --seeds 4 --batch-size 4 --workers 1
```

The build verifies the pinned Forge commit, applies the bridge, commander-identity, and performance patches in order, runs targeted tests, and packages the executable. Java 17+, Maven, Python, and Forge resources are required. The packaged executable alone does not contain the entire resource database.

The new runner defaults to commander-aware ninjutsu; use `--stock` for baseline comparisons. Use a new output directory for each run to preserve previous results. Increasing workers improves batch throughput when CPU and memory permit; it does not automatically accelerate each individual game.

## Remaining work

The profiler showed substantial additional cost in rebuilding static and replacement traits, card filtering, and AI evaluation. Those remain the main targets for further measured optimization. A general rules cache needs reliable invalidation when copies, continuous effects, zones, or keywords change; skipping those checks would undermine the deck comparisons. Broader commander inference and difficult-game loop handling are also incomplete. DragonMind's independent AI is still a narrow improvement over Forge's stock pilot, not four fully general language-model agents inside the simulator.
