# Stack removal notification repair

The pinned execution-evidence engine emitted a removal event even when neither
the live stack nor its frozen stack contained the requested instance. Native
Dawn aftermath resolution reproduced two notifications for one departing object:
the exile transition removed it, then resolution cleanup removed it again.
Repeated direct removal reproduced the same generic defect.

The overlay adds a membership guard to MagicStack.remove(instance). An absent
instance returns without a notification; a present live or frozen instance uses
the existing removal path. There is no card-name special case. Only this class
changes; every other executable entry is byte-identical to the pinned base.
The original executable and histories remain preserved unchanged.

Native old/new controls reproduce two versus one notifications for actual
five-mana aftermath casting and resolution to exile. Live and frozen removal
controls pass. A real opponent Counterspell response pays two blue mana, resolves
over Dawn, exiles the countered aftermath spell and produces exactly two removal
notifications, one per stack object. The existing 409-row controller tape remains
byte-identical. All 316 root Python tests pass.

Build with forge-fork/build_stack_removal.py against its exact pinned base;
compile/run StackRemovalRegression with the preserved native test dependencies
and resource directory. Private recovery evidence binds executable hashes,
commands, tapes and complete logs. This is a scoped event-integrity repair, not
complete-game certification. A fresh natural game has not used this repair yet.

Reference: Comprehensive Rules effective September 25, 2026, rule 702.127a:
https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt

Next: independently derive counter/removal causality, full casting/payment,
priority, combat, triggers, state-based actions and terminal conditions. Pilot B
and trusted outcome training remain gated on independent complete-game approval.
