# Experimental four-player visible-survival evidence

Cycle22 preserves the Cycle20 model and its three-player gate unchanged.
`MultiplayerCounterEvidence` executes four-player action pairs in reduced boards.
The current opponent has one visible, ready lethal attacker. Another opponent
casts Mortify either at that attacker or at an opposing Peacekeeper that stops
the attack. Both Swan Song and pass branches pay real costs, resolve the stack,
and execute an actual legal unblocked attack when available. Life, zones, blue
mana and Bird ownership/count are checked. These are not complete matches.

Twelve development pairs use two attacker identities, three life totals and two
roles. They share two templates and are not twelve independent strategic games.
Two extra checks vary an opponent's hidden hand while requiring the same public
features, live-state snapshot and RNG restoration. No library order or hidden
hand enters a model feature. There is no assumption of cooperation: the attack
is an explicit adversarial continuation, not an inferred opponent intention.

`GgsMultiplayerCounterFeatures` contrasts the current public attack exposure
before and after resolving the visible stack in a masked copy. The existing
two-argument copier keeps its behavior. A new explicit third argument includes
the visible stack without changing the global simulation flag. Early attempts
exposed a null stack-helper argument and omitted-stack projection; those failed
logs are retained and were not accepted as training evidence. The corrected
fixture passed 26 actual branches including the visibility controls.

Only scoped survival labels independently checked against actual branch
outcomes may support an experimental model. They do not supply game rewards,
expert strategic review, a calibrated multiplayer winning probability, politics
or a general threat-assessment oracle. A candidate remains off by default.
Held-out identities/seeds must be disjoint and frozen before evaluation. Preserve
failures, training data/review/model versions and the original v1 checkpoint.
