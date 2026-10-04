# Apex versus Layered: 100 scheduled pod games per deck

Matched valid pairs: **96**. Unresolved slots: **4**.

Both decks faced Jaymie’s supplied Ezio list, the Food and Fellowship proxy, and the Turtle Power proxy—not each other in the same game. Decklists, v17 engine, AI policies and allowances stayed fixed.

Twenty-five fresh seeds were rotated through all four seats. Game order was prespecified and shuffled, deck submission order alternated, and two independent JVM workers were used. Invalid slots received one identical-settings retry; unresolved slots are not wins or losses. The matched-valid subset is the primary comparison.

| Matched metric | Apex | Layered |
|---|---:|---:|
| Games | 96 | 96 |
| Wins | 35 | 27 |
| Win rate | 36.5% | 28.1% |
| Median engine seconds | 64.645 | 69.881 |
| 90th-percentile engine seconds | 139.652 | 132.555 |
| Median first commander cast: own turn | 4.000 | 3.000 |
| Games without logged commander cast | 2 | 0 |
| Commander recast events | 119 | 155 |
| Logged GGS triggers | 259 | 234 |
| Ninjutsu paid-return records | 54 | 93 |
| Median peak observed GGS creatures | 7.000 | 7.000 |
| Fresh attack turns with GGS observed | 245 | 263 |
| Fresh unblocked turns with GGS observed | 219 | 233 |
| Median global finish turn on GGS wins | 43 | 49 |

Apex-minus-Layered matched win-rate difference: **8.3 percentage points**. Exploratory seed-clustered bootstrap interval: **-5.0 to 20.4 points**.

The bootstrap resamples entire seed clusters, preserving the dependence among their four seat rotations. It is approximate, small-sample and conditional on valid pairs; it is not a guarantee of human-pod superiority. An interval crossing zero does not establish a clear ranking.

If unresolved outcomes are allowed to range from all losses to all wins, the possible Apex-minus-Layered difference across all scheduled slots ranges from **6.0 to 10.0 percentage points**. These are worst-case unknown-outcome bounds—not estimates or confidence intervals—and no invalid game is assigned a result.

## All-valid outcomes and seats

| All-valid result | Apex | Layered |
|---|---:|---:|
| Accepted games | 99 | 97 |
| Wins | 36 | 27 |
| Draws | 0 | 0 |

| Matched seat | Apex wins / games | Layered wins / games |
|---|---:|---:|
| Seat 1 | 11 / 24 | 7 / 24 |
| Seat 2 | 9 / 24 | 8 / 24 |
| Seat 3 | 6 / 25 | 6 / 25 |
| Seat 4 | 9 / 23 | 6 / 23 |

## Retained failures and retries

Retained attempts: **207**, including **200** initial attempts and **7** permitted retries. Invalid attempts retained: **11**. Slots recovered by retry: **3**.

| Invalid status, across all attempts | Apex | Layered |
|---|---:|---:|
| engine_error | 2 | 7 |
| not_run | 1 | 1 |

## Raw-audit recovery

All retained archive hashes match their original recorded metadata. One damaged historical archive was reconstructed byte-for-byte and saved separately as GGS_Private_Audit_v17_Repair.tar.gz. Full recovery requires this repair supplement plus every chunk listed by the raw-data index. Verify supplement and target hashes, then restore only the damaged audit archive as directed by the saved integrity record; accepted outcomes, logs, analysis and hash metadata remain unchanged.

## Interpretation limits

Wins are the primary endpoint. Secondary metrics describe activity and possible mechanisms, not causal card value. Announced GGS triggers are not verified resolved Dragon tokens; paid-return records are not independent opportunities; combat metrics union observations within a turn and may include extra combats. Face-down identities and post-elimination viewer gaps limit board observations. First-cast medians exclude games without a logged cast, whose counts are reported separately.

Audits and concurrent workers affect duration. These are descriptive collection times, not a controlled speed benchmark. Shared initial seeds do not force identical subsequent random choices once deck-dependent play diverges. Proxy opponents and AI piloting limit transfer to actual games. Unresolved games may be non-random, so failure counts and all-valid results accompany the matched analysis.

Raw logs and all attempts are retained in the saved data archive. Any private-audit retention issue is reported above. Public exports use explicit numeric/outcome allowlists and exclude hands, raw AI decision strings and card-level action records.
