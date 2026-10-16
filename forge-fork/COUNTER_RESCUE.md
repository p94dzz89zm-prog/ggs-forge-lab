# Scoped counter-rescue safeguard

A constructed three-player combat reproduced a losing choice: an unblocked
3-power attacker was about to kill the pilot at 3 life. Another opponent
actually paid for Mortify targeting that attacker. The pilot then spent its
available Island and Swan Song to counter Mortify. The attacker survived and
actual combat damage reduced the pilot to 0. On the same incumbent build,
explicitly passing instead let Mortify remove the attacker and preserved 3 life.
This is a constructed mechanism check, not a replay or certification of an
entire natural game.

GgsCounterRescuePolicy adds a narrow public-state exception before ordinary
counterspell evaluation: for the opted-in GGS pilot, do not use Swan Song to
counter a single plain targeted Destroy spell on the otherwise singleton stack
when it targets an unblocked attacker aimed at the pilot that is individually
lethal by the current life-damage forecast. This only covers the blockers step.
No card definition, spell cost, target legality or resolution rule is changed.
Ordinary counterspell evaluation remains in force outside that boundary.

CounterRescueRegression contains 24 constructed checks: eight boundaries under
three bounded profiles. The original Mortify case must distinguish incumbent
and guarded decisions. Other removal variants can already be declined by stock
logic; those are parity checks, not automatically additional improvements.
Actual removal payments, target legality, stack resolution, resulting combat,
preserved hand card and untapped blue mana are asserted for rescue cases.

Build with build_counter_rescue.py over the pinned March-corrected executable.
The overlay preserves both earlier March targeting and combined-lethal ninjutsu
corrections. Only AiController and its generated helper, plus the new policy
class, are overlaid; private game/model/audit data are not source artifacts.

This is not a full multiplayer counterspell policy. Nonlethal cross-opponent
removal, combined attackers, trample/poison/commander damage, first/double strike,
death or replacement effects, other counterspells and complicated stacks need
further review. A tactical correction does not certify whole games or establish
general strength. Outcomes stay provisional until full evidence-bound review.
