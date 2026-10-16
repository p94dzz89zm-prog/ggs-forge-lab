# Adaptive pilot: experimental strategy-profile learning

This component **does update its preferences automatically from actual Forge
games**, and retains them in a transactional SQLite experience database. It is
a contextual UCB bandit over three predefined profiles. It does not learn new
rules, generate tactics, retrain a language model, or establish perfect play.

The distinction matters: this is the first limited learning layer, not a
general self-improving Magic player. Forge executes card rules and costs;
learned preferences affect only bounded GGS strategy choices.

| Profile | Extra GGS connection weight | Ninjutsu mana penalty | Replay mana penalty | Slow-seven land threshold |
| --- | ---: | ---: | ---: | ---: |
| BALANCED | 90 | 6 | 4 | 4 |
| ENGINE | 120 | 6 | 4 | 5 |
| ECONOMY | 75 | 10 | 6 | 5 |

All existing legality, commander-preservation, lethal-connection and payment
guards remain in force. The profile does not change card text. The defaults
retain the audited BALANCED weights. An explicit invalid profile fails visibly.

## What learning means here

For each deck/engine/opponent context the trainer selects a profile, runs a
seeded game, records observed effects, and updates that profile's sample count
and mean utility. UCB explores under-sampled profiles and increasingly favors
those with higher observed utility. A later game can therefore use a different
strategy without a person changing source code or weights.

The fixed utility is 55% GGS triggers per own turn, 25% opponent-player combat
damage during own turns, 10% life gained per own turn, and 10% winning. Each
effect component is capped after scaling. Full vectors are retained. **GGS
trigger counts are not guaranteed Dragon token production.** These metrics do
not measure every card's usefulness, missed opportunities, defensive value,
card advantage, or causally attribute an episode's outcome to one decision.
They can be gamed and require review before stronger deployment claims.

## Reproducibility and interruption handling

Run from a checkout with the verified engine/resources available:

```bash
python adaptive_pilot.py --engine /path/to/forge-gui \
  --jar /path/to/pilot.jar --output /path/to/training-run \
  --model /path/to/experience.sqlite --games 6 --seed 2026102101
```

Repeat the exact command to resume; increase `--games` to extend that run.
The manifest pins deck hashes, engine hash, seeds and scoring version. A
different engine is a new learning context. Only one trainer may write a model
at a time. Crashes/timeouts are retained but receive no learning reward. A
previously running interrupted attempt is retained rather than overwritten.
Completed experience cannot be counted twice under a new output directory.

Use `--mode evaluate --seed <disjoint range> --output <new path>` for held-out
games. Evaluation freezes profile selections and never contributes rewards to
training. Until all three profiles have at least two training samples, it uses
BALANCED. This threshold merely enables exploratory comparison; it does not
certify significance. Seeds shared between training and evaluation are rejected.

Use `--decks GGS_Current GGS_Two_card_trial ...` to rotate existing validated
deck variants. Experience remains separate by deck and pod; success with GGS
does not prove skill on unrelated decks. This runner currently uses the saved
Ezio/Food/Turtles pod. A broad cross-archetype learner is future work.

No million-game run, unattended scheduler, or continuous background training is
enabled by this command. `--games` is a bounded total, not a claim of how many
games have already been completed. Training alone is not evidence of improvement:
that requires paired held-out comparisons and decision review.

## Fresh verification

`run_pilot_recovery.py` now verifies 121 distinct engine scenarios (137
executions including 16 repeated Prowler checks). The new combat fixtures pay
native ninjutsu and graveyard Sneak costs and resolve the real triggers: native
ninjutsu activates both Satoru rewards; paid Sneak does not. They also verify
supplementary fresh attacks and profile-dependent opening preferences.

`python -m unittest -v test_adaptive_pilot` verifies persistence, automatic
preference change under controlled feedback, held-out/failure isolation and
event-metric parsing. Controlled feedback tests are software tests, not evidence
that a particular profile is superior in real games.
