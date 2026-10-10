# Execution interruption at244 verified production games

The frozen comparison remains incomplete. Last observed collector progress was245 completed production games;244 had verified saved receipts through Evidence Part060. Execution transport then disconnected during read-only monitoring. An attempted diagnostic pwd could not complete and its waiting cell was terminated; no stop instruction was sent to the collector. Its present state is unknown. Do not claim further progress, a running background worker, or a final deck verdict.

Trusted durable production: stages032,064,096 have64 games each; stage128 has52 saved completed games. Validation gate16 is excluded. The planned total remains256,128 per arm. Twelve identities remain beyond the trusted saved set; one of those had a reported completion without a verified save at disconnection. Recover all saved manifests, verify each archive against its own member hashes and full gzip footer, and rebuild stage rows by unique keys. Verify any later archive before counting it. Check live collectors and the exclusive collector lock before starting another; do not assume the old collector stopped or continued.

The exact executable, resources, decks, pilot, opponents, seed/rotation schedule, timeouts and thresholds remain frozen. The isolated run had no further reported invalid engine/measurement outcomes. The previously documented overlapping output remains quarantined and excluded regardless of outcome. Its diagnostic bundle was saved successfully as DragonMind_Collector_Overlap_Diagnostic_2026-10-10.tar.gz. run.py's exclusive lock was tested: the second collector was rejected before writes.

The focused controller was to finish stage128, checkpoint, and uniformly run compare.py across all four production stages into comparison-128.json. That final analysis has not been confirmed. Do not export an interim sample as the final256-game result. export_results.py enforces256 unique identities,32 paired seed blocks,128 per arm and saved evidence coverage. The final13-point report and evidence-based slot audit remain outstanding; neither deck has been tuned.

## Additional reviewed evidence to preserve

Pure_GGS, seed202610202,r2: GGS remained operational without a logged commander disruption or wipe. Four Dragons were created on own turns5,8,9,10; observed Dragon combat damage was5 on turns6 and9. Royal Assassin destroyed Dragon411 after its attack and Dragon437 at global36. Shellshock dealt5 to Dragon451 and destroyed it at global38. Own combat-end surviving Dragon counts on turns8,9,10 were1,2,1; hand counts5,7,5. Jaymie then eliminated Destyn and won through Ramses, Assassin Lord at global40. This is observed Dragon-board attrition with production gaps, not established card exhaustion or commander downtime. Payoff delivery versus broader protection/removal/throughput remains causally unresolved. No alternate-line replay was performed. This control case itself contains the payoff package and cannot isolate the experimental changes.

The published manual-review.json also retains the uninterrupted-commander control case202610222,r0, where Dragons contributed to eliminating Destyn before Pure lost to Combustion Man and other attackers, and experimental202610216,r0, where five Dragons were produced but targeted exile/removal suppressed their board. These remain meaningful payoff-falsification candidates. Do not dismiss them automatically as commander protection failure or infer that zero automated POWER labels proves sufficiency.

## Latest balanced interim result —96 games per arm

| Observed outcome | Pure control | Truly Pure v2 |
|---|---:|---:|
| GGS ignition |72/96|73/96|
| Basic snowball |38/96|39/96|
| Strong snowball |43/96|36/96|
| Whole-board pressure after ignition |38/96|31/96|
| Strict GGS-Dragon pressure |14/96|14/96|
| Simulated wins |18/96|15/96|

Experimental-minus-control whole-board pressure was−7.29 percentage points, paired seed-block bootstrap95% interval[−15.63,+1.04]. The predeclared10-point material decline is not excluded. Ignition+1.04[−8.33,+10.42]; strong snowball−7.29[−17.71,+3.13]; strict Dragon pressure0[−10.42,+10.42]; wins−3.13[−11.46,+5.21]. These are interim estimates under the pinned AI environment, not real-pod win predictions or final hypothesis conclusions. Natural Dragon production can contribute to wins and eliminations; the strong no-payoff-package architecture claim remains unvalidated.
