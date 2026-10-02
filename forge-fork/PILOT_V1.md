# Experimental GGS pilot v1: ninjutsu decisions

Your current GGS 100 is unchanged. This update changes how one explicitly named AI
seat evaluates and pays for ninjutsu. It is an experimental candidate, not a proven
stronger overall pilot or a learned model.

## Decisions changed

Stock Forge requires at least one unblocked attacker's mana value to be lower than
the incoming creature's. Its generic return-cost chooser independently picks the
lowest-power eligible creature. V1 uses the same scored attacker plan for both
activation and return payment. Timing, affordability, payment, targets, triggers,
and combat are still enforced by Forge.

The score accounts for predicted damage change, selected combat-trigger utility,
the cost of replaying a returned creature, activation mana, losing a token, and
returning GGS/Satoru Umezawa/Tetsuko. It values an additional GGS Dragon only when
GGS remains available (or the arriving creature has its ability) and a fresh
unblocked attacker does not already cover that player. Returning GGS itself does
not earn an imaginary Dragon. It preserves an already lethal attacker.

Creature types and public card identities are used. Opposing hand information is
limited to its count for discard/theft utility. Opposing hand contents and library
order are not read by this policy.

Clones conservatively avoid copying a returned creature and duplicating an owned
legend. The actual clone target remains selected by stock Forge. After first
strike, a creature with first strike only is not treated as able to deal normal
combat damage. Before damage, double-strike attackers are retained because the
heuristic does not forecast both damage batches.

## How to enable

Build the pinned patched Forge using `build_bridge.py`. The script now runs both
`BridgeEngineTest` and `GgsPilotTest`. Use a new checkout, because the build script
intentionally refuses to overwrite an existing source checkout.

Add this JVM property before `-jar` to change just the specified seat:

```sh
'-Dforge.ai.ggsPilotPlayer=Ai(1)-GGS_Current'
```

Leave it unset for stock strategy. Controller bridging/audit is independently
configurable. This property does not require an external controller.

The batch runner now offers `--pilot stock` or `--pilot ggs-v1`, records the pilot,
pins all opponents to Default AI profiles, and validates that the jar contains the
new policy before enabling it. `--audit` records per-match offline decision files.
Resume rejects a differing pilot/audit configuration. Seat rotations are handled
when constructing the property.

Example, using an installed directory containing the built jar and upstream `res`:

```sh
python run_games.py --engine /absolute/path/patched-forge \
  --variants GGS_Current --pilot ggs-v1 --audit --workers 1 \
  --games-per-variant 4 --seed 20261001 --timeout 300 \
  --output pilot-v1-check
```

Run stock and v1 into separate output directories with matching seeds and seats.
A shared initial seed does not guarantee identical later draws after decisions
and random-number consumption diverge.

## What was verified

The actual Forge card database and rules engine run the new positions. The tests
compare the stock refusal and the new acceptance of an equal-value draw upgrade,
check the returned creature through real cost payment, and resolve combat to
create a real GGS Dragon. Other checks cover same-player Dragon redundancy,
different defenders, preserving lethal/Balefire connections, first strike,
double strike, activation cost, legend conflicts, clone costs, and keeping GGS.
See `evidence/pilot-v1-tests.json` for executed tests and compiler/runtime details.

Two four-player prototype smoke attempts used Jaymie's supplied Ezio main deck
and the unchanged stock proxies for Gabe/Destyn. Both timed out at 150 seconds;
neither reached a new-policy ninjutsu decision. They provide no win-rate evidence.
These were before the final clone/commander guards and are labelled prototype runs.

Two-seat smoke comparisons are integration checks, not pod benchmarks. The first
prototype comparison changed a real Yuriko ninjutsu return choice; stock won its
run while the candidate lost its run. That is retained, not filtered out. The final
revision also completed both runs: stock GGS won its run and the candidate lost
its run; the candidate made one new-policy return payment. See `evidence/pilot-v1-summary.json` for outcomes
and `evidence/pilot-v1-smoke.tar.gz` for full logs, commands, hashes and audits.
Repeated runs of the same seed are not independent samples.

## Limits

The utility weights are explicit heuristics, not learned probabilities, and do not
prove that every accepted swap is optimal. Activation cost modifiers, future
interaction reserves, static ability suppression on arrival, all trigger types,
and multi-step extra-combat lines are not fully forecast. The policy intentionally
avoids ordinary swaps after damage; rescue/redeployment decisions remain future
work. This version changes neither general attack/block planning nor wipe recovery,
mulligans, removal timing, draw/discard selection, or the broader stock AI.

Keep stock as the default until comparable completed games and decision reviews
show whether the candidate helps overall. Do not use these smoke results to select
deck swaps. Rule legality and strategic quality are separate checks.

Forge-derived Java changes remain GPL-3.0, under COPYING. The standalone Python
runner/helpers remain covered by the lab's root MIT license.

## October 1 retry correction

The Infiltrator forecast now excludes other Ninjas with zero predicted combat damage or a planeswalker defender. Two new positions fail against the previous policy and pass after the change; all 26 engine tests pass. See `evidence/retry-cycle` and the root TRAINING_PROTOCOL.md for the assisted match, delegated-choice counts, suspected rules-script issue, and scheduling blocker. No overall-strength claim or deck change follows from this correction.
