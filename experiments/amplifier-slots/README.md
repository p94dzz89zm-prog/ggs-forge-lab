# Six amplifier-slot tests

Pure_GGS remains frozen and Firework v1.0 is untouched. Six separate decks each replace one major amplifier with Night's Whisper. The other five remain. This measures whole-card value versus an ordinary draw spell, including body, haste and extra-combat roles; it does not establish optimal replacements or effects of removing all six together.

`protocol.json` preserves the already saved protocol: gate28 games, actual Forge v28 casual-seven engine, established pod, four seat rotations, reproducible seeds, 16/32/64 progressive samples per arm, optional96/128 for unstable arms. Primary comparisons use all-game ignition/basic/strong/threat rates. Conditional conversion/timing, recovery, card usage and wins are secondary. Positive paired retention effects favor keeping the amplifier. Bootstrap complete seed blocks; do not rank overlapping uncertain effects as established facts.

Restore `DragonMind_Engine_v28.tar.gz` into `restored-v28`, and the house executable from `Pure_GGS_Evidence_Part_01.tar.gz` into the original repository path. Its exact SHA-256 is in the protocol. Original128-game baseline results and evidence remain unchanged. `restore_baseline.py` restores original own-seat audits, canonical logs and summaries from remaining evidence archives; full baseline all-seat evidence remains in the original saved archives.

`setup.py` recreates exact frozen variants and mechanically checks all100 counts/differences. `SlotDeckValidation.java` initializes the real Forge model and checks actual Commander conformance for all ten imports. It is a standalone validation harness; the engine is not rebuilt or modified. `check_gate.py` requires28 clean games, four baseline canonical replays matching prior logs excluding elapsed-time fields, no missing GGS births and perfect life-state reconciliation. Clamp flags must be audited as surviving positive-toughness commander equips.

`run_batch.py` uses four isolated JVMs/profiles and300-second limits. Only deck seat-name and lossless-gzip support were generalized in the existing progression extractor. `checkpoint.py` saves completed-game metadata, all-seat decision/priority audits, exact canonical transcripts and derived timelines after each16 completions and at batch end. No live jobs or source code are exported to game-evidence bundles. Interrupted unsaved attempts are not experimental observations. `progress.py` advances only through passed gates and clean complete stages; it stops on real engine, integrity, or save failures.

Example from repository parent:

```sh
python ggs-forge-lab/experiments/amplifier-slots/setup.py
python ggs-forge-lab/experiments/amplifier-slots/run_batch.py --gate --seed 202610060 --seeds 1 --out amplifier-slots/gate
python ggs-forge-lab/experiments/amplifier-slots/progress.py
```

Keep the original baseline/control hashes fixed. Never silently approximate unsupported card text or combine untested cuts.

Audit compression publishes a completed temporary file by atomic rename. `inspect_games.py` prefers the complete compressed audit when redundant raw files also exist. `audit_integrity.py` verifies every finished stream through the gzip footer and JSON records before a stage comparison; it can recover an incomplete compressed copy only from a preserved raw superset, recording hashes and repairs. Redundant raw prefixes are removed only after durable saving and verification. This is evidence handling, not an engine/card/AI change.
