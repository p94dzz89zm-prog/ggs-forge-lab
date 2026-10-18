# Durable game evidence protocol

The production game path now begins a unique seed/UUID identity before simulation.
Audit rows go to exclusive `.partial` streams with monotonically increasing
sequence numbers. FileChannel writes preserve complete serialized rows, with a
forced progress checkpoint every 128 rows. Successful finalization forces and
closes channels, checks observed bytes against the writer's in-memory hash and
counts, atomically renames streams, syncs directories and writes separate stream
receipts. Canonical transcript and result use forced staged files and atomic
publication. A final game receipt binds status, event count and canonical/audit
checksums. It is written last. Unsupported atomic moves fail; there is no
non-atomic fallback. Existing output paths are not reused.

The Python collector stages the console log too. Its completion gate reopens the
writer receipts, validates every JSON row, sequence, game identity, count, hash,
four-view coverage and ownership schema. Missing receipts, partial streams,
changed bytes and interrupted results cannot become completed evaluation rows.
Exclusive side captures and external saved-byte readback remain additional
checks after collection. Absolute runtime paths are not stored in receipts;
restoration checks are relative to the selected evidence root.

A forced JVM halt in the production writer demonstrates interrupted-write
rejection while retaining partial evidence. This reproduces interruption, NOT
the historical post-finalization truncation. Its original root cause is unknown;
none of simulation, recovery, workspace shutdown or external mutation has been
proven responsible. Old damaged evidence stays quarantined. Hashes must never
be rewritten to bless changed bytes. No interrupted game is automatically run
again.

## Ownership scope and official rules

Player-visible card records include owner, controller, zone, token status and
phased-out status. Outside the battlefield/stack, controller_id uses owner as
the rules fallback and controller_basis makes that explicit. Face-down exile
records include ownership/control/zone without disclosing card identity.
Snapshots include phased-out battlefield objects, which the previous default
zone enumeration silently omitted. Opponent hands/library order stay hidden.

Engine regressions exercise temporary theft, graveyard return, phasing,
controller departure (control returns), owner departure (object leaves), phased
owner departure, commander identity after theft and command-zone return, and
hidden-card visibility. Direct moveToCommand tests the recorded transition; it
does not independently certify every commander replacement choice or tax.

Rules checked against Wizards' official September 25, 2026 Comprehensive Rules:
108.3 and 108.4 (ownership/control), 702.26k (phased-out owner departure), 800.4a
(multiplayer departure), 903.8 and 903.9a-b (commander tax/zone choices).
https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt

Record integrity and scoped regressions are necessary, but do not certify every
full-game action or decision. Full review/learning gates remain unchanged.

## Synchronization replay mitigation

A bounded kernel-event reproduction observed renamed staging files recreated
by a separate synchronization operation after finalization. Two runs inside
the managed workspace reproduced this, including a serialized control; a run
outside the workspace did not. This establishes a cause of the staging-name
resurrection. It does not prove the origin of older truncated records.

Run future evidence-producing stages through isolated_evidence.py with active
output under the system temporary directory outside /workspace. The command
receives a fresh {output} directory. Raw output is retained there on failure.
Only a hash/manifest-verified sealed archive is atomically linked into the
workspace; cross-filesystem publication fails closed. Restoration verifies the
archive and creates a fresh external directory, never merges a stale live tree.
Game commands must still use the writer, original-finalization, rules-review
and learning gates. Stage exit0 alone is not a game or learning approval.
