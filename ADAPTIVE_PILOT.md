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
  --model /path/to/experience.sqlite --games 6 --seed 2026102101 --pool sandbox
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

The learner is currently sequential: one full JVM game per update. Very large
runs need a distributed rollout service, storage budgets, broader deck
curricula and bounded reporting. This prototype is not advertised as a
million-game training platform.

## Fresh verification

`run_pilot_recovery.py` in the rigorous run verifies 157 targeted scenarios and 512 randomized full-controller combat positions (685
executions including 16 repeated Prowler checks). The new combat fixtures pay
native ninjutsu and graveyard Sneak costs and resolve the real triggers: native
ninjutsu activates both Satoru rewards; paid Sneak does not. They also verify
supplementary fresh attacks and profile-dependent opening preferences.

`python -m unittest -v test_adaptive_pilot` runs 18 checks of persistence, automatic
preference change under controlled feedback, held-out/failure isolation and
event-metric parsing. Controlled feedback tests are software tests, not evidence
that a particular profile is superior in real games.

Known recovery gaps remain: the later equipment/ninjutsu mana-reservation
heuristic and the older-body Trebuchet attack fallback have not been rebuilt
in this checkpoint. The new fresh-attack supplement covers a narrow small-body
case. There is no full-game tactical correctness certificate, broad card-rule
coverage certificate, or basis yet for card-cut recommendations.

## Referee gate added after the first experiment

The first six training games update **sandbox preferences only**. None has been
approved as strategically correct. New commands default to `--pool reviewed`;
that pool uses only complete measurable training episodes with a recorded pass
review. A high proxy reward cannot bypass this gate. `--pool sandbox` explicitly
opts into provisional experimentation. Evaluation never updates either pool.

`review_experience.py` records the referee, scope, reasoning and pass/reject/pending
status, with an append-only review history. Passing a scoped review is not a
claim that every decision was optimal. Poor but legal choices can be informative
negative examples; do not delete losses or approve only winning games.

`referee_games.py` checks canonical result/transcript agreement and engine-error
markers, then emits review leads. It never marks a game strategically approved.
The 64 seeded randomized combat probes additionally check attack/block legality
and that forecasts do not mutate the battlefield. They do not solve optimal play.

Legacy experimental manifests predate the pool field; preserve them with the
older committed implementation. Start a new output directory and disjoint seeds
for the gated runner rather than rewriting historical manifests. Existing
experience databases migrate additively and remain readable.

Audit collection can now target the GGS seat with `forge.audit.player`, avoiding
redundant snapshots of all four private views. This is an instrumentation scope
control, not a proven cure for all timeouts. The engine hash changes, so it is a
new learning context. Old evidence remains tied to its original engine hash.

## Rigor pass and attack-limit repair

Use `--random-cases 512 --random-start 20000` on the regression runner to
reproduce the expanded pass. The randomized referee now calls the full AI
controller, not just the low-level proposal builder. This matters: the
low-level planner can exceed Crawlspace, while the controller restores legality
by falling back to no attacks. A targeted full-controller fixture demonstrated
that lost safe attack. The new bounded subset recovery preserves useful legal
attacks before the empty fallback, including without GGS. It does not relax
combat requirements or mana checks, searches at most ten proposed attackers,
and leaves unhandled cases to the stock fallback.

One provisional game's `Correcting zone for Hithlain Rope` console messages
were temporarily withheld and then investigated. The pinned GameAction source
prints that message during normal controller changes, and Hithlain Rope passes
control as part of its abilities. That diagnostic alone is not corruption. The
review history preserves the investigation and the return to pending status;
none of the six sandbox games is strategically approved.

The reviewer now verifies console and canonical-file hashes, result agreement,
observed-effect counts and recomputed reward before accepting a scoped pass.
Genuine engine exceptions withhold collector rewards automatically. Tests cover
both corrupted evidence and this normal controller-change false positive.

The learner remains a limited profile tuner. The attack-limit fix and other
rule/timing repairs are programmed changes found through testing, not tactics
that a general learning model invented. No all-card tactical learner or
mistake-free-play certificate is claimed.
