# Private engine provenance and replay boundary

The evidence overlay instruments exact classes from the frozen executable,
including existing DragonMind fixes. It does not replace them with upstream
source. Offline ASM rewriting regenerates verifier frames using the executable's
class loader. Gameplay requires no agent, internal-JDK exports or network.
The build inventory lists every injected method and checks all other JAR entries
for byte equality. Experimental models remain disabled unless explicitly enabled.

`referee-events.jsonl` is an omniscient **private referee stream**, separate from
player snapshots. It records ordered initial zones, random-bit requests, engine
calls/returns, controller decisions, effect resolution, stack operations, events,
reveal recipients and mana/cost operations. It uses the same durable writer,
counts, receipts and final seal as the player streams. Never publish its raw
contents or use it as a pilot information set. Unsupported argument/result
objects are explicitly `unencoded`; they cannot be inferred to pass review.

Public reveals include all current players, even when the controller delivery
skips the owner. Restricted looks record their specified recipients. Per-controller
deliveries are separate events. A reveal does not move the card. Visibility
lifetimes still need substantive reconstruction from costs, effects, stack and
shuffle events; a delivery alone is not a persistent visibility entitlement.

Payment entries capture pool units, source identities, mana restrictions,
potential battlefield sources, chosen ability and X, optional/alternative costs,
commander-cast history and cost-adjustment returns. Non-mana cost decisions
include chosen cards. Actual mana-unit attempts retain success/failure and the
engine's test flag. Nested mana-planning calls are marked speculative; neither
those nor failed attempts count as paid costs. A potential-source inventory does
not assert every listed ability is legally activatable. Affordability calls and
cost adjustments outside a committed payment are not evidence of actual payment.

| Official CR, effective September 25, 2026 | Evidence obligation |
| --- | --- |
| 701.20a–e | Public reveal versus specified-player look, unchanged zone, duration/reordering |
| 106.4a–b | Remaining floating mana at payment and priority |
| 601.2b, 601.2f–i; 602.2 | Announced costs/choices, adjusted locked total, actual payment, activated abilities |
| 605 | Mana-ability timing and classification must be audited |
| 108.3–4; 800.4a | Stable ownership, controller changes, objects/effects on elimination |
| 903.8–10 | Command-zone casts/tax, commander-zone choices and combat damage |

Source: [Wizards Comprehensive Rules](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt), linked from [official rules resources](https://magic.wizards.com/en/rules).
Recording these fields is not proof the engine implements every current rule.

The opt-in `forge.referee.replayTape` plus mandatory `forge.referee.replaySha256`
loads a hash-bound reference tape. Recorded random bits drive a second execution;
every serialized initial-state/event/call/result must match in order. Only the
Set-derived card-statistics UI notification compares card membership without
iteration order; ordered zones and decisions remain strict. Missing,
extra or different records fail closed. This is **event-checked policy
reexecution**, not yet an engine loader driven entirely by recorded decisions.
Unsupported serialized objects remain gaps even when both executions match.
`referee_tape.py` checks structure and reports those gaps without granting rules
approval. No synthetic test or equal reexecution can independently approve a
whole game. Whole-game review and the strict learning gate remain mandatory.

Typed followup records stack/view targets, combat attacks/blocks, delayed reveal
payloads, replacement/static traits, structured map keys, priority owners,
engine visibility permissions, elimination states and the final state. Engine
permissions are evidence of implementation behavior, not independent rules
entitlement. Cost modifier hooks record source and before/after costs, including
reduction order. Color conversion and snow-spending flags are recorded.
`mana_unit_audit.py` independently checks pool membership and normal/generic/
hybrid/snow shard transitions; it does not certify mana-source restrictions,
entire payment transactions, ability timing or the whole game. Unsupported
cost representations stay explicit. Source hashes for both readers and this
checker are bound in future batch protocols.
