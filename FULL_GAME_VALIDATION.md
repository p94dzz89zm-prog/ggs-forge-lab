# Matched Commander evidence and review boundaries

`evaluation_batch.py` can freeze a shared v1 counter model and independent
baseline/candidate multiplayer models. It stores model bytes and SHA256 beside
the pair, passes explicit JVM properties, and rejects changed originals or
snapshots before resume and after each game. Use the same preserved executable
for both labels to isolate enabling the Cycle22 model. No fitting occurs here.
The default deck is the dated October17 baseline, not the Whip experiment.
The protocol fingerprints the complete resource file inventory, including card
definitions and editions, and rechecks it after each game. A model/JAR hash alone
does not freeze the rules implementation loaded from external resources.
Keep all-seat private audits and native opponent-profile hashes on both labels.

Example inputs: `--deck GGS_Apex_20261017_v1 --purpose heldout --population
unseen_evaluation --shared-counter-model V1.json --candidate-model C22.json`.
The ordinary required engine/JAR/output/seed/rotation arguments still apply.
Allocate each seed/seat pair durably before starting; never resume an unknown
in-flight attempt, change its inputs, or replay a completed game. Save each
completed pair before the next one. Timeouts and startup failures are not losses.

`commander_game_review.py` checks canonical record consistency, registered-seat
audit coverage, hand/library identity isolation and per-viewer turn progression.
It emits review leads and explicitly approves zero full games. It does not
verify every cost, priority window, target, block, trigger or replacement effect.
An audit containing only public zones and the viewer's hand is necessary but
insufficient to prove the pilot uses only legal information. Last-observed state
is not exact elimination timing. Counter context counts do not establish model
activation, payable answers or missed opportunities.

Compare canonical gameplay-event hashes separately from timing/result metadata.
Equal event transcripts establish equality only of the recorded events, not all
internal decisions or universal determinism. Report complete-game outcomes as
provisional until the full rules and critical-decision gate admits an actual
substantive review. Held-out games can never update the learner, even if reviewed.

## Rules authority and current gaps

Use the [official Comprehensive Rules](https://magic.wizards.com/en/rules),
currently the September25,2026 edition linked there. Relevant sections include
117/601/602/603/608 for timing, costs and resolution;702.49 for ninjutsu;800.4 for
elimination;903.8–903.10 for tax, commander-zone choices and commander damage.
Graveyard/exile commander movement uses a state-based choice; hand/library
movement uses a replacement effect. These must not be conflated in reviews.

The [official March of the Machine release notes](https://magic.wizards.com/en/news/feature/march-of-the-machine-release-notes)
clarify GGS haste: the affected creatures are fixed when the ability resolves.
Later entrants do not receive that haste. Treat current Oracle text as the card
authority and retain exact card/ruling versions for interaction reviews. Engine
definition presence and these selected references do not certify the full pod.

Not yet supplied: an independent action-level referee for entire arbitrary
Commander games; complete priority/payment event instrumentation; verified
specialist opponents; calibrated win-probability estimates; a sufficiently varied
reviewed match population. GGS/ninjutsu scenario tests remain narrower evidence.
