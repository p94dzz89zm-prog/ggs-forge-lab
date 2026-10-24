# Byte-preserving recorder optimization

The natural-game JFR showed substantial recording cost. EngineEvidence built
a JsonObject, serialized it, and passed the String to DurableEvidence, which
parsed that same JSON and serialized it again with stream metadata.

The new synchronous JsonObject overload removes that duplicate conversion.
It copies top-level members before adding metadata, leaves nested values and
the caller unchanged, validates finite typed numbers and retains the String
entry point. Callers must not mutate an object until synchronous append returns.
Existing receipt hashes, progress writes, fsync, atomic finalization, interruption
behavior and post-seal refusal remain. EngineEvidence uses the structured path;
other callers retain their existing behavior.

The exact-base overlay builder verifies every unrelated JAR entry. No card
rules, replay driver, strategic policy, private original executable or Stage48
working artifact changes. The optimized executable remains experimental until
broader gameplay coverage; it cannot approve old or new games by itself.

Validation on actual production classes:

* String and structured260-row synthetic streams are byte-identical, including
  Unicode, escapes, numbers, nested data and overwritten metadata fields.
* Structured input remains unchanged; nonfinite numbers fail without a receipt.
* The native four-player pilot fixture produces the exact original399-row tape,
  SHA256 b3883056c7102bfbfb59b931831b9555061a7eb91e6600462dd96f71cb227528.
* Its independent2 mana cost/pool checks retain0 gaps.
* Existing finalization/post-seal and abrupt halt17 controls pass.
* The96MiB production-writer stream still finalizes under64MiB heap.
* All304 root Python tests pass.

Four fresh-JVM recorder microbenchmarks use the same private399-row native corpus
and a warmup phase. Each measured run writes6384 rows/16200589 bytes with identical
SHA256029bd3f1922dd250465d01e87ada2f7aebb96a99e706b729da43054909149db2.
Order is String/structured/structured/String. Original String-path measured times
are0.6628s and0.7667s; structured times0.4192s and0.5416s. These are two runs per
condition on one repeated corpus, not an uncertainty-controlled game benchmark.
No whole-game speedup, stronger strategy or rules-engine correctness gain is
claimed. Current full-game approvals/training remain0. Unsupported keyword and
full independent legality/state-transition obligations remain open.
