# Equipment payment follow-up — October 23, 2026 UTC

The authorized original two-document checkpoint write succeeded and both saved
copies were restored byte-identical. Current private allocation gives this
independent equipment investigation a fresh bounded budget; it does not release
Stage48. The historical 403 cause remains unknown. Historical notes below are
preserved, not silently rewritten as successful attempts.

## Reproduced defect and narrow correction

Native Pilot A checks affordability before target selection, but target helpers
or intervening policy changes can invalidate a payment plan. A constructed
Foot Chopper fixture first selects a payable equip2 activation, then reserves
both Islands before execution. The prior controller enters native payment,
returns false and marks the ability skip. The regression fails on that skip
mutation. This is a pilot preflight defect, not evidence of a successful illegal
activation or a mana-production rules error.

The controller now checks native affordability after targets are selected and
again immediately before actual nonland execution. It never clears reservations,
changes mana rules, manufactures sources or bypasses native legality. The same
fixture now refuses without tapped sources, spent mana, stack entry or skip
mutation. Releasing the reservation permits reselection, real payment and
attachment. Normal payment and initially reserved refusal controls still pass.

The original turn34 failure remains unresolved: preserved rows show failed
equip2 payment, no mana activations/spending and three untapped potential lands,
but do not record contemporaneous policy memory. Potential sources are not a
proof of legal availability. The new constructed reservation transition is not
claimed to reproduce that exact historical cause.

## Independent resource and equipment controls

Four-player Skullclamp/Sol Ring controls assert equip1 spends exactly one of two
generated mana, leaves one floating through stack resolution, and clears that
remaining mana through the ordinary pool-clear service. Equip cannot target an
opponent's creature and cannot activate in combat. After normal resolution,
Grizzly Bears is3/1. Removing the target before resolution leaves Skullclamp
unattached on the battlefield and does not refund payment.

These directly exercise the prior Skullclamp/Sol Ring concern; they do not
reopen or advance the reserved original replay. Official CR106.4,117,602.2,
608.2b and702.6 govern the asserted behavior. Foot Chopper's equip2 and other
abilities were checked against Wizards' TMNT release notes:
https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes
Rules reference: https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt

Six patched native controls pass: late reservation, ordinary Foot Chopper,
initial reservation, Skullclamp floating mana, target removal and the existing
four-controller cast/removal/SBA integration fixture. An additional hash-bound
Skullclamp reexecution passes all215 event records; tape bytes match exactly.
Three new negative builder tests plus all prior root tests pass:333 total.
The initial missing fixture-classpath compile failure and expected pre-fix skip
failure are retained privately, not counted as passing tests.

Independent tape readers validate four successful cost/pool unit transitions
and two unchanged rejected unit attempts across the three distinct recorded
fixtures, with no scoped gaps or unencoded types. Reexecution separately repeats
one successful and one rejected check. Two in-memory corruptions of actual tape
rows (unspent pool and unpaid cost) are rejected. Writer receipts verify.
Fixture tapes contain no initial natural-game state; the reader is explicitly
called with require_initial=False. A recorder completion marker is not victory.

The exact-base overlay changes only RulesValidationController.class; every
other executable member is byte-identical. No full upstream Maven build is
claimed. The preserved runtime and executable delta chain were restored by
their recorded hashes; the latest stack fix remains included.

## Unchanged gates

Original replay remains466 consecutive choices and1790 conditional supported
decisions. Stage47/48 reservations are unchanged. Recovery series:3 completed
natural games,0 independently approved complete games,0 training admissions.
Pilot B remains experimental; no strategic benchmark or deck superiority was
established. GGS ninja/ignition research is preserved; no substitution proposed.
Next: reproduce original equipment failure with payment/policy memory, and
extend complete-game casting, priority, combat, triggers and terminal audits.
