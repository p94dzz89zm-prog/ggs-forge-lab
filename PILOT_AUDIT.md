# Forge pilot inspection

Inspected the official Forge 2.0.15 release source at commit `4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676`, dated September 28, 2026, and the 84 saved attempts (64 completed). No new games or AI modifications were made. Eight relevant release card scripts exactly match the SHA-256 hashes recorded from the installed engine. This does not independently verify the compiled AI classes; their release source and matching timeout stack locations are the available evidence.

## Concrete findings

| Area | Release-source behavior | Implication for GGS testing |
|---|---|---|
| Ninjutsu eligibility | Requires some unblocked attacker with strictly lower mana value than the incoming creature; refuses after the combat-damage phase | Can reject valuable equal-value swaps and end-of-combat activations. This is an AI restriction, not a Magic rule. It does not reject every ninjutsu activation: the saved Higure example succeeded. |
| Ninjutsu bounce selection | Generic return-cost selection sorts eligible creatures by power ascending | Low power is a crude proxy for what should be returned. Token value, combat-damage abilities and replay value can matter more. No particular bad bounce was proved from the logs. |
| War Cadence | Sets X to half estimated available mana; examines the strongest opponent; activation depends on estimated lethal damage or attackers outnumbering blockers | Does not explicitly value a single nonlethal connection producing a GGS Dragon. Actual defender mana and distributed attacks deserve better treatment. It is not wholly unsupported. |
| Creature-type choices | Uses weighted type prominence across owned cards, with hand/commander weighting and token information | Generic rather than tailored to Adaptation/Higure or Discovery/Dragon engines. It may still select an appropriate type. Previous wording suggesting simple printed-type counting was incomplete. |
| Breath of Fury | Card script explicitly contains `AI:RemoveDeck:All`; aura attachment uses generic Pump logic | A clear warning against treating stock AI performance as a reliable test of this engine. The marker is an AI deck-selection hint, not proof the rules engine cannot resolve it or that forced inclusion automatically prevents casting. |
| Aggravated Assault | UntapAll AI can activate after combat when a relevant controlled creature is tapped | Extra combats are not universally unsupported. This does not establish recognition of mana-positive Sword/Treasure loops or optimal sequencing. |
| GGS haste | Uses generic haste/pump evaluation and predicted attacks | There is existing haste support, but no explicit GGS Dragon-trigger bonus in the inspected haste branch. Timeout stacks pass through this expensive combat-prediction path; they do not identify the exact ability being evaluated. |

## Saved-game observations

Counts are games with an event placed on the stack, across 64 completed games spanning all variants. Not every version contains every card. Casts can be countered, permanents can be removed, and activation counts cannot identify how many good opportunities were missed.

| Card | Games with cast event | Games with activation event | Games with trigger event |
|---|---:|---:|---:|
| Goro-Goro and Satoru | 63 | 12 | 34 |
| War Cadence | 7 | 1 | 0 |
| Aggravated Assault | 9 | 4 | 0 |
| Breath of Fury | 0 | 0 | 0 |
| Higure, the Still Wind | 0 | 1 | 1 |
| Port Razer | 7 | 0 | 2 |

Higure's activation includes entering through ninjutsu and later making himself unblockable. His tutor trigger resolved in `results/logs/GGS_Four_card_package__seat3__seed20260930.log`. Port Razer resolved consecutive extra-combat triggers against different opponents in `followup/logs/GGS_Current__seat0__seed20261030.log`. These are positive examples of supported play patterns.

## Instrumentation gaps

The existing logs omit chosen creature types, declined-action reasons, full hands and complete decision-state snapshots. Therefore they cannot prove wrong type choices, missed protection opportunities or superior alternative plays in each position. Hidden information must be withheld from any improved pilot even if recorded privately for auditing.

The runner did not pass explicit `-a` AI profiles. The release simulation CLI supports per-seat profiles, but an unspecified profile inherits installed user preferences. The previous run did not record those preferences, so profile identity cannot now be reconstructed from its command alone. Pin profiles and hash their files in future runs. A profile change alone does not remove the hard-coded ninjutsu restriction.

## Before the large comparison

1. Record chosen types, active profile, legal candidate actions, selected action, rejected-action reasons and the pilot's information set.
2. Use actual engine positions to verify equal-mana-value ninjutsu, a War Cadence connection that produces a Dragon without lethal damage, Higure/Adaptation type choice, GGS haste, and multi-combat sequencing. These are proposed tests, not tests already executed.
3. Change only AI evaluation and choices; preserve game rules. Compare the original and modified pilots on the same predefined positions before comparing deck swaps.
4. Treat Breath of Fury as unvalidated for autonomous piloting until its sacrifice/reattach/haste loop passes an engine-backed position test.
5. Apply generic improvements fairly to opponents, document any GGS-specific choices, and keep original-pilot results separate. Do not train on which swap we hope will win.

Conclusion: there are concrete reasons stock Forge can mismeasure this deck. Existing results remain valid records of that pilot's games; they do not settle optimal human deck tuning. The pilot has not yet been improved or validated.

## Official source references

- [Ninjutsu eligibility](https://github.com/Card-Forge/forge/blob/4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676/forge-ai/src/main/java/forge/ai/ability/ChangeZoneAi.java)
- [Return costs and type choice](https://github.com/Card-Forge/forge/blob/4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676/forge-ai/src/main/java/forge/ai/ComputerUtil.java)
- [War Cadence evaluation](https://github.com/Card-Forge/forge/blob/4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676/forge-ai/src/main/java/forge/ai/ability/EffectAi.java)
- [Breath of Fury script](https://github.com/Card-Forge/forge/blob/4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676/forge-gui/res/cardsfolder/b/breath_of_fury.txt)
- [Untap/extra-combat evaluation](https://github.com/Card-Forge/forge/blob/4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676/forge-ai/src/main/java/forge/ai/ability/UntapAllAi.java)
- [Profile inheritance](https://github.com/Card-Forge/forge/blob/4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676/forge-gui/src/main/java/forge/player/GamePlayerUtil.java)
- [Reproducible exposure counts and script hashes](evidence/pilot_audit.json)
