# DragonMind

Latest accepted engine: v17 records combat relationships and private ninjutsu
attribution for diagnosis. The cost-source v18 candidate preserved tested traces
but produced no useful speed gain, so it was not adopted. See
[the experiment](performance/cost-source-v18-experiment/README.md). The runner
defaults to one game per JVM and two workers on sufficiently provisioned hosts:
complex warm batches can stop early and leave later seeds without results.
Earlier speed measurements remain in [the v15 follow-up](performance/README-v15-followup.md).

DragonMind is our Commander simulation and AI layer, built on the GPL-licensed
Forge 2.0.15 rules engine. Forge's source packages, attribution, and license remain.
The existing checkout and remote keep their names for compatibility.

## Fast unattended batches

Build the patched executable using `forge-fork/build_bridge.py`, then run:

```sh
python3 dragonmind.py --engine /absolute/path/to/forge/forge-gui --jar /absolute/path/to/forge/forge-gui-desktop/target/dragonmind.jar --seeds 4 --batch-size 1 --workers 2
```

Each process loads the card database and plays an independently seeded game.
Larger warm batches remain opt-in with `--batch-size`; they amortize startup but
can leave later seeds unrun after an incomplete game. Separate JVMs isolate
Forge's global RNG; games are not run concurrently inside one JVM. Audit is
off by default; use `--audit` for diagnosis. The commander-aware ninjutsu policy
is enabled by default; `--stock` is available for controlled comparisons.

The initial performance check reduced a completed test game from 46.2 seconds
unprofiled to 39.5 seconds cold and 34.8 seconds warm, with the same winner and
final turn. This is a small benchmark, not a general speed guarantee. Another
seed timed out at 90 seconds and is reported as incomplete. Interactive review
pauses are absent in batch mode. Seconds-to-instant games are still a target.

See `performance/` for raw measurements, source changes, and validation. A timeout
or engine failure aborts the remaining games in that JVM batch; those games are
reported as not run. No timeout counts as a win or loss.

A reproducible runner for **actual four-player Commander games in Forge**, using the supplied Goro-Goro and Satoru and Jaymie/Ezio lists. This project is a runner, not a newly invented Magic rules engine. All card resolution, priority, combat, triggers, replacement effects, commander rules and player decisions are delegated to Forge. Engine correctness remains subject to Forge's card scripts and bugs.

## Run

Requires Python 3.10+, Java 17+, and an external Forge 2.0.15 installation.

1. Download the official [Forge 2.0.15 Java installer](https://github.com/Card-Forge/forge/releases/download/forge-2.0.15/forge-installer-2.0.15.jar).
2. Verify installer SHA-256: `965ecae67e54369d3c98ed79ed9a62ee04b6c6be019b6d978c9cf71223c109aa`.
3. Install with `java -jar forge-installer-2.0.15.jar -console`, choosing an installation directory. The release tarball's desktop executable was corrupt in our download; the Java installer succeeded.
4. Run:

```sh
python3 -m unittest discover -s . -p 'test_*.py'
python3 run_games.py --engine /absolute/path/to/forge --games-per-variant 4 --workers 4 --timeout 240
```

Use `--resume` with the same arguments after an interruption. It verifies the recorded engine and deck hashes and skips saved game attempts, including incomplete attempts. Use a new output directory to rerun those games.

To test only selected versions:

```sh
python3 run_games.py --engine /absolute/path/to/forge --variants GGS_Current GGS_Two_card_trial --games-per-variant 12 --output followup
```

Four seats rotate per seed, and each subsequent group of four uses a new seed. Matching seeds are reproducibility inputs; they do not guarantee identical draws or decisions across changed decks. Each game starts a separate Java process; full logs, commands, seeds, seat order and classifications are retained. Hardware/time scheduling and Forge's AI may prevent perfectly deterministic replay despite the same seed.

## Deck scope

- `GGS_Current`: the exact supplied current 100-card list, including Draconic Visitor and Kindred Discovery.
- Jaymie: supplied 100-card main deck; sideboard excluded.
- Gabe: stock Food and Fellowship, Frodo/Sam commanders. This is a proxy for any unknown upgrades.
- Destyn: stock Turtle Power, Leonardo/Michelangelo commanders. This is a proxy for any unknown upgrades.
- `manifest.json` lists every variant and exact swaps. **Variants and diagnostic swaps are experiments, not approved deck changes.**
- All imported decks contain 100 cards including commanders. Forge spelling aliases are disclosed in the manifest; no card substitutions were made.
- Draconic Visitor uses Forge's upcoming-card script; that script is available in this installation, but the engine assigns upcoming cards to a future edition with unknown rarity. Its script quality needs separate scrutiny.

## Audit outputs

After each run finishes:

```sh
python3 summarize.py
python3 summarize.py --output followup
python3 summarize_all.py
python3 inspect_card.py "Orochi Soul-Reaver" --output followup
```

The combined report includes the first batch and the independent-seed follow-up. Original per-game records preserve what the running process reported; `audited_records.json` uses the latest parser to classify the original logs again. Read audited results for conclusions.

## Trust boundaries

The runner excludes engine/process errors, unresolved output and timed-out games from completed outcomes. Forge can print false winners after a timeout, even awarding all four players a win; those outputs are explicitly rejected. Exclusion creates selection bias: completed games must not be presented as an unbiased deck win-rate sample. No timeout is a game loss.

Forge AI is the pilot. These games do not measure how the real humans in the pod play or establish human pod win rates. Complex ninjutsu, token replacement choices, loops, tutors, politics and recovery choices can be poorly piloted. No unsupported card effects are approximated. Cast events recorded in JSON are attempts placed on the stack, not proof that a spell resolved or was a useful draw. Turn numbers are Forge's individual-player turn counter, not table rounds.

Do not interpret a four-game exploratory sample as evidence of a small card improvement. Read the complete logs and compare card usage and failures before recommending swaps.

## Files and provenance

- `run_games.py`: external-engine process orchestration and conservative outcome parsing.
- `inspect_card.py`: find a card's GGS stack events in audited logs, e.g. `python3 inspect_card.py "Higure, the Still Wind"`.
- `summarize.py`: re-audit every original log and build measured tables. Run it after the game runner finishes.
- `test_runner.py`: regression tests for false timeout wins, crashes, ambiguous outcomes and deck sizes.
- `CURRENT_MAINBOARD.txt`: supplied baseline in plain-text import format; no new swaps.
- `PURCHASED_CANDIDATES.txt`: screenshot candidates not already in the baseline, suitable for a maybeboard; excludes the unowned Naga diagnostic.
- `decks/`, `manifest.json`: frozen deck versions and card spelling aliases.
- `GAME_RESULTS.md`: combined audited counts and candidate exposure for both seeded runs.
- `results/` and `followup/`: complete logs and machine-readable records for this run.
- `EVALUATION.md`: measured results and practical conclusions after the completed 84-attempt audit.

Forge executable SHA-256 used: `85a4c31e07d4d5621a84bb03b6d75fd08e9f4ba289e575c870579b49c0033766`. Startup reports `2.0.15-SNAPSHOT-09.28` despite the release asset being 2.0.15.

Primary sources: [Forge release](https://github.com/Card-Forge/forge/releases/tag/forge-2.0.15), [simulation entry point](https://github.com/Card-Forge/forge/blob/master/forge-gui-desktop/src/main/java/forge/view/SimulateMatch.java), [AI documentation](https://github.com/Card-Forge/forge/blob/master/docs/AI.md), [Food and Fellowship](https://magic.wizards.com/en/news/announcements/the-lord-of-the-rings-tales-of-middle-earth-commander-decklists), [Turtle Power](https://magic.wizards.com/en/news/announcements/teenage-mutant-ninja-turtles-commander-decklist).

The original Python runner is MIT licensed. Forge is an external project under its own license; its executable, card database and implementation are not redistributed here. Magic card names and rules belong to their respective rights holders. This is an unofficial analysis tool.

The initial runner hashed decoded, newline-normalized log text. Two initial-batch logs contain carriage returns, so their recorded text hashes differ from raw-file hashes. The audit verified the original text hashes and records raw-file SHA-256 separately; the current runner hashes raw bytes. No log content was changed.

Final run: 84 attempts, 64 completed, 16 game timeouts, 4 AI evaluation errors. Eight regression tests passed. Every audited raw game-log hash and imported deck hash was verified. No engine binaries are bundled.
