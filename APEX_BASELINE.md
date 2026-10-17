# Apex War-Form baseline, 2026-10-17 v1

`baselines/apex_20261017_v1.txt` is the exact 100-card list supplied by the user
on October 17. It starts with Goro-Goro and Satoru and ends with Xander's Lounge.
`CURRENT_MAINBOARD.txt`, `decks/GGS_Current.dck` and the explicit dated baseline
now use that list. The prior defaults are retained byte-for-byte in
`baselines/pre_apex_20261017_legacy.txt` and
`baselines/GGS_Current_pre_apex_20261017.dck`. Historical evidence keeps its
original deck hashes; it is not relabeled as this baseline.

The material difference is Baleful Strix replacing the earlier reference's
Draconic Visitor. Faerie Seer is explicitly absent. Mistblade Shinobi is
physically present but absent from the supplied reference: the displaced card
has not been identified. Physical lands have not been checked card for card.
Neither discrepancy authorizes inventing a cut or adding a 101st card.

The static research workflow joins a verified Oracle snapshot and separately
verified rulings into a new, closed SQLite database. `apex_static_audit.py`
validates names, quantities, singleton and snapshot legality/color identity;
it generates an Oracle-linked first-pass functional model for every listed
card and retrieval tags across every snapshot-eligible Grixis card. Pattern
matches and provisional role classes are discovery aids, not performance
rankings or interaction certifications. Individual land slots provide core
mana infrastructure without making each particular land name indispensable.

The explicit Whip experiment changes only Breath of Fury to Whip of Erebos.
That is a hypothesis trading combat-chain ceiling for lifegain and recursion,
not a recommended/proven upgrade. Same-seed outcomes alone do not establish
that the substituted card caused a difference. Full-game evidence admission
and private all-seat review remain required.
