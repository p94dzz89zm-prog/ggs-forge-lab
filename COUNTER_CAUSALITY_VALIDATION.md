# Counter-removal causality audit

Run `python3 counter_causality_audit.py REFEREE_TAPE` on a complete private
stream. Verify writer receipts and referee_tape.py separately. This reader
reconstructs stack identities from announcements, validates resolution snapshots,
and links unresolved removals to an active CounterEffect call through actual
call ancestry and structured direct targets. It checks the target's departure
from the stack and graveyard ownership. Card names and descriptions do not drive
its result. Non-graveyard destinations retain a replacement-review gap.

The preserved turn55 house-profile game passes this limited audit across276864
records and259 resolution snapshots. Its one unresolved removal links Lightning
Greaves to Fierce Guardianship's direct target, active resolving context and
departure to its owner's graveyard. No additional unexplained counter-removal
causality gap remains in this reader. The original history-audit report is not
edited or relabeled: its broader effect-review requirement still applies.

The engine effect implementation label is not independently derived Oracle
behavior. Dynamic target characteristics, targeting restrictions, counter
prevention and replacement effects remain unverified. This result neither
certifies that casting the counterspell was legal nor approves the whole game.
There are still three completed recovery diagnostics, zero independently
rules-approved complete games and zero trusted outcome training admissions.

Fourteen new regressions cover wrong target/card identity, self-targeting,
resolution order, broken ancestry, missing target/departure evidence, owner
graveyard mismatch, replacement destinations, exceptional exits, sequence gaps,
incomplete streams and reused stack instances. The current330 root tests pass.

Reference standard: Comprehensive Rules effective September25,2026, sections
115.5,608.1,608.2b and701.6a-b. Countering removes an object without resolving it;
ordinary countered spells go to their owners' graveyards without cost refunds.
Card-specific text, prevention and replacements must be reviewed separately.
https://magic.wizards.com/en/rules
https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt

Next: independent target/casting/payment restriction and priority derivation,
then combat, triggers, continuous/replacement effects and loss/SBA derivation.
The original equipment-payment failure remains unresolved. This stage runs no
new natural games, changes no pilot policy and admits no learning.
