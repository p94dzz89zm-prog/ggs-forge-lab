# Experimental public-projection line planner

This adds a real two-action search to the existing rules engine. It is opt-in,
not a general learner or a replacement for Forge's rules implementation. The
cycle4 incumbent remains the default. Enable with `-Ddragonmind.linePlanner=true`
and the existing selected-player property `forge.ai.ggsPilotPlayer`.

The search copies player-visible positions, enumerates payable ordinary
nontarget permanent spells and GGS's exact haste ability, pays actual costs,
resolves the stack, and forecasts combat through Forge's phase handler. It
compares zero-, one- and two-action lines. Only the best two first-action
prefixes expand; at most six actions are admitted at each node (18 action nodes).
It replays only the first action and replans at real priority. Land drops,
targeted/unsupported stock actions and selected passes preserve the stock
choice. Thus this version can discover/reorder development but cannot reliably
veto bad stock casts or manage every interaction. It does not change card rules.

The transparent material heuristic values public permanents, own hand count,
life, untapped lands and terminal results. It adds no reward for activating GGS
or merely generating a trigger. These are heuristic units, never win
probabilities. No prior game feedback selects this implementation or updates
its coefficients. Outcome admission remains in EVIDENCE_ADMISSION.md.

## Information and isolation

Planner-only GameCopier paths replace opponents' hands, every library, and
face-down exile identities with inert unknown placeholders. Opponent deck
metadata is replaced by an empty projection. Our hand and public cards remain
available. Revealed hidden cards are currently conservatively forgotten.
Unknown cards entering our hand invalidate the review; this prototype cannot
value draws/tutors from unknown libraries. Face-down battlefield cards,
eliminated-player copy mismatches and experimental snapshot mode fall back.
The normal copier behavior is retained outside planner scopes.

The upstream copier stamps copied cards as entering now. Planner copies restore
actual zone-entry turn and controller to prevent old creatures creating false
GGS Dragons. This regression was reproduced and corrected. Other copier TODOs,
including complete zone transition histories and some remembered relationships,
remain limitations. This projection is not a certified full-state serializer.

Each review swaps in and restores a private deterministic RNG; tests check both
object restoration and unchanged next live value. Forge's RNG is global: run
one game per JVM and no concurrent live games in a planner JVM. This is not a
thread-isolation guarantee. Branch evaluations are excluded from actual-game
audit streams. Public snapshots add stack targets, paid X, combat assignments
and all mana pools. Separate private planner traces record assumptions,
considered lines, stock choice and effective choice, including fallbacks.

## Forecast assumptions

Combat uses cloned stock attacker/blocker controllers, no hidden-hand responses
and no searched priority spells. A common combat seed (715518) is reset for
every line so action-dependent RNG consumption cannot confound comparisons.
It is one conditional combat scenario, not an expectation over opponent choices
or a promise about a live attack assignment. Independent live attack-target
rolls produced different Dragon counts in a saved development failure. Exact
forecast/replay regression uses the declared common combat condition. This
limitation remains explicit for natural games and must precede promotion.

The default 2000 ms deadline is soft: checks occur between engine operations.
Uninterruptible engine operations can exceed it. Resolution is capped at 64
stack iterations. Deadline, action cap, unknown draw, illegal payment or engine
exceptions discard the proposed override and retain stock. Partial search is
not reported as a completed comparison. Invalid results are never feedback.

## Reproduce

Build with `build_line_planner.py --base <cycle4-jar> --output <fresh-jar>`.
The builder enforces the cycle4 SHA256 and an explicit class allowlist, checks
ZIP CRC and verifies that every non-overlay entry is byte-identical. All older
combined-lethal, counter-payment, haste and March corrections are preserved.

Run `run_line_planner.py` with actual `--jar`, `--engine`, `--testng`,
`--fixture-classpath` and a fresh `--output`. It checks 8 fork/isolation groups
and 17 decision/legality groups. These are constructed checks, not 25 natural
games. `run_pilot_recovery.py` separately runs all 17 incumbent suites and fresh
randomized positions on the same packaged build. The separate
LinePlannerHeldoutRegression requires `--purpose heldout`; it must be evaluated
once after freezing and not used to tune that build.

GameCopier.java derives from Card-Forge/forge commit
4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676,
forge-ai/src/main/java/forge/ai/simulation/GameCopier.java, under the Forge
project's GPL license (COPYING). Planner-only changes are isolated in this
source overlay. No private hands, models, audits or raw logs belong in GitHub.

## Frozen cycle5 validation

The packaged common-combat build passed all 17 existing engine suites and 128
fresh randomized positions (50640–50767), 82 Python tests, 25 constructed planner
check groups, and eight separately frozen held-out constructed cases. The latter
covered Goblin Instigator and Fanatical Firebrand on open, blocked, taxed, and
MAIN2 boards. These counts describe checked conditions, not general coverage.
The development regression preserved an actual independent-combat replay
mismatch; only the explicitly matched combat condition supports exact replay.
Natural-game integration and runtime evidence are recorded privately. No
candidate is promoted and no new game outcome is trusted learning feedback.
