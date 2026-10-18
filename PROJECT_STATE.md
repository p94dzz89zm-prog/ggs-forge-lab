# DragonMind public development state

Read this file and RESUME_DRAGONMIND.md at session start. Exact private artifact
identities, runtime hashes, job allocations, seeds and experimental model state
are in the private project-state document and authoritative private ledger.

## Verified source baseline

Repository: `p94dzz89zm-prog/ggs-forge-lab`.
Approved branch: `fix/pilot-recovery-v35` (default `main` is older).
Latest verified code/evaluation: `c2d1ee3908de0243879d0f8e235f8d403b2b8fe5`.
The Cycle20 learning implementation and model remain preserved, unchanged.
Hosted evaluation passed 135 Python tests and both six-check launcher runs:
https://github.com/p94dzz89zm-prog/ggs-forge-lab/actions/runs/39091218407 .
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
Cycle 21 reproduced the launcher-banner failure before repair. Its exact-output
self-test now isolates only its child JVM option environment; normal suite logs
retain all warnings. Six launcher checks pass with all three ambient JVM option
variables present, and 135 Python tests pass. CI includes this environment check.
The engine runner accepts repeated explicit `--jvm-property NAME=VALUE` options
and records them in its private manifest, avoiding compiler/child inheritance.
Hosted cycle21 launcher repair evaluation succeeded:
https://github.com/p94dzz89zm-prog/ggs-forge-lab/actions/runs/39090808717 .
The frozen Cycle20 model scored 24/24 against 12/24 baseline on 12 unseen-card
clusters in three-player local-resource diagnostics. Four-player scope controls
retained stock in all 24 conditions; both scored only 12/24. All 144 paid/resolved
branches passed assertions. These are correlated constructed cases with a Codex
rubric, not independent expert reviews, full games or a population estimate.
Another 128 fresh combat-legality positions passed using explicit model JVM
properties. No new model training, full-game reward admission or promotion.
Dashboard source recovery succeeded with a fresh credential. The owner-private
dashboard was published successfully with cycle21 results, a manual refresh
button and a 30-second visible-tab refresh. Refresh replaces rows and clears
stale values on failure; static/data and DOM-contract checks passed. Browser
visual verification was unavailable. See the private ledger for saved receipts.
https://dragonmind-performance.symbols.chatgpt.site
This changes learned local decisions only; no whole-game admission, broad
strategic strength or incumbent promotion is established.

Next resumable learning milestone: collect and review a separate four-player
development set with opposing-creature survival/protection-dependency controls,
then fit an immutable candidate and evaluate on new identities. Never train on
Cycle20 or Cycle21 held-out identities. Keep v1 and the incumbent unchanged.
Complete-game critical-decision review and specialist opponents remain open.

Cycle22 evidence milestone: twelve four-player action pairs and two hidden-hand
controls passed (26 actual branches). They distinguish removing an immediate
lethal attacker from preserving an opponent's attack-prevention permanent.
An explicit public-stack-copy API avoids an omitted-stack forecast and leaves
existing copier calls unchanged. Both early failed attempts are retained.
See forge-fork/MULTIPLAYER_LEARNING.md. A separate immutable two-feature survival
model was then fitted from the12 reviewed pairs; unchanged v1 remains intact.
On a frozen same-executable comparison with three unseen card identities, the
new model improved conditional survival6/12 to12/12. Six local changes, no
observed regressions; two correlated templates, not a full-game strength result.
141 Python tests pass. Broad candidate engine/planner checks are in progress;
recover their saved status before retrying. No default activation or promotion.
