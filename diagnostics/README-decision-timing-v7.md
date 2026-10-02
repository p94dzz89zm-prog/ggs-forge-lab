# Complete-decision timing and repeated stack simulations

October 2, 2026. Production runtime remains accepted v7; these changes build a separate diagnostic overlay and do not alter game decisions or disable rules.

## Findings

Two diagnostic runs of seed 20261012 completed. Their 1,103 tracked events each match the slower control game. The refined run completed in 67.711 seconds of engine time. Diagnostic overhead and runtime variation mean this is not a speedup measurement.

The refined timers distinguish method nesting, calling threads, hypothetical static rebuilding, live-state rebuilding, the stack-keyword simulation branch and restoration. Their scoped cleanup runs on returns and exceptions. The summary verifies that exclusive durations are nonnegative and sum to instrumented root durations **within the nested accounting model**. Roots on different threads can overlap; summing them does not produce whole-game elapsed time. The recording includes process setup, so reported method totals are not restricted to the game-time interval.

| Instrumented stage | Calls | Measured inclusive duration |
| --- | ---: | ---: |
| Choose action | 2,142 | 50.289 s |
| Discover abilities | 2,112 | 23.158 s |
| Candidate worker evaluation (root canPlayAndPayFor) | 18,005 | 19.756 s |
| Candidate-thread wait | 1,936 | 20.654 s |
| Block searches | 1,562 | 25.711 s |
| All hypothetical static rebuilds | 35,776 | 9.416 s |
| All live static rebuilds | 41,426 | 10.044 s |
| Stack-keyword rebuild wrapper | 34,671 | 9.049 s |
| Restore-live-state wrapper | 34,811 | 7.847 s |
| Ability resolution | 396 | 1.476 s |

Inclusive stages overlap. Candidate-thread waiting overlaps the worker's evaluation and is not another 20 seconds of independent computational work. Block searches are nested inside other forecasts. The two static rebuild categories are distinct; wrapper durations additionally include trivial instrumentation overhead.

During main-thread ability discovery, 34,156 stack-keyword simulations took 8.836 seconds inside checkStaticAbilities and 34,230 restorations took 7.665 seconds. Most of the approximately 19.46 seconds spent rebuilding static effects occurs while considering possible spells, rather than resolving selected spells.

## Concrete architectural target

GameActionUtil.getAlternativeCosts first asks GameAction.hasStaticAbilityAffectingZone(Stack, ABILITIES), a global existence check. If true, it creates a stack copy, rebuilds continuous effects, collects granted spell abilities, and rebuilds live state afterward. The existence check does not test whether the particular candidate spell can be affected. Scanning explicit card scripts in these deck lists identifies Ezio's Assassin/YouCtrl/wasCast freerunning grant as a source of this stack-ability path. Dynamic granted and copied abilities can also contribute; source inspection alone is not a per-call attribution counter.

The next implementation experiment should replace broad discovery with conservative candidate-specific source discovery, or isolate the hypothetical card evaluation and restoration from unrelated world reconstruction. It must retain a fallback when applicability depends on stack-zone changes, controller changes, type changes, characteristic-defining abilities, generated keywords, static-layer dependencies or changed faces. Evaluating current hand characteristics alone cannot prove that a future stack effect will be inapplicable. No broad rebuild was skipped in this pass.

This identifies a large repeated-work target but does not establish a 16.9-second obtainable speedup. Some rebuilds are necessary, and even eliminating all work in that branch would leave substantial combat search time.

## Tools

Build: `python3 diagnostics/build_decision_profile.py SOURCE_PATH V7_JAR_PATH OUTPUT_PATH`.

Run with the overlay classes before v7 on the classpath and `-Ddragonmind.decisionProfile=OUTPUT_CSV`. Use the existing stock pod benchmark flags. Summarize with `python3 diagnostics/summarize_decision_profile.py OUTPUT_CSV`.

The first diagnostic did not separate cross-thread waiting and reported an incorrectly named union duration. The refined summary explicitly reports the sum of per-thread root durations and warns about overlap. Use decision-profile-v7-separated.csv and decision-profile-v7-separated.log for this report. Unrefined data are retained only for investigation.

Source tools and these findings are checkpointed locally. No production speed improvement is claimed for adding instrumentation; no external upload was performed.
