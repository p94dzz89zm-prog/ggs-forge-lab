# Frozen Truly Pure v2 versus Pure GGS

## Final status — completed

All256 production games (128 per arm) are completed, saved and verified;16 validation games are excluded. Both decks remain unchanged. See [the final13-point report and slot audit](FINAL_REPORT.md), [corrected summary](final-summary.json), [representative canonical log excerpts](representative-log-excerpts.md), and [reporting corrections](FINAL_MEASUREMENT_CORRECTIONS.md). The full result bundle retains all per-game observations, source hashes, archive-member hashes and11 complete representative transcripts. Historical interruption notes remain evidence of prior states, not the current status.



This is a prospective paired package comparison, not individual card ablation. Pure_GGS remains byte-identical to its frozen baseline. Truly_Pure_GGS_v2 imports the supplied audited100-card list, including Ingenious Infiltrator and Sakashima's Student and excluding Reconnaissance Mission and War Cadence. Firework v1.0 remains untouched.

Both experimental decks and Jaymie_Ezio, Gabe_Food and Destyn_Turtles must pass actual Forge Commander conformance before any games. `protocol.json` pins every deck and the already repaired decision-clock executable. No rules, pilot or deck changes are introduced for this comparison. All seats use the established casual full-seven reshuffle house rule; no London sculpting.

`run.py` runs isolated actual Forge games with identical pod/pilot settings, common seeds, all four rotations, two workers,600-second game budget and30-second AI decision budget. It stops submitting games on a genuine runtime/measurement failure. It never retries invalid games or approximates card behavior. Eight audit streams, canonical transcripts and engine records are retained per game. The16-game validation gate is excluded from experimental estimates.

The four planned production stages add32 games per deck each, to128 per deck. Rates and timing are compared at64,96 and128; unresolved uncertainty is reported at the cap. Common seeds do not guarantee identical draws or counterfactual trajectories because changed choices consume RNG differently.

`measure.py` supplements the existing phase/life/token-reconciled extractor. It distinguishes hostile commander loss from voluntary reload/protective bounce; records observed responses plus commander preservation; measures reentry and actual subsequent Dragon production; observes card/Treasure return and continuation; distinguishes factory deployment/token creation from fresh factory tokens actually attacking; and tracks Student copies. Resource attribution is conservative and may miss returns when several effects resolve without an intervening priority snapshot.

First ready ignition opportunity is a candidate, not proof of legal connection. Protection cards visible in hand are candidates, not proof of mana/target legality. Untapped-source budgets omit floating mana and special source restrictions. War Cadence analysis is an observed-blocker and affordability screen, not a replayed causal counterfactual. Actual spells/activations on those turns are preserved as opportunity-cost evidence; precise payment attribution is unavailable.

Whole-board pressure uses the existing objective damage/attack threshold. A stricter Dragon-specific measure requires20 ready flying power from GGS-created Dragons or15 GGS Dragon combat damage in one own turn. Neither is a claim of guaranteed table lethal. Strong/basic snowball definitions remain aligned with the original Pure study.

`compare.py` uses paired four-seat whole-seed bootstrap95% intervals. Timing and recovery use explicit conditional denominators and censoring. AI bias is not included in statistical intervals. Wins are secondary. Automated pillar labels are screens requiring log review, especially POWER/PAYOFF candidates. Becoming threatening and then receiving multi-opponent pressure remains separate from engine failure.

`checkpoint.py` saves only completed evidence, validates all member payloads and the gzip footer, and verifies a fresh saved copy byte-for-byte before advancing receipts. Runtime caches and live audit files are excluded. Its Library transfer helpers must be fetched from the current Library skill, not an old project copy.

Run from the repository parent, with the saved repaired executable in `decision-clock-probe/engine-decision-clock.jar` and pinned resource tree in `restored-v28/engine`:

```bash
python3 ggs-forge-lab/experiments/truly-pure-comparison/run.py --out truly-pure-comparison/gate --seed 202610200 --seeds 2
python3 ggs-forge-lab/experiments/truly-pure-comparison/check_gate.py truly-pure-comparison/gate
python3 ggs-forge-lab/experiments/truly-pure-comparison/run.py --out truly-pure-comparison/stage-032 --seed 202610202 --seeds 8
```

No production begins until the gate is accepted.
