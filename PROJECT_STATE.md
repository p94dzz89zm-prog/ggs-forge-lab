# DragonMind verified state and recovery

Repository `p94dzz89zm-prog/ggs-forge-lab`, branch `fix/pilot-recovery-v35`.
At session start read AGENTS.md, this file, RESUME_DRAGONMIND.md and the current
authoritative private ledger/project state. Reconcile leases, seeds, saved
checkpoints and unknown outcomes before compute. Chat is not authoritative.

## Swan Song and a created-object identity blocker

Driver contracts1773/1985. The engine executes348 consecutive recorded
choices, matches172 canonical gameplay lines and779 engine RNG requests.
This is not complete-state replay verification: the first actual Bird Token is
original card412 but replay card406. No identity mismatch is silently accepted.
Actual target choice is independently recovered from original public cast
announcement15114 (Swan Song242 targets Rampant Growth381), applied to a live
legal stack spell, and paid with actual Island blue. Native resolution moves
both spells to their owners' graveyards and creates a2/2 Bird Token owned and
controlled by the countered spell's controller. Scoped legality/ownership
checks pass; exact created-object identity comparison fails and is retained.

Four corrected actual four-player controls pass: real selection/payment/
counter/token, missing target, illegal artifact target and tapped mana source.
Three fixture setup/assertion failures retained: stack isn't a player zone,
stack setup resets priority, and zone moves invalidate old Card references;
current-zone IDs are checked instead. Affected encoder test rejects missing
or ambiguous public target provenance. Independent pool/shard arithmetic
checks1 fixture and12 original-prefix paid units. No unrelated suites rerun.

Two gaps now need work: causal identity allocation/mapping for created objects
(Bird412→406), then next controller root348 Sam Partner trigger coordinator.
Original and actual token creation are both nested in TokenEffect.resolve;
matching effects/characteristics alone do not prove allocation-cause history.
AI speculative allocations are a hypothesis until instrumented.212 roots
remain unsupported; complete independent rules approval0, training0 and
eligible comparisons0. Existing sealed evidence remains unchanged.

## Targetless Rampant Growth casting and actual payment

Conditional coverage1771/1985; original consecutive prefix303,774 engine RNG
requests and146 canonical gameplay lines agree. The exact targetless Rampant
Growth definition is supported for live hand-spell selection and actual mana
payment, with source/parameters, timing, restrictions, alternative/additional
cost and X exclusions. Actual engine casting creates the stack object; its
library effect is not copied or assumed resolved. Original299 pays Command
Tower green and Plains white for1G. Four targeted actual four-player controls
pass: valid selection, missing source, altered definition, and real1G payment
from Island/Forest. Affected encoder test passes. The original prefix verifies
unchanged earlier casting/payment paths as well.

Independent pool/shard checker validates2 fixture and8 original-prefix paid
mana units and nested green choice. Initial checker expectation7 omitted the
Phoenix cast's earlier unit; corrected to8 with all arithmetic guards intact.
No whole-game rules certificate. Next303 is Swan Song selected in response to
Rampant Growth; historical public stack announcement identifies its target,
while legacy targets[] omits it. Need live stack-target reconstruction, actual
blue payment, counter resolution, Bird creation and independent legality.
214 original roots still lack contracts; approved games0, training0, eligible
pilot comparisons0. Historical archives remain unchanged.

## First actual combat reconstructed

Conditional driver contracts1769/1985; consecutive original replay298/1985.
774 engine RNG requests and143 canonical gameplay lines match. Two recorded
single-Phoenix player-attack declarations now have bounded contracts. The live
actor/turn/step/empty stack, untapped controlled creature, haste/sickness,
legal opponent/defender, native attack restrictions/requirements and absent
attack costs are checked. Recorded attacker/defender choices are applied to
actual Combat; the caller performs tapping, triggers and damage. Invalid
self-defender and tapped attacker reject before combat mutation. The positive
four-player fixture and affected encoder test pass. A fourth actual native-AI
fixture traces defender-selector RNG; static review also identifies attack
aggression percent choices. Only controller declarations and cost-estimation
calls are allowed inside the bounded original selector scope; unknown effects
remain unsupported. No broad AI fallback or recorded outcome copying.

A separate checker confirms real caller tap,1 combat damage, defender life
39→38 and no blockers, matching all4 relevant original public events. This is
scoped arithmetic/provenance verification, not independent full combat or
whole-game approval. Official CR508.1a–f governs declaration, defenders,
restrictions/requirements and tapping; additional attack costs remain rejected.

Next298: Rampant Growth hand-spell selection (ChangeZone API), followed by
actual mana payment and hidden-library selection/reveal/shuffle.216 original
roots remain unsupported. No complete replay or independently approved game;
training and pilot comparisons remain gated. Original evidence is unchanged.

## Empty Partner search and private look delivery

Conditional coverage1767/1985; actual original prefix264 decisions,774 engine
RNG requests and126 canonical gameplay lines match. Decision197 reconstructs
the optional empty Frodo Partner library search from live source/target,
destination/origin, offered domain, complete library order, ownership and look
recipient. It invokes actual controller delivery, returns the recorded null
choice and lets the caller execute the real shuffle. All three native delivery
calls show the same89 cards only to the searching player. No recorded zone or
shuffle outcome is copied. Official CR effective September25,2026:701.20e,
701.23a–b and702.124j govern private looking, search/fail-to-find and Partner.

Targeted four-player valid, wrong-recipient and wrong-library-domain controls
pass; affected encoder test passes. Three fixture setup failures are retained:
controller interception class changed with early audit setup, and the pinned
single-zone DelayedReveal constructor discards its message argument. The
corrected fixture uses the actual Set-zone constructor matching this capture.
No unrelated suites rerun. Original archives and prior checkpoints unchanged.

Next original decision264: first declareAttackers, actor2 during turn7.
Attack declarations and defender choice require independent combat legality,
actual declared attackers and subsequent trigger/damage reconstruction.218
original decisions remain outside driver contracts. Whole-game independent
priority/APNAP, costs, combat, visibility, ownership/elimination and terminal
outcome verification are still incomplete. Full approvals0, training0 and
eligible comparisons0. Historical truncation cause remains unproven.

## Explicit optional-action confirmations

Conditional coverage1766/1985 includes ten immutable confirmAction choices.
The recorded boolean is returned only after checking actual source identity,
API/parameters, enum mode, prompt and absent extra context. The caller performs
the actual effect; confirmation copies no library/search/zone outcome. Actual
four-player accept, decline and wrong-prompt rejection pass; the affected
encoding check passes. The original game reaches197 consecutive choices,
686 engine RNG requests and matching canonical gameplay. It stops before
chooseSingleCardForZoneChange197: optional empty Partner search with a delayed
library reveal. Reveal entitlement/delivery and shuffle must be reconstructed,
not skipped to manufacture a pass. Full approvals0; no training or pilot claim.

## Recorded player-entity choices

Conditional driver coverage1756/1985 includes six pure player choices with no
delayed reveal, extra context or argument mutation. Offered IDs must be unique
and match the actual live domain; source/API/parameters, prompt and optionality
must agree. The driver returns the selected live Player, or null only when
optional; it applies no effect outcome. Card-entity choices remain unsupported.
Actual four-player selected-player, unoffered-player rejection and optional
decline controls pass; one affected encoding check passes. Separate checks
confirm membership of all six original choices, not independent derivation of
the offered domain. The original replay reaches196 consecutive decisions,
686 engine RNG requests and matching canonical gameplay, then stops at
confirmAction196: the optional Partner library search. Full approvals0;
no natural games, training or strategic improvement from this stage.

## Partner trigger and direct target provenance

Conditional driver coverage1750/1985; original replay195 consecutive decisions,
686 engine RNG requests and96 canonical gameplay lines match the saved original.
The next explicit failure195 is chooseSingleEntityForEffect during Partner
resolution. One Partner trigger coordinator now reconstructs recorded order and
the player target from the original public stack announcement, validates the
live underlying ability's target domain, and executes actual zero payment and
stack addition. The other53 trigger coordinators remain unsupported.

Recorder defect established: SpellAbility.getUniqueTargets traverses parent
abilities, omitting this ability's own targets. New direct_targets records the
actual local target choices; wrapped_ability records the underlying trigger.
Legacy targets retain their documented ancestor meaning; historical evidence
is unchanged. Separate review confirms original/replayed source99, actor0,
target0 and public entitlement, with explicit direct underlying target evidence.
Official September25,2026 CR603.3b/d,603.5 and702.124j guide this bounded review;
global APNAP/trigger/visibility and whole-game legality are not approved.

Actual four-player target/stack and invalid-target controls pass. A native AI
trace identifies pre-payment randomness in ChangeZoneAi.hiddenTriggerAI's
preferred-defender target selector. Only bounded Partner preparation randomness
is projected out; effect-scope randomness excludes support. Opt-in RNG-origin
diagnostics remain default-off. Initial trace reset during an active game was
correctly rejected; corrected setup before recording passes, failure retained.
An affected encoding check passes; no unrelated suites repeated. Recovery used
the last saved189 prefix; interrupted unsaved195 observations were not assumed.
Fully rules-approved0, training0, measurable pilot improvement unestablished.

## Selected mana, commander payment and original prefix189

Conditional coverage1749/1985; original prefix189 choices reconstructed from
recorded choices, with686 engine RNG requests and matching canonical gameplay.
Payment184 now executes Command Tower's selected black mana and Brushland's
selected white mana plus its actual1 self-damage subability. No pool, damage or
zone outcomes are copied. Nested color choices check live production legality,
the offered domain and original choice. Unsupported subabilities still reject.
Live Commander permission selection explicitly binds the recorded ephemeral
ability identity to the actual copied spell before subsequent payment checks.

Actual first-cast, taxed-cast and illegal-color controls pass. The taxed cast
pays2WB from four actual units; illegal color rejects before tap/damage. Initial
tax fixture omitted the2 in the already adjusted component; failure retained,
corrected control passes. First original replay found the copied-ability ID
binding gap; failure retained, corrected replay reaches189. Separate checker
validates5 actual-prefix and6 fixture paid-unit pool/shard transitions, recorded
commander tax counts and nested color choices. These remain scoped checks.
The first fixture harness omitted durable finalization; only affected positives
were repeated with explicit fixture seals. Final compiled produced-color guards
pass floating-mana and tax controls, plus the original189-decision replay;
95 canonical gameplay lines match. All earlier failures/partial streams retained.
Next stop189 is orderAndPlaySimultaneousSa;54 trigger-order roots unsupported.
Fully approved games0; full-game replay/independent legality still pending.

## Command-zone selection and original prefix184

Conditional coverage1742/1985 includes ten plain command-zone permanent-spell
selections. Actual original replay reaches184 consecutive choices and stops
before payment184, following its successful live Frodo selection. It consumes
686 engine RNG requests and matches the initial state and canonical transcript.
The driver checks designation, owner, prior cast count and2-per-cast metadata,
then binds the live Commander Effect permission with full mana cost. It neither
copies a zone transition nor grants payment. Official CR903.8 and702.124d
require commander-specific cast counts, including separate partner counts.

Actual selection, missing-source and wrong-count controls pass. The first
positive control failed because a raw hand-zone ability lacked the engine's
live command-zone permission; that failure is retained. The corrected positive
binds the actual permission and passes; the affected encoding test passes.
Next payment184 uses Command Tower color choice and Brushland color choice
plus damage subability. These are unsupported, explicitly rejected; no silent
approximation. Fully rules-approved0; full independent legality remains pending.

## Partial mana spending and original prefix183

Driver-contract coverage1732/1985; continuous original replay183 decisions,
684 engine RNG requests and89 canonical gameplay lines match. Fixed tap-only
Sol Ring production now yields2C, spends actual selected units and preserves
the remaining1C. The original payment includes a second failed attempt after
the cost is paid; replay executes and checks it without spending that unit.
Floating-pool passes check live inventory. Production, payment, pool-after and
public count-only announcements are recorded separately; private referee
context is not declared public. CR106.4/106.4a/106.4b and118.3a guide these
scoped checks (official September25,2026 Comprehensive Rules).

Two actual four-player fixtures pass: partial spending and multiple sources,
both with a failed redundant attempt, priority/resolve persistence and actual
PhaseHandler.onPhaseEnd clearing. Five affected Python tests pass; two payment
encoding tests rerun after failed-attempt support changed. An initial test
fixture insertion error is retained and corrected. Original state/canonical
prefix consistency and separate mana arithmetic pass; no full rules approval.
New original replay stops explicitly at decision183: first command-zone cast
of Frodo, Adventurous Hobbit. Command-zone spell selection and commander cost
payment remain unsupported. Original announcement provenance is still an
independent audit obligation; replay announcements do not repair old evidence.
Fully rules-approved games0; training admissions0; pilot improvement unmeasured.
Original sealed archives, decklists, models and atomic recovery remain unchanged.

## Recorded basic-land mana execution

Driver-contract coverage is1720/1985, adding six fixed-cost permanent-spell
payments using recorded basic-land tap and individual mana-spending choices.
The extractor retains the actual nested choice arguments. The driver prechecks
live source abilities and adjusted cost, then pays the tap cost, resolves the
actual mana ability and spends the actual produced unit through engine APIs.
It copies no tapped, pool, payment or spell-resolution outcomes. Other payment
sources, extra production, conversions, X and ambiguous identities remain gated.

The original four-player game now executes112 recorded decisions, including
two actual Island/Sol Ring payment-and-resolution sequences. Its684 engine
random requests and56 canonical gameplay lines agree; it safely stops at the
next unsupported payment, decision112. Partial stream/error result retained.
Independent arithmetic checks six recorded payment color/count plans; two
actual replay pool/shard transitions pass the separate mana checker. These are
scoped checks, not independent whole-game legality or complete game approval.

Three live controls pass: actual payment/cast/resolution, tapped-source rejection
and wrong-color rejection. An initial fixture assertion inspected the pre-stack
ability instead of the actual stacked copy; failure retained and only that
fixture retried against the stacked object. One relative-path compile failed
before launching; retained. Seven relevant Python tests pass after extraction
of nested payment choices changed. No unrelated passing engine suite repeated.

Payment-selector RNG is distinguished from actual effect RNG. The pinned
ComputerUtilMana disassembly's sole random invocation is its source-reservation
preference. Only requests with that innermost selector scope are skipped;
instrumented game-effect randomness excludes this family. This is a bounded,
causally reviewed prefix; not a general rule to discard RNG inside payments.
Remaining265 decisions include57 payments,48 priority actions,54 trigger orders
and the remaining effect/combat families. Fully approved games0, training0.
Next reconstruct the fixed nonbasic/artifact mana sources at decision112 and
preserve any floating mana with required public announcement provenance.

## Plain hand-permanent spell selection

Driver-contract coverage is1714/1985, adding20 plain fixed-cost hand permanent
spell selections. The driver binds the actual live card and its unique spell
ability using source/API/parameters/cost, verifies timing and engine restrictions,
and returns that object without copying a stack or battlefield outcome. X,
alternate costs, modes, targeting, subabilities and command-zone casts remain
unsupported by this family. Three actual four-player selection/invalid-source
controls pass. Targeted encoding/projection tests pass; an observed file-handle
warning was repaired and the projection check rerun specifically for closure.

The original game now consumes67 decisions and684 engine random requests,
including selection of its actual Sol Ring object/ability. Initial recorded
state fields and35 canonical gameplay lines agree. It stops at payment decision67
with an explicit diagnostic, engine_error result and retained partial stream.
The next boundary is actual resource-changing payment, not spell resolution.
Fully approved games0, training0; no new natural game or pilot improvement.
CR601.2a–h distinguishes spell proposal, cost determination and payment; this
selection support does not certify that the spell has been legally cast.

## Original-game decision-driven opening replay

The original four-player Commander game now executes66 recorded decisions
without recomputing AI choices. Its684 engine random requests replay separately
from43 requests inside skipped pure-choice AI scopes. Registered initial-state
fields and the canonical gameplay prefix agree; only three previously added,
nullable cast-provenance fields are new. Replay stops at decision66, the first
unsupported selected spell (Sol Ring), before its payment. The retained result
is engine_error with a partial stream and an explicit decision/RNG diagnostic,
not a complete game. No full-game seal or approval is granted.

Randomness projection is deliberately restricted to the supported pure-choice
prefix. Mixed controller actions may execute actual effects, so their random
requests must not automatically be discarded as AI work. Width, value, checksum
and exhaustion controls reject; one targeted projection test passes. The engine
RNG provider cannot combine with strict same-policy event replay, and remains
disabled unless explicitly configured. Choice-contract coverage stays1694/1985;
continuous original decisions executed66, fully approved games0, learning0.

Next implement selected spell/ability reconstruction and actual mana/resource
decisions at the observed boundary, then extend the causally reviewed prefix.
Full priority, triggers, combat, visibility and independent legality still need
review. Production replay also needs an explicit decision/RNG terminal check at
successful game finalization before any whole-game replay certificate.

## Explicit zero-mana acknowledgments

Driver-contract coverage is1694/1985, adding79 zero-only effect payment choices.
CR118.5 requires acknowledgment even when no resources are required. The driver
uses the recorded pay choice, binds the live source/parameters/actor, verifies
both component and entire ability cost are zero-only, then runs actual engine
mana adjustment and requires no unpaid shards. X, waterbend, announcements,
non-mana costs, prior spending and non-effect calls reject. It invokes no AI
mana selection. The other63 payment roots remain explicitly unsupported.
Three new actual four-player fixtures pass: zero payment without resource
transfer and rejection of nonzero and non-mana payment cases. One targeted
Python test covers exclusion of resource-changing and announce/X cases.
Official September25,2026 CR107.4d,118.3a and118.5 support this narrow scope.
No spell/activation is inferred legal from its zero mana component.

Original-game decisions executed0; fully approved games0. Next address actual
resource-changing payments and spell/ability choices, including deterministic
ability identity and engine-versus-AI RNG separation. Trigger order54 and other
effect/combat families remain. Models, training gates and sealed captures remain
unchanged. A successful fixture is not a fully replayed or rules-approved game.

## Land actions and pregame choices

Driver-contract coverage is1615/1985: the preceding1575 plus32 hand-land
special actions, one starting-player choice and seven mulligan choices.
Land choices rebind actual hand cards, check live type/ownership/priority,
main-phase timing, empty stack and engine land-play restrictions, then execute
through the normal engine. All32 recorded land names independently match the
pinned card database. The starting-player domain uses only registered player
identities from the later GameStarted record, never its resulting game state.
The mulligan hook's Player argument identifies the starting player, not the
choosing player. The caller still performs reshuffles and London bottoming.

Five new actual four-player fixtures pass: legal land execution, illegal second
land rejection, pregame choices with a different starting player, unavailable
starting-player rejection and empty-hand mulligan rejection. Seven relevant
Python tests pass after the extractor's initial-state scan changed. These
fixtures are not complete Commander games. Original-game decisions executed0;
fully approved games0. CR103.1,103.5/103.5c and305.1–305.2a were checked against
the official September25,2026 Comprehensive Rules. Full pregame ordering,
reshuffle/bottoming and global action-by-action legality remain to be verified.

Recovery also found a local runtime ZIP truncated to an exact prefix of its
intact saved original. A fresh copy restored the expected full checksum.
This establishes a local cache-retention anomaly after interruption, not the
cause of historical game-log truncation. Historical sealed evidence is intact.
Next implement real payment decisions and selected spells/abilities;54 trigger
orders and remaining effect/combat choices also need support. Continuous replay
must separate engine randomness from skipped AI randomness and rebind dynamic
ability identities. No training, pilot comparison or new game was run.

## Encountered effect choices

Driver-contract coverage is now1575/1985:1534 empty-pool priority passes plus25
replacement-effect,14 counter-type and2 color choices. Offered replacement
identities must be unique and bind to actual live effects; the chosen effect
must not have run and its engine requirements must hold. Counter choices bind
to offered enum objects with source/prompt/parameter checks. Color choices
preserve permitted colors and cardinality, including excluded colors.
An actual Cinder Glade/Hydra/Thriving Grove fixture checks all three families
without applying copied outcomes. Three invalid-choice controls reject and
retain exact diagnostics. Three new targeted Python tests pass. Four launch
failures after a fixture compile error were retained; only those unstarted
fixtures were retried after correcting the Iterable check.

All142 payment roots return true;90 have zero-mana components without recorded
argument mutation, while52 mutate arguments. Returning true for the latter
would skip actual resource changes. Even zero components need adjusted-cost
validation before support. The91 selected priority actions include32 apparent
land special actions, with spell/activated ability choices still requiring
proper reconstruction. No payment/cast outcome is copied to gain coverage.

Independent checks confirm original offered-domain membership for the41 newly
supported effect choices. They still trust the offered domain; independent
replacement applicability, pending actions and continuous full-game replay
remain unresolved. Original-game decisions executed0; full approvals0. Models,
decks, historical evidence and training admissions remain unchanged.

## Encountered priority-pass replay

Driver-contract coverage is1534/1985 recorded decisions: empty-mana-pool priority
passes now use recorded choices, not recomputed AI decisions. The driver checks
the live actor, turn, phase and priority holder; wrong context and wrong holder
reject with reproducible private diagnostics and cannot complete. An actual
four-player controller fixture passes even with a spell available, leaving
resources/stack unchanged. Two actual invalid-context controls reject. This is
row-level supported coverage, not1985 decisions executed in a continuous replay.
Original-game replayed decisions remain0; whole-game approvals0.

Of1634 priority roots,1543 pass and91 select actions. Nine passes retain mana
and remain unsupported until public mana-announcement provenance is implemented.
All1985 roots retain mechanic, transition, rules obligations and support status.
The independent priority consistency check trusts the recorded priority holder;
deriving global priority, stack readiness, pending state-based actions and
triggers remains unresolved. It cannot confer full rules approval.

Next continue with the encountered142 payment roots and91 selected priority
actions, including ability identity/clone/land binding, targets, modes, X and
non-return mutations; starting-player/mulligan, triggers, combat, replacement
and effect choices also remain. Do not replace these actions with recorded
outcomes, drop unsupported rows, or train from this evidence. Policies/models,
decks, historical archives and reserved seeds are unchanged.

## Complete-capture decision coverage

The new streaming extractor retains every non-speculative root controller
decision, including explicit unsupported records and original call/return record
references. It checks source bytes against the archived checksum, call/return
nesting, initial state and completion before exclusive publication. Nested AI
implementation choices are not double-counted. Mutated arguments require explicit
driver support; they cannot silently become pure return-value decisions.

Applied to the existing149802-record complete capture, it retains1985 root
decisions across17 hook signatures. Priority selection accounts for1634,
mana payment142, simultaneous-ability ordering54, attack/block declarations43
and combat damage assignment19. Neither of the two currently implemented bounded
fixture families occurs in this game: current driving coverage is0/1985.
This explicitly limits the preceding fixture result. Do not infer full-game
replay readiness from that result or repeat those fixtures unchanged.

Next implement the encountered priority-selection return types and recorded
ability mutations (including targets, modes and X), with live legal-candidate
binding. Starting-player/mulligan, payment, triggers, combat and all other
encountered choices also remain. No unsupported row may be dropped. Five new
extractor tests cover nested roots, unsupported preservation, mutation/invalid
choice rejection, source integrity and incomplete/unpaired evidence rejection.
No new simulation, training, full-game approval or pilot comparison.

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
