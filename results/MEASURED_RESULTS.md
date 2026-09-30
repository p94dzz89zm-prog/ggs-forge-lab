# Measured game outcomes

Counts only; no inferred human win rates. Completed games exclude runtime errors and timeouts. Missing games are not losses. Four exploratory games per variant cannot distinguish small improvements.

| Version | Attempts | Completed | GGS wins in completed games | Timeouts | Engine errors | Other incomplete |
|---|---:|---:|---:|---:|---:|---:|
| GGS_Biting_Palm_diagnostic | 4 | 4 | 2 | 0 | 0 | 0 |
| GGS_Cover_diagnostic | 4 | 3 | 1 | 1 | 0 | 0 |
| GGS_Cruise_diagnostic | 4 | 3 | 1 | 1 | 0 | 0 |
| GGS_Current | 4 | 4 | 0 | 0 | 0 | 0 |
| GGS_Four_card_package | 4 | 4 | 0 | 0 | 0 | 0 |
| GGS_Herald_diagnostic | 4 | 3 | 0 | 1 | 0 | 0 |
| GGS_Higure_Adaptation | 4 | 2 | 0 | 2 | 0 | 0 |
| GGS_Higure_only | 4 | 3 | 0 | 1 | 0 | 0 |
| GGS_Ink_Eyes_diagnostic | 4 | 2 | 0 | 1 | 1 | 0 |
| GGS_Mission_diagnostic | 4 | 2 | 2 | 2 | 0 | 0 |
| GGS_Naga_diagnostic | 4 | 3 | 1 | 1 | 0 | 0 |
| GGS_Oni_diagnostic | 4 | 4 | 2 | 0 | 0 | 0 |
| GGS_Orochi_only | 4 | 4 | 2 | 0 | 0 | 0 |
| GGS_Reality_Shift_diagnostic | 4 | 3 | 0 | 0 | 1 | 0 |
| GGS_Slitter_diagnostic | 4 | 3 | 1 | 1 | 0 | 0 |
| GGS_Throne_only | 4 | 2 | 0 | 2 | 0 | 0 |
| GGS_Two_card_trial | 4 | 2 | 0 | 2 | 0 | 0 |

## Commander usage in completed games

These are cast attempts and triggered abilities put on the stack. They do not prove every spell or trigger resolved. Repeated casting is evidence that recasting happened; it does not measure complete board-wipe recovery.

| Version | Commander cast attempts per completed game | GGS trigger stack entries across completed games |
|---|---|---:|
| GGS_Biting_Palm_diagnostic | 2, 4, 1, 3 | 6 |
| GGS_Cover_diagnostic | 2, 2, 2 | 2 |
| GGS_Cruise_diagnostic | 1, 1, 2 | 1 |
| GGS_Current | 2, 2, 4, 1 | 13 |
| GGS_Four_card_package | 2, 2, 3, 2 | 3 |
| GGS_Herald_diagnostic | 2, 2, 3 | 0 |
| GGS_Higure_Adaptation | 1, 1 | 4 |
| GGS_Higure_only | 1, 2, 3 | 5 |
| GGS_Ink_Eyes_diagnostic | 0, 2 | 1 |
| GGS_Mission_diagnostic | 3, 1 | 11 |
| GGS_Naga_diagnostic | 1, 3, 1 | 1 |
| GGS_Oni_diagnostic | 4, 4, 1, 2 | 6 |
| GGS_Orochi_only | 1, 1, 4, 3 | 5 |
| GGS_Reality_Shift_diagnostic | 3, 4, 1 | 6 |
| GGS_Slitter_diagnostic | 1, 1, 1 | 1 |
| GGS_Throne_only | 1, 2 | 0 |
| GGS_Two_card_trial | 1, 1 | 1 |

True completed draws, if any, have status `completed_draw` in the audited JSON and are included in the completed column. Individual audited records and original full logs are included. The three-player infrastructure smoke test is excluded. The separate invalid four-player timeout smoke test is also excluded.
