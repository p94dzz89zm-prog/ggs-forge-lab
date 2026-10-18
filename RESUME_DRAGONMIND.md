# Resume DragonMind without losing or duplicating work

1. Materialize authoritative `GGS_Training_Day_State_2026-10-16.json`, Library
   `libfile_0a30bbcadf1881918f7e5eac839f2e2d`, using the current Library skill.
   Retain its version number for a guarded replacement. Inspect its active lease,
   unresolved historical attempts and any collector, including manual launches.
   Do not infer stoppage from a missing process in another workspace.
2. Use `next_cycle_number` explicitly. Allocate bounded lease and seed/random
   ranges in the guarded ledger before execution. Never duplicate unknown or
   completed attempts. Development seeds are2026110000+cycle*10; reserved
   heldout seeds2026120000+cycle*10; random50000+cycle*128. Record actual bounds.
3. Recover the newest private archive named by the ledger. Verify outer SHA256,
   ZIP CRC and every MANIFEST member hash before extraction. Restore exact JARs,
   historical model checkpoint and provenance. Never replace the adopted trusted
   engine with the pinned initial executable or silently select an older build.
4. Recover code at the ledger's exact commit on
   `p94dzz89zm-prog/ggs-forge-lab`, branch `fix/pilot-recovery-v35`. Read
   DAY_CYCLES.md, POLICY_RESEARCH.md, EVIDENCE_ADMISSION.md and learning_gate.py.
   Keep private hands, models, audits, dashboard data and raw game logs off GitHub.
5. Pinned runtime Library `libfile_9933e8e344148191ada429ff4272e4b8`, SHA256
   `5044f0aeed36cbda2639d14e68d23e1aa55fb0fb703fee760babf849cdbe675d`,
   supplies engine/res, TestNG and AITest. Verify RUNTIME hashes and ZIP contents.
   Use actual restored absolute paths; scratch locations are not persistent.
6. Run targeted reproductions, smallest correction and full checks. Freeze build,
   source and separate evaluation cases before evaluation. `run_pilot_recovery.py`
   accepts `--expected-jar-sha256` and rejects corrupt/changing inputs. Preserve
   every failure and timeout; require exact completion markers.
7. `evaluation_batch.py` runs one bounded baseline/candidate natural comparison
   with actual native Forge personalities and all-seat private audits. Supply
   engine, baseline/candidate JARs, output, allocated seed, seat, purpose and
   population. Default max120seconds/game, serial, two attempts. It records
   profile/deck/build/collector hashes. Resume matching saved completed attempts;
   changed inputs, changed evidence, prior failures and unknown in-flight jobs
   require explicit reconciliation, never automatic reruns. It never trains.
8. `adaptive_pilot.py` persists episodes in SQLite, serializes writers and uses
   only evidence-bound reviewed statistics for selection, including in sandbox
   mode. Native `diverse_training` differs from `unseen_evaluation`; the latter
   cannot train. It remains a three-profile contextual bandit, not a neural
   Commander expert. No new trusted update is claimed without admitted evidence.
9. `performance_registry.py` imports completed technical logs and paired records
   into private SQLite. It verifies hashes, reopens game admission, deduplicates
   evidence IDs and rejects conflicting imports. Export JSON for the owner-private
   dashboard. Unknown metrics remain absent, not zero accuracy or estimated wins.
   Keep builds/decks/populations separate. Report seed clustering and withheld
   learning. Published data are snapshots; publication is not live training.
10. Save cycle evidence and model privately, verify saved bytes by materializing
    them again, append exact Library identities/hashes/results to the guarded
    ledger, advance next cycle and clear the lease only after confirmed saving.
    Commit only reviewed public source/tests on the approved branch.

## Automation boundary

The repository is public. GitHub Actions runs bounded Python and pure-JDK
contract evaluations on pushes and pull requests, with read-only permissions,
10-minute timeout and one active run per branch. It does not receive private
runtime/model/game data and does not train the pilot. Use the actual run URL
and observed conclusion as evidence; a configured workflow alone is not success.

Private scheduled Forge training is not configured: this connection does not
supply a supported private checkpoint credential path to a persistent runner.
The approved source branch is not the default branch; GitHub cron requires the
default branch. No unrelated branch is modified just to imply a live schedule.
Do not put expiring Library URLs or private artifacts in public workflow files.

The old GGS automation remains canceled. Academy was restored; do not recreate
or consume that temporary task slot.
