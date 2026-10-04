# Cost-source discovery experiment: not adopted

The candidate shares an ordered, complete list of battlefield, stack and command
sources within an existing read-only combat forecast. It appends absent hosts
without replacing equal-ID live sources. Callers continue reading current
abilities, modes, amounts and conditions; no cost or affordability outcome is
cached. Scope invalidation and a dedicated disable switch retain the full path.

The candidate passed 114 engine checks, including new ordering, mutation,
phasing, face-down, nested-scope and virtual-host differential checks. However,
it produced no useful measured speed improvement, so v17 remains active. The
candidate patch is retained here as an experiment; the normal build driver does
not apply it.

## Repeated isolated comparison

| Run | Seed 20261011 | Seed 20261012 | Total |
|---|---:|---:|---:|
| Control 1 | 18.456 s | 31.393 s | 49.849 s |
| Candidate 1 | 18.848 s | 31.777 s | 50.625 s |
| Candidate 2 | 17.554 s | 30.990 s | 48.544 s |
| Control 2 | 17.936 s | 31.409 s | 49.345 s |

Control total: **99.194 seconds**; candidate total: **99.169 seconds**.
The 0.025-second difference is practically a tie and does not establish a gain.
All four runs matched the same 2,146 tracked events. This used the fixed Layered
pod, stock Default pilot, two seeds per JVM, ABBA order, Java 17, 1536 MiB heap,
Parallel GC, non-tiered compilation and threshold 1000. Audit and profiling were
off. There were no concurrent games, compilation, tests or archive verification
during these timed runs. Light source reads and report preparation occurred.

A separate commander-aware Apex seed-25 pair targeted the crowded case.
Control took **80.104 seconds** and candidate **81.167 seconds**. Both completed
without engine errors and matched all **1,650** tracked events and the full
phase-scoped combat inventory. A single pair is limited evidence, but it does
not support adopting the candidate either.

The full Maven reactor was not rerun. Focused compilation, source reconstruction
and package comparison are recorded separately. Complete benchmark logs and
candidate sources are retained in the saved experiment data. Numeric results,
tests and the unadopted source patch are published here; private game records
are excluded.
