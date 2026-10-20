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

Validation status: completed with a corrected fixture on attempt2.
Source: forge-fork/StateReadinessRegression.java. Preserve failed attempts and
require its exact PASS marker, not just exit0. Stop at three attempts; record
all results. Stage47 remains the immutable gameplay checkpoint; Stage48 unknown
ownership and partial evidence remain untouched.

## Observed native results

Both compilations succeeded. Attempt1 exited1 at the pending death-trigger
assertion: the manually assembled fixture omitted the normal pre-action
last-state battlefield history. Attempt2 calls game.copyLastState before the
native readiness routine and exits0 with the exact PASS and SCOPE markers.
Original source, both full logs and compilation logs are retained under
forge-fork/validation/state-readiness-20261020, bound by RESULT.json hashes.
No gameplay-engine rule or strategic policy was changed. This repaired the
fixture setup, not a demonstrated engine rules defect.

Actual four-player native assertions verify:

- Grizzly Bears with lethal damage moves to the graveyard.
- Darksteel Myr with lethal damage remains on the battlefield.
- A second indestructible Myr with explicit synthetic zero toughness moves to
  the graveyard; this is not destruction.
- Doomed Dissenter dies and exactly one death trigger is put on the stack.
- No token exists before that trigger resolves; checking readiness again does
  not duplicate the trigger or resolve it prematurely.
- Native stack resolution creates one2/2 token owned/controlled by the source
  controller; a subsequent readiness check leaves an empty stack stable.

These outcomes implement the scoped assertions of CR117.5,603.3,704.5f-g and
702.12b in the September25,2026 official Comprehensive Rules:
https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt
The four resource definitions used by the fixture are hashed in RESULT.json;
indexing or loading other definitions does not certify their implementations.

## Reproduce

Use Java17's `java -m jdk.compiler/com.sun.tools.javac.Main` with a classpath
containing the exact Stage47 engine, verified fixture-classes directory and
testng-7.10.2.jar. Compile forge-fork/StateReadinessRegression.java into a fresh
directory outside /workspace. Run StateReadinessRegression with those classes
first on the same classpath, -Djava.awt.headless=true, -Xmx1536m, a fresh isolated
user.home, and the verified engine resource directory as cwd. Require exit0
AND the exact `PASS StateReadinessRegression:` marker. Each native attempt is
bounded to90seconds. No replay property, audit writer or model fitting is enabled.

## Coverage boundary

This tests native readiness behavior for one deliberately constructed board,
not every state-based action, simultaneous trigger APNAP ordering, replacement
effect, or multiplayer elimination condition. Reflection invokes the exact
private routine used by the native priority path, but does not independently
observe every natural priority grant. Existing captures lack those routine
entry/exit hooks, so global readiness approval remains unavailable. Next:
introduce separate fail-closed readiness instrumentation with causal before/
after state and trigger-queue evidence, without modifying Stage48 artifacts.

Stage47 remains at466 verified replay choices. Stage48's513-choice report is
still uncheckpointed. Complete rules-approved games0; new natural games0;
trusted training updates0. This commit preserves the public native regression
and its full constructed-case evidence; it does not advance replay coverage.
