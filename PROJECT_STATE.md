# DragonMind public development state

Read this file and RESUME_DRAGONMIND.md at session start. Exact private artifact
identities, runtime hashes, job allocations, seeds and experimental model state
are in the private project-state document and authoritative private ledger.

## Verified source baseline

Repository: `p94dzz89zm-prog/ggs-forge-lab`.
Approved branch: `fix/pilot-recovery-v35` (default `main` is older).
Latest verified learning implementation: `e64115895fe9a61bca4ba0e9e75c00c61e04ebaa`.
Hosted evaluation passed 135 Python tests and six launcher checks:
https://github.com/p94dzz89zm-prog/ggs-forge-lab/actions/runs/39089201096 .
The current containing commit may update documentation only; recover exact
runtime/model provenance and completion state from the private ledger.

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
All scope/corruption controls passed. The supervised model agreed with local
review preferences in four unseen-card constructed conditions versus two for
the model-disabled baseline. This is a narrow learned choice change, not a
full-game accuracy or win-rate result. Engine coverage verified 25 suites / 597
groups across attempts, including 128 distinct combat positions. The initial
combined run retained an exact-output launcher failure from a JVM environment
banner; the remaining two suites passed with direct properties. No model or
completed suite was replayed or altered to reconcile those checks.
Dashboard refresh failed at source opening; the existing published snapshot is
unchanged and new results are retained privately. See the latest ledger for
checkpoint saving/readback status.
This changes learned local decisions only; no whole-game admission, broad
strategic strength or incumbent promotion is established.
