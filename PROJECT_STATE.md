# DragonMind verified state and recovery

Repository `p94dzz89zm-prog/ggs-forge-lab`, branch `fix/pilot-recovery-v35`.
At session start read AGENTS.md, this file, RESUME_DRAGONMIND.md and the current
authoritative private ledger/project state. Reconcile leases, seeds, saved
checkpoints and unknown outcomes before compute. Chat is not authoritative.

## Cycle22 handoff, reconciled during Cycle23

Preserved learning implementation: `266a3065add0efb8af455422043aacedb52785a2`.
Hosted code evaluation succeeded:
https://github.com/p94dzz89zm-prog/ggs-forge-lab/actions/runs/39092607836 .
The containing commit adds evaluation infrastructure; no retraining or change
to the preserved executable/models.

Cycle20 v1 remains intact. Cycle22 fitted a separate two-coefficient supervised
survival model from12 actual four-player action pairs. A frozen unseen-card test
improved conditional survival6/12 to12/12 across two correlated templates.
Review was Codex plus a separate arithmetic/resource referee, not independent
expert strategy review. No winning-probability calibration, full-game improvement,
default activation or promotion. See forge-fork/MULTIPLAYER_LEARNING.md.

The candidate checkpoint was restored: hashes, markers and all12 reviewed rows
verified. Original full-engine/planner logs were excluded and lost when scratch
reset. Preserve this retention gap; summaries cannot replace raw evidence.
Fresh recovery verified25 suites /597 groups across attempts,128 NEW combat
positions53072–53199,41planner groups and24 wrong-hash/zero-weight controls.
One initialization exit0 without a marker was rejected and retained; only
failed/unstarted suites were rerun. The intermittent startup-exit defect remains.
Recovered Cycle22 source passed141 Python tests; eight new harness contracts
bring the current verified total to149. Completed training was not replayed.
Private artifact identities, hashes and saved-byte receipts stay in the ledger.

## Full-game work

evaluation_batch.py freezes model identities separately from executables, passes
explicit per-side model properties, and rejects changed inputs. Its default deck
is the dated October17 Apex baseline rather than the Whip trial. Same-executable
pairs can isolate enabling the Cycle22 model while retaining v1 on both sides.
All-seat audits stay private. Unknown/incomplete attempts never auto-resume.
commander_game_review.py checks records and hand/library visibility, but approves
zero complete games. See FULL_GAME_VALIDATION.md for official rules references
and the coverage limits.

Next: allocate a small matched held-out pair using the preserved models,
October17 Apex and archived pod proxies. Save each pair before another seed.
Review real costs, priority, interactions and critical decisions before claiming
rules-valid strategic results. Compare trajectories separately from outcomes.
Longer survival alone is not stronger play. Do not train on held-out outcomes.

## Open limitations and deck research

No verified full-game strategic improvement, specialist control/combo/tempo
opponents or general rules oracle. Native personalities remain heuristics;
Jaymie/Gabe/Destyn lists are archived proxies. Complete critical-decision review,
commander tax/damage/zone choices, politics, blocking/prevention and responses
need more evidence. Historical unknown attempts and damaged logs stay quarantined.
GGS remains the centerpiece; resilience is deck-level insurance. Physical
Mistblade displacement and land inventory remain unresolved. The ranked
APEX_RESEARCH_BACKLOG.md treats Whip as a hypothesis, not a proven upgrade.

## Persistence and automation

Use <=15-minute independently resumable stages. Commit public source/tests and
verify readback; save private evidence and restore saved bytes before closing
a stage. Stop expensive work on save failure. Never overwrite a successful
checkpoint or publish private hands, raw logs or models to public GitHub.

GitHub push/PR/manual code jobs have10-minute limits, read-only permissions and
90-day artifacts; they do not run private training. Check actual execution.
An enabled task is not continuous compute. Update the guarded ledger and concise
private state with exact next steps and preserve significant evidence privately.

Dashboard: https://dragonmind-performance.symbols.chatgpt.site .
Cycle22 refresh is being published; reconcile native deployment status and saved
receipts before retrying. Browser visual QA is unavailable; static/data and
refresh/failure/retry contracts pass.
