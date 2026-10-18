# Experimental supervised counterspell preference

This experiment adds an actual learned parameter model to the controller's
counterspell selection. `tactical_preference.py` fits logistic weights with
batch gradient descent from reviewed, engine-executed decision pairs. The
learned coefficient is not installed as a source-code rule. Model JSON, training
observations and their explicit reviewer labels remain private.

The local lesson is conserving a Swan Song instead of saving an opponent's
creature, while retaining protection of our own creature. These are supervisor
preferences about immediate resources, not proven whole-game optimal decisions.
Six distinct constructed decision pairs used three training card identities;
twelve branches paid costs and resolved in Forge. Repeated profiles are not
counted as independent games. Two different card identities were frozen for four
paired evaluation conditions before evaluation. No natural-game seed was used.

The opt-in Java policy requires both `dragonmind.counterPreferenceModel` and
`dragonmind.counterPreferenceSha256`. Missing, changed, malformed or unsupported
models retain the stock decision. The current validated family is deliberately
limited to three-player opponent-MAIN1 positions at 30–40 life, Swan Song versus
single-target creature destruction, and bounded target power. Continuous rules
such as Peacekeeper's attack restriction are outside the learned family.
The model can veto a selected counter; it cannot create a new spell action.
It is off by default, experimental and not promoted to the incumbent.

The trainer requires a scoped review bound to exact engine-log and dataset
hashes. Every row must match the engine-emitted decision, both action outcomes
must be present, and each label must be explicit. Held-out inputs, duplicate IDs,
missing reviews and altered evidence are rejected. The full-game outcome gate
is unchanged: this decision-level supervision admits no game reward and makes
no claim of general strategy, autonomous learning or a win-rate improvement.

Reproduce using `forge-fork/build_learned_counter.py` over its pinned prior
experimental engine, the actual paid/resolved fixture
`forge-fork/LearnedCounterPreferenceRegression.java`, and privately preserved
training/review/model files. Freeze all input hashes before evaluation. Preserve
all failed attempts and compare model-disabled and model-enabled controllers on
the same executable and conditions. Do not tune from the evaluation results.

## Cycle 21 frozen-model validation

`LearnedCounterHeldoutRegression` extends the paid/resolved fixture with 12 new
card identities and fixed seeds 2026120210–2026120221. It rejects player counts
other than three or four. Run through `RegressionLauncher` with arguments
`3 baseline`, `3 learned`, `4 baseline` and `4 learned`; only learned runs receive
the exact model path/hash JVM properties. Use a new evidence directory per run.
Compile both preference fixtures against the pinned runtime and candidate JAR.
Baseline three-player execution includes both actual action branches per state.

The unchanged Cycle20 model agreed with the predefined local-resource rubric
in 24/24 new three-player conditions versus 12/24 with the model disabled.
No observed preference regressions occurred. These are 12 card/seed clusters,
not 24 independent games. The rubric is Codex review, not independent expert
judgment. No population confidence interval or Commander win-rate estimate is
supported by this purposive, same-family sample.

Four-player checks expose the current deployment limitation: stock actions and
resolved outcomes remain identical in all 24 matched conditions, and both builds
agree with the local rubric only 12/24. The v1 policy intentionally declines
four-player input. Its success at three players does not yet help a four-player
Commander pod. Across the four runs, 144 paid/resolved branches passed resource
and zone assertions. None are full games, training rows or evidence for card
substitutions. Preserve these held-out card identities from future training.
