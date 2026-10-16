# Rigor pass

The repaired executable passes **157 targeted scenarios and 512 randomized
full-controller positions**. That is 685 executions including 16 repeated
Prowler checks. All ten engine suites pass. Separately, all **18 Python
learning/integrity tests** pass. Logs, fixture hashes and executable provenance
are in `forge-fork/validation/rigor-r8/`.

## Confirmed improvement

The expanded planner probe found seed 20128 proposing three unblockable/flying
attackers into Crawlspace. Investigating the full controller showed that it
already prevented illegal combat, but fell back to attacking with nothing.
The targeted before-fix full-controller fixture reproduces that empty result.

The fix preserves a useful legal subset of the proposed attacks. Targeted tests
verify two attacks under Crawlspace, one under Silent Arbiter, retaining a fresh
GGS connection, ordinary non-GGS use, the disabled boundary, valid declarations
and unaffordable attack taxes. It does not change card rules or add attacks to a
new defender. Search is bounded to at most ten proposed attackers; other cases
retain the existing fallback.

The final 512-position run exercises the full controller, including seed 20128.
It uses the subset repair three times and reports no remaining invalid-attack
fallbacks in that batch. This establishes a specific behavior improvement, not
globally optimal combat or a proven win-rate increase.

## Integrity and false positives

The gate rejects changed consoles, records or transcripts; duplicate completion
markers; forged metrics or rewards; winner mismatches; unsafe evidence paths;
failed/held-out training approval; and engine errors. Reviewed inference cannot
consume unreviewed high-scoring episodes. File checks and reward recomputation
pass for all six original sandbox episodes. **Strategy-approved episodes: zero.**

One sandbox episode was temporarily withheld because of repeated `Correcting
zone for Hithlain Rope` diagnostics. The pinned upstream
`GameAction.controllerChangeZoneCorrection` prints that message as part of
normal control changes. The Rope's card script passes control to the next
player. The diagnostic alone therefore does not establish an invalid result.
The episode is back to pending, and both review events remain in the history.
The test suite now verifies that this normal diagnostic is not treated as an
engine failure. No episode was rejected simply because it lost.

## Reproducibility and remaining limits

Two runs with the same executable, decks, seat, seed and strategy flags timed
out at a 180-second budget. Their common recorded prefix matches; one recorded
1,313 lines and the other 1,328 before the result marker. Completion and full
game reproducibility are not established by that truncated comparison.

A separately instrumented profiling run completed in 83.727 seconds and yielded
5,683 execution samples. Static-ability traversal and collection construction
are prominent. This is profiling evidence, not proof that a performance fix was
made: instrumentation and execution path differ from the timed-out runs.
Timeouts and their records remain preserved and are not learning completions.

The earlier paired held-out comparison showed identical measured effects for
the learned and baseline profiles on both tested seeds. There is no evidence
yet of broader learned improvement. A profile bandit over three fixed strategies
is not an all-deck tactical learner, and the current reward omits important
aspects of card advantage, defense and opportunity cost.

The private supplementary archive preserves the diagnostic games, original
failed probes, final results, profiler output and updated experience database.
It is intentionally separate from the public source branch.

## Final runtime smoke

Both full-pod smoke games on the repaired executable completed: GGS_Current
seed 2026106101 (59.070 seconds) and GGS_Two_card_trial seed 2026104103
(32.749 seconds). They are runtime checks, not evidence that the repair improves
win rate. Across all engine versions and diagnostic runs in this session there
were 21 full-game attempts: 17 completions and four timeouts. Do not pool their
win rates or treat different builds and instrumentation as one experiment.
