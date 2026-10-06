# Frozen Pure GGS experiment

Firework v1.0 is the separate, unchanged control; this experiment runs Pure_GGS against Jaymie_Ezio, Gabe_Food and Destyn_Turtles. All four imports were validated by actual Forge Commander conformance before games. Pure's file is exactly 100 cards with SHA-256 `166a88df0207b4792d3784f7ef0218510e3c0114a7208368b079ce99bdc07cf7`.

The pinned upstream resources are commit `4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676`. The base engine is v28, SHA-256 `d9278b1ddd644ef6dd458b19cfabee20d3c2e9fde51d1cf10827a91c842616ee`. The frozen experimental executable is SHA-256 `43b8dded3ad4316c12632cd0ed359f687b79c461da3b8a68e365481d5f15dcfb`.

The only runtime overlay is the explicit casual-seven mulligan house rule. It changes MulliganService and its compiler-generated switch class and adds CasualSeven. Every other class/resource is byte-identical to v28. `build_house_engine.py` rebuilds all three class files identically; ZIP container timestamps can produce a different overall archive hash. Never overwrite the frozen executable during collection.

CasualSeven returns the entire dysfunctional seven, shuffles, and draws another seven for all seats. Redraw only zero effective land faces, six or more, or one without Sol Ring; keep other random sevens. MDFC land faces count. No London bottoming or engine/color sculpting. Twenty redraws is an invalid-game error, not a forced keep.

`PureDeckValidation.java`, `PureRulesGate.java`, and the existing `forge-fork/AccessPackageRegression.java` use the actual Forge engine. The four-game short gate is excluded from experimental estimates. Focused checks establish fresh vs stale GGS, Human/Goblin Throne doubling, Forge each combat, Krenko tokens not attacking, paid additional combat, real Thousand-Faced Shadow ninjutsu and attacking copy, access and symmetrical Cover.

`run_batch.py` runs one isolated actual Forge process per reproducible seed/rotation, two concurrent workers, a 300-second timeout, full priority and decision audits, and atomic result/transcript reconciliation. It stops submitting jobs on a failed game. The batch metadata retains deck/runtime hashes, commands, seed, seats and timeout.

`analyze.py` reconciles exact GGS-created token births with canonical resolved creation triggers. It does not count changelings or Thousand-Faced Shadow copies as GGS creations. Timing uses observed Pure personal turns, not global-turn division. Damage attribution follows exact phase, combat ordinal and canonical life changes. Whole-turn future extra-combat damage must never leak into an earlier threshold. Material amplifier contribution is distinct from card presence. Counterfactual necessity is observational; uncertain amplified cases are retained and flagged.

`protocol.json` records operational thresholds and analysis clarifications. Clarifications were made while auditing initial batches and applied uniformly to all games; this is not a claim that every final measurement detail was preregistered. `summarize.py` reports denominators, Wilson intervals and whole-seed cluster bootstrap intervals. Neither interval quantifies AI-model bias. Review automatic stall labels and any artifact flags against canonical logs before the final report. A dangerous board losing after interaction is not an ignition failure.

Typical commands from repository parent:

```sh
python ggs-forge-lab/experiments/pure-ggs/run_batch.py --seed 202610061 --seeds 4 --out pure-ggs/batch-01
python ggs-forge-lab/experiments/pure-ggs/analyze.py pure-ggs/batch-01
python ggs-forge-lab/experiments/pure-ggs/summarize.py pure-ggs/batch-01/analysis/games.json
```

Do not reuse an existing batch output directory. Restored paths may need adjustment while preserving recorded arguments and hashes. Durable evidence bundles contain the exact executable, all four seats' decision/priority logs, engine records, transcripts and batch metadata; the final per-game dataset supersedes provisional checkpoint classifications.
