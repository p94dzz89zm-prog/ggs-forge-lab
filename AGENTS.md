# DragonMind session recovery and persistence

At the start of every resumed session, read PROJECT_STATE.md and
RESUME_DRAGONMIND.md from the remote approved branch, inspect its current HEAD,
and materialize the current authoritative private ledger. Conversation history
is context, never the authoritative job or checkpoint state.

Preserve active leases and unknown outcomes, even when no local process exists.
Do not replay completed work, reuse reserved seeds or silently recover an older
checkpoint. Reconcile concurrent changes before publishing; never force-push.
Read EVIDENCE_ADMISSION.md before admitting any training result.

Use milestones of at most 15 minutes or one reproduction/fix/evaluation stage,
whichever ends first. Before starting, save the allocation and exact inputs.
After each useful stage, commit public source/tests with its validation status;
fetch the commit back and compare changed file bytes. Save private evidence with
an immutable manifest and persist its receipt in the guarded ledger. Verify the
saved archive by restoring its bytes. Scratch files alone are not checkpoints.
If durable saving fails, stop expensive work and preserve the last verified
state; do not mark the milestone complete.

Keep incomplete/failing logs and unknown in-flight outcomes. Check hashes and
explicit completion markers, not exit status alone. Record seeds, budgets,
versions, opponents, review status and exact next command. A technical pass does
not admit learning or establish strategic improvement.

Update PROJECT_STATE.md whenever verified source, defects, experiments or next
steps change. Keep private hands, raw game logs and models off this public repo.
CI artifacts expire after 90 days; archive significant evidence privately before
expiry. Only report external jobs as executed after observing their run result.
