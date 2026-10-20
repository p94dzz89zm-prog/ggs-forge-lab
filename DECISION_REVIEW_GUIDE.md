# Refereeing learning experience

Record completion is not strategic correctness. Keep these judgments separate:

| Layer | Evidence | What passing establishes |
| --- | --- | --- |
| Record integrity | Canonical result, transcript, status, hashes | The recorded episode agrees with its reported result |
| Tested rules | Actual engine payment/resolution fixtures and legal combat probes | The named mechanics work in the tested situations |
| Decision review | Player-view state, available options, costs, action and resulting state | A scoped finding about a particular decision |
| General strength | Paired held-out trials, varied opponents and effect metrics | Evidence of performance in that distribution, with uncertainty |

The automatic referee checks only record integrity and emits leads. It never
approves an episode for strategy learning. The review tool requires a stated
scope, finding and reviewer; its review history is retained. A pass under a
narrow scope must not be described as an optimal-play certificate.

For GGS, review the relevant windows for commander availability, fresh-body
production, legal combat access, mana reservation/payment, and the actual
resulting triggers. Check multiple attackers hitting the same player as one
damage event rather than assuming each body gives a separate Dragon. Check
native ninjutsu, Sneak casting and the Satoru triggers separately. Preserve an
available lethal connection and verify the commander is not casually returned
as a cost. Observe stack interaction and opponents' visible blockers and taxes.

When protection or removal appears missed, establish that a legal, payable
answer was available at that moment. Do not infer a missed answer from losing
to a threat. If the hand, available mana or timing evidence is missing, record
the question as uncertain. Simultaneous triggers, first strike and priority
windows need their own reconstruction rather than a prose guess.

Retain poor legal choices and losses: they can be negative examples. Do not
approve only winners or delete strategically weak games. Exclude an episode's
reward from the reviewed pool when an engine/record error invalidates it, or
when the review cannot establish the required evidence. Keep the rejected or
pending raw episode for debugging. Referee findings should identify concrete
mistakes, not relabel all unsuccessful actions as errors.

When a mistake is confirmed, create a reproducible engine fixture, apply a
scoped fix, and replay separately. Preserve the original episode and engine
hash. The gate prevents unreviewed high scores from silently becoming trusted
preferences; it does not make a weak reward proxy complete or a human/AI
reviewer infallible.

Current scope: a strategy-profile bandit with a GGS-specific proxy. It cannot
yet learn arbitrary tactics, all decks or Magic rules. No reviewed samples have
been promoted at this checkpoint, and no deck-cut recommendation follows from
the sandbox experiments.

Before a pass review is accepted, the tool also reopens the canonical files, checks their captured hashes and result agreement, recomputes observed effects and proxy reward, and rejects unsafe paths, duplicate completion markers and engine failures. These are integrity preconditions, not strategic approval by themselves.
