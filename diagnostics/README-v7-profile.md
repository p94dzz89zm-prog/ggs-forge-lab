# v7 whole-process profile: next architectural targets

October 2, 2026. Java Flight Recorder profile of stock four-player seed 20261012 on packaged v7. Engine time: 68.330 seconds. All 1,103 tracked game events match the slower control seed. This is a diagnostic run, not a paired speed measurement.

The recording covers startup as well as the game. Of 4,784 execution samples, these inclusive stacks were observed:

| Path | Samples |
| --- | ---: |
| predictNextCombatsRemainingLife | 1,984 |
| assignBlockersForCombat | 1,779 |
| getAllPossibleAbilities / ComputerUtilAbility.getSpellAbilities | 1,636 |
| GameActionUtil.getAlternativeCosts | 1,450 |
| GameAction.checkStaticAbilities | 1,406 |
| canPlayAndPayFor | 1,316 |
| canPlaySa | 1,253 |

Counts overlap because stacks contain nested calls; they must not be added or presented as exclusive elapsed time. Collection add, addAll and construction were the three leading nearest-Forge frames (489, 357 and 298 hits respectively). Allocation sampling also points strongly to collection construction/copying and static-ability synthesis; sampled weights are estimates, not a heap-size measurement.

The next experiment should time complete decision boundaries, separating time spent in legal-ability generation, hypothetical board/combat evaluation, static-layer rebuilding and actual action resolution. Measure counts and exclusive/inclusive duration, and distinguish actual game-state mutations from repeated unchanged-state evaluations before attempting incremental recalculation. Continuous-effect dependencies, timestamp ordering, copied state, keyword synthesis and hypothetical-state rollback must remain correct.

The current evidence supports profiling repeated rebuilding before expanding combat-result caching. It does not establish that sub-second, general four-player Magic games are attainable, nor that a rewrite would outperform this engine. An event-driven, dependency-indexed rules engine and reusable read-only decision views are candidate designs, not demonstrated speedups.

Raw workspace recording: v7-whole-game.jfr. Analysis command: java -cp ggs-forge-lab/diagnostics JfrDecisionPaths v7-whole-game.jfr. Rules were not disabled. No external upload of the recording was performed.
