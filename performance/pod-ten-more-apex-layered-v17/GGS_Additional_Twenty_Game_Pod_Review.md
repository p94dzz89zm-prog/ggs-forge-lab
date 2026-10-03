# Additional twenty-game GGS pod review

Ten more accepted games per deck are complete. Apex won **4/10** and Layered **2/10**. Including the previous five per deck, the totals are **5/15** and **4/15**. These small fixed-seat samples do not establish a deck ranking or a benefit from any pilot change.

## What changed

V17 adds attacker, defender, blocker and blocked/unblocked relationships to public-state snapshots. Private evaluation rows now identify the host and whether the candidate is ninjutsu. No deck swaps, strategy weight changes, rules changes or CPU shortcuts were adopted. This improves diagnosis; it does not establish a speedup.

Validation passed 110 engine checks and 34 Python checks. All 19 patches reproduced the 51 managed sources; freshly compiled production classes matched the packaged jar. The audited seed-19 control preserved all 887 tracked v16 events. The full Maven build was not rerun; build verification records the focused compilation and checks.

## Collection and exclusions

Seeds 20261024–20261033 used the unchanged Apex and Layered lists against Jaymie Ezio, Gabe Food and Destyn Turtles. GGS occupied seat 0 throughout. Each game ran in its own JVM with one worker, the same Java/GC/JIT flags, four-seat auditing and a 600-second game allowance. The separate AI evaluation allowance remained five seconds. Identical seeds across different lists do not imply identical opening hands.

There were **22 attempts for 20 accepted completions**. Apex seed 28 initially declared a win but contained an AI evaluation TimeoutException, so that result is excluded. Layered seed 31 initially exited without a terminal result and is also excluded; the available log does not establish its cause. Both seeds were rerun under unchanged settings and completed cleanly. Accepted seed 28 is an Apex win; accepted Layered seed 31 is a Jaymie win. Failed logs and private four-seat records are retained in the saved data archive. `attempt-selection.json` identifies original and accepted log hashes.

## Results

| Measure | Apex | Layered |
|---|---:|---:|
| New GGS wins | 4/10 | 2/10 |
| Cumulative GGS wins | 5/15 | 4/15 |
| Median new audited time | 33.163 s | 48.801 s |
| Median cumulative audited time | 33.719 s | 32.211 s |
| New logged GGS triggers | 21 | 25 |
| Observed own combat turns with GGS seen | 48 | 64 |
| Those turns with a fresh attacker | 19 | 25 |
| Those turns with a fresh unblocked attacker | 17 | 24 |

Times include audit overhead and refer to accepted games. Cumulative figures combine the earlier v16 and new v17 audit cohorts; they are descriptive, not a controlled speed comparison. Peak observed creature boards reached 37 for Apex and 36 for Layered in the new cohort. Hidden face-down types may be undercounted.

| Seed | Deck | Winner | Seconds | Global turns | GGS triggers |
|---|---|---|---:|---:|---:|
| 20261024 | Apex | Gabe Food | 64.974 | 61 | 0 |
| 20261024 | Layered | Destyn Turtles | 41.514 | 46 | 2 |
| 20261025 | Apex | Destyn Turtles | 89.257 | 58 | 0 |
| 20261025 | Layered | Destyn Turtles | 31.344 | 46 | 1 |
| 20261026 | Apex | GGS | 24.279 | 33 | 9 |
| 20261026 | Layered | Destyn Turtles | 56.088 | 58 | 4 |
| 20261027 | Apex | Jaymie Ezio | 26.799 | 43 | 2 |
| 20261027 | Layered | Destyn Turtles | 16.572 | 33 | 0 |
| 20261028 | Apex | GGS | 71.869 | 58 | 0 |
| 20261028 | Layered | GGS | 74.019 | 56 | 7 |
| 20261029 | Apex | Gabe Food | 98.226 | 66 | 3 |
| 20261029 | Layered | Gabe Food | 102.527 | 75 | 5 |
| 20261030 | Apex | Jaymie Ezio | 32.606 | 44 | 0 |
| 20261030 | Layered | Jaymie Ezio | 31.415 | 54 | 0 |
| 20261031 | Apex | GGS | 29.646 | 40 | 6 |
| 20261031 | Layered | Jaymie Ezio | 140.905 | 57 | 2 |
| 20261032 | Apex | Jaymie Ezio | 33.719 | 47 | 0 |
| 20261032 | Layered | GGS | 118.675 | 52 | 1 |
| 20261033 | Apex | GGS | 31.742 | 44 | 1 |
| 20261033 | Layered | Gabe Food | 24.824 | 42 | 3 |

## Fresh attacks and ninjutsu

Fresh attacks appeared on 19 of 48 observed Apex turns with GGS seen and 25 of 64 Layered turns. At least one fresh attacker was observed unblocked on 17 and 24 of those turns respectively. This points toward reviewing setup and sequencing before increasing rewards for evasion. It does not prove that any particular fresh creature could legally attack, that an alternative play was affordable, or that a snapshot would ultimately produce combat damage.

These counts union observations from declare-blockers and first-strike-damage phases within each own global turn, including observations across extra combats. They count turns, not distinct combats or attackers. GGS name presence is a public-state proxy, not proof its ability was active. Snapshot timing, removals, damage prevention and subsequent actions can change the outcome. Logged GGS triggers are trigger events, not guaranteed resolved Dragon tokens.

Ninjutsu evaluation records contain 20 scored plans and 85 no-damage-plan records for Apex, versus 87 and 155 for Layered. Paid-return records were 5 and 15. Candidate evaluations repeat across priority passes and include legality/affordability rejections; these are workload counts, not independent opportunities or missed-play rates. We should inspect individual fresh-attack sequences before changing policy weights.

Layered logged more GGS triggers despite fewer wins in this cohort. Trigger production alone is therefore a poor upgrade criterion. The data does not yet justify a specific card replacement. Preserve both lists for the next controlled test; examine engine establishment, fresh-creature availability and conversion of connections into wins.

## CPU findings and next experiment

The separate crowded-board JFR reproduction of v16 Apex seed 21 completed in 270.439 seconds at global turn 88. Its earlier audited trace ended at turn 75, so the durations are not comparable. Inclusive execution samples included spell-ability discovery in 67.1%, static rebuilding in 50.8%, block search in 16.2%, and attack search in 14.9%. These categories overlap. The profile does not show that block search alone accounts for the remaining runtime.

The invalid original Apex seed-28 timeout ran through pump evaluation, attack planning, nested next-combat forecasting, blocker assignment, available mana estimation and cost adjustment. CostAdjustment currently assembles battlefield, stack, command and host source collections repeatedly. A concrete next experiment is conservative source discovery shared within a bounded read-only forecast. It must retain ordering, zones, host/LKI priority, face-down behavior, live modifier conditions and invalidation. Do not cache cost outcomes or affordability. No speed improvement is claimed until a controlled trace-equivalence and timing comparison passes.

## Evidence

- `analysis.json`: public aggregate game data, observed combat turns, hashes and workload counts. All card-level action, damage, trigger and evaluation details are excluded from this export; full records remain in the saved archive.
- `metrics.json`: cohort and cumulative measures.
- `attempt-selection.json`: two excluded originals and selected retries.
- `../combat-audit-v17-build-verification.json` and `../combat-audit-v17-engine-test-summary.txt`: source/package/control verification and checks.
- `../README-crowded-game-v17.md` and `../crowded-v16-jfr-summary.txt`: profile interpretation.
- Saved `GGS_Additional_Twenty_Pod_Games_v17_Data.tar.gz`: all accepted logs and full private audits, both excluded originals, metadata, summaries and full analysis.
- Saved `GGS_Crowded_Game_Profile_v16.tar.gz`: complete JFR recording and diagnostic logs.
