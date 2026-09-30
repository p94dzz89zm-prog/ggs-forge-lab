# Measured game outcomes

Counts only; no inferred human win rates. Completed games exclude runtime errors and timeouts. Missing games are not losses. Four exploratory games per variant cannot distinguish small improvements.

| Version | Attempts | Completed | GGS wins in completed games | Timeouts | Engine errors | Other incomplete |
|---|---:|---:|---:|---:|---:|---:|
| GGS_Current | 4 | 3 | 1 | 0 | 1 | 0 |
| GGS_Higure_only | 4 | 3 | 1 | 1 | 0 | 0 |
| GGS_Orochi_only | 4 | 4 | 1 | 0 | 0 | 0 |
| GGS_Throne_only | 4 | 3 | 0 | 0 | 1 | 0 |

## Commander usage in completed games

These are cast attempts and triggered abilities put on the stack. They do not prove every spell or trigger resolved. Repeated casting is evidence that recasting happened; it does not measure complete board-wipe recovery.

| Version | Commander cast attempts per completed game | GGS trigger stack entries across completed games |
|---|---|---:|
| GGS_Current | 3, 3, 1 | 2 |
| GGS_Higure_only | 3, 1, 4 | 5 |
| GGS_Orochi_only | 3, 3, 5, 1 | 5 |
| GGS_Throne_only | 3, 1, 1 | 5 |

True completed draws, if any, have status `completed_draw` in the audited JSON and are included in the completed column. Individual audited records and original full logs are included. The three-player infrastructure smoke test is excluded. The separate invalid four-player timeout smoke test is also excluded.
