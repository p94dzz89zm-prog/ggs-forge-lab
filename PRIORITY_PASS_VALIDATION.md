# Priority-pass evidence checkpoint

Base published source: 4d22ce618e9c6b69e5230e70def6d35a597151ea.
This independent maintenance milestone leaves Stage48's reservation, dirty
checkout, partial prefix, completed fixtures and all seeds untouched. Ledger194
still has no owner/heartbeat/release; it cannot establish a safe takeover.

## What the observer checks

The private referee reader now checks completed outer, nonspeculative priority
passes independently of the replay driver. It compares the acting player's
identity/loss status against the recorded priority holder, checks unchanged
controller arguments and rejects ordinary untap priority. Cleanup is not
blanket-rejected: exceptional cleanup priority can exist under CR514.3.

For a nonempty recorded mana pool, the observer requires the current recorder's
immediately following public priority-pass announcement. It compares exact
color counts (including duplicate units), player identity, reason and visibility.
Recipients must match the recorded active-player snapshot, updated by recorded
elimination snapshots. Missing legacy announcements or active-player evidence
remain explicit gaps; altered counts/actors/recipients fail the scoped audit.
It does not silently reconstruct omitted announcements from hidden tape data.

Rules reference: CR117.3d and106.4b, September25,2026 official edition:
https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt
The official117.5 obligations (state-based actions and pending triggers before
priority) remain separate. Matching a recorded holder is NOT independent
derivation of who should have priority. No full priority or game approval follows.
Recorded active-player snapshots are likewise inputs, not independent proof of
correct elimination timing. Public announcement checks establish the recorded
emission and recipient domain, not an independently observed UI delivery.

## Validation and reproducibility

`python3 -m unittest discover`: 270 tests pass. Eleven new tests cover correct
counts, missing disclosures, altered player/count/reason/audience, eliminated
actors, untap, exceptional cleanup, selected actions, nested/speculative queries,
empty pools, missing context, audience completeness and elimination updates.
These are constructed observer tests, not new native game executions.

Read-only streaming inspection of the existing149802-record full-game tape
reverified its original615764572-byte writer digest and record count. Result:

| Scope | Result |
| --- | --- |
| Completed priority passes | 1543 |
| Consistent with recorded priority holder/phase | 1543 |
| Floating-mana passes missing recorded announcement | 9 explicit gaps |
| Fully checked recorded mana announcements | 0 on this older tape |
| Independent derivation of priority | Not approved |
| Complete rules-approved games | 0 |
| New gameplay / trusted training updates | 0 / 0 |

The nine gaps identify missing historical evidence, not nine proven native
rules violations. Existing157 cost-transition passes and157 missing historical
pool-after snapshots remain unchanged. No old evidence was backfilled.

## Recovery and next work

The source/test/report Git commit is the recovery point for this milestone.
Stage47 remains the verified private gameplay checkpoint at466 replay choices;
Stage48's513 local choices remain uncheckpointed. Before takeover, obtain an
explicit owner handoff or otherwise reconcile the unknown attempt; absence of
a local process alone is insufficient. Independent next work is causal
priority/stack/readiness instrumentation and separate assertions for the actual
SBA-trigger-priority cycle, followed by full-game review. No pilot training
until the whole-game admission gate passes.
