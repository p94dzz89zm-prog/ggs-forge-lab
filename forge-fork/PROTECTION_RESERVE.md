# Public-removal protection reservation

Cycle7 reproduces two connected pilot failures with actual costs and resolution:
GGS haste uses the two available mana, leaving March unpaid against a ready
public tap-to-destroy ability; and the existing threat predictor follows the
activated ability's reset template instead of its targeted stack instance, so
the real priority controller declines March even when resources remain.

The predictor now keeps the live targeted stack ability. The original template
fallback remains for nontarget abilities. This changes shared AI threat
prediction for all seats, not card rules. Natural build comparisons therefore
cannot attribute every outcome difference solely to the selected GGS pilot.

The opt-in planner adds a narrow reservation proof. For one executable public
creature ability with exact tap cost, Destroy API, one creature target and no
subability, it compares a proposed development/haste spend with retaining March.
The proof pays and resolves the proposed action, verifies that protection is no
longer payable and the removal actually removes GGS, then checks that the actual
priority controller chooses March, pays it and phases GGS out when mana is kept.
Only a complete proof vetoes the proposed spend. No reward is added for Dragon
activity, and coefficients/model data are unchanged.

The guard is intentionally bounded: one present legal public removal, GGS on
board, ordinary X=1 March, no other blue hand card requiring alternate-exile-cost
analysis, and supported planner proposals. Multiple removal sources, other
protection packages, speculative hidden spells, future draws, general recovery
and response trees remain outside this version. It does not prove a held mana
line is optimal, nor search a new best action after a veto. It may pass priority
to preserve the demonstrated response. A later instant-speed rescue still
requires actual opponent action. The branch does not predict its probability.

Use `-Ddragonmind.linePlanner=true` for the experimental planner. For a controlled
ablation, `-Ddragonmind.disableProtectionReserve=true` disables just this guard;
the shared target-prediction correction stays in the build. The soft probe
budget defaults to1500ms and can be set with `dragonmind.protectionProbeMillis`.
Engine operations and the controller's worker can exceed a soft budget. A
partial/failed proof retains stock; it never supplies feedback. Run one game
per JVM, not multiple live games sharing Forge's global RNG.

Controller evaluation spawns a worker. PlannerContext now inherits its branch
flag into that worker so copied evaluations do not pollute real-game audits.
The fork regression checks both inheritance and absence of branch audit output.
The original live RNG is restored; this is not a claim of arbitrary concurrent
thread isolation. The separate trace records reservation status and elapsed
probe time along with stock/effective actions and the actual visible snapshot.

ProtectionManaRegression has ten constructed groups, including actual automatic
March selection/targeting/payment/resolution and controls for tapped or sick
removal, sufficient remaining mana, no March, Avacyn-granted indestructibility,
a disabled guard and unmodeled alternate blue exile costs. Avacyn is a constructed
rules control, not a suggested deck swap or a natural GGS game. An initial test
used the battlefield iterator that excludes phased-out cards; its failed oracle
is retained and replaced with getCardsIncludePhasingIn. No phasing rule changed.

ProtectionManaHeldoutRegression requires `--purpose heldout`, uses separate
Visara and Royal Assassin conditions, and runs both actual priority decisions.
All selected-player protections are chosen by the pilot, not manually scripted.
Opponent removal is a declared constructed response, not a claim that a natural
opponent necessarily takes it. Natural games remain separate, with all-seat
private audits, matched120-second budgets, one seed/seat per pair, and no
promotion or trusted outcome learning from results alone.


Frozen evaluation: all four fresh constructed paired conditions preserved GGS
with automatic protection in the corrected build; the previous build lost GGS
in all four. This is scoped response evidence on deliberately constructed
threats, not four natural games or an estimate of general strength. The full
17 engine suites,82 Python tests and128 disjoint random positions passed. The
41 planner groups passed in a fresh rerun; an earlier process exited0 before
its required completion marker, which remains an invalid unexplained startup
attempt rather than a pass. Natural evidence uses two separate seed clusters,
with one matched seat rotation in each, and remains evaluation-only.
