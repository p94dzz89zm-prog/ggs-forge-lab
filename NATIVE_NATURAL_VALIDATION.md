# Native Pilot A natural-game diagnostic

The deterministic native rules-validation policy completed one fresh natural
four-player Commander diagnostic: turn36,41.442 engine seconds,48.505 wall
seconds,98.254 user and6.866 system CPU seconds,801108KiB peak RSS. This is a
completed natural engine outcome, not an independently rules-approved game.
No scripted victory, outcome training, strategic promotion or deck recommendation.

Runtime inputs were frozen before execution and verified unchanged afterwards:
four archived decks, seed, policies, command/environment, configuration, source
commit, Java/executable and resource fingerprints, and rules-reference metadata.
The private recovery checkpoint preserves all inputs, actions, RNG, events,
canonical transcript/result, console, JFR, writer receipts and audit reports.
Exact source/runtime provenance is in that checkpoint; raw histories and decks
are deliberately excluded from the source repository. The executable is restored
from the separately saved and verified structured-writer delta checkpoint.

Installed Commander deck-conformance checks passed. Independent Oracle/ban-list
review remains incomplete. The frozen profile is standard Commander; it does
not certify the requested no-commander-damage/three-free-seven house profile.

## Independent checks and their limits

- All6 writer receipts and the canonical result/transcript hashes verify.
-163045 engine records contain79951 paired calls, one four-player initial
  state,3142 RNG requests and155 visibility events; no open call remains.
-131 actual successful mana-unit cost and pool transitions pass with0 gaps.
-1587 passes agree with recorded priority-holder fields. Priority entitlement
  is not independently derived from the rules.
-1680 readiness windows pass the scoped protocol checks;1 game-over exit is
  unverified. Readiness snapshots remain partial diagnostics.
-2 KeywordWithCost values are unencoded. Complete stack/combat/trigger/SBA,
  commander, replacement/layer and terminal derivation remain incomplete.

The prior profiled stock-policy diagnostic completed turn47 in107.563s. The
old turn64 attempt timed out and remains incomplete. Different seeds and policy
and writer changes prevent a causal speedup or strategic comparison. The old
partial snapshots progressed (maximum observed exact repetition2), so they do
not demonstrate a fixed-state priority loop; the exact timeout cause is open.

## Rejected payment verification repair

The trace contains one actual single-unit refusal: a colorless unit offered
against a remaining red cost. Both cost and pool were unchanged. It is distinct
from the later failed equip activation reported by the console and cost hooks.
The latter needs a minimal native reproduction and full rollback/state review;
no rules-engine defect or successful illegal activation is established yet.

The independent reader previously counted refusals without checking their
resource transitions. It now checks unchanged structured cost and full mana-pool
multisets, including duplicates and recorded restrictions. Missing legacy
snapshots remain explicit gaps. Test/speculative calls remain excluded. This
single-unit API check does not approve rollback of an entire failed activation.
Five regressions cover unchanged/reordered pools, resource loss/addition, cost
mutation, restriction mutation, missing/malformed evidence and reader integration.
All309 root Python tests pass; re-auditing the completed tape verifies the one
refusal with0 gaps. Original raw evidence remains unchanged.

Current recovery work has2 fresh complete natural diagnostics (one stock, one
native Pilot A),0 complete independently approved games and0 training admissions.
Pilot B remains an offline experimental scorer. Stage47's466 verified replay
choices and Stage48's unresolved reservation are unchanged.
