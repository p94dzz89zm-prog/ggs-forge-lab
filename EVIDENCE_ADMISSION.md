# Trusted learning evidence

Completed games and matching logs establish record integrity. They do not
establish correct rules resolution or sound play. Keep raw wins, losses,
timeouts, crashes and unresolved decisions as diagnostic evidence. Historical
records without a qualifying review remain provisional even if old JSON files
contain numeric experimental feedback. Do not derive trusted card swaps or
strength claims from those values.

The coefficient search now writes `observed_outcome` separately from
`feedback`. The latter stays null until `learning_gate.assess` admits an
explicit review of the exact evidence. Parent selection ignores legacy numeric
feedback. In the default reviewed profile pool, narrowed pass reviews likewise
cannot contribute episode rewards. Full reviews are reopened and checked
against current files before reuse. Sandbox results remain provisional.

A `learning-review.json` beside an attempt must specify version 1 and scope
`full_game_rules_and_critical_decisions`; bind `evidence_fingerprint` to the
current console, canonical record/transcript, decision audits, engine/deck
inputs and policy weights (or profile). Require explicit `rules_status` and
`critical_decisions_status` passes, every registered seat in `reviewed_seats`,
every `learning_gate.MECHANICS` entry in `reviewed_mechanics`, a named reviewer,
substantive `findings`, and explicit empty `unresolved_issues` and `limitations`.
These fields record a justified review; filling them is not a substitute for
reconstructing actual legal options, costs, timing and consequences. A missing
opponent information set or unverified critical interaction must be retained as
a limitation and cannot support full admission. Do not approve from the result
alone or mass-fill pass reviews.

New coefficient searches and audited profile runs collect all seats privately
for offline review. Each pilot still acts from its own information set. A
selected-seat-only audit cannot pass all-seat admission. All-seat collection
adds logging overhead; match the audit mode and time budget across comparisons,
retain timeouts, and do not interpret fewer completed games as weaker strategy.

The fingerprint is portable across restored directories, but any changed build,
deck, weights, audit or canonical bytes invalidates a prior approval. Use
`policy_search.py --purpose heldout` for reserved evaluation conditions; even a
full review cannot feed their outcomes into training. Never tune from held-out
results. Resume only runs with matching input protocols; retain old attempts
and use a new directory when source inputs differ.

For a reproduced rules error, quarantine the affected result, identify its
mechanic/build, add an actual payment/resolution regression, fix and retest on
new conditions. For a material pilot error in a valid game, preserve the losing
decision as a corrective example and verify the repair separately. A scoped
decision repair can establish a specific improvement while the full game
remains unapproved. Do not mislabel every legal loss as an error, or discard
negative examples. Earlier exploratory candidate lineage remains experimental.

The gate is an admission policy, not a complete Magic rules referee or a proof
of perfect strategy. The reliability goal remains unresolved until the actual
mechanics and critical decisions are reviewed with adequate evidence. Report
exact tested coverage and remaining uncertainty; no universal zero-error claim.
