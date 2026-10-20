# Independent mana audit repair

This bounded maintenance milestone runs separately from the existing Stage48
reservation. It does not modify replay encoding, engine source, private games,
reserved seeds, model weights, or the Stage48 checkout.

Base: d21790b3b47af27a3183f0611b02ef043e91695d.

## Reproduction and repair

The independent mana checker previously accepted a U unit paying a W shard
when the recorded possible-color-use mask was -1. Python bitwise operations on
negative integers see leading set bits, so the mask erroneously enabled every
color. The reproducer returned None (approval) before repair.

Require an exact integer in the six-bit domain 0..63 before interpreting the
matrix. Reject negative, out-of-domain and non-integer masks. Zero remains a
valid empty conversion set and cannot pay a generic shard. Ordinary masks,
hybrid payments, snow and colorless distinctions retain their existing checks.
This validates the recorded representation; it does not independently derive
conversion permissions or mana restrictions from the complete battlefield.

Validation: 42 tests pass across test_mana_unit_audit, test_referee_tape,
test_validation_evidence and test_learning_gate. New controls cover malformed
masks and the valid domain boundaries. No new gameplay or training executed.

## Development dashboard at inspection

| Field | Evidence status |
| --- | --- |
| Durable replay checkpoint | Stage47: 466 choices, 1043 RNG requests, 223 transcript lines |
| Stage48 | Reserved in ledger194; separate checkout has unpublished local work; do not duplicate |
| Local Stage48 report | 513 choices, 247 transcript lines, 1791/1985 conditional contracts; not checkpoint-certified by this milestone |
| Independent whole-game approvals | 0 at current durable checkpoint |
| Independently validated decisions | No aggregate certified count established; scoped fixture checks remain separate |
| Rules versus tooling failures | This repair addresses audit input validation, not a demonstrated native Magic rules defect |
| Card indexing / execution coverage | No current complete denominator established here; conditional replay contracts are neither metric |
| Pilot benchmark / training | No new games, updates, promotion or demonstrated strategic improvement |
| Next priority | Reconcile Stage48 owner/evidence and persist it; then continue replay and whole-game legality review |
| Recovery | Existing Stage47 immutable archive retained; this repair is recoverable from its Git commit |

No complete-game, universal card-implementation or autonomous-learning claim
follows from these checks. Keep uncommitted Stage48 results provisional until
the owning workflow seals, saves, restores and records the checkpoint.
