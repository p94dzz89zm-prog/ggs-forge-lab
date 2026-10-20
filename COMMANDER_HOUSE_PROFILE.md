# Explicit Commander house profile

Enable the native variant with the JVM option
`-Ddragonmind.houseProfile=ggs-house-v1` before `-jar`. Default behavior remains
standard Commander. Unknown profile identifiers fail closed.

The profile enforces40 starting life through registered-player starting-life
access, at most3 full-hand reshuffles drawing7 each with no bottom/tuck payment,
and no loss for21 commander combat damage. The fourth redraw is unavailable;
keeping earlier is allowed. Actual commander damage history remains recorded;
only the commander-damage loss predicate is bypassed. Ordinary life, poison,
empty-library and card-specific win/loss rules remain in the native engine.
This is an explicit house variant, not an amendment to official Commander.

Native tests verify registered life is40 even if configured otherwise; all
four seats in the actual mulligan service stop after3 declines with7 cards and
no London tuck; a fourth direct redraw fails;21 commander damage does not cause
a loss; and zero life still does. Default-off controls preserve configured17
life and standard commander-damage loss. Unknown profile refusal is tested.
The overlay modifies only three narrow existing classes and adds two house
classes. Every other executable member is byte-identical to its pinned base.
Historical engines and reservations are never edited.

Frozen natural-game preflight binds the declared profile to exactly one active
JVM flag, before `-jar`, and the exact40/false/3 configuration. Missing, duplicate,
misplaced, unknown or contradictory flags/configuration are rejected. This
configuration check does not certify deck legality, card behavior or a game.
311 root Python tests pass. No new natural game has yet run under this profile;
the earlier standard-profile diagnostics are not relabeled as house games.

Next: a fresh independently allocated Pilot A game with this executable/profile,
complete frozen input manifest and full private history. Full-game approval
still requires substantive independent casting, costs, priority, stack, combat,
trigger, SBA, commander, layers/replacement and terminal review, with no unresolved
issues. Pilot B remains experimental and all outcome training stays blocked.
