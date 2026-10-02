# DragonMind v12: affected-card selection breakdown

2026-10-02. Diagnostic investigation; production remains v12.

## Result

The isolated diagnostic game for seed 20261012 completed in 63.538 engine
seconds. Destyn won at logged turn 44. All 1,103 tracked Turn, Phase,
Add To Stack, Resolve Stack, Damage, Life and Combat events matched the
second game of the existing v12 static-source control exactly.

| Selection stage | Calls | Exclusive instrumented seconds |
|---|---:|---:|
| Validity predicates | 981,973 | 4.790395 |
| Zone assembly | 981,973 | 0.771081 |
| Hypothetical-card selection | 981,973 | 0.224436 |
| Defined-card selection | 981,973 | 0.149154 |
| Shaman’s Trance guard | 981,973 | 0.054890 |
| Ignore-card removal | 981,973 | 0.043921 |
| Union assembly | 981,973 | 0.037876 |
| Shaman’s Trance add-back | 981,973 | 0.026803 |

The full affected-card method ran 1,135,910 times, including characteristic
-defining early returns; the general path ran 981,973 times. Validity checks
are the largest measured substage. The next investigation should distinguish
restriction parsing and individual card-property predicates before proposing
an optimization. No eligibility result cache or skipped rebuild is justified
by this profile.

## Validation and interpretation

The diagnostic overlay compiled on Java 17. The standalone
`--affected-internals` option now also enables its enclosing static timers,
and that invocation compiled successfully. The nested timing summarizer
verified nonnegative exclusive times and exact root/exclusive accounting.
Profiling adds overhead, including almost one million scopes per general
substage. Durations are diagnostic, not unprofiled speed comparisons.
Inclusive parent/child timings and cross-thread roots overlap.

No production source or jar changed. Full engine regression tests were not
rerun for this diagnostic-only change. The earlier v12 validation remains the
production evidence; sampled trace equality is not exhaustive rules certification.

## Reproduction

Build from the restored v12 source checkpoint:

```bash
python3 diagnostics/build_decision_profile.py SOURCE V12_JAR OUTPUT --affected-internals
```

Run the game from the resource directory with OUTPUT/classes before V12_JAR
on the classpath, main class `forge.view.Main`, and
`-Ddragonmind.decisionProfile=PROFILE.csv`. Use 1536 MiB heap, Parallel GC,
non-tiered compilation, compile threshold 1000, disabled JVM performance data,
headless mode, stock Default AI profiles, Commander format, seat rotation zero,
seed 20261012 and a 180-second game limit. Deck order: GGS_Layered_v1,
Jaymie_Ezio, Gabe_Food, Destyn_Turtles. Summarize with
`python3 diagnostics/summarize_decision_profile.py PROFILE.csv`.

Machine-readable totals: `diagnostics/affected-internals-v12-summary.json`.
Raw CSV and game log are retained under the current diagnostic workspace;
only the summary is committed.
