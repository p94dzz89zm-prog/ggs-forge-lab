# Recorded commander cast cost contributions

Stage51 independently derives prior command-zone casts from completed cast
announcements and their matching selected executions. It initializes commander
identities from the game-start command zone, checks each recorded pre-execution
zone against the ability's origin, and never reads cached commander-cast counts.
Separate cards and players have separate counters; casting from hand adds no tax
and does not increment command-zone casts.

The preserved house-rule natural history contains ten commander spell casts:
nine from Command and one Goro-Goro and Satoru cast from Hand. Three command-zone
recasts contribute two generic mana each: Ezio on turn24, Frodo on turn37, and
GGS on turn39. All ten locked costs equal their captured plain printed costs
plus these independently counted contributions. The three other Stage50 cost
differences still require independent reduction derivations: Blasphemous Act,
Excalibur, Sword of Eden, and Vanquish the Horde.

The audit checks arithmetic against captured costs and origins. It does not
prove Oracle characteristics, origin-zone entitlement, every cost modifier,
continuous-effect history, casting timing or complete-game legality. Its output
always keeps rules approval, complete-game approval and training admission false.
The complete source tape and immutable receipt remain private. Full-tape and
reduced-input results, mutation outcomes, source version and input hashes belong
to the private checkpoint; no raw history or decklist is published here.

Reference: Wizards' Comprehensive Rules effective September25,2026,
[903.8, 702.124d and 601.2f](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt),
linked from the [official rules page](https://magic.wizards.com/en/rules).
Commander tax applies to command-zone casts per card and player; total-cost
derivation also requires independently establishing all applicable modifiers.

Reproduce with `python3 commander_cast_audit.py PRIVATE/referee-events.jsonl`
and `python3 -m unittest test_commander_cast_audit`. A passing scoped audit must
never be promoted to complete-game certification.
