# Pilot recovery checkpoint

The workspace was cleared twice. This branch reconstructs selected later pilot
changes from the documented diagnoses over the exactly reproduced v28 engine.
It is not a byte-identical restoration of v31–v35. Missing historical logs are
not recreated or counted as newly verified games.

## Verified checkpoint r3

* Prowler chooses a legal unblocked attacker with pending positive damage for
  lifelink, instead of putting the keywords on an idle commander. Actual target
  selection and keyword resolution are tested, including first-strike timing.
* The opt-in GGS pilot rejects a narrow class of seven-card hands with four or
  more lands and no inexpensive development/interaction. This is a heuristic,
  not proof that every such mulligan is optimal. Reduced hands use stock logic.
* Assault recognizes a prospective Sword combat even when the carrier is
  already untapped. The fixture pays the real 3RR and verifies the additional
  combat phase. Sick creatures, taxes, legal blockers, insufficient mana,
  disabled policy and other timing retain stock behavior.

Fresh validation: **99 distinct scenarios, 115 executions**, including 16
seeded repetitions of the same Prowler target scenario. These are not 115
independent games. All five suites passed with exact completion markers;
exit code alone is not accepted. Logs and checksums are under
`validation/pilot-recovery-r3/`.

## Reproduce

Use Forge source commit `4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676`
(tag `forge-2.0.15`) for resources and AITest. Use TestNG 7.10.2.
First run `build_access_repair.py` over the retained verified v24 executable;
then run `build_pilot_recovery.py` over that v28 output. Both refuse a base
with the wrong checksum. Run `run_pilot_recovery.py --help` for validation
arguments. Never replace a JAR while games are using it.

The base JAR is not checked into this source repository. Its SHA-256 is
`7c48b167f44b6bcf4cdc3472425346a0cad3deb2fcddaeb5e4029465201e1e60`.
The reproduced v28 SHA-256 is
`d9278b1ddd644ef6dd458b19cfabee20d3c2e9fde51d1cf10827a91c842616ee`.

## Evidence limits and next work

No current win-rate improvement is claimed. Card cuts remain on hold. Keep
losses in the dataset; annotate decision errors and separately replay after
repairs. Passing these fixtures does not establish globally optimal play.

The existing pilot is a programmed heuristic, not a learning model. Repetition
alone does not update it. A future experience learner must keep rule legality
outside the learned strategy, store immutable experience, evaluate on held-out
seeds/decks, and never equate winning a game with every action being correct.
Broader training and Sneak/fresh-attack restoration are subsequent checkpoints.
