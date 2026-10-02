# DragonMind: conservative stack-effect discovery

**Retired in v9:** a subsequent diagnostic game had exactly the same hypothetical stack-rebuild counts as the v7 diagnostic. The apparent small timing gain below did not establish a reduction in that work. v9 removes this conservative stack filter and its extra world scan; the v8 measurement is retained as historical evidence, including its noise caveat.

October 2, 2026. Candidate v8 narrows repeated hypothetical stack rebuilding while preserving the full calculation whenever applicability is uncertain.

| Complete four-player game | v7 control | v8 candidate |
| --- | ---: | ---: |
| Seed 20261011 | 29.907 s | 29.623 s |
| Seed 20261012 | 59.524 s | 57.693 s |
| Combined engine time | 89.431 s | 87.316 s |

The observed combined reduction is **2.36%**. All **2,146** tracked turn, phase, stack, combat, damage and life events match in order. Jaymie/Ezio won the first seed and Destyn/Turtles the second. This is one paired observation per seed; differences this small can include runtime noise and are not a statistically established general speedup. The first game is essentially unchanged. Fresh games remain far from instant.

## What changed

Alternative-cost discovery previously entered a full hypothetical stack simulation whenever any currently applicable continuous effect could grant abilities on the stack. This is broad enough to run for other players' spells when Ezio's controller-restricted freerunning effect is present.

The new check rejects a stack simulation only when potential grants are demonstrably restricted to another controller and the world has no relevant uncertainty. It makes fresh queries rather than caching final applicability, spell types, costs or game-state results.

The original calculation remains for borrowed spells, last-known-information copies, grants belonging to the candidate's controller, characteristic-defining behavior, uncertain or unrestricted validity branches, and special MayPlay handling. A no-effect result from the original existence check is preserved.

Before rejecting a simulation, the check traverses the same world as a rebuild, including hand/library cards and hidden static traits. It considers inactive effects that might become active after a hypothetical cast. Control, copy and text layers, uncertain generated statics, shared/gained abilities and unknown generated variables force fallback. Defined-card selection is checked separately because it can bypass ordinary affected-zone filtering.

Only a narrow whitelist of harmless combat/protection changes, simple generated battlefield bonuses and the literal MustBeBlocked combat directive can pass these uncertainty guards. Generated definitions are read live from script data without constructing new traits or advancing IDs. Unknown definitions retain the rebuild. The diagnostic property `dragonmind.disableStackCandidateFilter=true` restores the original broad discovery.

This does not replace the rules engine with a faster approximation. It avoids entering a calculation in restricted cases that cannot produce a relevant grant. The all-world safeguard scan has its own cost and the conservative fallbacks limit the obtainable gain.

## Verification

**88 targeted checks passed:** 34 performance/rules checks, 19 Commander-pilot checks, 12 bridge checks and 23 Python checks.

New cases cover own versus opposing spells, borrowed and copied hosts, live controller changes, validity disjunctions, MayPlay fallbacks, inactive control/text effects, off-board hazards, defined-card selection, changing generated static definitions and generated variables. An own Assassin retains the same freerunning alternatives as the unfiltered calculation. Alternative-cost signatures match the original path for both an own Assassin and an opposing creature.

These checks and two matching game traces are targeted evidence, not universal rules-conformance certification. The narrowly supported cases are deliberate; broader type/controller prediction needs additional rules work and measurement.

The ten ordered patches reproduce **35 checked source files** byte-for-byte. The v8 delta changes GameAction, GameActionUtil and the performance tests. The executable archive passed integrity verification and overlays **4 production classes** onto v7; tests and profiling classes are excluded. Changed Java classes were compiled against the accepted runtime, and targeted tests were run directly. A full Maven rebuild was not run. The source build script applies all ten patches and runs designated engine tests. Upstream attribution remains intact.

## Reproduction

The new patch is `forge-fork/dragonmind-stack-v8.patch`, following the v7 defensive discovery patch. Build from pinned upstream using `forge-fork/build_bridge.py`.

The paired benchmark used Java 17, 1536 MB heap, Parallel GC, `-XX:-TieredCompilation`, `-XX:CompileThreshold=1000`, headless mode, stock Default AI, unchanged GGS/Jaymie/Gabe/Destyn deck order, sequential seeds 20261011 and 20261012 and 120-second game limits. Games ran sequentially without concurrent simulations, test suites or profilers. Raw logs are `stack-control.log` and `stack-candidate.log`; `stack-measurements.json` retains the times and trace comparison.

The source changes, tests and this report are checkpointed locally. No GitHub upload was performed. The larger remaining architectural target is repeated hypothetical board and combat reconstruction; this filter alone does not approach sub-second games.

The packaged v8 executable completed its end-to-end runner check in 27.454 seconds of engine time; all 1,043 tracked events match the first control game. Runner metadata retains executable/deck hashes and the command. This is a separate packaging check, not another paired speed estimate. The stable `dragonmind.jar` now uses v8, with earlier executables retained.
