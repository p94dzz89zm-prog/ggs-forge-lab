# Whip cast-and-activate mana reservation

The stock pilot chooses Whip with four Swamps and four other basic lands,
then taps all four black sources while casting it. Its next recovery ability
becomes unpayable despite a legal eight-mana cast/return sequence. Reserving
two Swamps through Forge's existing one-spell memory fixes that execution.

`GgsWhipManaPolicy` wraps only a stock-selected Whip cast. In a masked game
copy it reserves the same two untapped ordinary Swamps, actually casts Whip,
clears the one-spell reservation as the normal next decision does, and actually
pays and resolves a legal creature return. Only successful projected execution
within a cooperative one-second deadline installs those reservations in live
AI memory. It does not choose Whip, alter costs/card rules, or make a deck swap.
No opponent hand or future draw is used to choose the reservation. Unsupported
positions fall back. Existing one-spell reservations are preserved.

Candidate66c1dba5dde1f2b85fbd59d07c114d727fd87347b0b3b07593c166fdece77744
is built by `build_whip_mana.py` over verified mixed-mana Kaito base1c191.
All unrelated JAR entries remain byte-identical. It retains previous combined
lethal, protection, Student and Kaito corrections. The adopted incumbent is
not automatically replaced.

Development reproduces the stock-selected cast and failed payment; manual
reservation and the automatic candidate complete the real return. Before any
fresh test, the source/JAR and `WhipManaFreshEvaluation` were frozen. Three new
creatures and land mixes verify actual stock cast, preserved live state,
reservation cleanup, real next-controller return, eight mana consumed, haste,
attack damage and lifelink. Three controls verify no reservation for missing
graveyard target, seven total mana, or only two black sources. The prior build
completes zero of the three recovery lines; the candidate completes all three.
These are correlated constructed mechanisms, not natural-game strength data.

Open scope: nonbasic-only reservation, floating mana/general multi-spell color
planning, mana-ability opportunity costs, and full Whip deployment/recovery
strategy. An empty-board stock pass remains unchanged. The first payable
projected graveyard target is a feasibility witness, not a target ranking.
The actual subsequent stock controller still chooses the return target.
Full-game admission and independent strength evaluation remain required.
