# Stage49 historical equipment investigation

Starting source975869b and all414 source-inventory entries verified. The private
71-member checkpoint restored and its declared logs, hashes and source bundle
verified. The authoritative ledger confirmed466 consecutive original choices,
1790/1985 conditional supported decisions,333 prior Python tests and unresolved
Stage48 ownership. Original replay was not advanced under that reservation.

## Historical failure reconstructed and reproduced

The complete preserved native diagnostic contains163045 referee records. On
turn34, Island and Forest paid2 for a Food activation in upkeep. At main-phase
selection, the active player had priority, an empty stack and empty mana pool.
Foot Chopper was attached to a Ninja token; its equip2 targeted the controlled
Michelangelo. Command Tower, Hinterland Harbor and Cinder Glade were untapped.
The recorded player snapshots before and after failed payment are equal.

A diagnostic overlay observes the original ComputerUtilMana return values and
AI memory in a separate private stream. It changes no returned values, policy
code or referee record generation. It changes only ComputerUtilMana.class and
adds ReservationProbe.class; all other executable members remain byte-identical.
The original executable, JDK modules, decks, policies, seed and historical rules
configuration are bound by hashes. One reexecution completes turn36 in85.232s
wall time. The original reference checker accepts all163045 records. Independent
comparison also matches them after removing session identity/sequence metadata
and normalizing only Set-derived GameEventCardStatsChanged card order.4442 such
UI ordering differences are explicitly counted; gameplay lists remain strict.
Five original and five reexecution stream receipts verify independently.

The69 new diagnostic rows establish the missing mechanism: equip preflight finds
a plan while MAIN2 reservations are empty. Before actual payment, all three
untapped lands appear in HELD_MANA_SOURCES_FOR_MAIN2 and the native reservation
predicate returns true for them. Actual payment finds no plan and marks skip.
This directly corroborates the reservation-change class repaired in975869b.
It does not establish a mana-production arithmetic defect or successful illegal
activation. The exact helper that installed the reservations was not separately
instrumented; the before/after reservation state and payment rejection are known.

A minimal late-MAIN2 fixture reproduces skip mutation with the old controller;
the current payment guard refuses before mutation, then permits real equip
payment/attachment after release. The fixture explicitly loads the historical
Default profile and asserts its reservation setting100. Two initial probes
omitted profile loading and paid successfully; those failed fixture assumptions
are preserved, not described as failed engine regressions. The corrected old
controller failure is expected; the corrected guarded control passes.

## Independent audit and certification limits

equipment_attempt_audit.py reconstructs failed payment identity, selected action,
observed main-phase priority/empty stack, creature control, frozen equip cost,
pool size, untapped land inventory and prior attachment. Eight regressions reject
wrong priority/timing/targets/costs, ambiguous identities/pools and missing cost
evidence. This reader alone does not infer internal reservations or full legality.
All341 Python tests pass. No whole-game certification or training admission.

Full-stream consistency of the historical natural game verifies106 LIFO
resolutions,108 stack announcements/removals,29 life-chain events and final
last-player-standing consistency. Two removal-effect reviews and three loss/SBA
derivations remain, alongside general casting/payment restrictions, priority,
combat, trigger and continuous/replacement derivations. This historical game
uses standard commander damage and one free mulligan, so it cannot be relabeled
as a house-profile game. Recovery series remains3 natural diagnostics,0 approved
complete games. The new run is a historical diagnostic reexecution, not a fourth
new game or evidence of strategic improvement.

## PR2 integration

GitHub now reports mergeable=true, draft=true, merged=false. The integration
head is an ancestor of the recovery head; merge-tree produces the exact recovery
tree with no conflicts. The earlier false mergeability is no longer reproducible;
its historical server-side cause is unknown. Prior CI39878853743 is successful.
No integration branch/ref was advanced. Keep draft pending review of source
integrity and dependencies; branch-protection configuration was not exposed by
the available read tools. A fast-forward-compatible history requires no conflict
resolution or protected-history rewrite.

Official reference: Wizards TMNT release notes (Foot Chopper equip2 and card text),
https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes
and the frozen Comprehensive Rules reference in the historical input manifest.
Next: full house-game casting/payment and priority derivation; preserve Stage48
until ownership/outcome is reconciled. PilotB and GGS card research remain gated.
