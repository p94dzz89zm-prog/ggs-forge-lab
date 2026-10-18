# DragonMind public development state

Read this file and RESUME_DRAGONMIND.md at session start. Exact private artifact
identities, runtime hashes, job allocations, seeds and experimental model state
are in the private project-state document and authoritative private ledger.

## Verified source baseline

Repository: `p94dzz89zm-prog/ggs-forge-lab`.
Approved branch: `fix/pilot-recovery-v35` (default `main` is older).
Latest previously verified implementation: `a33579a92d4a6ee38e39e1023e1e3e611485eb86`.
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
- 118 Python tests passed locally for this recovery revision. Local JDK compiler
  was unavailable; the hosted job installs Java and must verify its contracts.

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
