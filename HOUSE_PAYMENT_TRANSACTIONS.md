# House-game payment transaction audit

Stage50 resumes verified source0695a1a and the saved Stage49 checkpoint. The
source inventory and all64 checkpoint members verify. The authoritative ledger
still leaves Stage48 allocated; no original replay takeover was attempted.

The preserved house-profile game is restored from its lossless transport. Exact
raw hash/size and writer receipt match the original276864-record capture. No
new natural game, training or strategic benchmark is executed in this stage.

payment_transaction_audit.py checks full call ancestry, associates actual mana
units with the nearest committed payment plan, validates paying ability/source/
actor identities at entry and return, and independently checks each successful
cost/pool transition and rejected unchanged transition. It follows unpaid shards
from plan entry through payment to return. A successful plan with unpaid costs
is rejected; missing progress evidence is reported as a gap. Speculative plans
cannot provide actual payment credit. Successful selected actions are also
checked against recorded priority ownership, without asserting entitlement.

## Observed results

- 768 committed plans have complete recorded unit-progress chains:168 spending
 mana and600 requiring zero mana.
- 419 successful unit payments and4 unchanged rejected unit attempts are linked
 to the paying plans, with no gaps within these checks.
- 214 successful selected actions have matching recorded priority owners.
- 48 plain fixed spell costs equal their recorded locked totals. Six differ and
 require independent modifier derivation: Blasphemous Act, Ezio Auditore da
 Firenze, Excalibur Sword of Eden, Vanquish the Horde, Frodo Adventurous Hobbit,
 and Goro-Goro and Satoru. These are review obligations, not confirmed defects.
- Four in-memory corruptions of actual history are rejected: claimed success
 with unpaid cost, another ability receiving payment credit, unspent pool unit,
 and removed payment evidence. Original history bytes are not changed.
- 14 new unit regressions pass; all355 root Python tests pass.

The new tests cover partial success, missing events, recipient changes, ambiguous
identities/test flags, zero costs, speculative payment, legacy missing data,
pool/color corruption, ancestry, failed plans and wrong observed priority.

These results extend the earlier individual-unit audit into full recorded
payment continuity. They do not approve mana-source generation, restrictions,
non-mana costs, all Oracle cost modifiers, targets, casting permissions or full
priority/pass derivation. Cost entry is recorded evidence, not an independent
Oracle calculation. Zero scoped continuity gaps does not mean zero game-level
rules discrepancies. Whole-game approvals remain0, training admissions0 and
completed recovery natural diagnostics3. Original replay remains466 consecutive
choices and1790/1985 conditional supported decisions. Stage47/48 unchanged.

The official Comprehensive Rules effective September25,2026 were retrieved
through the current Wizards rules index. CR601.2f-h requires determining and
paying the total cost; CR602.2 applies that procedure to activations; CR106.4
governs unspent mana; CR117 governs priority. The reader implements only the
declared continuity checks, not those rules in their entirety.
https://magic.wizards.com/en/rules
https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt

Next: independently derive the six modified totals from their announcements,
commander cast history, board characteristics and verified Oracle effects, then
audit alternate/free costs and non-mana payments. Full priority entitlement,
combat, triggers, replacements, state-based actions and terminal approval remain
open. PilotB and GGS deck evaluations receive no unapproved outcomes.
