# DragonMind public development state

Read this file and RESUME_DRAGONMIND.md at session start. Exact private artifact
identities, runtime hashes, job allocations, seeds and experimental model state
are in the private project-state document and authoritative private ledger.

## Verified source baseline

Repository: `p94dzz89zm-prog/ggs-forge-lab`.
Approved branch: `fix/pilot-recovery-v35` (default `main` is older).
Latest previously verified implementation: `266b91f14c5c74f851b3e0fb85408ea4e63ed39a`.
Hosted evaluation passed 118 Python tests and six launcher checks:
https://github.com/p94dzz89zm-prog/ggs-forge-lab/actions/runs/39088100107 .
The Git commit containing this file records the recovery infrastructure revision.
Check its hosted workflow result before calling it externally verified.

## Completed public milestones

- Persistent paired-evaluation provenance, reviewed-learning admission gates,
  scoped pilot corrections and native opponent personality support.
- Immutable milestone archive creation/verification/restore with explicit file
  hashes and optional completion markers; no implicit learning admission.
- Bounded CI stages persist status before execution and preserve failures,
  timeouts and partial logs. Completed stage artifacts upload immediately.
- Session recovery and <=15-minute checkpoint cadence are required in AGENTS.md.
- Learning checkpoint utility uses SQLite online backup to retain committed WAL
  transactions; immutable publication and an actual evidence-readiness audit
  keep pending rewards, held-out games and missing reviews out of learning.
- Runtime checkpointing and readiness verification do not themselves train a
  policy or establish strategic improvement. Gameplay evidence remains private.
- Regression finalization now reopens saved logs and rejects changed hashes,
  missing/wrong/duplicate completion markers or incomplete suite coverage before
  reporting success. Original suite observations remain intact for diagnosis.
  129 Python tests pass on the integrated source. Separate frozen constructed
  checks cover appended/deleted logs and a rehashed wrong marker. This guards
  finalization-time drift, not later filesystem damage; saved archive readback
  and semantic verification remain required. No gameplay policy changed.

## Open work

- Diagnose intermittent startup exits and historical evidence retention gaps.
- Review complete gameplay decisions before trusted learning or deck conclusions.
- Preserve rules correctness separately from measured strategic improvement.
- Keep the exact Apex baseline and GGS centerpiece; substitutions remain
  experiments until supported by controlled, validated gameplay evidence.

## Exact next steps

1. Fetch this approved branch; inspect remote HEAD, local changes and history.
2. Read the current private project-state document and authoritative ledger.
   Reconcile active reservations and saved outcomes before starting any game.
3. Verify the newest named archive, member hashes and completion markers;
   restore to a fresh directory. Never silently substitute an older checkpoint.
4. Run `python -m unittest discover -s . -p 'test_*.py'` after code changes.
5. Allocate one small milestone, execute, commit public code, save private
   evidence, verify readback and update state before the next expensive stage.

## Automation boundary

Push/PR/manual GitHub jobs run bounded public code tests, with a 10-minute job
limit, read-only permissions and per-branch serialization. Logs/status/hash
artifacts retain for 90 days; archive significant evidence privately before
expiry. These jobs do not execute private Forge games or train a model.
A configured task or workflow is not proof of execution: inspect its actual
run status. Private job schedules and outcomes must be recovered from private
state, never inferred from conversation history or absent local processes.

## Current bounded learning experiment

An opt-in supervised tactical counter preference now has actual engine branch
evidence and frozen unseen-card comparison. See TACTICAL_LEARNING.md.
Controls and full regression acceptance must finish before closing the cycle.
This changes learned local decisions only; no whole-game admission, broad
strategic strength or incumbent promotion is established.
