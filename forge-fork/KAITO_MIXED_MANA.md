# Kaito mixed-mana equipment threat

This experimental policy extends the existing Kaito MAIN2 survival guard. A
saved diagnostic game exposed the pilot choosing Kaito's draw ability before
visible Regalia/Sword made an opposing creature unblockable and lethal. The
old ordinary-untapped-Swamp test missed the actual mixed lands, all tapped in
MAIN2 but available after their owner's next untap.

The guard now uses a masked game copy. It projects land untaps, pays Vorpal
Sword's constrained BB equip first, then the cheapest legal Regalia equip,
and resolves both. Mana is consumed once and actual attachment targeting is
checked. The public attacker must be ready, targetable by Kaito, and able to
attack unblocked for at least the player's life. Kaito's real -2 must be payable.
Other stock decisions are retained. Card rules and the incumbent are unchanged.

The projection uses no opponent hand or future draw. It clears the projected
opponent mana pool rather than carrying present floating mana into a later
turn. Stun and untap restrictions apply to lands. Nonstatic P/T modifications
are conservatively rejected because game copies do not reconstruct scheduled
cleanup callbacks. The deadline is cooperative, one second per projected line;
it cannot interrupt a single engine call. Unsupported runtime cases fall back.

## Checked scope

Candidate SHA256: `1c191916bcf3cb71a9a683571adfb687c86564268846e5b94617a4ac8d48e125`.
Previous experimental comparison: `9670bccd2fb184ad6506b4bff3d09069049a5170ba7786053cd73d523e722831`.
Build over the pinned Student-corrected base with `build_kaito_threat.py`.

`KaitoMixedManaRegression` reproduces critical public features, including the
actual static power boost, mixed tapped lands, legal Kaito payment, two stun
counters, untap consuming one, and the paid equipment/combat consequence. It
is not an exact whole-game replay. Unknown land color choices and unrelated
permanents are omitted. Both cheapest and observed higher Regalia equip modes
are tested. Four negative forecast controls cover black mana, combined mana,
stun-locked lands, and temporary power. Privacy controls vary hidden hands and
check the public forecast, live state and live RNG state.

`KaitoMixedManaFreshEvaluation` was frozen separately before execution. Three
new lethal conditions use Dragonlord Kolaghan, Nicol Bolas the Ravager, and
Doom Whisperer with mixed tapped mana. Four controls cover insufficient black,
insufficient total mana, hexproof and nonlethal damage. The old build lost all
three lethal lines; the candidate paid the Kaito defense and preserved life.
The four controls retained drawing. These are correlated constructed cases,
not independent natural seed clusters or a win-rate estimate.

The first evaluation family became development after its baseline exposed
incorrect generic-first payment sequencing. That failed attempt, the earlier
candidate and fixture compile failures are retained. Its revised seven checks
are not counted as fresh evaluation. No policy change followed the final fresh
evaluation. Earlier Kaito families are regression rechecks, not new evidence.

## Limits and next work

The guard does not solve attached equipment, ward payments, arbitrary pumps,
all attack triggers, prevention/replacement effects, extra combats, intervening
opponent actions or hidden responses. It is a narrow risk detector, not a
certificate of lethal or safety across future turns. Full all-seat episode
review remains required for learning admission. No natural game was played in
this cycle, no settings were promoted, and historical model data did not change.

`WhipRecoveryDecisionRegression` is separate package research. With both
Breath of Fury and Whip in hand and no creature on the battlefield, the pilot
passes rather than deploying Whip. Forced legal deployment demonstrates paid
Strix recovery, ETB card draw, haste, damage and lifelink without GGS. This is
an experimental capability comparison; it does not establish the best initial
choice or justify a deck cut by itself. A four-black/four-other-mana fixture
also reproduces greedy casting that consumes black needed to activate Whip;
floating two blue mana before casting legally preserves the recovery line.
That payment-planning fault remains open in the automated pilot. The synthetic
hand and board here are constructed scenarios, not natural game records.
