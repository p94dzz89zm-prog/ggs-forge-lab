# Resumable pilot training cycle

`train_pilot_cycle.py` runs the learner tests, pinned-engine regressions,
audited experimental games, record checks, decision checks and a consistent
SQLite checkpoint. Increase `--games` to resume the same experiment; its seed,
engine, source and deck configuration must match. Each attempt is saved before
the next begins. An interruption cannot turn an incomplete game into a win.

Required arguments are `--engine`, `--jar`, `--forge-source`, `--testng`,
`--output` and `--seed`. Defaults are eight attempts, two saved GGS variants,
180 seconds per attempt and 128 randomized full-controller positions. Use a
new output when source, engine, decks or experiment settings change.

New training defaults to `game-outcome-v2`: win = 1; completed loss/draw = 0.
Errors and timeouts have no reward. The older engine-shaped objective remains
available by name and is retained when resuming an old manifest. Reward version
and engine hash separate contexts, so old scores are not silently reinterpreted.
The review gate recomputes the objective from preserved evidence.

The cycle explicitly uses a **sandbox** preference pool. It adapts among three
fixed strategy profiles; it is not a neural or general tactical learner. Its
preferences are provisional. Automated evidence checks do not approve a game's
strategy or promote the sandbox model into reviewed inference.

The r9 repair refuses GGS's unmodified pure-haste activation when every current
creature either has haste or has no summoning sickness. It leaves useful haste,
other ability shapes, disabled-policy and other-seat paths to the existing AI.
The new suite covers nine boundaries. Full regression counts are 166 targeted
scenarios plus the configured random positions, with 16 repeated Prowler checks
reported separately from distinct scenarios.

Decision reports check one observed error (redundant haste) and whether the
selected-seat snapshots expose opposing hands. They are not exhaustive rules
or strategy certificates. Paired seeds are diagnostic aids: changed actions
can change later random events. Deck and opponent proxies, stock mulligans,
small samples and sparse outcome feedback still limit conclusions.
