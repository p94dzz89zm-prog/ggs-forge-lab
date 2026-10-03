# Current Apex War Form vs Layered GGS: two pod games

The current Apex list is the exact 100 supplied by Dimitri on October 2, 2026.
It supersedes the older Apex v3 for current testing. Commander: Goro-Goro and
Satoru. The named deck file has the same cards as GGS_Current. The Layered list
is GGS_Layered_v1. The supplied Draconic Visitor/Purphoros slots are tested as
listed; the reference does not claim all cards are physically owned.

## Results

| Deck | Winner | Engine seconds, with audit | Last logged global turn | GGS first cast, own turn | GGS triggers logged |
|---|---|---:|---:|---:|---:|
| Current Apex | GGS | 52.340 | 44 | 7 | 3 |
| Layered v1 | Destyn | 28.518 | 44 | 3 | 5 |

Both used seed 20261019, the same seat order (GGS, Jaymie Ezio, Gabe Food,
Destyn Turtles), the same accepted v15 jar and commander-aware GGS ninjutsu
policy, with stock AI handling the other seats and unoverridden choices.
One game per deck is not a win-rate estimate or proof one deck is stronger.
Different deck contents/order mean the same seed did not produce the same hand.
The older Apex v3 game started before the supplied-list correction is excluded.

## What actually contributed

**Purphoros was Apex's clearest contributor.** Cast on Apex's sixth own turn,
it recorded 15 creature-entry triggers and 38 two-damage records to opponents:
30 to Jaymie, 26 to Gabe, 20 to Destyn, **76 noncombat damage total**. This is
aggregate damage across players, not 76 damage to one player. Opponents dying
partway through the sequence explains the unequal totals. Late Kari Zev and
Goldlust Triad entries helped trigger this engine; ordinary creatures and new
Dragon Spirits also contributed. Goldlust itself logged four combat damage to
Jaymie and four to Gabe. Purphoros's late pump activations also preceded Apex's
final combat. These observations support keeping the supplied Purphoros slot
in the tested Apex reference and selecting it for a future Layered trial.

Official rules reference for its creature-entry damage ability:
https://magic.wizards.com/en/news/feature/commander-masters-release-notes

**Layered did make its commander engine work.** It cast GGS on its third own
turn and recorded five GGS triggers. Orochi Soul-Reaver logged 20 combat damage
across Gabe/Destyn; Dragon Spirit tokens logged another 15 to them. The deck
also played stolen/manifested cards and reanimated Krang. It still lost to
Destyn's developed counter/token board. More GGS triggers alone did not decide
this pair. The comparison suggests testing an additional way to convert entries
into table-wide damage, rather than concluding Layered cannot make Dragons.

**Commander deployment needs a pilot audit.** Apex did not cast GGS until own
turn seven (global turn 26). At global turns 14/18, recorded MAIN1 evaluations
rejected GGS as CantPlayAi. The earlier turn-14 snapshot shows Xander's Lounge,
Watery Grave and Raucous Theater untapped, covering U/B/R. Later MAIN2
observations report CantAfford after the pilot spent mana elsewhere. This is
consistent with strategic sequencing delays, not only insufficient lands.
It is an investigation target, not a reconstructed legality proof for every
priority window. The commander-aware extension currently focuses on ninjutsu;
most permanent sequencing still uses the stock pilot. Test precombat commander
priorities and mana reservation before interpreting this run as a mana-base
failure or changing the user's list.

**No verdict on Draconic Visitor.** It did not appear in Apex's recorded hand
snapshots and was not cast. This game cannot establish whether it improves its
slot. No unobserved card was recommended for cutting from one result.

## Upgrade and speed conclusions

The best next deck experiment is **a single-slot Purphoros trial in Layered**,
using matched repeated seeds and seats after auditing commander priorities.
A specific cut has not been selected from this two-game sample. This is a
playtest candidate, not a measured upgrade or purchase recommendation. No deck
changes were made beyond importing the exact current Apex reference.

The stronger immediate simulation improvement is **commander sequencing in the
pilot**: test whether MAIN1 creature heuristics miss fresh-attacker/ninjutsu
opportunities that require GGS already in play. Improving that play may change
game lengths and outcomes; it must not be called a CPU-only optimization.

The timing difference is not an engine speedup. Both runs ended at logged
turn 44 but followed different states and actions. Apex recorded 2,103 priority
snapshots and 19,243 evaluation rows; Layered recorded 1,911 and 16,297. Audit
output was 57.594 MB vs 45.118 MB. Full private-state recording and file I/O are
included in both engine times. Counts locate workload differences; they do not
attribute seconds to combat prediction or prove more rows caused all of the
extra time. Production throughput should continue using audit disabled unless
these detailed decisions are needed.

For actual engine optimization, resume the previously selected computation
inside attacker/blocker survival predictions after this diagnostic review.
These two games did not time those individual functions, and no v16 patch,
search reduction or runtime setting was introduced.

## Reproducibility and limits

Apex completed October 2; Layered ran October 3 after the earlier engine-resource
workspace expired. The retained jar and deck hashes matched the original Apex
metadata. Layered resources were restored from exact Forge source pin
4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676. Resource hashes and the prior preference
files were not captured; this is not a same-session performance benchmark.
Both used Java 17, 1536 MiB heap, Parallel GC, non-tiered compilation, threshold
1000, headless mode, one JVM worker and a 180-second game limit, with audit enabled.
Both produced trusted completed results. No simultaneous games, profiling or
compilation ran during the Layered game; Apex's original run also ran alone.

Jar SHA256:
9389e96f9190e051f1b739460e61e0b407b087aa7fb3f5f423d6169bc5eeab68

Raw logs (lossless .log.gz archives), metadata and derived counts are committed under
performance/pod-apex-layered-20261019. The complete private audit streams remain
local; selected hand/board snapshots and evaluation records substantiate this
report. 'Own turn' is counted from the GGS Turn log entries, distinct from the
engine's global-turn index and final Game Outcome display.
