# Firework simulator repair (v28)

The repair leaves Firework Protocol v1.0 and the Jaymie_Ezio / Gabe_Food / Destyn_Turtles pod unchanged. Validate all four frozen 100-card decks before running. The final report and runtime package carry the reliability gate outcome; do not infer a deck recommendation from this source change.

## Build

Requires Java 17 with compiler modules. The exact audited v24 base is `DragonMind_Firework_Verified.jar` (SHA-256 `7c48b167f44b6bcf4cdc3472425346a0cad3deb2fcddaeb5e4029465201e1e60`). Its historical filename does not mean its old gate passed: that run was 15 valid games and one timeout. The executable is retained with the engineering artifacts.

```sh
python forge-fork/build_access_repair.py --base /absolute/path/DragonMind_Firework_Verified.jar --output /absolute/path/dragonmind-v28.jar
```

Expected v28 SHA-256: `d9278b1ddd644ef6dd458b19cfabee20d3c2e9fde51d1cf10827a91c842616ee`. The builder overlays five compiled classes onto that exact base, writes source hashes, and preserves archive metadata. This is a partial Java rebuild, not a clean Maven rebuild of all Forge modules. `baseline-src/` preserves recovered v18–v24 source snapshots beyond the older patch chain, with their hashes. Forge source/resource baseline is commit `4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676`.

## Verify and run

```sh
python forge-fork/verify_firework_runtime.py --engine /absolute/path/engine --jar /absolute/path/dragonmind-v28.jar
python -m unittest discover -s . -p 'test_*.py'
python forge-fork/run_access_regressions.py --engine /absolute/path/engine --jar /absolute/path/dragonmind-v28.jar --testng /absolute/path/testng-7.10.2.jar --forge-source /absolute/path/pinned-forge-source --logs /absolute/path/access-checks
python dragonmind.py --engine /absolute/path/engine --jar /absolute/path/dragonmind-v28.jar --variant GGS_Firework_Protocol_v1_0 --seed 202610052 --seeds 4 --rotations 0 1 2 3 --workers 2 --batch-size 1 --timeout 300 --audit --stop-on-failure --output /absolute/path/new-gate
```

The runner requires a fresh output directory. Each game uses a separate JVM and runtime profile. `--stop-on-failure` stops new submissions, while already running jobs finish within their time bounds. It does not silently discard failed attempts or count exit code zero as game completion.

## Scope

Higure, War Cadence and Gingerbrute now recognize useful, payable access during the actual attacker window for the opted-in GGS pilot. Higure targets legal Ninja attackers; War Cadence evaluates the actual defending player and public available mana; Gingerbrute respects haste blockers. The pilot skips stale, redundant and irrelevant effects. Frostcliff Siege receives the scoped cast-evaluation repair while its default Jeskai mode and actual card rules remain unchanged.

Cover of Darkness grants fear to all creatures of the chosen type, including opponents. Fear still permits black and artifact blockers. Frostcliff Temur grants power, haste and trample, not unblockability; power changes can remove Tetsuko access. Engine regression fixtures cover these boundaries and the wider access package.

Headless result recording now persists the actual engine outcome atomically and writes a canonical game transcript independently of console printing. The runner accepts fallback records only when they agree with that transcript and no console exception invalidates the attempt. It rejects disagreement. Normal GUI logging remains the default outside opted-in console simulations.

A previous concurrent run exited normally without a final result. Profile isolation and console-only logging alone did not fix that case. The precise original cause remains unproven; direct records address the reporting path and must pass the fresh 16-game gate before promotion.
