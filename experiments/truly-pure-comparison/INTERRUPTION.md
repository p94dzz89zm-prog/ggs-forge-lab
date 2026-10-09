# Truly Pure GGS comparison — interruption checkpoint

Status: INCOMPLETE. No deck-slot conclusions are supported yet.

## Frozen experiment
- Control: decks/Pure_GGS.dck; SHA256 166a88df0207b4792d3784f7ef0218510e3c0114a7208368b079ce99bdc07cf7
- Experimental: decks/Truly_Pure_GGS_v2.dck; SHA256 59b5e9d0ada799a7f1e2380bfc2faf908ab43642c75d1da8fb5e283ad1cb29a7
- Both imported as legal 100-card Commander decks. No substitutions/tuning permitted.
- Established Jaymie_Ezio / Gabe_Food / Destyn_Turtles pod; fixed repaired engine and casual-seven pilot assumptions.
- Engine jar SHA256 dbfba4a2af104503f063a5569597f04b57957a7ccdd52dce8dc9ed742b3b1061.
- Protocol and source at commit 35b281890dc725f27d71ecb2000b09bb42d006f7.

## Verified progress
- Reliability gate: 16/16 actual Forge games completed; all 128 audit streams validated, GGS creation and life-state reconciliation passed. Gate is excluded from performance.
- Production: 15 games were observed completed without simulator errors before execution access disconnected.
- Eight production games have verified durable logs in evidence Part 006. Do not assume these are balanced pairs: inspect the manifest.
- Seven later observed completions require workspace recovery before they can be audited or counted.
- No completed comparative report, cumulative rates, War Cadence conclusion, or slot recommendation exists.
- Execution failure was platform access: 409 environment_offline, Environment is not connected. This is not evidence of a Forge defect.
- Background jobs may or may not remain alive; do not assert continued execution.

## Pending measurement correction (must finish before interpretation)
The reused pure-ggs/analyze.py evasion helper treats printed Oracle text containing "can't be blocked" as active evasion. Activated/targeted abilities such as Alora do not confer unconditional evasion. This may inflate the 15-evasive-power Strong Snowball branch and access proxies.
Actual games, token births, damage/life logs and strict GGS Dragon-pressure events remain usable.
Verify active keywords and actual combat states. Recompute Strong Snowball and related attribution uniformly for both decks from raw audit snapshots. Do not reuse old dependency labels blindly. Document limitations for conditional/static access. This is an analysis correction, not deck/pilot/rules tuning.

## Durable evidence identifiers
- Validation JSON: libfile_8905116df6c88191a2200be1e8c82c6a
- Part 001 (5 gate): libfile_d8053bb6114c81919e15e4c35db0487b
- Part 002 (3 gate): libfile_50ccb58005688191a10a16cca6abe6a9
- Part 003 (2 gate): libfile_660dd9fb33a48191b5bece1b9fa46311
- Part 004 (2 gate): libfile_6f2169c28d9c8191aaa74204e2febc1b
- Part 005 (4 gate): libfile_9a29a3202c9c8191be9b2070394ad004
- Part 006 (8 production): libfile_c909b9cd290881918e45aefa9d4c32ac
All six archives were materialized back after saving and verified byte-identical with full gzip footer checks. Read manifests for game keys/member hashes. Do not publish download credentials or signed URLs.

## Resume procedure
1. Try existing workspace first; inspect running processes, controller.log, stage-032-progress.log, summaries and metadata.
2. Preserve all raw files. Recover missing checkpoints with current supported materialization helpers; validate archive footers and member hashes.
3. Reconcile the seven unsaved completions if present. Otherwise record availability loss; do not invent results.
4. Correct the evasion/Strong measurement above and reanalyze uniformly.
5. Resume only trusted completed rows under exact protocol hashes. Quarantine unrecorded unfinished/orphan attempts without overwriting their evidence. run.py --resume requires matching completed summaries; controller intentionally rejects an existing batch, so do not blindly restart it.
6. Do not rerun the complete reliability gate or begin broad simulator engineering unless real engine/pilot changes or defects require it.
7. Continue paired four-seat conditions: production seeds 202610202–233, four rotations each, both decks; predeclared stages 32/64/96/128 games per deck. Two workers; 600-second game budget; 30-second decision clock; no silent retries.
8. Save evidence frequently. Finish paired comparisons, manually review bottlenecks/AI artifacts and War Cadence mana counterfactuals, then issue the requested report and evidence-backed slot audit.

War Cadence analysis is observational plausibility, not randomized single-card causality. Mana screens omit some producers and exact payments. Card association is not isolated causality. Review POWER/PAYOFF candidates manually. Never infer healthy engine failure from win rate alone.
