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

## Counter-family extension and recovery boundary

Cycle9 reproduces the same losing choice with An Offer You Can't Refuse
(present in the archived GGS list) and Counterspell (a constructed control).
The safeguard now includes those two tested unconditional counters as well as
Swan Song. It remains selected-pilot-only and retains the prior timing,
targeted-removal and ordinary combined-damage boundaries. Other counterspell
effects and complicated stacks retain stock evaluation; this is not a generic
counterspell solver.

CounterFamilyRegression contains28 groups: three development positions under
three profiles for each of the two added cards, plus five boundary decisions
for each card. The positive cases use actual full-priority selection, colored
payment, resolution and combat. They also assert that a paid Offer creates
two Treasures for the removal caster, and a paid Counterspell taps two Islands.
The corrected policy preserves the saving removal and its own counter/mana.
Profile repetitions are correlated cases, not independent games. The existing
CounterRescueRegression Counterspell case is now a positive rescue assertion
rather than an intentionally unsupported boundary; its actual removal/combat
checks remain enabled.

Build with build_counter_family.py over the recovered defense executable
SHA256 e9ebc23c353706d2e1d1a8e66a38bf16b54996a0881a5449bca005415daadb2f.
Only GgsCounterRescuePolicy.class changes. To reconstruct the historical
cycle8 two-step build, use the source at7dadd311d07789894cd502201cdc7a9902e0c4b3;
its earlier build scripts refer to that version's policy, not the new family.

Cycle8 raw game/audit logs were not confirmed saved before workspace pruning.
Its reported constructed observations above are historical, not a recoverable
full-game certificate. The final19-suite/natural evaluation completion remains
unknown and its reserved conditions must not be replayed as fresh. Cycle9
recovered the prepared public source tree and repeated the two mechanisms,
saving those logs and exact rebuilt executables before additional work.

## Ordinary blocked-trample rescue

Cycle10 reproduces a remaining losing choice with all three supported counters:
at5 life, Colossal Dreadmaw is blocked by Memnite and another2-power attacker
is unblocked. A third player pays Mortify on Dreadmaw. The pilot counters it,
then takes5 trample damage plus2 from the other attacker and ends at-2.
Explicitly letting the paid removal resolve leaves3 life. The current repair
replaces that manual intervention with the actual priority controller's pass.

The public life-damage forecast now includes ordinary blocked trample using
the engine's blocker shield and damage-prediction helpers. Combined damage is
summed only for the selected defender; attacks at other players cannot provide
missing lethal damage. Plain blocked nontrampling attackers contribute zero.
Blocked first/double strike, infect, deathtouch and first/double-strike blockers
remain unsupported; complex prevention/replacement/commander/poison/death-effect
lines still need review. No card definition, cost or combat rule is changed.

TrampleCounterRescueRegression has66 groups:45 profile/life-boundary positive
executions, three additional mixed-defender positives and18 boundary decisions.
The positive cases execute full priority, colored payments, Offer Treasures,
paid removal, legal initialized blocks and actual combat damage. Controls keep
ordinary evaluation for nonlethal damage, no trample, another defender, attacker
first strike, blocker first strike and remaining damage already lethal. These
are selected constructed cases with correlated profile repetitions, not games.

build_counter_trample.py overlays only GgsCounterRescuePolicy.class on the
verified cycle9 a2e981 executable and verifies all other entries byte-for-byte.
The default incumbent and outcome-admission requirements remain unchanged.

## Cycle11 single-blocker strike extension

The cycle10 exclusions above left a reproduced losing decision in three
constructed mechanisms: first-strike trampler, double-strike trampler, and
first-strike blocker. Actual countering died in nine card/mechanism executions;
explicit passes survived. Cycle11 extends only a single-blocker trample forecast.
It retains the blocker's full current lethal-damage shield in each damage step,
so double strike deliberately undercounts spill when the blocker dies early.
An attacker that can die to the blocker's first-strike damage gets no later-step
forecast. Multi-blocker strike, infect, deathtouch and wither blockers retain
stock evaluation. Trigger-driven changes, prevention and replacement effects,
regeneration, poison and commander loss still require broader review.

StrikeCounterRescueRegression checks actual automatic priority, legal payment,
Offer's Treasures, paid removal and both damage steps, plus nonlethal and lethal
first-strike-blocker boundaries. The two formerly unsupported strike assertions
in TrampleCounterRescueRegression now require the saving pass; all other
ordinary scenarios remain present. These are correlated constructed checks.
Fresh frozen evaluation is required separately; a passing regression alone
does not establish general strength or admit a full episode.

build_counter_strike.py changes only GgsCounterRescuePolicy.class over verified
cycle10 build49d294ae9e5a7be3bdcdf96500326f4b3f5440d9144e160f869159318c2e8719.
No card rules, decks or coefficients change; the candidate is experimental.

## Cycle12 Anguished Unmaking rescue

The destruction-only gate missed saving exile removal. A constructed Dreadmaw
board reproduced three supported counter choices dying at-2 while explicit
passes survived at3. Cycle12 recognizes only Anguished Unmaking's tested
Battlefield-to-Exile effect followed by LoseLife3 on its activating player,
with no further subability. Existing plain Destroy support is preserved.
The three-life loss occurs on resolution, not as a casting cost. Other exile,
bounce, tuck and compound effects still need their own actual-resolution review.

ExileCounterRescueRegression executes colored mana, exile, life-loss resolution,
the caster leaving at zero life, and protecting the pilot's own necessary
blocker. Nonlethal decisions retain stock evaluation. Fresh heldout constructed
cases are separate from the repeated reproduction. No card rule, deck or model
is changed. build_counter_exile.py overlays only the policy class on verified
cycle11 build879c8fc6d792c7270efb6432a0d1748c62ab082b5e5565bd26deb9034b2b6f85.
