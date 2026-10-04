# Matched 100-game-per-deck collection

This collection schedules 100 independent pod-game slots for each unchanged
GGS list: 25 new seeds (20261038–20261062), each at all four seat rotations.
The decks do not face each other in the same pod. Each faces the same supplied
Jaymie Ezio list and the same Food and Fellowship / Turtle Power proxies.

Accepted v17 jar SHA-256:
`41cce57aa2e64156365440e33b8c9ca83eb406e4cbc53d0e4876b59f025af3c5`.
The cost-source experiment is not enabled. Decklists and pilot weights are fixed.

Two independent JVM workers use one game per process, private four-seat audits,
the existing commander-aware GGS pilot, stock Default opponent profiles,
1536 MiB heap, Parallel GC, throughput compilation and a 600-second game allowance.
The existing five-second AI decision allowance is unchanged.

The seed/rotation pair order is prespecified and shuffled with Python RNG seed
20261004. Submission order within each pair alternates between Apex-first and
Layered-first. Workers may advance independently: timing is descriptive, not a
controlled latency or throughput benchmark.

Every invalid slot receives at most one identical-settings retry after the initial
collection. All attempts remain recorded. No substitute seed is used. Persistent
invalid slots are not counted as losses, wins or draws. Matched-valid pairs are
the primary comparison, with all-valid outcomes and failure counts alongside.

The primary endpoint is GGS victory. Secondary metrics include seat-specific
wins, opponent victories, first commander-cast timing, recast activity,
announced GGS triggers, ninjutsu paid-return records, fresh combat observations,
observed creature-board peaks and simulation duration. They are descriptive,
not proof of a card's causal value. Exploratory uncertainty resamples whole seed
clusters to preserve dependence among the four rotations.

Run `diagnostics/run_matched_pod_collection.py` to collect data and
`diagnostics/analyze_matched_pod_collection.py` to produce allowlisted public
results. The runner checkpoints each game, analyzes it while raw audits are
available, and losslessly compresses and verifies those audits before reclaiming
the newly generated uncompressed files. Logs and every attempt are retained.

The protocol is not a claim that the collection has finished. Final counts,
results, uncertainty and unresolved slots will be reported after completion.
