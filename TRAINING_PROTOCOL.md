# GGS pilot training protocol

Goal: improve observable decisions with the current GGS 100, then evaluate deck changes. Regression tests or one match do not establish that a pilot matches or exceeds an external pilot.

## Game settings

Use the pinned Forge 2.0.15 build. Record its SHA-256, source patch hash, card-resource version, deck hashes, seed, seats, AI profiles, JVM flags and timeout. Commander starts at 40 life in this engine. Use the Commander format and engine-managed command zone, commander tax, damage, triggers, priority, mulligans and costs. Record the engine's mulligan preference; do not assume a house rule. Do not alter card rules to make a pilot succeed.

The pod benchmark is four-player free-for-all: GGS, Jaymie's supplied Ezio list, and the identified stock proxies for Gabe and Destyn. A two-seat Commander match is a diagnostic duel, not a multiplayer pod estimate or Duel Commander rules. Keep lists fixed while comparing pilots. Verify initial life and seats from snapshots.

Stock Default AI is the control. Strategy candidates must be opt-in and affect only the named GGS seat. Identical seeds and seat rotations control the starting setup; divergent random consumption can change later draws. Use fresh seeds for independent trials and separate training from held-out evaluation positions.

## Each training iteration

1. Retrieve the latest committed source, protocol and evidence. Build or verify a pinned engine; do not assume workspace files or processes survived.
2. Attempt a game with an externally controlled opponent against GGS. Use only that seat's legal observations. Keep private audits away during play. Record the commander/list, external choices, explicitly delegated prompts and unoverridden assisted hooks. Mostly delegated games test integration and cannot rank the external pilot's strength.
3. After play, inspect private audits. Separate proven mistakes, speculative alternatives and engine/card-script issues. Capture a reproducible position before changing strategy.
4. Test the position against the previous and candidate policy. Preserve failing and corrected results, and counterexamples where acting is wrong. Never repair a heuristic by falsifying game rules.
5. Run bounded stock/candidate comparisons with matched initial seeds/seats. Retain losses and invalid runs. Exclude timeouts, exceptions, multiple winners, unresolved outcomes and demonstrated rules-script errors from strength conclusions. Report failure rates by pilot; exclusions can be selective.
6. Commit code, tests, settings, commands and evidence. Report the correction, remaining limits and next issue. Do not imply a process keeps running after a chat turn or a schedule guarantees an available engine.

## Improvement gates

- Rules: engine-backed resolution supports the forecasts. Passing tests can encode an incorrect rule and need independent review.
- Decisions: held-out positions show useful choices gained, harmful choices avoided, no illegal choices and no opponent-private-information dependency. Inspect actual baseline/candidate disagreements.
- Games: independent completed matched trials show performance and failure estimates with uncertainty. Inspect Dragon generation, card/mana spending, stalled turns and recovery; wins alone do not explain improvement.
- External-pilot comparison: predeclare information, assistance, decks, seats and time budget. Use fresh seeds and disclose delegation rates. A small sample cannot support universal stronger-than-human or stronger-than-assistant claims.

Keep stock as default and strategy candidates experimental until these gates support promotion. Preserve the user's current deck. If a credible comparison supports the requested target, present evidence and pause recurring training.

## Scheduling status

Hourly task creation was attempted October 1, 2026 and rejected because all five active task slots were in use. No task was created or existing task changed. A scheduled chat iteration is not a durable game-engine process. Use a computer or configured durable runner for uninterrupted long games.
