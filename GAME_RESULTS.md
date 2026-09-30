# Game results

84 attempted games recorded. Status counts: 64 completed, 4 engine_error, 16 timeout.

True completed draws, if any, are included in the completed column with no winner. Actual four-player Commander games in Forge. Jaymie uses the supplied main deck; Gabe and Destyn use stock proxy lists. These are Forge AI outcomes, not estimates of the human pod’s win rates. Completed-game outcomes exclude every logged exception, timeout, nonzero exit and ambiguous or incomplete outcome. Exclusion can bias the sample.

| Version | Recorded attempts | Completed | GGS wins in completed games | Timeouts | Engine errors | Other incomplete |
|---|---:|---:|---:|---:|---:|---:|
| GGS_Current | 8 | 7 | 1 | 0 | 1 | 0 |
| GGS_Orochi_only | 8 | 8 | 3 | 0 | 0 | 0 |
| GGS_Throne_only | 8 | 5 | 0 | 2 | 1 | 0 |
| GGS_Two_card_trial | 4 | 2 | 0 | 2 | 0 | 0 |
| GGS_Higure_only | 8 | 6 | 1 | 2 | 0 | 0 |
| GGS_Higure_Adaptation | 4 | 2 | 0 | 2 | 0 | 0 |
| GGS_Four_card_package | 4 | 4 | 0 | 0 | 0 | 0 |
| GGS_Naga_diagnostic | 4 | 3 | 1 | 1 | 0 | 0 |
| GGS_Biting_Palm_diagnostic | 4 | 4 | 2 | 0 | 0 | 0 |
| GGS_Cover_diagnostic | 4 | 3 | 1 | 1 | 0 | 0 |
| GGS_Herald_diagnostic | 4 | 3 | 0 | 1 | 0 | 0 |
| GGS_Reality_Shift_diagnostic | 4 | 3 | 0 | 0 | 1 | 0 |
| GGS_Mission_diagnostic | 4 | 2 | 2 | 2 | 0 | 0 |
| GGS_Oni_diagnostic | 4 | 4 | 2 | 0 | 0 | 0 |
| GGS_Slitter_diagnostic | 4 | 3 | 1 | 1 | 0 | 0 |
| GGS_Cruise_diagnostic | 4 | 3 | 1 | 1 | 0 | 0 |
| GGS_Ink_Eyes_diagnostic | 4 | 2 | 0 | 1 | 1 | 0 |

## Candidate exposure

Games with a GGS cast attempt or activation of each candidate, among completed games of a version containing it. This does not prove resolution or usefulness. A candidate with no observed use is untested in practical play by this sample, even if its deck version won.

| Candidate | Completed games with cast/activation | Trigger stack entries |
|---|---:|---:|
| Arcane Adaptation | 0 | 0 |
| Biting-Palm Ninja | 0 | 0 |
| Cover of Darkness | 0 | 0 |
| Determined Iteration | 9 | 57 |
| Goldspan Dragon | 6 | 16 |
| Higure, the Still Wind | 1 | 1 |
| Ink-Eyes, Servant of Oni | 0 | 0 |
| Mist-Cloaked Herald | 0 | 0 |
| Mist-Syndicate Naga | 0 | 0 |
| Orochi Soul-Reaver | 3 | 3 |
| Reality Shift | 1 | 0 |
| Reconnaissance Mission | 1 | 29 |
| Roaming Throne | 1 | 0 |
| Silent-Blade Oni | 1 | 1 |
| Throat Slitter | 0 | 0 |
| Treasure Cruise | 0 | 0 |

Four exploratory games per version in the first batch; four more games with a fresh seed for Current, Orochi, Throne and Higure in the follow-up. Seat rotations are not independent seeds. These samples cannot reliably rank close card choices.

Forge’s type-choice scripts for Arcane Adaptation, Kindred Discovery, Cover of Darkness and Roaming Throne prefer the most prominent creature type in the deck. The runner does not override these choices. Consequently the Higure/Adaptation games do not guarantee that the AI named Ninja, and Discovery games do not guarantee that it named Dragon. That limits comparison with intended human play.

Keep the supplied main list as the baseline. The logs have not established that cutting Goldspan Dragon or Determined Iteration improves it. Higure is a legitimate potential trial without Adaptation, but no mainboard change is prescribed by these automated counts.

Original logs, commands, seeds and classifications are included in both run directories. Invalid output is retained, never hidden or converted into a loss.
