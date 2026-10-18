# Resume DragonMind without losing or duplicating work

1. Read AGENTS.md and PROJECT_STATE.md from the approved remote branch. Inspect
   remote HEAD and local uncommitted work. Do not reconstruct state from chat.
2. Recover the current private DragonMind project-state document and authoritative
   development ledger through authenticated durable storage. Preserve their
   current version numbers for guarded writes. Exact private artifact identities,
   runtime/model hashes, seeds and job reservations stay in private storage.
3. Inspect active leases and saved attempts, including scheduled/manual jobs.
   A missing local process or expired lease does not prove an external job stopped.
   Never replay completed or unknown attempts or reuse reserved evaluation seeds.
4. Restore the newest checkpoint named by that ledger. Verify the expected outer
   SHA256, ZIP CRC, every manifest member, and the technical logs' own hashes and
   completion markers. Restore into a new directory and verify exact engine/model
   versions. Never silently substitute an older checkpoint or initial runtime.
5. Recover code at the ledger's exact commit. Read DAY_CYCLES.md, POLICY_RESEARCH.md,
   EVIDENCE_ADMISSION.md and learning_gate.py before gameplay or training. Keep
   raw private games, hidden hands, model files and private dashboard data off
   this public repository. Source and private experimental engines are distinct.
6. Reconcile the active job before allocating any compute. Reserve exact inputs,
   seeds, purpose and budgets durably. Use <=15-minute milestones or one completed
   reproduction/fix/evaluation stage, whichever comes first. Save after each stage.
7. `evaluation_batch.py` retains matched completed attempts and refuses changed
   provenance, failures and unknown in-flight outcomes. It never trains. Use the
   existing strict admission gate for reviewed development evidence; held-out
   observations cannot update training. Record integrity alone is insufficient.
8. `milestone_checkpoint.py create --root ROOT --output NEW.zip --spec SPEC.json`
   accepts explicit `files`, `metadata` with milestone/source_commit, and optional
   per-log `markers`. `verify --archive NEW.zip --sha256 HASH` checks exact bytes.
   `restore --archive NEW.zip --sha256 HASH --destination NEW_DIRECTORY` restores
   without merging into existing work. This archive is local until durably saved.
9. Save each private milestone externally, restore the saved copy and verify it
   before recording completion in the guarded ledger. Commit public source/tests,
   fetch the commit back and compare bytes. Reconcile concurrent branch/ledger
   changes without overwriting them; never force-push. Stop expensive work if
   durable saving fails. Preserve incomplete/failing evidence and exact next steps.

## External execution and reporting

GitHub Actions runs bounded Python and pure-JDK code evaluation, not private
Forge gameplay or training. It records stage status before execution, uploads
Python evidence immediately and all available logs on success/failure, retains
artifacts for 90 days, uses read-only permissions and a 10-minute job timeout.
Significant evidence must be archived privately before artifact expiry.

Inspect the current private scheduler/ledger for authorized Work tasks, leases
and actual saved outcomes. Do not alter unrelated schedules. Do not claim a task
ran from its configuration alone. Report observed run URLs/conclusions, unknown
outcomes and private execution blockers accurately; never imply continuous
training without a verified active external runner.
