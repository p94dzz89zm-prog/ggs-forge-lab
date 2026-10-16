# Hourly GGS test cycles — October 16

The user authorized repeated training, testing and fixes throughout this day.
`day_training_cycle.py` runs one bounded batch with an exclusive process lock.
It does not schedule itself and does not promise persistent compute.

Use the pinned `GGS_Test_Runtime_2026-10-16.zip` dependencies and the current
`fix/pilot-recovery-v35` source. The runtime includes engine resources, the historical r10
executable, TestNG and a pinned compiled AITest helper. The day ledger
identifies the currently adopted corrected executable: do not revert to r10. The regression runner
accepts `--fixture-classpath` so a vanished upstream source checkout does not
block retesting; its manifest records the helper's SHA-256.

An ordinary batch runs the 50 admission/learner/research Python checks, all
current engine suites (14 with MarchDefenseRegression), 128 disjoint randomized
positions and three tactical vectors across all four seat rotations of one
shared development seed. A third vector may mutate a parent only after
evidence-bound full-game rules and critical-decision admission. Matching
records alone never permit outcome feedback. Distinct
cycles reserve separate development and held-out seed ranges. Never treat four
seats of a seed as four independent random seeds.

The lock prevents duplicate batches under this driver. Inspect any manually
started collector before invoking it; the lock cannot cover an older process
that never acquired it. Outputs append to fresh cycle directories. Failures,
timeouts and logs remain preserved. Incomplete attempts contribute no reward.

Two gates remain separate:

1. Technical acceptance: regression checks and canonical game records pass,
   with no detected rule, process, timeout or evidence-integrity failures.
2. Pilot improvement: a reproduced decision error has a verified correction,
   or a frozen candidate beats the incumbent in sufficient independent held-out
   comparisons with the uncertainty and clustering reported.

A clean technical batch does not establish strategic correctness. The script
keeps strategy review pending and makes no automatic trusted-policy promotion.
An agent must review actual decision states and payable alternatives, add
regressions for reproduced mistakes, freeze changes and evaluate them with
fresh held-out conditions. Counterspells in a hand are not available answers
when every relevant mana source is tapped. Retain poor legal decisions as
potential negative examples rather than deleting their games.

Keep the current deck unchanged while measuring pilot changes. Preserve GGS
synergy as the first design priority and judge resilience at package/deck level.
Opponent lists are archived proxies, not verified current human-pod decks.
Query the complete card snapshot and weakness watch only after separating pilot
errors from possible deck failures; no causal card-cut verdict follows from
raw activity counts or a single loss.

Schedule only within the user's requested day. Report material improvements,
new blockers or the end-of-day evidence summary, with exact scoped counts.
Never claim universal zero-error play, guaranteed monotonic learning, a stronger
model from unchanged outcomes, or computation that did not actually execute.
Save private logs and model checkpoints privately after each bounded batch;
publish only source changes to the approved repository branch.

The March defense overlay is rebuilt separately with forge-fork/build_march_defense.py
over its pinned combined-lethal base. See forge-fork/MARCH_DEFENSE.md. Engine
regressions now isolate each suite's mutable user profile; missing completion
markers remain failures even after exit 0. Preserve and investigate failures.
Until incomplete model-startup exits are explained, run full engine validation
after pod collectors finish. Isolation alone did not eliminate those observed
concurrent-startup failures. Never count an unmarked exit as a clean suite.
