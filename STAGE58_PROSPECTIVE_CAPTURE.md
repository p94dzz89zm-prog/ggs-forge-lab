# Stage58: prospective setup capture and independent RNG/permutation checks

The exact Stage57 native base2acaeed is extended with opt-in offline observers,
enabled by `-Ddragonmind.prospectiveOpening=/private/opening.jsonl`. The observers
record actual initial starting-player determination and choice, each library
before shuffle, its generated permutation before controller handling, the final
library, consumed RNG bits, mulligan declarations, bottom choices and before/
after mulligan-service state. Existing game execution and policy logic remain
in place; unrelated archive entries are byte-identical. Omniscient evidence is
never supplied to a pilot or training dataset.

Two completed **constructed capture fixtures**, standard and house, use seed58,
the actual starting-player determination and actual MulliganService. The fixture
decks deliberately contain duplicate Runeclaw Bears and are illegal Commander
decks. These are not natural games, legal opening certifications or gameplay
performance results. Both stock policies keep the initial hand; this stage's
capture fixtures do not exercise redraws. Stage57 full-service controls cover
redraw/bottom behavior separately; general independent redraw-state derivation
is still pending.

The Python reader does not call the simulator. It recomputes the Java48-bit LCG,
bounded nextInt including rejection sampling, descending Fisher-Yates swaps,
initial four-seat random chooser, starting-player response, exact library tails,
unordered seven-card opening-hand membership and recorded object conservation.
Each fixture independently matches393 RNG requests,4shuffle permutations and
4opening hands, with starting player2. Across both fixtures,8mutations of RNG,
generated permutation, starting-player result and opening-hand membership reject.
This is scoped mathematical/setup verification, not approval of game actions.

The snapshots contain400 deck-card objects and4 auxiliary Commander Effect
objects. Forge's Flashback playable view repeats references to physical-zone
cards; the reader validates these references without counting another location.
Unknown nonempty auxiliary zones fail closed. The first reader rejected those
virtual duplicates; its failure is preserved, followed by the reviewed fix and
regression controls. Hand ordering is not a rules constraint; library order is.

Three native fixture JVMs ran: the first produced intact partial streams but
failed finalization because its fixture result omitted the writer's status key.
That partial attempt was preserved. Two fresh completed fixture streams passed
with explicit `completed_fixture` status and `fixture_only=true`; neither is a
completed game. An initial compiler-loader failure is also preserved.415Python
tests pass (407baseline); eight new tests cover the independent mathematics,
virtual-reference handling and certification gate.

## Separate certification tracks

Historical games2026202028/2026202029/2026202030 remain uncertifiable from the
currently reviewed capture: historical card-data/setup provenance and missing
opening obligations remain unresolved;2026202029 additionally retains its
confirmed illegal mulligan ordering. Original evidence is preserved. Authentic
future recovery can add proof but must not invent missing observations.

Prospective capture now has a working native setup observer and independent
scoped reader. `prospective_certification.gate` lists the remaining obligations
and refuses full-certification launch. It cannot be opened with caller-supplied
pass flags. Missing canonical deck/reference binding, full opening pregame/
first-turn derivation, complete engine-generated legal-action alternatives and
general independent action/effect/SBA/terminal derivation remain explicit.
Partial existing referee capture does not meet those requirements.

No fresh natural game was launched under an incomplete protocol. New fully
instrumented natural games0, complete-game certifications0, approved game
actions0, strategic training0. Original replay466choices and1790/1985conditional
support remain unchanged; Stage47/48 are untouched.

Build and audit with preserved resources and private transcripts:

```
python3 forge-fork/build_prospective_opening.py --base /runtime/integrated.jar --output /fresh/opening.jar
python3 prospective_opening_audit.py /private/opening.jsonl --seed 58
```

The native fixture source and exact JVM flags, raw outputs, receipts, failed
attempts and independent results are checkpointed. Next: bind canonical legal
decks and frozen references into a launch manifest, derive redraw/bottom state
transitions independently, capture legal alternatives and the complete pregame/
first-turn boundary, then allocate a fresh natural-game seed after preflight.
