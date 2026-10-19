# DragonMind verified state and recovery

Repository `p94dzz89zm-prog/ggs-forge-lab`, branch `fix/pilot-recovery-v35`.
At session start read AGENTS.md, this file, RESUME_DRAGONMIND.md and the current
authoritative private ledger/project state. Reconcile leases, seeds, saved
checkpoints and unknown outcomes before compute. Chat is not authoritative.

## Bounded recorded-decision driver

A new disabled-by-default driver intercepts110 inventoried controller hooks.
Bounded number and cards-for-effect choices can now come from a hash-bound
recorded decision tape, with exact hook/actor/source/prompt/bounds matching.
Card IDs must match the current engine-offered inventory and rebind to its
actual live objects. Choice counts, optionality and duplicate selections are
checked. Unsupported inventoried hooks fail before AI execution; a failed
replay cannot report completion. Exact consumed-input hashing and an explicit
counted terminal marker are required. Fractional, quoted and overflowing integer
choices are rejected rather than rounded. This is not a complete replay driver.

An actual-controller fixture records its choices, then reconstructs the same
initial fixture in a fresh JVM and returns those recorded choices, including
live card identity. The unsupported-overload negative control rejects without
AI fallback or completion. Only these two choice families are implemented.
Priority ability selection/mutations, targets/modes/X, mana and other costs,
mulligans, combat/void decisions and remaining controller coverage still block
full-game replay. Per-action independent legality/visibility certification also
remains. No new full game, approval, training or comparison is claimed.
Executable delta recovery now also preserves appended class metadata and checks
the exact reconstructed whole-JAR hash; the earlier delta format remains readable.

## Storage recovery and announced X provenance

The previously unsaved verification bundle is now saved, retrieved and restored
with all outer and nested manifest checks passing. Cleanup removed only a
byte-verified redundant transport prefix; its complete master and all unique
sealed archives remain preserved. Capacity remains tight. New executable
checkpoints can carry a small delta bound to the exact archived base JAR and
the full reconstructed JAR checksum, without rewriting historical archives.
Recovery rejects wrong bases, altered entries, wrong target hashes and overwrite.

The Hydra metadata discrepancy is traced to a cached description using card
cast history before that history exists. The original structured chosen X,
effective cost, actual mana payment and entry counter agree. Future recording
retains the original engine description, separately records announced X and
nullable card cast history, and captures the live ability at stack announcement.
An actual-engine X=2 Hydra cast pays {2}{G}{G}, preserves X=2 on the stack and
enters with two counters before its ETB trigger resolves. This is a targeted
provenance regression, not a new complete game or whole-game rules approval.
Only evidence recording changes; policies, models and decks remain unchanged.

Current counts since the earlier recovery checkpoint remain two complete
development captures, two rejected attempts, zero fully rules-approved games,
zero training admissions and zero eligible learned-pilot comparisons. The next
engineering blocker is decision-driven replay: recorded choices must drive the
engine with live-object rebinding and legality checks, rather than rerunning AI
choices. Complete action-by-action rules and visibility review is also required.

## Typed provenance and independent mana checks

One new typed four-player development capture now completed with149802 referee
records and its615764572-byte stream sealed by the repaired writer. Original
bytes were saved externally, restored and verified. Scoped independent checks
find stable ownership across417 card identities, no unpaid shards after348
successful actual mana-payment calls and a consistent52-event life chain.
Substantive critical-sequence review reconciles commander-tax increments,
ninjutsu/GGS trigger timing and the final post-blocking menace/trample/lifelink
sequence against official rules. These findings are not whole-game approval.
Same-policy verification matches all149802 events and the canonical gameplay
digest. The157 spent mana units pass independent pool/color/shard checks; five
failed payment attempts are retained, not counted as spent units. Decision-driven
replay and complete action-by-action legality review remain outstanding. Learning0.

The actual capture exposed depth-truncated player-view leaves in nested blocker
notifications. Direct combat state retains those card identities. A finite
player-identity leaf now bypasses only the recursion cutoff, without traversing
the player graph. An actual old/new nested-blocker event regression reproduces
the old omission and verifies preserved owner/controller IDs after repair.
Only the two recorder classes change in the pinned writer-corrected executable;
all other entries remain byte-identical. Original captures are not backfilled.

The first repaired-writer typed diagnostic reached turn37 but hit its explicit
180-second engine limit. Its interrupted streams and writer receipt were sealed
as rejected diagnostic evidence, externally saved and restored. It is not a
completed game. Richer recording needs an explicitly larger time allowance;
the collector now permits up to600 seconds while retaining its120-second
default. Collector hashes, immutable-side copying and learning/review fingerprints
now also stream large evidence instead of materializing each tape. Learning and
rules gates are unchanged; the next fresh diagnostic remains separately allocated.

A subsequent typed full-game attempt reached the engine terminal record but
failed durable finalization: the old writer materialized the entire referee
stream for checksum validation and exhausted its heap. It is rejected, not a
completed capture. This establishes that attempt's failure, not the historical
truncation cause. Workspace cleanup later removed its unsaved raw failure and
an uncommitted repair; the private ledger explicitly records that retention gap.
The original externally sealed captures and verified engine remain unchanged.

Finalizer validation now hashes files incrementally. Checkpoint creation,
verification and restoration also stream members, checking for source mutation
between fingerprinting and sealing. A real old-writer control fails with heap
exhaustion and no completion manifest; the repaired writer seals a96MiB stream
under64MiB heap with384 records and matching checksum. Twenty-seven relevant
checkpoint/isolation/writer tests pass, including192MiB create/verify/restore
under128MiB address limit and a chunk-boundary completion marker. Only the two
writer classes change in the pinned engine; all other executable entries are
byte-identical. No strategy, model, deck, approval or learning change.

The first new full development game completed verification reexecution:
135197 recorded events, with4128 Set-derived UI notification rows differing only
in iteration order. All1263 canonical gameplay lines match after duration/result
timing is omitted. This remains same-policy reexecution, not decision-driven
replay or independent whole-game rules approval. Original failure retained.

Future recordings now type stack instances/views/targets, combat assignments,
delayed reveals, static/replacement traits and structured maps. They include
priority/turn owners, visibility permissions and public stack announcements,
elimination snapshots and final state. Cost-modifier hooks identify source and
before/after costs; nested speculative payments remain marked. Nineteen actual
engine checks and record/reexecution fixtures pass with zero unencoded values
in those fixtures. An independent Python mana-unit checker covers recorded pool
membership, colored/generic/hybrid/snow cost transitions and color-conversion
claims. Twenty-eight relevant Python checks pass. Full mana restrictions and
whole-game rules remain separate review obligations. The first typed full game
failed finalization as recorded above. Models and October17 baseline are unchanged;
learning admissions0.

## Fresh provenance capture

One newly allocated four-player development game completed under the evidence
overlay. Original sealed bytes were externally saved, restored and verified.
Its private tape has135197 records,65003 paired engine calls, one four-player
initial state,49 visibility events,158 actual mana units paid and5190 RNG
requests. Structural checks pass; typed stack/combat/delayed-reveal and other
serialization gaps remain. Zero fully rules-approved games or comparisons.
Replay reference and Python inspection now stream large tapes, avoiding whole
JSON-tape materialization. The targeted fixture reexecution still passes.
The batch protocol binds both evidence-reader source hashes for future runs.
No old journal or sealed capture was rewritten. Compatibility reexecution was attempted and rejected at opening-draw record445:
a card-statistics UI notification is built from a Set, so its collection order
is unstable. The original failure is retained. The comparator now treats only
that notification's card membership as unordered; zone/choice order remains
strict. Twelve targeted engine/comparator checks and fixture reexecution pass.
A private expected/actual divergence record is now retained on failure. Next:
a separately allocated verification of this specific fix, then typed gap repair.

## Provenance milestone, October18

The evidence-only overlay now instruments exact frozen engine classes for reveal
recipients, mana production and unit payments, cost adjustment/non-mana costs,
controller decisions, effects, stack and engine events. A private referee tape
records ordered initial zones and RNG bits separately from pilot observations.
Nine actual-engine provenance checks pass. A separate fresh-process fixture
reexecution consumed recorded RNG and matched all62 serialized records; this is
not yet a decision-driven game replay or independent rules certification.
Eighteen relevant Python tape/writer contracts pass. The first bytecode-verifier
failure and subsequent frame-loader build failure are retained privately; frames
are now regenerated with the application class loader. New games0, full-game
approvals0, training updates0. Unsupported serialized values remain explicit.
See ENGINE_PROVENANCE.md. Next: run one newly allocated isolated full-game
recording, diagnose its exact gaps, and verify reexecution before substantive
whole-game approval. No batch scaling or strategy/deck/model change.

## Current verified followup

The approved engineering tree was published as81f0e2d and read back byte-for-byte
against reviewed localbc7a821. The connected GitHub workflow changed commit
metadata, not source. Isolation followup698dadb also passed hosted CI.

Kernel-event diagnosis reproduced external synchronization recreating renamed
staging files in two managed-workspace runs; an external temporary-root control
did not reproduce it. This identifies the cause of staging resurrection, not
necessarily the older truncation. Active evidence is now isolated outside the
managed workspace, with exclusive atomic sealed-archive publication. Managed
CLI evaluation uses isolation automatically; direct live output there is
rejected. Five transport contracts and targeted collector integration pass.

Both sealed diagnostic transcripts received substantive critical-rules review.
Ninjutsu/Purphoros devotion changes, grouped GGS triggers, Ezio reflexive
elimination and Ramses alternate victory were consistent in reconstructed
states. Missing counter/damage/chosen-color/commander-history evidence was found
and implemented for future recordings; seven engine checks pass. No existing
game was backfilled or admitted. Explicit public reveal and exact payment-event
provenance remain incomplete. Zero new games, training admissions, model updates
or win-rate comparisons. Original captures and anomalous staging trees retained.

## Current engineering repair

Local commits implement durable staged game evidence, writer receipts/counts,
forced atomic finalization, ownership/control/zone fields and phased-out object
coverage. See EVIDENCE_WRITER.md. Ownership regression passes14 actual-engine
checks. Full Python suite passed179 before the final staging-resurrection guard;
its24 targeted follow-up checks pass. Public push was rejected by automatic
approval review; local commits are preserved privately, not claimed published.

Two fresh four-player diagnostics completed. Both original sealed captures pass
writer-origin counts/hashes, own-view visibility and ownership-field validation.
The first also passed external saved-byte restoration. The second live directory
later contained nine reappeared staging prefixes with the same game ID; original
finalized hashes and sealed capture remain intact. Preserve the directory;
resume rejects these unbound staging files without rewriting the journal.
Restoration from the original sealed capture passes. This is a reproduced
post-run retention symptom, not proof of its historical root cause.

A reader integration defect mistook completion-receipt JSON for game records;
fixed with a regression. No replay, game-evidence repair, learned promotion,
training admission or fully rules-reviewed game. No candidate counterpart was
launched after the live-directory anomaly. Historical quarantines remain.
Next: diagnose staging resurrection across workspace/tool boundaries while
using verified sealed captures for offline review. Complete all-seat rules and
critical-decision review before any paired strategic claim.

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
Recovered Cycle22 source passed141 Python tests; sixteen new harness contracts
bring the current verified total to157. Completed training was not replayed.
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

Cycle23 allocated two held-out seed/seat pairs. First pair recorded two Apex
wins on logged turn46 with equal canonical gameplay events (timing excluded).
Baseline has a verified durable checkpoint. Candidate is QUARANTINED: five
outer-log/audit files changed after finalized hashes; four streams lost valid
JSON tail rows. Original journal hashes and damaged bytes are retained. No
second pair launched, no replay, no full-game admission or performance estimate.
Neither stream contains the narrow Swan-context prefilter; activation is not
instrumented. This does not demonstrate a learned decision change.

commander_game_review.py now binds every review to finalized journal hashes,
rejects missing, unsafe, extra or changed evidence, and rejects unfinalized
attempts. It accepted the real baseline and rejected the actual damaged
candidate. Four new regression contracts bring the suite to157 passing tests.
The repair detects drift; the post-finalization truncation root cause remains
unknown. Never rebuild candidate evidence from matching baseline streams.

Next: diagnose post-finalization evidence mutation and implement a verified
immutable per-side capture before any new game. Preserve the failed pair and
the reserved second seed/seat allocation in the private ledger. Then complete
substantive rules/critical-decision review of the intact baseline, and only
after the evidence gate is reliable consider the second allocated pair.
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
Cycle22 and Cycle23 publications succeeded with saved receipts. The dashboard
shows the quarantined candidate and zero admitted full-game comparisons.
Verified code CI: run39108781493 (157 Python tests and launcher contracts).
The private recovery task was updated to the integrity hold; next-run time
remains unreported, so no continuous/private training claim. Browser visual QA is unavailable; static/data and
refresh/failure/retry contracts pass.
