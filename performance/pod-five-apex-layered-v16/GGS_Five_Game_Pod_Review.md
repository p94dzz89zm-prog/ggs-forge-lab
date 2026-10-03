# Five-game Apex versus Layered pod review

All ten final games completed without engine errors or timeouts. Current Apex won **1/5** and Layered won **2/5**. These are small, fixed-seat samples of two different decks under the adjusted pilot; they do not establish a reliable ranking or a benefit from the pilot change.

## Changes and collection design

The opt-in GGS pilot now considers its commander before combat when the existing engine profile requires creatures that entered this turn to connect. Normal affordability, legality and candidate ranking remain in place. This preference can be disabled with `dragonmind.disableGgsMain1Deployment=true`. Other seats and commander profiles retain their prior behavior.

The collection exposed an existing snapshot bug: generating live ability descriptions evaluated modal targets without an activating player. Visible snapshots now read current-face Oracle text and mark it with `rules_text_kind: oracle_current_face`. Statistics, keywords and attachments remain separate fields; Oracle text does not render every modified ability. Hidden-card guards remain in place.

Both decklists remained unchanged: the supplied 100-card current Apex and existing GGS_Layered_v1. Each played against Jaymie Ezio, Gabe Food and Destyn Turtles, always in that seat order. Seeds were 20261019–20261023. Each final game used its own JVM, one worker, the same Java/GC/JIT flags, full four-seat auditing and a 600-second allowance. Identical seeds do not mean identical opening hands between different lists. No manual decisions or midgame changes occurred. Metadata includes jar and deck hashes.

## Completed games

Times are audited engine elapsed time, including recording overhead; logged turns are global pod turns. Commander timing is the GGS player's own turn number. Trigger counts measure logged trigger events, not guaranteed resolved tokens.

| Seed | Deck | Winner | Seconds | Logged turns | First GGS cast, own turn | GGS triggers |
|---|---|---|---:|---:|---:|---:|
| 20261019 | Apex | Destyn Turtles | 24.643 | 36 | 4 | 2 |
| 20261019 | Layered | Gabe Food | 30.075 | 51 | 3 | 0 |
| 20261020 | Apex | GGS | 47.617 | 45 | 4 | 3 |
| 20261020 | Layered | Jaymie Ezio | 38.840 | 42 | 5 | 0 |
| 20261021 | Apex | Destyn Turtles | 370.535 | 75 | 4 | 1 |
| 20261021 | Layered | Destyn Turtles | 23.173 | 48 | 5 | 1 |
| 20261022 | Apex | Jaymie Ezio | 50.538 | 51 | 6 | 0 |
| 20261022 | Layered | GGS | 32.211 | 35 | 3 | 3 |
| 20261023 | Apex | Jaymie Ezio | 30.007 | 43 | 3 | 1 |
| 20261023 | Layered | GGS | 26.725 | 52 | 3 | 2 |

| Measure | Apex | Layered |
|---|---:|---:|
| GGS wins | 1/5 | 2/5 |
| Median audited game time | 47.617 s | 30.075 s |
| Mean audited game time | 104.668 s | 30.205 s |
| Median first commander cast | Own turn 4 | Own turn 3 |
| Total logged GGS triggers | 7 | 6 |
| All-seat priority snapshots | 11,855 | 10,315 |
| All-seat ability evaluations | 124,419 | 84,928 |

All ten initial GGS casts happened precombat. Some later Layered recasts occurred postcombat; the change is a preference, and combat can change available mana or the game state. Aggregate decision counts measure workload, not CPU time.

## What the games suggest

**Deployment is improved mechanically, but its effect on strength remains unproven.** Apex seed 19 cast GGS on its fourth turn, compared with its seventh turn in the earlier v15 audited game. The adjusted game lost where the earlier game won. This is a useful warning against treating earlier deployment as automatic improvement. A controlled v15/v16 comparison across more seeds and seat rotations is still needed. Low trigger counts despite deployment make fresh-creature attacks and ninjutsu sequencing useful pilot-review targets.

**The long game is the strongest speed lead.** Apex seed 21 completed in 370.535 seconds at global turn 75; its observed peak included 52 visible creatures and 123 battlefield permanents at turn 70. Layered on seed 21 completed in 23.173 seconds at turn 48 and peaked at 13 visible creatures. The other Apex games took 24.643–50.538 seconds; all Layered games took 23.173–38.840 seconds. Crowded game states plausibly increase combat evaluation work, but these logs do not attribute CPU time. Face-down identities remain hidden, so visible creature counts can undercount creatures.

The next CPU investigation should profile crowded-board combat forecasting, particularly attacker/blocker destruction predictions identified in the previous profile. That earlier profile recorded 42,515 such calls consuming approximately 6.12 exclusive seconds. This batch is not evidence of an engine speedup, and adding more caching without fresh dependency checks would not be justified.

**No card swap is yet supported strongly enough to adopt.** Apex cast Purphoros in two games, with logged damage totaling 24 and 14 to opponents; both games were losses. That supports testing noncombat pressure in Layered as a separate controlled variant, rather than declaring Purphoros an established upgrade. Draconic Visitor was cast in one Apex game and logged 5 damage to Gabe; one exposure cannot establish its value. Layered's two wins involved its combat package: seed 22 logged 20 Dragon Spirit token damage to Jaymie, and seed 23 logged 70 Dragon Spirit token damage to opponents. Those examples support keeping the combat core for further tests, without assigning causal credit to individual cards from two wins. Damage is drawn from named sources in the full pod log; it is not a card-value score.

## Failed attempts and validation

The original audited five-game batches each completed seed 19 and then aborted at seed 20 with the modal-description snapshot error; seeds 21–23 did not run. After fixing the recorder, an Apex batch completed seeds 19–20 and timed out at seed 21 under the original 180-second allowance; seeds 22–23 did not run. All are preserved separately and excluded from the final ten-game table. Seed 21 was retained in the final sample and completed under the longer allowance; no slow game was discarded to improve the averages.

The modal regression reproduces the null-activating-player crash against v15 using Brotherhood Outcast, and passes against v16. The engine passed 108 checks (105 reflective test methods, including one method containing four lifecycle checks), and Python passed 34 checks. All 18 ordered patches reproduced 51 managed source files from the pinned Forge commit. Freshly compiled production classes from that reconstruction match the two packaged class entries. A full Maven rebuild was not rerun. The previous v15 jar is retained. The deployed v16 jar hash is `79a16f73adb86e910bc370ab331ee6d61cedc4cd79a0fbfa452ba67d37cc6b76`.

`analysis.json` contains per-game timing, commander casts, stack actions, trigger counts and board peaks. Private opening hands and repeated hand observations are excluded from the public JSON and retained only in the separate audit archives. Adjacent files preserve metadata, summaries, performance records, test summaries and public-event exports. The exports contain only turns, phases, announced stack actions, damage and results; they exclude hand, draw and private-audit records. Full lossless logs and four-seat audits are saved separately, with archive identities and hashes in `audit-archive-manifest.json`. The analyzer checks final completion counts, seed order and audit segmentation; raw log SHA-256 values are recorded in the analysis.
