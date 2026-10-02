# DragonMind: share discovery inside hypothetical-combat searches

October 1, 2026 (America/New_York). This pass targets repeated battlefield scans underneath attacker/blocker forecasts while keeping Forge's rules checks enabled.

## Result

| Complete four-player game | v5 control | v6 candidate | Observed reduction |
| --- | ---: | ---: | ---: |
| Seed 20261011, first game in process | 31.355 s | 30.803 s | 1.8% |
| Seed 20261012, second game in process | 69.646 s | 65.835 s | 5.5% |
| Both engine times combined | 101.001 s | 96.638 s | 4.3% |

All 2,146 compared turn, phase, stack-addition, stack-resolution, damage, life and combat events matched. Jaymie/Ezio won the first game on global turn 45; Destyn/Turtles won the second on global turn 44. These are two sequential games per executable, one paired observation per seed. The small first-game difference may include runtime noise; this is not a statistically established general speedup. The changes were measured together, not independently. No deck-strength or win-rate conclusion follows from these runs.

## Architecture change

Combat forecasts repeatedly compare attacker/blocker pairs. Power/toughness bonus prediction and first-strike destruction checks repeatedly assemble battlefield and command-zone traits while doing so.

The new lookup shares **possible source-card discovery**, using the existing read-only combat-inspection scope around candidate evaluation and attack/block searches:

- On the first request for a zone, one lazy scan identifies cards with static abilities and cards with triggers, retaining their original order.
- Subsequent forecast queries in that scope use those host lists rather than traversing every card again.
- Every query rereads the hosts' current trait collections. Mode checks, validity, parameters, trigger conditions, attacker/blocker state and predicted values remain live. Neither trait applicability nor a final combat result is cached.
- Existing mutation invalidation propagates through nested scopes. Added hooks cover intrinsic static/trigger additions, intrinsic static removal, keyword-instance trait additions, and zone changes, including reordering and forced clearing.
- A mutation causes the scope to fall back to the original full-zone scan. The lookup is thread-local and discarded when the enclosing search ends. It is not retained across actions or games.
- The diagnostic property `-Ddragonmind.disableCombatTraitIndex=true` disables this new host filtering for comparisons, without disabling a Magic rule. Outside a valid combat-inspection scope, queries use the original scan.

The patch also avoids building an empty trigger collection when a card has no intrinsic, split-state, changed or keyword-provided triggers. Keyword trigger presence is read live; only keyword membership iteration uses the already-existing mutation-tracked snapshot. Mutable trigger contents are not permanently cached.

This reduces repeated discovery *inside* combat searches. It does not eliminate entire hypothetical combats or memoize blocker assignments. Broad rules-sensitive static-layer recalculation remains in place.

## Verification

79 targeted checks passed: 25 performance/rules checks, 19 Commander-pilot checks, 12 bridge checks and 23 Python checks.

New checks exercise:

- Intrinsic, keyword-provided and changed triggers appearing after an empty lookup; changed triggers disappearing after removal.
- Ability additions inside nested scopes invalidating the enclosing host lookup.
- Direct zone removal and re-addition making host membership fresh.
- Live static parameter changes affecting predicted power immediately.
- Indexed and unindexed attacker/blocker power, toughness and destruction forecasts agreeing with ability consideration both enabled and disabled.
- Retained keyword-instance trigger additions and split-card trigger combination remaining visible.

These checks and two matching game traces are targeted regression evidence, not a universal rules-conformance proof. The scope's validity relies on read-only usage and its known mutation hooks; it is not a general persistent game-state cache.

The eight ordered patches reproduce all 33 checked source files exactly. The v6 delta changes ReplacementHandler, CardState, KeywordCollection, KeywordInstance, Zone, PlayerZone, ComputerUtilCombat and the performance regression test. The executable archive passed integrity verification and overlays 17 production classes onto v5. Tests and diagnostic code are excluded from the playing executable. The pinned upstream source and GPL attribution remain intact.

Changed Java classes were compiled against the accepted runtime and the targeted tests were run directly. A full Maven rebuild was not run here. The source build script applies all eight patches and runs the designated engine tests.

The packaged executable passed an end-to-end Python runner check: seed 20261011 completed in 32.786 seconds with Jaymie/Ezio winning, and all 1,043 tracked events matched the first control game. Runner metadata records the executable/deck hashes and exact command. This separate packaging check is not an additional paired speed estimate.

## Reproduction

Build from source with forge-fork/build_bridge.py. The new patch is forge-fork/dragonmind-combat-v6.patch, following dragonmind-discovery-v5.patch. The packaged executable is dragonmind-v6.jar.

The paired benchmark used Java 17, a 1536 MB heap, Parallel GC, -XX:-TieredCompilation, -XX:CompileThreshold=1000, headless mode, stock Default AI, unchanged deck order GGS/Jaymie/Gabe/Destyn, sequential seeds 20261011 and 20261012 in one process, and explicit 120-second game limits. Benchmarks ran sequentially; no other game simulation or profiler ran concurrently with them.

Raw logs are combat-control.log and combat-candidate.log in the working workspace; combat-measurements.json records times and trace equality. The patch, build integration and report are checkpointed locally. No GitHub upload was performed.

Full games still take tens of seconds. Instant fresh simulation has not been achieved. Remaining targets include repeated pairwise combat evaluation itself, expensive card-specific forecasts and static-layer work; further changes need measured gains and fresh-state guarantees.
