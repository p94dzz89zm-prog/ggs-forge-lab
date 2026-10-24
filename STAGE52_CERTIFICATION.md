# Complete-game certification inventory

The three historical diagnostic archives were restored with their original
manifest hashes. All full referee streams were read and matched their sealed
writer receipts: 210122,163045 and276864 records. The house-profile history is
the leading candidate; the first two histories used commander damage and one
free mulligan, so they cannot be relabeled as house-profile games.

`certification_inventory.py` produces a private machine-readable ledger of
initial structure, earliest unresolved setup prerequisites and nine categories
of event-anchored audit obligations per game. Each obligation retains its first
observed event, turn, phase, call/sequence identity, applicable rules, minimal
reproduction and required engineering. Missing event applicability stays a gap.
These obligations are not counted as independent engine root defects.

All twelve initial seats have100 physical cards and40 life. Exact name-multiset
binding remains unresolved in two seats per game: frozen single-part names
versus captured full two-part names. The inventory deliberately does not guess
aliases by splitting names. Full Oracle identity, color identity, commander
eligibility/partner, singleton exceptions and effective format legality still
need independent evidence. The earliest remaining prerequisite is at turn0,
GameEventGameStarted call25, before any certified gameplay prefix. Engine-only
deck conformance is not sufficient. No complete game has been approved.

Three house-history self-reduction contributions were independently computed
from captured characteristics, using exact battlefield identity matches between
the selected execution and public snapshots:

| Spell | Captured contribution | Locked cost |
| --- | --- | --- |
| Blasphemous Act | Eight creatures | R |
| Excalibur, Sword of Eden | Controlled historic mana value6 | 6 generic |
| Vanquish the Horde | Ten creatures | WW |

The calculation adds explicit increases before reducing generic costs, floors
generic at zero, preserves colored requirements, excludes phased-out permanents
and counts each historic permanent once. Current Gatherer access returned403.
Official release notes support Act/Excalibur; Vanquish has an official printed
card image reference and captured Oracle text. Current Oracle/format truth,
characteristic/layer timing, absence of external modifiers and spending-source
restrictions remain unapproved. The arithmetic explains the recorded differences
without proving complete casting legality or identifying a new engine defect.

References: [Act release notes](https://magic.wizards.com/en/news/feature/commander-legends-release-notes-2020-11-06),
[Excalibur release notes](https://magic.wizards.com/en/news/feature/assassins-creed-release-notes),
[Vanquish official image](https://media.wizards.com/2021/mid/en_3huadc37Wc.png),
[Comprehensive Rules](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt).

Original replay remains466 consecutive choices and1790/1985 conditionally
supported decisions. Stage48 still has an allocated unknown outcome; no reserved
replay execution was attempted. No new natural game, pilot policy change,
strategic finding or training admission occurred.
