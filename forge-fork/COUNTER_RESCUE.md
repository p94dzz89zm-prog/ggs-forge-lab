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
removal, complicated combined attackers, trample/poison/commander damage, first/double strike,
death or replacement effects, other counterspells and complicated stacks need
further review. A tactical correction does not certify whole games or establish
general strength. Outcomes stay provisional until full evidence-bound review.


CounterRescuePaymentRegression also executes both controller choices at three
life totals. It asserts actual blue-mana spending, stack resolution, attacker
survival/removal and resulting combat life. Six executions are three paired
constructed states, not six independent games or a whole-game approval.

Cycle8 reproduces another actual losing priority decision: at5 life, the
pilot pays Swan Song to counter Mortify on a3-power attacker, leaving that
attacker and a2-power companion to deal lethal damage. Letting Mortify resolve
preserves3 life. The new extension sums the current unblocked life-damage
batch and declines Swan Song only when that sum is lethal and removing the
target takes it below lethal. The extension declines to reason about blocked
attackers, other defenders, first/double strike or infect. The previous
individually lethal safeguard remains unchanged. No card rules are altered.

CombinedCounterRescueRegression exercises actual full-priority selection,
targeting, blue-mana payment, removal resolution and combat at three distinct
development positions under each of three profiles. Nine executions are
correlated profile repetitions of three positions. Five boundary checks retain
ordinary counter evaluation: nonlethal damage, another defender, a blocked
companion, remaining damage already lethal, and first strike. These boundary
checks compare decisions; they are not full resolution certificates.

Build with build_combined_counter.py over the pinned cycle7 candidate. Only
GgsCounterRescuePolicy.class changes; other engine entries remain byte-identical.
The experimental planner is still off by default and the day incumbent is not
automatically promoted. Fresh evaluation and full natural-game review remain
separate from these constructed checks.

Frozen constructed evaluation had four lethal combined-damage conditions and
two nonlethal controls. The corrected build survived all six; the previous
build survived only the two nonlethal controls and countered removal in all
six. An initial fixture assertion incorrectly treated a3-power Hill Giant
plus a2-power companion as lethal at6 life. That failed attempt was retained;
the oracle was corrected without changing the frozen policy, and the rerun
is explicitly a fixture retry, not an additional fresh sample.
