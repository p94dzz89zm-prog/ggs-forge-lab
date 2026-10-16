# Pilot lab checkpoint, October 16 UTC

The first sandbox learner updated its preferences automatically after six
complete games. It explored BALANCED, ENGINE, ECONOMY, then selected ENGINE,
ECONOMY and BALANCED from its accumulated feedback. Each profile has two samples.
ECONOMY had the highest mean proxy utility (0.3723), not a demonstrated win-rate
or strategic advantage.

Two held-out paired comparisons found **identical measured effects** for the
learned ECONOMY profile and the BALANCED control:

| Seed | Own turns | GGS triggers | Opponent combat damage on own turns | Life gained | Proxy utility, either profile |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026103101 | 10 | 3 | 25 | 1 | 0.1262 |
| 2026103102 | 15 | 1 | 13 | 0 | 0.0328 |

Neither profile won either held-out game. This sample does not support an
improvement claim. It also does not prove the profiles make identical decisions
in every situation or that every decision in these games was correct.

The separate variety probe used saved Two-card-trial and Orochi-only decks,
four seeds and all four seat rotations. Three games completed; one timed out
at the 300-second engine limit, turn 59. The timeout has no winner and is not
eligible for learning. None of these probes feeds the training database.

This evidence archive contains **14 attempted games: 13 complete and one
timeout**. Six were sandbox training, two learned-profile held-out tests, two
baseline controls and four separate variety probes. Additional diagnostic
replays are outside this archive and must be reported separately.

The source checkpoint adds the reviewed-experience gate. **Zero episodes are
strategy-approved.** Normal reviewed inference retains BALANCED. A high reward
cannot make unreviewed data eligible. Referee output distinguishes record
integrity from rule coverage and strategic review; it does not silently equate
a completed game with correct piloting. All losing results remain preserved.

Fresh engine validation passes 131 targeted scenarios and 64 seeded randomized
combat positions: 211 executions including 16 repeated Prowler checks. Six
Python learner/gate tests pass. The combat randomizer checks legal attacks and
blocks and that forecasting does not mutate the battlefield. These checks are
scoped software evidence, not a certificate of perfect Magic play.

The full-game experiments used engine SHA-256
`4ad8de999aca2c4e76b6d3cb7a4c586b6b8b69a59a6e92b68db49e2d2124fad2`.
The final audit-scope repair has a different hash, recorded under
`forge-fork/validation/pilot-recovery-r6/`. Do not pool them silently.

`evidence.zip` contains complete canonical records/transcripts, inputs and
commands, sandbox experience and a consistent SQLite backup. Variety probes
include the GGS seat's private audit stream; other seats' private audit streams
are omitted. Its manifest hashes every member. The archive passes ZIP CRC
verification and has a separate SHA-256 receipt.

The report at `reports/pilot-lab.html` is a read-only view of the eight learner
episodes. Controls and separate probes are in this archive rather than that
table. No million-game run or continuous background training is claimed.
