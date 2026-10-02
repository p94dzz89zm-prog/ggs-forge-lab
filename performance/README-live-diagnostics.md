# DragonMind live bottleneck diagnosis

October 1, 2026 (America/New_York). A fresh four-player game was run with Java Flight Recorder after the streaming interruption. The goal remains faster fresh games while preserving rules checks and competent Commander play.

## What the live run establishes

The profile contains 2,441 execution samples, 2,432 with at least one Forge frame. Sampling covers JVM startup and gameplay. The table counts samples containing each named method anywhere in the captured stack, once per sample. These are inclusive, overlapping CPU-location indicators, **not elapsed seconds or percentages**; do not add them. Stack truncation and sampling frequency also limit precision.

| Path | Inclusive sample hits |
| --- | ---: |
| AI ability enumeration / Card.getAllPossibleAbilities | 830 |
| Alternative-cost discovery, GameActionUtil.getAlternativeCosts | 689 |
| Candidate evaluation, AiController.canPlayAndPayFor | 655 |
| Static-ability recalculation, GameAction.checkStaticAbilities | 654 |
| Card-specific heuristics, AiController.canPlaySa | 565 |
| Hypothetical combat prediction | 520 |
| Blocker searches, including hypothetical ones | 421 |
| Replacement-effect queries | 380 |
| Attacker searches, including hypothetical ones | 378 |
| Board-position evaluation | 181 |
| Actual attacker-declaration controller entry point | 173 |
| Static alternative-cost helper alone | 127 |

The distinction matters: optimizing the static alternative-cost helper alone addresses a smaller part of discovery than optimizing the full discovery pipeline. Likewise, combat searches run inside other decisions; actual declaration entry points do not account for all combat computation.

The leading nearest-Forge leaf frames were CardState.getStaticAbilities (218 hits), FCollection.add (205), CardType.hasSubtype (147), FCollection construction (74), and FCollection.addAll (74). Prominent stack paths included:

- Replacement queries repeatedly retrieving card replacement traits and checking special card types such as Saga.
- Static recalculation collecting static traits from cards across the game.
- Alternative-cost discovery building and copying source-card collections before checking abilities.
- Validity filtering constructing additional card collections.

Sampled allocation weights also pointed at FCollection construction, addition and iteration, Card.getName, and Card.updateStaticAbilities. Allocation weights are estimates attributed to captured stacks; they are not exact allocation counts, retained memory, or proof that removing a particular method will save that amount.

The concrete next architectural target is reducing repeated **source/trait collection construction within a well-defined query**, while keeping alternative hosts, card state, active zones, conditions and replacement eligibility fresh. Full static recalculation is invoked for rules-sensitive alternate-host checks (including CR 601.3e); bypassing it wholesale would risk incorrect options. Hypothetical combat remains a second major target, especially repeated blocker and board forecasts within candidate evaluation.

## Runtime and correctness evidence

This diagnostic game used stock Default AI, GGS/Jaymie/Gabe/Destyn seat order, seed 20261011, Commander format, explicit 120-second limit, Java 17, 1536 MB heap, Parallel GC, and throughput compilation settings. Forge's rules-skipping performance mode remained disabled.

The game body finished in 34.687 seconds under profiling. This is a diagnostic runtime, not an uninstrumented speed benchmark or a comparison with the earlier trials. JVM startup and card-database loading are additional process work.

Jaymie/Ezio won. All 1,043 tracked turn, phase, stack-addition, stack-resolution, damage, life and combat events matched the available v3 baseline log for this seed. That is targeted trace equivalence, not universal Magic rules certification or a deck win-rate estimate.

Thread-parking measurements also illustrate why waits cannot simply be removed: the timeout supervisor parked for about 34.6 seconds while the game ran, and AI ranking/awaiting parked for about 7.5 seconds while workers evaluated candidates. These times overlap work on other threads; they are not independent delays to add to game time.

## Interruption recovery

The interruption restored an older local checkpoint at db09d05. The prior accepted v4 commit, raw v4/v5 logs, and diagnostic source files were absent. The saved v4 report remained available. The accepted v4 architecture was reconstructed from the documented design and current v3 source, rather than presented as a byte-for-byte recovery of the unavailable commit.

Recovered behavior includes a lazy, thread-local replacement-source index for DamageDone, Tap, Untap and ProduceMana, bounded by candidate evaluation and attack/block searches. It stores host membership only, checks conditions on every query, propagates invalidation through nested scopes, and falls back to full lookup after known mutations. Card-counter setter hooks cover newly created shield-counter replacement effects.

The recovered six-patch chain reproduces all 28 checked current source files exactly. The reconstructed patch and build integration are committed locally. The executable archive passed integrity checking and contains 22 overlaid production classes; the diagnostic reader and tests are excluded.

Fresh verification: 18 performance/rules checks, 19 Commander-pilot checks, 12 bridge checks, and 23 Python checks passed (72 total). The recovered regression includes replacement already-run flags, nested effect addition, zone departure, and shield-counter membership. The fresh profiled game is additional end-to-end evidence. A full Maven rebuild and a new paired uninstrumented performance benchmark were not run during this recovery.

Before the interruption, three candidate experiments were observed to fail to improve combined two-game runtime reliably: a damage-modifier lookup candidate, a wider combat scope, and a static-ability source index. Their raw logs are now absent, so those observations are not claimed as newly reproduced results. None of those candidates is included in the recovered playing executable.

## Reproduce the diagnosis

Build the recovered engine with forge-fork/build_bridge.py. Run it from the directory containing Forge's res assets, adding Java Flight Recorder's StartFlightRecording option with settings=profile and dumponexit=true. Keep deck order, seeds, AI profiles, JVM flags and explicit timeout fixed.

Compile diagnostics/JfrDecisionPaths.java with Java 17 and pass the resulting JFR recording to JfrDecisionPaths. It prints nearest Forge frames, sampled stack paths, inclusive decision-method hits, and sampled allocation weights. Profiling is separate from production behavior.

The raw recording and game log are available locally as resumed-diagnostics.jfr and resumed-diagnostics.log. The sampling reader is reusable in the project. Seconds-to-instant full games have **not** been achieved.
