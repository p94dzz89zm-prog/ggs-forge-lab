# Separate pilots and natural-game progress diagnosis

Source-only/offline maintenance, independently allocated from Stage48. No new
game, seed consumption, native policy change, rules-engine repair or training.

## What actually exists

`pilot_architectures.py` defines an engine-owned action-offer/execution protocol.
Pilot A is a reproducible seeded least-visited action-kind policy with stable
ties. Pilot B is a separate fixed feature scorer for offline position experiments.
Only the engine can execute an action and must atomically recheck revision,
actor, costs, targets and timing. Invalid or stale choices cannot be promoted
to successful actions by either policy. Action tokens do not establish legality.

These are tested Python architectures, NOT integrated native Forge pilots.
Engine test doubles establish interface contracts, not actual Magic legality.
The existing Forge bridge offers timing-eligible candidates, with later payment
and target checks. It cannot be cast to a fully executable legal-action offer.
Native action enumeration/selection integration is the immediate pilot blocker.
Least-visited-kind exploration may still play badly or fail to finish games;
neither competence nor improved win rate has been demonstrated.

Pilot B does not read an omniscient tape, train, update weights, execute an
offline action or approve outcomes. Offline evaluation binds evidence bytes and
requires an independently supplied position verifier; a caller returning true
is not itself a rules proof. There is no production position verifier yet.
Self-play, opponent modeling, uncertainty, long-term planning, trusted datasets,
fixed strategic benchmarks and outcome training remain unimplemented here.

## Turn64 timeout: observed versus unknown

The new read-only streaming diagnostic binds the exact saved readiness bytes:
111725820 bytes, SHA256
`baa322692a8ed85ecffe4db3a8577be660ebce83ec501acae6d2a8f412e9cfda`.
All64 turns have priority offers;3262 offers total. The most offers in one
turn/phase is59. No exact recorded partial priority state occurs more than twice.
Final offered life totals are8/5/38/36, all four players active, with42/15/17/11
battlefield objects. This is actual advancing gameplay, not an observed fixed
priority-state loop. A partial snapshot cannot rule out omitted-state defects.

The original result explicitly reports the180-second engine timeout. The
previous188.439-second process duration is not a new measurement. There is no
historical CPU/IO profile or per-offer timing, so slow engine evaluation, recorder
overhead and weak strategy remain unresolved explanations, not proven causes.
Board growth/life changes show activity, not strategic quality or full legality.
Original incomplete frames and open calls remain intact. Nothing is resealed.

## Input-freeze foundation

`natural_game_inputs.py` fingerprints executable, Java, policies, four decks,
rules reference, a bound legality report and all resources before execution.
It requires explicit seed, source commit, argv, subprocess environment, four
policies, house configuration and bounded timeouts. Rechecking detects changed
inputs, including resource/deck/policy changes. This is a provenance helper,
NOT a launcher: it does not enforce argv-to-config consistency, validate report
findings or guarantee every implicit native input has been inventoried. Future
launch integration must supply only the recorded environment and enforce every
configuration choice rather than merely recording intended house rules.
It grants no deck-legality/game/training approval. The older attempt's missing
pre-run resource freeze is not retroactively repaired.

## Verification and gates

298 Python tests pass, including17 new deterministic, stale/unoffered/rejected
action, finite-score, position-evidence, partial-progress and input-drift
contracts. No native engine change was made; no new native regression claimed.
New complete games0; new independently approved complete games0; training0.
Stage47 remains466 verified choices. Stage48 unknown reservation unchanged.
Card indexing/implementation coverage and strategic benchmarks unchanged.

Next bounded milestone: integrate a native engine-owned action adapter for
Pilot A (including targets/cost choices/combat), validate it against native
regressions, then allocate a fresh seed with verified legal decks and actual
house-rule configuration. Freeze all inputs BEFORE launch and capture a Java
CPU/IO profile alongside full histories. A completed game still requires full
casting, mana, priority, stack, combat, trigger, SBA and terminal review; a
sealed stream or passing prefix is never complete-game certification.
