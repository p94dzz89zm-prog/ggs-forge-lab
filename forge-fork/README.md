# DragonMind engine integration

This is a custom, opt-in controller overlay for Card-Forge/forge 2.0.15, pinned to
`4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676` (2026-09-28).
Forge remains the rules engine. This does not implement Magic independently.

## What it changes

An external client can select timing-eligible spells/abilities, X, targets,
attacks, blocks, creature types, effect card/entity choices, confirmations, and
basic bounded-number choices. Forge checks timing, targets, combat constraints,
and payment. Illegal responses stop the run; there is no silent replacement move.
Each response must match the current request ID. The file interface has no network
listener. A request/response transcript records decisions.

**This is assisted control.** Stock AI still handles mana selection, cost payment
(including some sacrifice/bounce choices), mulligans, damage assignment,
trigger preparation, and controller hooks not overridden in the patch. An explicit
`{"auto":true}` delegates a supported prompt to stock AI. Such decisions must be
labelled delegated in any analysis. This is not a fully manual pilot or a trained AI.
The bridge itself does not alter stock strategy. The optional [GGS pilot v1](PILOT_V1.md)
changes ninjutsu decisions for one named seat. Without its property, stock strategy
is retained. When neither bridge nor audit is enabled,
Forge constructs its normal AI controller.

The commander-identity follow-up exposes search and modal-effect choices to the
external pilot, and adds public rules text, commander flags, attachments, phasing,
and entry-this-turn state. Its opt-in ninjutsu policy preserves commanders and
recognizes the GGS Dragon engine from its scripted trigger conditions. Recognition
is deliberately narrow; this is not a general commander strategy model. It does
not prohibit commanders from attacking. Rescue or redeployment through ninjutsu
needs a separate decision policy.

The guided seed-20261012 game won with GGS still in play and six permanent Dragons
created, on the guided player's tenth turn. It used the earlier executable plus
external decisions; it does not validate the follow-up policy's independent play.
Targeted follow-up checks: 19 pilot tests and 12 bridge tests passed. Invalid
interface attempts are excluded. One assisted game cannot establish a win rate.

`viewer/index.html` is a self-contained recorded replay, not a live stream. Rebuild
from the guided seat's transcript with `forge-fork/build_replay.py`; never feed
opponent-private audit hands into its input.

## Build

Install Java 17+, Git, Maven, and Python 3. From the lab checkout:

```sh
python forge-fork/build_bridge.py ../forge-ggs
```

The script refuses to overwrite an existing checkout, verifies the pinned commit,
creates branch `ggs-assisted-bridge`, applies the five ordered patches, runs the engine tests,
and packages the desktop build. Dependencies require internet access.
The sparse checkout used for development is unnecessary on your computer.
The executable is also packaged as `dragonmind.jar`. Use `../dragonmind.py` for
unattended warm-process batches. Interactive bridge sessions intentionally wait
for external decisions and are not simulation throughput benchmarks.

## Start a controlled Commander seat

Use the built desktop jar and upstream `forge-gui/res` assets. The packaged build reads `res` from its working directory, so run
from `forge-gui`. Substitute absolute paths below. The bridge seat must match
the printed `Ai(N)-<deck metadata Name>` exactly. This example controls Ezio and
leaves GGS on stock Default AI; it is an interface example, not a matchup claim.

```sh
cd /absolute/path/forge-ggs/forge-gui
java -Djava.awt.headless=true \
  '-Dforge.bridge.player=Ai(1)-Jaymie_Ezio' \
  -Dforge.bridge.directory=/absolute/path/live-bridge \
  -Dforge.bridge.timeoutSeconds=600 \
  -Dforge.audit.directory=/absolute/path/offline-audit \
  -jar ../forge-gui-desktop/target/forge-gui-desktop-2.0.15-jar-with-dependencies.jar \
  sim -D /absolute/path/ggs-forge-lab/decks \
  -d Jaymie_Ezio.dck GGS_Current.dck -f Commander \
  -a Default Default -n 1 -s 20301001 -c 7200
```

The match timeout includes time waiting for external decisions. Adjust it for an
interactive match. This foreground process must stay running on your computer.

In another terminal:

```sh
python /absolute/path/ggs-forge-lab/forge-fork/bridge_client.py /absolute/path/live-bridge interactive
```

For agent control, use `show`, then send a response bound to its request ID:

```sh
python forge-fork/bridge_client.py /absolute/path/live-bridge show
python forge-fork/bridge_client.py /absolute/path/live-bridge respond 'SESSION:1' '{"index":-1}'
```

Responses: priority/entity `{"index":0}` (priority -1 passes); targets/cards
`{"indices":[0]}`; attack/block `{"pairs":["cardId:defenderId"]}` using offered
keys; type `{"type":"Ninja"}`; confirm `{"yes":true}`; number `{"number":3}`.
Empty attack/block lists declare none, subject to engine constraints. Priority
options are timing-eligible candidates; not all are payable. X can be supplied
as `{"index":0,"x":3}`. Cost choices remain assisted.

## Information and audit boundaries

Live snapshots include your hand and public zones. Other hands and all libraries
are counts only; opposing face-down identities are hidden. Engine-issued own-library
search choices can reveal names needed for that choice. This conservative prototype
does not expose every legally visible revealed-card state.

**Do not give the external pilot the offline audit directory during a match.** Each
seat's priority audit contains that seat's hand. Audit is for post-game review and
therefore can expose opponent private information. Candidate evaluation events log
stock AI accept/reject decisions; ninjutsu policy rejections have named reasons.
Type choices are recorded. These are diagnostics, not proof an action was optimal.

## Validation and interpretation

See `verification.json` for executed checks and smoke-run status. Tests use the real
Forge card database and rules engine, not a Monte Carlo substitute. They cover paid
Lightning Bolt resolution, externally chosen combat and creature type, hidden
information, invalid indices, stale responses, upkeep without land candidates,
and a legal equal-mana-value ninjutsu activation rejected by stock AI.

Exception runs and timeout runs are invalid for win-rate analysis, even if Forge
prints a winner. A controlled smoke run establishes integration, not strong play
or better card recommendations. See [PILOT_V1.md](PILOT_V1.md) for the separately tested experimental strategy update.
Keep deck swaps provisional until pilot decisions
and completed, comparable games have been reviewed.

## License and attribution

Forge and this Forge-derived patch/source are GPL-3.0; see COPYING and upstream
<https://github.com/Card-Forge/forge>. The lab's root MIT license does not replace
Forge's license. The independent Python helper scripts remain under the lab MIT
license. No upstream ownership or universal AI improvement is claimed.

The public request/response transcript is gzip compressed (`*.jsonl.gz`).
Seat-private post-game audit files are published under `evidence/offline-audit`
with explicit user authorization to publish the internal audits, including hidden
hand information. Keep these files away from the external pilot during matches;
they are for post-game inspection.

## DragonMind v3 performance

The runner now records a throughput compiler policy (`--jit throughput`, the default) or standard Java compilation (`--jit default`). Tracked live keyword views preserve membership caching while invalidating on edits; hidden-ability empty fast paths preserve suspicion and keyword counters. See [the v3 measurements](../performance/README-v3.md). Fresh games still take tens of seconds, and timeouts are excluded from deck comparisons.
