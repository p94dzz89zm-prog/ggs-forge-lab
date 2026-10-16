# Scoped March lethal-defense correction

A constructed, legally assigned defensive combat exposed an actual targeting
mistake in the combined-lethal engine (SHA-256 a885657a37bbc02604a469f09dcd261e7d004ab996882a80871e2c6962ebb7e1).
At 2 life with Island and Mountain untapped, the GGS pilot used March of
Swirling Mist at X=1 to save a Balefire Dragon blocking Typhoid Rats while a
Centaur Courser was unblocked. Real payment tapped both lands, the Dragon
phased out, and actual combat damage reduced life to -1. Phasing the Courser
was legal, payable, and survived that combat at 2 life.

The correction changes only target ranking in empty-stack defensive combat
when the existing forecast reports serious danger. Unblocked attackers aimed
at the pilot rank by their predicted incoming damage before ordinary creature
value. Other players' attackers, untargetable creatures, color payment, X,
stack resolution and card rules remain governed by the existing engine.

`MarchDefenseRegression` checks 27 constructed decisions across three bounded
profiles, including bigger attackers, combined incoming damage, a threat aimed
at a third player, two-target costs, absent blue mana, shroud, nonurgent
combat and the opt-in boundary. These are constructed cases, not 27 natural
games or independent strength samples. Separate frozen-build fixtures and
pod comparisons remain private evidence.

Use `build_march_defense.py --base <verified combined-lethal jar> --output <new jar>`
to rebuild this overlay. It verifies its exact base, replaces only
FireworkPilotPolicy.class, and writes hashes. The older build_pilot_recovery.py
builds a different historical layer and does not apply this baseline-source
overlay. Preserve the combined-lethal correction underneath it.

This is not a universal defensive solver: blocked trampling damage, poison,
commander damage, damage replacement, first/double strike timing, alternative
life-gain lines and stack-dependent tradeoffs require additional review. No
full-game admission follows from passing these scoped fixtures. Natural-game
counterspell expenditure on cross-opponent removal remains an unresolved
review lead; it is not changed by this fix.
