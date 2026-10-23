# Opening-state derivation and historical mulligan sequencing defect

The three original diagnostic archives were restored by manifest hash, including
the exact lossless house referee capture. Unmodified prefixes through turn4 were
extracted with their own byte hashes and original complete-stream receipts.

Independent opening-zone calculations check400 physical cards, twelve seven-card
opening hands, declared starting-player/first-cycle turn order, first upkeep
priority observations, and twelve first-turn draw-step moves. Top-card derivation
checks32draws in the profiled history,29in the native Pilot A history and32in the
house history. A wrong top-card mutation in the actual house prefix is rejected.
These are scoped checks under captured initial-state premises, not certified
historical events or complete games.

The native Pilot A history has a confirmed CR103.5 sequencing discrepancy:
turn0/null phase, call171, sequence732, player3 returns the first hand card to
Library while players0,1,2have not declared their first-round mulligan choices.
Its first rejection is call166; its shuffle follows at203; other first-round
choices begin at240. Seven returns/redraws share this one sequencing root cause.
The independent minimal fixture rejects this order and accepts all declarations
before mulligan execution. Public upstream MulliganService likewise performs a
rejected player's mulligan inside the declaration loop. A native correction is
not yet implemented or verified; the next stage must bind and repair the exact
engine method without disturbing existing overlays or historical evidence.

The other two histories record no mulligans. The native history has three free
first mulligans, one each for players3,1,2, with final seven-card hands. Its
post-shuffle permutations are not captured, leaving24draw-order gaps. Initial
shuffle entropy and starting-player selection remain unproved for all games.
The house prefix also contains a later first-cycle shuffle; its subsequent order
is not inferred. First two games retain their original nonhouse rules profiles.

No opening state, historical event or complete game is independently certified.
Historical Oracle/format provenance and general action/effect permissions remain
unapproved. No new game, pilot-strategy update, reserved replay or training ran.

Primary standard: [Comprehensive Rules effective September25,2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt),
103.5(all declarations precede simultaneous mulligans),103.5c(first multiplayer
mulligan free),103.8c(first multiplayer turn retains its draw),903.6-7(setup).
Upstream source: [MulliganService](https://github.com/Card-Forge/forge/blob/master/forge-game/src/main/java/forge/game/mulligan/MulliganService.java).
