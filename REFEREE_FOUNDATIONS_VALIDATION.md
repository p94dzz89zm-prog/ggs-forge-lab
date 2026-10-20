# Independent referee foundations checkpoint

Base source: 6173f57fcec72930a8545a03e2b206aaaa440fe1.
Scope: nonconflicting evidence-reader and mana-resource assertions. No engine,
replay-driver, model, deck, seed reservation or Stage48 evidence was modified.

## Coordination findings

The authoritative private ledger194 still reserves Stage48 with a start and
15-minute budget, but supplies no stage-specific owner, heartbeat, lease expiry,
or release/handoff record. No matching local Java/compiler/collector process
was observed. This does not establish another session has stopped. Reservation
and unknown outcomes remain preserved; no takeover or gameplay rerun occurred.

The local 513-choice report is provisional: its replay referee stream still has
a `.partial` suffix and an in-progress writer receipt, rather than a final seal.
Do not convert the prefix to a completed tape or replace its expected failure
with a fabricated terminal record. The separate Signet fixture has a complete
127-record receipt; its bytes, size and digest were verified before read-only
inspection. Both recorded payments pass independent cost and pool transitions.
This fixture lacks a full initial game state and cannot approve a game.

Stage47's saved archive still matches its original outer SHA256 and all ZIP CRCs
(34 members). This check preserves the known recovery boundary; it is not a new
full member-manifest restoration or game approval.

## Reproduced failures and repairs

1. The old reader accepted format=true, a return call_id=true matching call1,
   parent_call_id=false matching root0, and completion calls=1.0. These are
   Python numeric-equality aliases, not valid typed engine evidence. Require
   exact integer schema/identity/sequence/count fields and nonempty call hooks.
   Explicit speculative markers must be booleans; strings cannot bypass actual
   payment checks. Reject duplicate initial states even in scoped-fixture mode.
2. The old reader checked cost reduction but did not assert the spent unit left
   the pool. A synthetic successful payment could keep the unit and still pass.
   Now compare before/after pool multisets and remove exactly the recorded unit.
   This detects absent units, retained units, extra spending, changed survivors
   and duplicate-unit errors. Missing legacy pool snapshots remain explicit
   gaps, rather than becoming passes. Schema tests reject ambiguous mana IDs
   and snow status.

Rules basis for resource removal: CR118.3a, September25,2026 edition, retrieved
from the official Rules page on October20,2026:
https://magic.wizards.com/en/rules
https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt

The new counter checks recorded per-unit pool conservation. It does not derive
mana production legality, spending restrictions, replacement effects, or other
intervening resource effects. An unexplained transition blocks this scoped
audit; it is not automatically a proven native rules-engine defect. Historical
records are not rewritten or retroactively approved.

## Reproduce

Run `python3 -m unittest discover`: 259 tests passed.
Focused suites: test_mana_pool_audit, test_referee_tape_types,
test_referee_tape and test_mana_unit_audit: 28 tests passed.
The added regression modules include the malformed-ID and retained-mana cases;
the existing successful-payment controls remain unchanged.

## Dashboard

| Metric | Verified status |
| --- | --- |
| Replay recovery checkpoint | Stage47, 466 completed choices |
| Stage48 | Reserved; 513 locally reported choices remain uncheckpointed |
| Independent additional checks | Typed call causality; exact mana pool removal |
| Existing sealed fixture inspected | 127 records; 2 cost transitions and 2 pool transitions pass; no gaps |
| Complete rules-approved games | 0 |
| New games / training / pilot promotions | 0 / 0 / 0 |
| Card implementation coverage | Not established by this work; distinct from indexing and replay contracts |
| Outstanding rules review | Full casting/priority/stack/combat/SBA and global state legality |
| Next priority | Resolve Stage48 ownership and preserve its interrupted-prefix evidence; continue independent full-game referee coverage |

This Git commit is the recovery checkpoint for these public sources and
regressions. The prior immutable private game checkpoint remains unchanged.
