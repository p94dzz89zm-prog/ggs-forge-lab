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

## Learned candidate and frozen evaluation

`multiplayer_preference.py` fits two logistic coefficients from explicit,
hash-bound development reviews. A separate arithmetic/resource referee checks
both actual attack branches and the labels without using model predictions.
Six admission tests cover immutable reload, held-out rejection, altered damage,
spoofed features/labels, missing contrast and changed evidence. This is a scoped
rules/outcome review by Codex plus an independent calculation, not an independent
human strategic review. The objective is survival under the recorded visible
attack, not a calibrated chance of ultimately winning.

The immutable candidate uses 12 pairs (24 action branches) from Peacekeeper,
Gigantosaurus and Ancient Brontodon. Two additional visibility controls passed.
Frozen evaluation uses Stormtide Leviathan, Scaled Wurm and Enormous Baloth with
12 disjoint seeds/conditions. On the same executable, enabling the fitted model
increased conditional survival from 6/12 to 12/12, with six changes and zero
observed regressions. Life perturbations of two templates are correlated; no
population confidence interval or complete-game win rate is justified.

Build with `build_multiplayer_counter.py --base FROZEN_V1.jar --output NEW.jar`.
Fit with `python multiplayer_preference.py --evidence REVIEWED --output NEW.json`.
The hook requires both `dragonmind.multiplayerCounterModel` and
`dragonmind.multiplayerCounterSha256`. It vetoes a stock-chosen Swan Song only
inside four-player opponent-MAIN1 single-creature-destruction scope when the
public exposure contrast is nonzero and the fitted probability is below .25.
Missing/corrupt/unsupported models and zero contrast preserve stock. The v1
model and its properties are separate and unchanged. New fits and held-out data
remain private. No full-game rewards, default activation or promotion.

The feature detects a single currently legal unblocked lethal body, not all
combat interactions. Only the tested plain-body attack continuations have been
validated here. Future draws, responses, blocks, damage prevention, commander
damage, political effects and long-horizon recovery require separate evidence.
