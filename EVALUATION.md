# GGS deck evaluation

The supplied current 100-card list is the baseline. **No experimental swap in this package is an instruction to edit the main deck.** Draconic Visitor and Kindred Discovery are already in that supplied list; do not add a second copy. Mistblade Shinobi is already absent.

## Direction

Keep the deck centered on fresh creatures connecting in combat, then using Dragons, tokens and extra combats to close the game. There is no reason to make Humans and Dragons equal in number. Humans and Ninjas supply the attackers and value engines; Dragons are the payoff. Creature types should support useful effects, rather than dictate an arbitrary quota.

This is a synergy deck with several overlapping routes. It should contain independent mana, interaction and card advantage so it can continue without GGS. It cannot make every draw equally useful in every board state: extra-combat enchantments need attackers, token doublers need tokens, and protection needs something worth protecting.

The baseline contains **nine creatures printed with the Ninja type plus Changeling Outcast, which is also a Ninja**, for ten Ninja creature cards. Kaito is additional Ninja support and becomes a Ninja creature during your turn; he is a planeswalker card in the library. GGS itself is a Goblin Human, not a Ninja. The deck has six mana rocks, 31 dedicated lands and three land-capable MDFCs, for 34 possible land cards. A previous count of seven mana rocks was incorrect.

## What the disputed cards contribute

| Card | Function | What it depends on | Assessment before trustworthy game evidence |
|---|---|---|---|
| Goldspan Dragon | Hasty evasive threat; produces Treasures and increases their mana | Its own attacks already make Treasure | Important independent threat and mana recovery piece. Its removal is a real cost, not a free upgrade. |
| Determined Iteration | Creates a hasty copy of an existing creature token every combat | Existing creature token | Cheap direct GGS support and extra-combat payoff. Empty-board draw is weak. Temporary copies are sacrificed at the next end step. |
| Orochi Soul-Reaver | Ninjutsu attacker; turns creature connections into Treasure and manifest value | Creatures connecting, including tokens | Fits Ninja identity and can generate value without GGS. Visitor replaces newly created Treasures, so it also changes the mana benefit. |
| Roaming Throne | Doubles triggered abilities of other creatures of a chosen type | A relevant creature trigger | Human supports GGS and several engines. It does not double Draconic Visitor's replacement effect or Kindred Discovery's enchantment ability. It is a four-mana support card, not automatically superior to Iteration. |
| Higure, the Still Wind | Tutors Ninjas on combat damage; pays to make a Ninja unblockable | First connection for tutor, mana for evasion | Legitimate fit with ten baseline Ninja creature cards. He can find Changeling Outcast. Test him alone before adding a type-changing enchantment. |
| Arcane Adaptation | Broadens creature types in battlefield, hand and library | A payoff for the chosen type | Naming Ninja expands Higure's creature tutoring and targets. It does not grant ninjutsu. It consumes a slot and mana without producing a creature or card on its own. |
| Draconic Visitor | Converts new artifact tokens into Dragons | Artifact-token creation | A second payoff route without GGS, not a complete independent engine. It replaces new Treasures and forfeits their mana/sacrifice use. Existing Treasures stay Treasures. |

The comparison versions isolate Orochi, Throne and Higure before testing packages. The larger package is a stress test of how much setup the deck can tolerate. Its existence is not a recommendation to remove four good cards.

## Recovery and interpretation

Count completed games separately from crashes and timeouts. Check logs for commander recasts, small-creature deployment, draw engines, mana use and whether candidate cards actually entered play. A win in a variant does not prove the swapped-in card caused it; sometimes the candidate is never cast. Countered casts and abilities placed on the stack do not prove successful resolution.

Forge's AI is expressly weak with many combo decks. This deck has intricate timing and overlapping replacement/trigger effects, so automated outcomes alone cannot settle optimal human play. The current run uses Jaymie's supplied main deck and stock proxies for the other two decks, not verified exact upgraded pod lists. These are honest engine games, but calling them measured win rates against your actual human pod would overstate what was tested.

Higure can fit without Arcane Adaptation. Goldspan and Iteration remain meaningful baseline pieces. Keep them in the main list unless the logged evidence and practical play experience justify a specific trial. Put experimental alternatives in the maybeboard until that decision is made.

## Evidence

See `GAME_RESULTS.md`, `results/MEASURED_RESULTS.md`, `results/audited_summary.json`, `results/audited_records.json` and original logs. The final audit covers 84 attempted games: 64 completed, 16 game timeouts and 4 AI evaluation errors. There are no remaining scheduled games in this run. Incomplete attempts are excluded, and the detailed tables list their statuses.

## Why the cheaper Ninjas remain useful

Moon-Circuit Hacker provides a one-mana ninjutsu activation and an early card on its first connection. Higure costs four mana to ninjutsu and five to cast, and his tutoring still requires a connection. Ink-Eyes also occupies an expensive payoff slot and needs a useful creature in an opponent's graveyard. Satoru Umezawa can reduce the cost of expensive creatures while he survives, but a resilient list cannot assume he is always available. Cheap enablers and expensive payoff Ninjas perform different jobs.

Higure, Ink-Eyes, Orochi and the other purchased Ninjas are legitimate candidates. Orochi and Higure merited screening alongside the early candidates. The earlier emphasis on cheap enablers does not make the larger Ninjas bad; their cost and the amount of setup they demand need to be considered alongside their ceiling. The deck's philosophy should remain GGS combat value, with Ninja identity where it helps that plan.

## Secondary candidates

| Candidate | What the diagnostic tests | Main concern |
|---|---|---|
| Biting-Palm Ninja | Disruption instead of Prosperous Thief's mana | Cuts ongoing mana production for a limited hand-disruption effect. |
| Silent-Blade Oni | Expensive stolen-spell payoff instead of Fallen Shinobi | Higher native ninjutsu cost; relies more on Satoru for discount. |
| Throat Slitter | Combat-based creature removal instead of Feed the Swarm | Needs a connection and cannot replace Feed's enchantment-removal role. |
| Ink-Eyes | Graveyard theft instead of Balefire's combat cleanup | Strong situational value, but needs a suitable graveyard and mana. |
| Cover of Darkness | Cheap tribal evasion instead of War Cadence | Fear is restricted by black/artifact blockers and only the chosen type benefits. |
| Mist-Cloaked Herald | Cheap unblockability instead of Gingerbrute | Loses Gingerbrute's haste; the two enablers have different timing advantages. |
| Reality Shift | Exile creature removal instead of Chaos Warp | Cannot hit enchantments or other noncreature permanents. |
| Reconnaissance Mission | Broad combat draw instead of Frostcliff Siege | Gives up the alternative haste/combat support mode. |
| Treasure Cruise | Burst draw instead of Grazilaxx | Delve consumes graveyard resources; loses Grazilaxx's ongoing combat draw and bounce protection. |
| Mist-Syndicate Naga | Self-copying Ninja instead of Krenko | Requires its own connection and loses Krenko's attack-based token production; included as a diagnostic, not claimed as owned. |

These are controlled comparisons of named slots, not statements that each pair is interchangeable. A successful creature-removal trial still needs the deck to retain enough enchantment answers.

## Logged examples worth inspecting

- `followup/logs/GGS_Current__seat0__seed20261030.log`: baseline victory with Fallen Shinobi, repeated Port Razer triggers, Moon-Circuit Hacker/Ingenious Infiltrator value, three commander cast attempts, and late Krenko/Purphoros. This illustrates overlapping routes rather than one permanent engine.
- `results/logs/GGS_Four_card_package__seat3__seed20260930.log`: Higure entered through ninjutsu, dealt combat damage, put his tutor trigger on the stack, and later resolved his unblockability activation. The log does not identify the tutored card.
- `results/logs/GGS_Higure_only__seat3__seed20260930.log`: Goldspan was cast and generated repeated triggers. The outgoing card in the Orochi trial had a real role.
- `results/logs/GGS_Biting_Palm_diagnostic__seat0__seed20260930.log`: Determined Iteration generated repeated combat triggers. Trigger counts alone do not prove each populate created a useful token.
- `followup/logs/GGS_Orochi_only__seat2__seed20261030.log`: Orochi entered through its activated ability and generated combat-damage triggers. This shows the intended engine can function, not that replacing Goldspan raises the deck's win rate.

**Mainboard decision: zero additional swaps from the supplied list.** Keep Goldspan and Iteration. The 13 purchased candidates not already in the baseline are listed in `PURCHASED_CANDIDATES.txt` for the maybeboard. Mistblade is already absent from the baseline; Kindred Discovery is already present. The tested diagnostic cuts are not an instruction to make those cuts.
