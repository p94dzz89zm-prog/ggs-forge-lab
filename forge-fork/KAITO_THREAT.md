# Kaito public equipment-threat correction

The stock controller preferred Kaito's surveil/draw before a visible
Regalia/Sword attack could be made lethal. The reduced development regression
uses six life and base-power Combustion Man, rather than the original game's
seven life and buffed body. Paying the minus-two loyalty cost first taps the
attacker and adds two stun counters, preventing that attack. Both equipment
activations, their payments and subsequent combat are executed in the fixture.

The controller guard only changes a selected Kaito surveil in the GGS pilot's
MAIN2. It requires a targetable, untapped, ready creature, both visible and
unattached equipment cards, enough ordinary untapped Swamps to cover their
combined printed equip costs, and power sufficient to reach the pilot's life.
It checks the actual equip abilities' targeting restrictions. Protection from
artifacts disproved the first candidate's forecast; that counterexample is a
permanent regression, with a separate protected creature in fresh evaluation.

The guard deliberately has a narrow mana certificate. The original mixed-mana
historical board remains outside it. Other mana sources, modified equip costs,
broader attack restrictions, triggered damage/life changes and hidden responses
are not a general future-combat solution. This corrects demonstrated reduced
decisions, not every lethal board or the entire historical game. No card rule
was changed.

`build_kaito_threat.py` requires the exact Student-corrected base hash and
overlays only the controller entry point and new policy classes. It preserves
the combined-lethal correction and prior engine behavior. Set
`dragonmind.disableKaitoThreatPolicy=true` for an ablation. The new policy is
not a model-learning update or general strength certification.

`KaitoThreatReviewRegression` reproduces the first mechanism with actual
payments. `KaitoThreatEvaluation` has explicit initial, targetability,
artifact-targetability and separate fresh modes. The final fresh set uses
Glorybringer, Bloodbraid Marauder and Thraximundar for three lethal conditions,
plus protected/nonlethal/insufficient-payment/tapped/no-Sword controls. Different
profiles or repeated runs are not independent natural games. Full-game
admission and held-out deck-strength evaluation remain separate requirements.
