# Truly Pure GGS v2 versus frozen Pure GGS — final controlled comparison

Completed sample: **256 actual Forge games, 128 per deck**, across 32 common seed blocks and all four seat rotations. Another 16 validation games are excluded. Both decks passed 100-card Commander conformance, including exactly one commander, and remained byte-identical throughout. No deck tuning was performed.

## Verdict

**Truly Pure v2 is not a demonstrated upgrade.** It started GGS somewhat more often and returned resources more often/earlier, but did not turn those improvements into stronger snowball or equally frequent whole-board pressure. Its observed threatening-state frequency fell 8.59 percentage points; the paired 95% interval was−16.41 to−0.78 points. The predeclared 10-point material-decline margin is therefore not excluded. A statistically inconclusive win-rate difference does not establish equivalence.

**GGS can supply enough payoff to win without a dedicated fireworks package. This particular reallocation did not make that payoff reliably arrive, survive and convert quickly enough.** That is narrower than either “fireworks are mandatory” or “fireworks are unnecessary in every optimized build.”

The main measured failure screen remains protection/recovery. There is also a distinct Dragon-board attrition/delivery problem: an operational commander can produce several Dragons while targeted removal prevents those Dragons from accumulating. More cards in hand or more total Dragons over a long game does not necessarily create concentrated pressure soon enough.

## 1. Overall performance

Rates use all 128 games per arm. Differences are experimental minus control; intervals resample whole four-seat seed blocks 4000 times. They quantify seed variation under the fixed simulator, not pilot bias. Intervals are unadjusted for multiple outcomes.

| Outcome | Pure control | Truly Pure v2 | Difference, pp | Paired 95% interval, pp |
|---|---:|---:|---:|---:|
| First GGS-created Dragon |95/128, 74.2%|102/128, 79.7%|+5.47|−3.13 to+14.06|
| Basic snowball |50/128, 39.1%|50/128, 39.1%|0.00|−9.38 to+8.59|
| Strong snowball |56/128, 43.8%|45/128, 35.2%|−8.59|−17.97 to+1.56|
| Whole-board threatening state after ignition |49/128, 38.3%|38/128, 29.7%|−8.59|−16.41 to−0.78|
| Strict GGS-Dragon pressure |21/128, 16.4%|17/128, 13.3%|−3.13|−12.50 to+6.25|
| Simulated win |23/128, 18.0%|19/128, 14.8%|−3.13|−10.94 to+4.69|

This is a nine-slot package comparison, not a clean “payoff versus engine” ablation. Several removed cards also do engine jobs. **Goldspan Dragon is the clearest example: haste, evasive fresh ammunition and Treasure/mana production are role compression, not merely a separate finish.**

Actual control-only cards: Aggravated Assault; Dragon Tempest; Fallen Shinobi; Goldspan Dragon; Karlach, Fury of Avernus; Port Razer; Purphoros, God of the Forge; Roaming Throne; War Cadence.

Actual experimental-only cards: Dauthi Voidwalker; Dour Port-Mage; Ingenious Infiltrator; Kaito, Cunning Infiltrator; Mystic Remora; Sakashima's Student; Siren Stormtamer; Spellskite; Swiftfoot Boots.

Truly v2 correctly excludes Reconnaissance Mission and War Cadence and includes Ingenious Infiltrator and Student. Reconnaissance Mission is also absent from the frozen control; this experiment does **not** isolate Mission versus Infiltrator.

## 2. Ignition and opening hands

| Observed measure | Pure | Truly v2 |
|---|---:|---:|
| Mean mulligans; median |0.28; 0|0.28; 0|
| Initial keeps with 2–3 effective land faces |97/128|96/128|
| GGS cast, observed games |127/128|124/128|
| Mean first cast turn; median |3.93; 3|3.72; 3|
| First ready-body/GGS combat-begin candidate |101/128|96/128|
| Mean candidate turn; median |6.73; 6|6.19; 6|
| Mean first Dragon turn; median |6.93; 6|6.85; 6|
| Second Dragon observed |73/128|73/128|
| Mean second Dragon turn; median |8.15; 7|8.23; 8|

Timing is conditional on observing the event; the successful groups differ. A lower conditional mean is not an unconditional speed guarantee. The ready-body candidate misses attack-trigger tokens and later-combat ninjutsu, so it is not a complete count of viable ignition opportunities. Blocker/target legality is not proven by that metric.

The experimental first-Dragon rate improved by 7 games, but first-Dragon timing barely changed and the number reaching a second Dragon did not improve. Among ignited games, another Dragon within two own turns occurred 61/95 for Pure versus 59/102 for Truly. **The weak point shifts from starting to converting the start into repeatable growth.**

Per-game exports retain the observed initial hand, effective land-face count, mulligans, cast events, first candidate opportunity, separate trigger events and resolved Dragon births. These are not sculpted London-mulligan hands: the frozen pilot used the stated casual full-seven reshuffle house rule.

## 3. Access

| Measure | Pure | Truly v2 |
|---|---:|---:|
| Recognized access permanent deployed |119/128|109/128|
| Repeated fresh unblocked connections confirmed |67/128|73/128|
| Mean confirmation turn; median |8.31; 8|8.26; 8|
| Games with an observed blocked-fresh ignition combat |36/128|33/128|
| Such combat windows |76|74|
| Fresh bodies held back despite public blockers |15 games|24 games|

Deployment is not functioning access: an activated access card can sit unused. Repeat connections are the stronger execution observation. The cut did **not** produce an aggregate increase in observed blocked-fresh games, and repeat connections slightly increased. However, actual blocked windows still occurred in about a quarter of experimental games. Held-back candidates are uncertain: blocker presence does not establish legal blockage or explain the AI's choice.

Cheap/permanent access is therefore **not shown insufficient in aggregate**, but the claim that it makes Cadence redundant is **not proven**.

## 4. Ammunition

| Measure | Pure | Truly v2 |
|---|---:|---:|
| Recognized factory/reload deployed |110/128|111/128|
| Same recognized source produced ammunition on two own turns |76/128|77/128|
| Mean confirmation turn; median |7.62; 8|6.45; 6|
| Fresh factory ammunition actually attacked on two own turns |62/128|66/128|
| Mean usable confirmation turn; median |8.08; 8|7.05; 7|

Truly's ammunition became renewable/usable earlier among games establishing it, but confirmation frequency only modestly improved. Urabrask's Forge, Fire Navy Trebuchet, Lagomos and Loyal Apprentice generated the most observed fresh factory attacks. Experimental counts were 148, 77, 71 and 58 respectively; these are event counts, not independent games or causal win contributions.

Kaito's factory role was corrected before final export:30 Ninja creation events were observed, but **zero of those tracked tokens attacked while fresh**. That is a tempo/conversion warning under this pilot, not proof the tokens had no later use. Its six canonical loot resolutions across four games are card selection, not net hand growth.

Factories are recognized source families, not exhaustive detection of every copied opponent ability or possible reload line. Read factory deployment, repeat creation and actual fresh attacks separately.

## 5. Momentum and self-feeding connections

Observed card/Treasure return was established in 92/128 Pure games versus 109/128 Truly games; conditional mean turn 7.48 versus 6.52, median 7 versus 6. Resource-exhaustion screens occurred in 31 versus 24 games. **This is the clearest favorable experimental direction**, but it did not carry through to strong snowball.

| Resource-return source followed by GGS creation within two own turns | Pure games | Truly games |
|---|---:|---:|
| Orochi Soul-Reaver |16|21|
| Prosperous Thief |10|18|
| Frostcliff Siege |11|14|
| Professional Face-Breaker |10|13|
| Skullclamp |6|13|
| Mystic Remora |—|13|
| Dour Port-Mage |—|12|
| Enduring Curiosity |5|10|
| Grim Hireling |5|9|
| Ingenious Infiltrator |—|8|
| Goldspan Dragon |16|—|

These are **feedback associations**, not proof a particular drawn card/Treasure paid for the next action. Remora is opponent-fed draw, not a connection-triggered loop. Source attribution uses recognized abilities and net hand gain; simultaneous draw/discard, impulse access and copied opponent abilities can be missed.

The most persuasive role-compressed engine contributors are Orochi and Prosperous (ninjutsu/fresh action plus Treasure), Frostcliff (actual return plus access configuration), Face-Breaker (Treasure plus resource conversion), Dour (draw/reload/protective bounce), and Infiltrator (ninjutsu plus actual draw). Remora returned 136 observed net cards, Infiltrator 46 and Dour 36; these are conservative snapshot attributions.

Goldspan returned 66 observed Treasures in the control and appeared in 16 continuation games. Removing it removed engine acceleration as well as an evasive threat. That is a regression candidate; its isolated effect was not tested.

Frostcliff's draw mode and haste/trample mode are selectable alternatives, not simultaneous benefits. Net-hand-gain counters also miss looting/card selection and some impulse or copied-card utility.

## 6. Protection and recovery

| Observed measure | Pure | Truly v2 |
|---|---:|---:|
| Games with nonvoluntary commander loss |99/128|107/128|
| Nonvoluntary loss events |189|221|
| Removal/exile/wipe/bounce/counter |92/14/74/8/1|115/17/78/11/0|
| Targeted or known-wipe threats logged |171|203|
| Threats with protection candidates visible |74|118|
| Threat events with observed responses |5|15|
| Responses preserving commander on board/phased |4|8|
| Responses avoiding loss, including save to hand |4|12|
| Such responses followed by Dragon within three own turns |3|7|
| Post-cast operational combat uptime |927/1088, 85.2%|962/1133, 84.9%|
| Mean observed reentry downtime; median |1.60; 1|1.49; 1|
| Restart within three turns with adequate followup |57/133, 42.9%|79/170, 46.5%|
| Restart at any observed time after loss |92/189|115/221|
| Post-wipe Dragon plus board-power recovery |28/66, 42.4%|30/71, 42.3%|
| Observed command-to-stack casts, including initial casts |272|300|

**Truly improved observed active protection, but did not improve commander uptime or post-wipe recovery.** Reentry was slightly quicker among observed reentries; restart-with-followup was slightly higher, without establishing a reliable causal improvement. More command casts suggest repeated redeployment remained costly; exact commander-tax payments are not logged.

Commander preservation is not momentum preservation. Only seven experimental response events were followed by another Dragon within three own turns. Dour saved GGS to hand on four logged threat responses, with two followed by Dragon production. Spellskite appeared in two response events, one avoiding loss, neither followed by a Dragon within that window. Response-source counts can overlap within one threat event.

“Removal” includes combat deaths/unattributed zone losses, not only opposing removal spells. The pilot sometimes attacked GGS into lethal blocks. Candidate cards visible in hand are not verified castable protection. Boots' static protection is a separate presence proxy; it cannot establish how many targeting attempts were deterred.

Recovery censoring is substantial:56 Pure and 51 Truly loss events lacked the full followup window and no observed early restart. Reentry averages omit nonreturning commanders. Operational uptime excludes phasing; successful protective phasing is not counted as removal. A Dragon resolving from a pending trigger after GGS leaves is legitimate production but **not** an engine restart.

## 7. Threatening-state frequency and timing

The whole-board threshold is 20 unblocked attacking power, 15 own-turn combat damage, or 20 own-turn total damage after ignition. It is a pressure proxy, not table lethal. Truly reached it less often, although its conditional mean among successes was 9.32 versus 9.71 own turns (medians 9 versus 10).

Strict Dragon pressure requires 20 ready flying power from GGS-created Dragons or 15 Dragon combat damage in one own turn. It occurred 17 versus 21 times, with conditional mean 10.47 versus 10.67 turns; both medians 10. Copies of existing Dragons are excluded. Control Dragon production can still be amplified by Throne/extra combats.

Truly created 311 GGS Dragons versus 294 in Pure and logged 1899 Dragon combat damage versus 1805. **Higher totals did not mean more frequent timely threatening states.** Totals mix game duration, more ignited games, outliers and opponents' life gain. They do not prove better per-game snowball or survival.

The control's threat-path classifier found material amplifier contributions in 28 of 49 threshold games, including Purphoros in 19. Fifteen paths passed a subtraction-based dependency screen. These are observed contribution/arithmetic screens, not replayed proof that those cards were necessary. They are evidence of conversion value, not an instruction to restore all nine removed cards.

## 8. Wins

Pure won 23/128 versus Truly 19/128. The difference's paired interval includes both a meaningful experimental loss and a small gain. Conditional mean winning own turn was 13.26 versus 13.21; medians 13 versus 12. These are different winning subsets.

Every experimental win included GGS Dragon production; 22 control wins did, with one fallback win without any GGS Dragon. This establishes that a no-dedicated-payoff build can win in the tested environment, not that Dragons alone caused all 19 wins. Other creatures, copied abilities and opponent choices also contributed.

Wins are reliable recorded engine outcomes but **not calibrated real-pod win predictions**. The frozen pod was Ezio/Food/Turtles, not the later live goblin configuration. Human piloting and political targeting were not modeled faithfully.

## 9. Stall/failure distribution

The automated primary screen is priority-ordered and mutually exclusive. It is not an independent prevalence count for each pillar. Losses after pressure and unresolved followup remain separate rather than forcing every loss into a deck defect.

| Automated primary screen | Pure losses | Truly losses |
|---|---:|---:|
| IGNITION |6|4|
| ACCESS |3|4|
| AMMUNITION |7|6|
| MOMENTUM |1|2|
| PROTECTION/RECOVERY |53|64|
| Unresolved payoff-screen candidate—not confirmed POWER |1|0|
| Opponent won after threatening state / focused |28|20|
| Opponent won before threshold / limited followup or unresolved |6|9|
| Total losses |105|109|

Protection takes precedence in this screen and can hide a later ammunition stall. For example, Truly 202610202, r2 has an automated protection label but a reviewed terminal ammunition failure. The dataset retains both observations rather than silently rewriting the history.

An independent payoff-review queue ignores Strong and the automated primary label:nonwinning, no threshold, at least three cumulative Dragons, and at least three own turns after first production. It contains 17 Pure and 14 Truly games. All 31 have compact production, phase, Dragon-loss and disruption evidence in the accompanying file. The manual-review file contains six deeper case adjudications, four within this queue. Twenty-eight candidates had commander disruptions and/or recognized wipes; that history does not prove their later engines were unhealthy. The other three are the Dragon-attrition/opponent-race cases discussed below. Exact causal primary attribution remains uncertain for overlapping/unreplayed cases.

**No reviewed case cleanly isolates “an intact sustained five-pillar engine's Dragons lack enough power.” That is not proof POWER/PAYOFF never occurs.** Other causes overlap, thresholds miss some eliminations, and alternate-line replay was not performed. The strongest experimental falsification candidate remains healthy-commander production followed by Dragon removal, not commander downtime.

## 10. War Cadence cut

Truly had 33 games and 74 combat windows with fresh creatures actually blocked, GGS operational, no unblocked fresh connection, and no GGS creation in that combat. These satisfy the requested observed-access-deficit flag. Coverage of states where absent GGS merely “could become operational” is uncertain and is not invented.

Assuming Cadence was already deployed, the untapped-source screen was potentially affordable in 49 of 74 windows, across 26 games. Pure had 38 of 76 windows across 22 games. The screen chooses an activation sufficient to exceed the attacked defender's observed budget; it omits floating mana, red requirements, special sources, response choices and Cadence's earlier casting cost. Adding a simplistic three-mana deployment allowance reduces the experimental count to 35 windows; even that is **not** a legal counterfactual replay.

Actual experimental actions on flagged turns included development in 57 windows, commander development/haste in 16, protection in 9, and a recognized ninjutsu activation in 1. Categories overlap. In the 25 screened-unaffordable windows, development occurred 20 times, commander development/haste 10, and protection 2. These show competing uses for mana, not exact causal “mana saved by the cut.” Cast-based ninjas can fall into development; the ninjutsu category is not exhaustive.

Representative Truly 202610210, r1 had fresh Lagomos tokens blocked on turns 7–10. Turns 7/8 had zero screened combat-begin budget and actual commander redeployment. Turn 10 had budget 8 versus an already-deployed Cadence screen 4, but Shadow Rift was assigned to GGS rather than fresh ammunition. Cadence plausibly could have mattered there; cheaper access being available is not proof of correct deployment.

In the control, Cadence was exposed in 27 games, deployed 24 times, and activated only nine times across five games. Low activation count limits the inference. It can serve existing-army finishing access too, which the fresh-ignition flag does not exhaustively test.

An instructive tempo case is Pure 202610219, r1:Cadence was activated atX=5 andX=1 on own turn 17 (nominal activation costs 6+2), but Purphoros plus attack-created tokens killed the final opponent **before blockers/combat damage**. Those activations did not deliver that game's decisive connection. Conversely, Pure 202610203, r2 had a Cadence activation and another Dragon on turn 9; association is not isolated necessity.

**Conclusion:** no aggregate access regression condemns the cut, but 26 games with plausible already-deployed affordability windows prevent calling Cadence redundant. Student-versus-Cadence is unresolved and deserves a dedicated one-slot paired test. Do not automatically restore or permanently cut Cadence from this package comparison.

## 11. Individual-card audit

Counts describe observed contributions, not card-level causal improvements. Exposure is not randomized; tutors, survival and game length differ.

| Slot/card | Evidence | Evidence-based disposition |
|---|---|---|
| Orochi Soul-Reaver |21 experimental continuation games; 82 attributed Treasures|Protect this engine role: fresh ninjutsu action plus mana.|
| Prosperous Thief |18 continuation games; 43 attributed Treasures|Strong role-compression keep.|
| Frostcliff Siege |14 continuation games; 108 attributed net cards|Strong momentum/access core; actual configuration still matters.|
| Professional Face-Breaker |13 continuation games; 60 Treasures|Strong engine core; conversion attribution is incomplete.|
| Dour Port-Mage |12 continuation games, 36 net cards, four commander saves to hand|Best-supported added multi-role card; keep for next architecture test.|
| Ingenious Infiltrator |33 deployment games, 46 net cards, eight continuation games|Supported engine contributor; Mission comparison was not isolated.|
| Mystic Remora |28 deployment games, 136 net cards, 13 continuation games|Strong observed return; opponent-fed, not a connection engine. Upkeep cost not fully measured.|
| Swiftfoot Boots |35 deployment games; static protected-combat games increased 33→40|Useful redundancy, not demonstrated wipe/combat survival improvement.|
| Siren Stormtamer |21 deployment games, zero logged activations|Pilot/usage review before a cut; do not equate zero use with zero legal value.|
| Spellskite |24 deployment games, two commander-threat responses, one avoidance, no near-term Dragon after either response|Watch slot; observed protection did not sustain the loop here. Human/target-legality test needed.|
| Dauthi Voidwalker |29 deployment games, zero logged activations|Shadow body/graveyard prevention not fully valued by resource counters; no evidence for automatic removal.|
| Kaito, Cunning Infiltrator |11 of 35 exposures unconverted for≥3 turns; 30 Ninja births, zero tracked fresh attacks; six loots|Strongest added-slot tempo/conversion concern under this pilot. Existing tokens/access can still matter.|
| Sakashima's Student |22 deployment games from 33 exposures; repeated forms corrected|Flexible copy/ninjutsu value exists, but engine-copy selection was sparse. Resource tracking undercounts opponent-copy abilities. Cadence replacement not validated.|
| Goldspan Dragon, removed |31 deployment games, 66 Treasures, 16 continuation games|Highest-priority restoration **test**: it fits engine-role compression rather than abandoning it.|
| Fallen Shinobi, removed |33 deployment games; control fallback example used it|Access-cheated action/resource conversion plus threat; stolen-spell value undercounted. Test separately if fallback resilience matters.|
| Purphoros, removed |Material in 19 control threat paths; fallback and pre-blocker finish documented|Real immediate conversion value. Test a small delivery module only if that bottleneck persists—not a generic package restoration.|
| Karlach / Port Razer / Assault, removed |Material in 8/4/3 strong paths respectively, with overlap|Compounding acceleration can be engine work. Port Razer had 8 prolonged unconverted exposures out of 32; do not restore the whole suite blindly.|
| Dragon Tempest / Roaming Throne, removed |One/two material threat paths respectively|Some contribution observed; low/conditional attribution prevents claiming necessity or permanent dispensability.|
| War Cadence, removed |Few activations, real plausible blocker states, one documented unnecessary expensive turn|Dedicated one-slot test, not an automatic verdict.|

Other watch-list observations:Enduring Curiosity had 10 prolonged unconverted exposures out of 31 despite 146 attributed net cards once operating; Dauthi Trapper had one logged action despite 21 deployment games in each arm; Satoru Umezawa had only six experimental logged actions. These warrant sequencing/pilot review. Held protection is often deliberately unused. **“Unconverted hand exposure” is not a dead-card rate**, and action counts can include triggers rather than profitable activations.

Krenko also deserves an architecture check: its own fresh, hasted attack can ignite GGS, but its newly spawned Goblins do not attack in that same combat. The experimental factory tracker observed no fresh Goblin-token attacks from Krenko, versus two such events in the control. Cutting extra combats removes one conversion route for those new bodies; that does not make every Krenko draw dead, but factory presence alone overstates its immediate ammunition contribution.

### Recommended next architecture—not implemented

1. Retain the proven draw/Treasure/reload core. The experiment does not support abandoning the five pillars.
2. Test **Goldspan in / Kaito out** as a single-slot revision first: immediate evasive fresh action and mana versus the observed slow-token conversion. This is a proposed controlled test, not a claimed optimal list.
3. Independently test **War Cadence versus Student**, holding every other slot constant and reviewing both fresh ignition and existing-Dragon finishing access. Do not conflate it with the Goldspan revision.
4. Improve future pilot sequencing:avoid unnecessary commander attacks when another fresh creature can trigger GGS; assign cheap access to the fresh trigger body; reserve protection when legal; test haste use for Kaito-created ammunition. Do not retroactively substitute better-play outcomes into this experiment.
5. If throughput/Dragon survival still fails, compare broader board preservation against a **small immediate-conversion module** such as a single existing payoff candidate. Diagnose before adding slots. Commander-only protection is not a complete Dragon-army protection plan.

Both tested 100-card lists remain frozen. No tuned v3 list has been silently installed.

## 12. Representative actual games

The accompanying bundle includes complete canonical transcripts for these examples and their per-game data. Turns below are the GGS deck's own turns, not global pod turns.

| Game identity | Observed sequence | What it shows |
|---|---|---|
| Truly 202610208, r3 |GGS/first Dragon 3; second 4; strong 5; Dragon pressure 6; win 8; five Dragons. Orochi/Prosperous returned Treasure. Commander died 6 with a pending Dragon; reentered 7 and produced again 7.|Natural payoff can snowball and restart. Pending creation is not itself recovery.|
| Truly 202610212, r3 |GGS 3; first/second Dragons 6; strong 6; whole-board pressure 7; Dragon pressure 8; win 12; seven Dragons, 160 cumulative Dragon combat damage.|Natural Dragon production has ample demonstrated damage capacity; the total includes a long fight/life gain, not 160 simultaneous power.|
| Pure 202610204, r3 |GGS 3; Dragons 4/5; strong/pressure 6; win 15; 11 Dragons. Draw/Treasure contributions included Goldspan and the shared engine.|Control succeeds through compressed engine work as well as payoff.|
| Truly 202610216, r0 |Uninterrupted GGS; five Dragons on turns 5–8; three were exiled/destroyed by Unmaking, Etrata, Mortify; Dragon damage 10 on 7 and 5 on 8; loss 8.|Strongest reviewed challenge to delayed Dragon accumulation:board attrition/delivery, not commander downtime. Protection versus faster conversion is unresolved.|
| Pure 202610202, r2 |GGS operational; Dragons 5/8/9/10; Royal Assassin and Shellshock removed Dragons; hand 5/7/5 at combats 8–10; Ramses alternate win ended the game.|A payoff package also fails against attrition/production gaps. Not card exhaustion or clean insufficient-power proof.|
| Pure 202610222, r0 |GGS 4; Dragons 5/6/8; Dragon damage helped eliminate Destyn; then Combustion Man's15-damage attack trigger plus attackers killed Pure.|Threat threshold misses a real elimination; opponent burst/race and access allocation coexist with delivery latency.|
| Truly 202610202, r2 |Mortify 3, reentry 6; first Dragon 9; later wipes; two Dragons eliminated Gabe on 13; GGS attacked into death and was recast; no fresh-ready body at own combat beginnings 13–18.|Early disruption followed by terminal ammunition failure. More protection slots do not ensure the right late-game reload.|
| Truly 202610210, r1 |Repeated blocked Lagomos tokens 7–10; redeployments consumed early budgets; Student copied Thief 5 and returned as Eagles 7; first Dragon 13; loss 16.|Access deficit plus competing mana and copy/pilot choices; Cadence counterfactual remains plausible, not proven.|
| Truly 202610211, r3 |Own March phased GGS through Game Over on 9; GGS returned and produced a Dragon 10; later disruptions still occurred.|Actual successful protection must not be mislabeled as commander removal.|
| Pure 202610208, r3 |First commander cast 11; zero GGS Dragons; win 12. Shinobi, Goldspan and Purphoros contributed.|A genuine control fallback victory; post-ignition pressure metrics miss it.|
| Pure 202610219, r1 |CadenceX=5 andX=1 on 17; Purphoros/token attack triggers killed the last opponent before blockers.|Expensive access can consume tempo without supplying the decisive payoff in that observed state.|

## 13. Confidence, limitations and error cleanup

High confidence:the 256 completed identities, 128/arm, deck/runtime hashes, recorded winners, canonical life reconciliation and GGS Dragon births. Every final game has no measured creation gaps and 100% life-snapshot reconciliation. The exporter rejects incomplete samples, duplicate identities, unsaved evidence and mixed measurement-source versions.

Moderate confidence:relative pressure/snowball direction **within this fixed pilot/pod**. The threatening-state decline is the strongest statistical warning, but the small cap, unadjusted multiple outcomes and AI limitations preclude a universal deck ranking. Conditional timing and disruption strata differ between arms.

Low confidence:individual changed-card causal effects, precise mana opportunity cost, War Cadence counterfactual wins, fully legal protection availability, and a universal yes/no verdict on payoff packages. No alternate-line replay or single-card ablation was performed. Token-factory/source whitelists and priority snapshots can miss copied/compound effects. Kaito looting is separately counted; Student resource attribution is incomplete for opponent-copy abilities.

The pressure proxy misses distributed damage, lower-life eliminations, pre-ignition fallback pressure and some noncombat paths. The Strong proxy is not proof of a healthy self-feeding engine. The power-review queue is intentionally independent of it. Zero confirmed POWER diagnoses cannot be used as proof of sufficiency.

Errors corrected/preserved:

- Temporary-workspace losses were recovered from 60 independently verified evidence archives; the 12 remaining identities were collected once in an isolated final run. New archives 61–63 were saved and byte-for-byte verified. The 16 gate games remain excluded.
- Earlier overlapping unsaved collector output remains quarantined/excluded regardless of outcome. Its diagnostic bundle is preserved. Saved games were not rerun. No deterministic agreement with unavailable/contaminated trajectories is claimed.
- Exclusive collector locking was tested against a duplicate start. Final-analysis locking was also tested and rejected duplicate derived writes. The focused controller now has its own guard.
- Activated access text/readiness interpretations were corrected uniformly; complete compressed audits take precedence over redundant raw prefixes.
- Student original identity/repeated copy forms were corrected. A misleading Reanimate zero-life resolution description was not treated as a rules error:the canonical life event actually recorded 40→36.
- Pending-trigger Dragons were separated from actual post-reentry restart. Protective phasing was separated from removal. Canonical target lists supplement generic stack descriptions; exile effects and commander destinations are distinguished.
- Kaito's factory/access roles and draw-discard selection were included. All 256 games were re-extracted uniformly; earlier derived exports were superseded, not extra samples. Primary comparison outcomes were unchanged by this role correction.
- Conservative mana screens now account for Goldspan's two-mana Treasure modifier while it is active, including when tapped. Normal, active and phased modifier fixtures passed. Floating mana, exact spending and legal colors remain uncertain; the modifier fix did not change primary performance outcomes.
- Final source hashes accompany the summary and every game. Raw archived evidence remains immutable; older archived derived metrics are not the authoritative final analysis.

**Bottom line:** GGS's Dragons are a viable payoff source. The evidence does not validate Truly Pure v2 as an equally threatening, more resilient implementation of that idea. Preserve the five-pillar architecture, restore/test lost role-compressed acceleration, improve access/protection execution, and distinguish Dragon-board survival from commander survival. Only then test whether a small conversion slot is actually needed.

## Deliverables and reproducibility

The companion ZIP contains this report, the 256-game JSON, summary, protocol, archive member-hash index, all 31 compact payoff-candidate traces, final card/War audit data, selected complete canonical transcripts, the two frozen decks, and final analysis-source hashes. Source code is maintained in the public repository. The 63 evidence archives contain original audits and canonical records; the index maps every production identity to its archive.

Reproduction source:public repository `p94dzz89zm-prog/ggs-forge-lab`, branch `experiment/truly-pure-v2-comparison`. The protocol pins deck hashes, engine SHA 256, resources, seed schedule, rotations, mulligans, budgets and thresholds. Recompute via `compare.py`; export via `export_results.py`. Do not interpret archived intermediate metrics as the corrected final dataset.
