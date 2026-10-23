# Stage56: native mulligan declaration barrier

The historical PilotA game 2026202029 returned player3's first hand at turn0,
call171/stream732, before players0/1/2 declared. CR103.5 requires the round's
declarations first. The original history remains discrepant and unapproved.

The pinned recovery runtime reproduces this class of defect: the second
declaration observes the first player's completed redraw. A one-method overlay
collects declarations, then applies the round's keep/redraw actions in existing
player order. Previously kept players remain excluded; game-over during a
declaration returns without executing queued actions. Policy selection, cost of
mulligans, initialization and post-mulligan methods are unchanged.

Three native controls used deterministic fixture seed56:

| Control | Observed result |
|---|---|
| Original standard multiplayer policy | Expected failure at second declaration |
| Patched standard multiplayer policy | Four free redraws, then four keeps; barrier and conservation pass |
| Patched house policy | Three rounds of four free seven-card redraws; automatic keep; barrier and conservation pass |

The standard control means **one redraw per player**, not four free redraws per
player. Tests inspect all player counters and keep states at every declaration.
Policies are deliberately injected into the actual private round method; this
does not establish full service configuration integration or the correctness of
every London mulligan detail. No new natural game or historical event approval.

Runtime archive SHA256:
`5044f0aeed36cbda2639d14e68d23e1aa55fb0fb703fee760babf849cdbe675d`.
Base JAR: `c695dc79f5c5c1165c16c42c0419e2628cbdcfaac41a53168eb45bb4aa1a3c79`.
Overlay: `c2a80cd3f3f30cfa16ebd6b7f5716641031a33c5ef0b3404e1ddd30e6b0b133e`.
All other JAR entries are byte-identical; normalized bytecode of the other four
MulliganService methods is identical. The base is an earlier pinned recovery
runtime, not a claim that the latest historical native overlays were rebuilt.

Reproduce with Java17 compiler modules, the preserved runtime/resources, and:

```
python3 forge-fork/build_mulligan_round.py --base /runtime/pilot-recovery-10.jar --expected-base-sha256 c695dc79f5c5c1165c16c42c0419e2628cbdcfaac41a53168eb45bb4aa1a3c79 --output /fresh/mulligan-round.jar
python3 forge-fork/run_mulligan_round.py --runtime /runtime --patched /fresh/mulligan-round.jar --logs /fresh/controls
```

The initial three controls used the equivalent captured invocation, before the
reusable runner was added. Raw outputs and exact inputs are checkpointed. The
runner itself was syntax-checked; its three JVMs were not repeated this stage.
The complete Python suite remains407passing. No pilot training, natural-game
certification or reserved replay work was performed. Original replay466choices
and1790/1985conditional support remain unchanged. Stage47/48 remain untouched.

Next: bind this narrow overlay to the latest verified native overlay chain,
verify full service selection under house opt-in, and audit London bottom-card
timing separately. Opening shuffle/selection evidence and historical card-data
provenance remain blockers for all three preserved games.
