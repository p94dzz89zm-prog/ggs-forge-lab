# GGS seat-rotation comparison and speed investigation

**Apex won 5/14 matched valid games and Layered 4/14.** This is a small observed lead, not a clear deck ranking. Each deck has fifteen clean new completions; fourteen seed-and-seat combinations are valid for both. With the earlier fifteen fixed-seat pairs, the combined matched results are **Apex 10/29 and Layered 8/29**.

## What we ran

Four new seeds, 20261034–20261037, across all four rotations of the fixed GGS / Jaymie Ezio / Gabe Food / Destyn Turtles pod: sixteen planned slots per deck. Both lists, rules and pilot weights remained unchanged. Accepted engine v17 and the commander-aware GGS pilot were used throughout. Initial collection used two JVM workers and four seeds per JVM, with private four-seat auditing, a 600-second game allowance and the unchanged five-second AI evaluation allowance.

The initial run produced 23 clean completions, three completions invalidated by AI errors, and six slots without results. Nine individual recovery games used the same seeds, seats, lists, pilot and allowances; seven recovered cleanly. Two slots remained invalid after their retries: Apex seed 20261035 at rotation 1 (GGS seat 3), and Layered seed 20261034 at rotation 0 (GGS seat 0). No declared winner from those invalid runs is counted.

Those two slot combinations are excluded from the matched comparison for both decks. The extra unmatched clean loss from each deck remains in its all-completion figures. We did not replace difficult seeds or keep retrying until they supplied favorable results. Four shared seeds with rotated seating remain limited evidence; identical seeds across different lists do not create identical hands.

## Comparison

| Measure | Apex | Layered |
|---|---:|---:|
| Matched new wins | 5/14 | 4/14 |
| All clean new wins | 5/15 | 4/15 |
| Combined matched wins | 10/29 | 8/29 |
| All clean historical wins | 10/30 | 8/30 |
| Median new audited game time | 41.959 s | 44.188 s |
| Median first GGS cast | Own turn 3 | Own turn 4 |
| New logged GGS triggers | 28 | 45 |
| Observed own combat turns with GGS seen | 75 | 93 |
| Those turns with fresh attackers | 33 | 42 |
| Those turns with fresh unblocked attackers | 29 | 42 |

The combat and commander measures above cover all fifteen clean new games per deck. Times include audit overhead, parallel execution and mixed warm/individual JVM runs. They do not establish a CPU speed improvement or a deck-strength advantage from shorter runtime. Earlier and new cohorts use different seating and audit versions; combined results are descriptive.

| GGS seat | Matched games per deck | Apex wins | Layered wins |
|---|---:|---:|---:|
| 1 | 3 | 2 | 1 |
| 2 | 4 | 0 | 1 |
| 3 | 4 | 2 | 0 |
| 4 | 3 | 1 | 2 |

## What the play data suggests

Apex typically established GGS on its third own turn; Layered on its fourth. Layered logged 45 GGS triggers and 31 paid ninjutsu-return records, versus Apex’s 28 triggers and eight returns. It generated more engine activity without winning more of the matched games. That supports reviewing how connections are converted into a finish, rather than treating Dragon production alone as an upgrade criterion.

Both lists had fresh attackers on about 45% of observed own combat turns with GGS seen. At least one fresh attacker was observed unblocked on 29 of Apex’s 33 such turns and all 42 of Layered’s. The first review target is repeated fresh-attacker setup and subsequent payoff. These observations do not prove that an omitted attacker could legally attack or that an alternative play was affordable.

An illustrative Apex win, seed 20261037 at rotation 1, logged one GGS trigger alongside five Balefire Dragon triggers and seven Purphoros triggers. Layered wins at rotation 1 logged five GGS triggers each and multiple Orochi Soul-Reaver triggers. These are public announced trigger records, not proof of causal card value or guaranteed resolved effects. Repeated card and candidate events should not be treated as independent samples. No specific card swap is justified by this cohort alone.

The fixed Default pilots and GGS policy are a model of play in this pod. They do not represent human politics or prove a general power rating. The unresolved crowded games further limit confidence: deck effects that the engine struggles to evaluate cannot be assessed from those failed outcomes.

## Speed and waiting time

The cost-source candidate passed 114 engine checks and matched the tested traces, but its isolated repeated benchmark was essentially tied: control 99.194 seconds, candidate 99.169. The crowded Apex pair was slower with the candidate, 81.167 versus 80.104 seconds. It was not adopted; v17 remains active. Full results and the unadopted source patch are in `../cost-source-v18-experiment/`.

The actual collection and recovery took **1,697.066 seconds (28.3 minutes)** for thirty accepted completions, or **1.061 clean games per minute**. This includes failed/missing-slot recovery, excludes investigation, analysis and saving, and is not a controlled comparison with an earlier batch. Expensive games and invalid runs dominate waiting time.

The runner now defaults to **one game per JVM**, retaining parallel workers. A problem game therefore cannot leave later seeds in that JVM without results. Larger warm batches remain opt-in. This is a reliability change with a direct effect on queue isolation; no measured throughput gain is claimed for the new default.

## Actual setup, including the screenshot suggestions

We use Forge command-line `sim` with headless mode, without GUI driving or manual review pauses. The JVM reports an effective eight-core CPU quota and an 8 GiB memory limit. Java is OpenJDK 17.0.20. Current flags use a 1536 MiB heap, Parallel GC, non-tiered compilation and compilation threshold 1000. Two workers are the previously measured default on this resource budget. A larger heap or one JVM per nominal CPU is not automatically faster.

Example single-game launch, from the Forge `forge-gui` directory:

```sh
java -Xmx1536m -XX:+UseParallelGC -XX:-TieredCompilation -XX:CompileThreshold=1000 \
  -Djava.awt.headless=true -Dforge.ai.ggsPilotPlayer=Ai\(1\)-GGS_Apex_War_Form_Current \
  -jar /absolute/path/dragonmind.jar sim -D /absolute/path/decks \
  -d GGS_Apex_War_Form_Current.dck Jaymie_Ezio.dck Gabe_Food.dck Destyn_Turtles.dck \
  -f Commander -seeds 20261034 -c 600 -a Default Default Default Default
```

The detailed collection additionally sets `-Dforge.audit.directory=...`. For unattended comparisons, `dragonmind.py --workers 2 --batch-size 1` launches independent JVM jobs. Both batch size and flags are retained in metadata.

Parallel jobs can reduce waiting for many results while leaving individual games long. Cutting AI lookahead would require a separate quality comparison; simplifying the pod would change the question. The screenshot’s 1–10-second-per-game claim has not been demonstrated for this workload.

## Accepted games

| Seed | Rotation | GGS seat | Deck | Winner | Seconds | Matched pair | GGS triggers |
|---|---:|---:|---|---|---:|---|---:|
| 20261034 | 0 | 1 | Apex | Destyn Turtles | 163.595 | No | 0 |
| 20261034 | 0 | 1 | Layered | Unresolved AI error | — | No | — |
| 20261035 | 0 | 1 | Apex | Destyn Turtles | 197.333 | Yes | 0 |
| 20261035 | 0 | 1 | Layered | Destyn Turtles | 161.856 | Yes | 3 |
| 20261036 | 0 | 1 | Apex | GGS | 41.959 | Yes | 0 |
| 20261036 | 0 | 1 | Layered | Destyn Turtles | 90.549 | Yes | 0 |
| 20261037 | 0 | 1 | Apex | GGS | 46.635 | Yes | 4 |
| 20261037 | 0 | 1 | Layered | GGS | 44.188 | Yes | 3 |
| 20261034 | 1 | 4 | Apex | Jaymie Ezio | 35.821 | Yes | 0 |
| 20261034 | 1 | 4 | Layered | Destyn Turtles | 44.481 | Yes | 0 |
| 20261035 | 1 | 4 | Apex | Unresolved AI error | — | No | — |
| 20261035 | 1 | 4 | Layered | Gabe Food | 34.719 | No | 2 |
| 20261036 | 1 | 4 | Apex | Destyn Turtles | 21.609 | Yes | 0 |
| 20261036 | 1 | 4 | Layered | GGS | 27.836 | Yes | 5 |
| 20261037 | 1 | 4 | Apex | GGS | 27.215 | Yes | 1 |
| 20261037 | 1 | 4 | Layered | GGS | 80.316 | Yes | 5 |
| 20261034 | 2 | 3 | Apex | Gabe Food | 93.723 | Yes | 3 |
| 20261034 | 2 | 3 | Layered | Jaymie Ezio | 45.994 | Yes | 3 |
| 20261035 | 2 | 3 | Apex | Gabe Food | 95.089 | Yes | 7 |
| 20261035 | 2 | 3 | Layered | Jaymie Ezio | 15.701 | Yes | 2 |
| 20261036 | 2 | 3 | Apex | GGS | 24.348 | Yes | 4 |
| 20261036 | 2 | 3 | Layered | Jaymie Ezio | 41.661 | Yes | 2 |
| 20261037 | 2 | 3 | Apex | GGS | 63.716 | Yes | 5 |
| 20261037 | 2 | 3 | Layered | Jaymie Ezio | 28.361 | Yes | 1 |
| 20261034 | 3 | 2 | Apex | Destyn Turtles | 46.968 | Yes | 0 |
| 20261034 | 3 | 2 | Layered | Destyn Turtles | 162.345 | Yes | 3 |
| 20261035 | 3 | 2 | Apex | Destyn Turtles | 21.286 | Yes | 1 |
| 20261035 | 3 | 2 | Layered | GGS | 14.548 | Yes | 3 |
| 20261036 | 3 | 2 | Apex | Destyn Turtles | 36.350 | Yes | 1 |
| 20261036 | 3 | 2 | Layered | Jaymie Ezio | 84.666 | Yes | 11 |
| 20261037 | 3 | 2 | Apex | Jaymie Ezio | 32.775 | Yes | 2 |
| 20261037 | 3 | 2 | Layered | Destyn Turtles | 18.188 | Yes | 2 |

## Verification and saved evidence

Thirty clean logs and four-seat audit streams were staged by seed and rotation. Turn-reset partitions and selected result markers were checked. The analyzer follows the actual GGS seat; any snapshot taken after the viewer has left the live player list is excluded from its board/attack measures and counted separately. Combat counts union declare-blockers and first-strike observations within an own global turn, including extra combats; they count turns rather than distinct combats. GGS name presence does not prove an active ability or eventual damage. Face-down types can limit observed board counts.

All 34 Python checks passed. The unadopted candidate’s twenty-patch reconstruction reproduced 52 managed sources, and a fresh production compile matched its packaged classes. The full Maven build was not rerun. Accepted v17’s earlier engine/source/control verification remains unchanged.

Public `analysis.json`, `metrics.json`, `attempt-selection.json`, `throughput.json` and `data-verification.json` contain allowlisted outcomes, numeric observations and verification metadata. Private hands, raw evaluation strings and card-level audit details are excluded. The saved `GGS_Seat_Rotation_Pod_Data_v17.tar.gz` retains all original and recovery logs/audits, selected per-game logs, metadata and full analysis. The saved `GGS_Cost_Source_Experiment_Data.tar.gz` retains the experiment’s full logs and sources.
