# Native state-readiness allocation

Base published source: 8dfaf89f72821f6f20643d64dd7fa3c248a5d4d1.
Scope: one constructed native four-player fixture, at most three attempts;
no natural game seeds, replay tapes, training, or Stage48 file modifications.
Input engine: verified Stage47 JAR SHA256
b1521760e6448630079102e9917ecd74293300e34ab577140ccc0de67b8e8762.
Fixture helper AITest SHA256
627896571a72011a000891d05cb7a6b17b62b206ee103c94150b104c5084671d.

The native PhaseHandler.checkStateBasedEffects routine is called by the priority
path before chooseSpellAbilityToPlay. Bytecode inspection shows it invokes native
GameAction.checkStateEffects, stages waiting triggers, and repeats after triggers
are added. Existing referee instrumentation does not observe this full routine.
Static inspection is not a rules pass; the allocated fixture tests actual
lethal-damage/indestructible/zero-toughness transitions and a death trigger that
must enter the stack and resolve later. The second indestructible creature has
explicit synthetic zero base toughness; this is not a card Oracle change.

Validation status: allocated; native fixture not yet claimed executed.
Source: forge-fork/StateReadinessRegression.java. Preserve failed attempts and
require its exact PASS marker, not just exit0. Stop at three attempts; record
all results. Stage47 remains the immutable gameplay checkpoint; Stage48 unknown
ownership and partial evidence remain untouched.
