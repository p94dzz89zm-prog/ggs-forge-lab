# Completed natural-game performance diagnostic

One separately reserved four-player Commander diagnostic completed naturally
on turn47. Wall107.5625s; engine99.388s; user CPU167.6188s; system CPU13.6100s;
peak resident memory914036KiB (about893MiB). Multiple threads contribute CPU time.
The original180-second turn64 timeout remains separately preserved and was not
reexecuted. This fresh seed is not a controlled causal comparison with that game.

All executable, Java/modules, resource, deck, policy-source, explicit argv/env,
configuration and versioned official rules-reference metadata were frozen before
launch. Post-run fingerprints remain unchanged;55369 resource files are covered.
Installed Commander conformance passes for all four archived decks; independent
Oracle/banlist certification is outstanding. The diagnostic uses the same native
standard Commander profile as the old attempt; the user's house configuration
is not certified. No deck recommendation or strategic strength claim follows.
Rules reference: official September25,2026 Comprehensive Rules, verified through
https://magic.wizards.com/en/rules . Full rules text is not copied into the inputs.

All9 original writer receipts and the complete engine/readiness streams verify.
The private checkpoint retains actions, RNG, all-seat audits, original JFR,
commands, configuration, frozen inputs and complete-game result/transcript.
The493MiB derived JFR JSON is regenerable from the original recording and excluded
from the archive; its extraction command is retained. Original evidence is intact.

| Scoped independent observation | Count |
| --- | ---: |
| Engine records / paired entered calls |210122 /98815|
| Actual mana cost AND pool transitions |186 each;0 gaps|
| Passes consistent with recorded priority holder |2060|
| Public mana disclosure checks |3;0 gaps|
| RNG requests |12491|
| Readiness/action boundaries |2155|
| Unsupported KeywordWithCost values |2|
| Independently approved complete games / training |0 /0|

These checks do not derive full legality from Oracle rules. Missing keyword
serialization, complete casting/combat/stack/trigger/terminal derivation, layers,
replacement effects, hidden-information discipline and house rules remain gaps.
The final readiness stream has one game-over exit explicitly unverified by the
readiness auditor. A natural terminal record cannot fill those obligations.

## Runtime profile

JFR contains5621 execution samples and633 native samples. Of4046 sampled stacks
containing PhaseHandler,1629 also contain recorder frames (40.26%). The most
frequent application frame in that subset is DurableEvidence.append (1103).
Fourteen sampled stacks were truncated. Counts are observed stack prevalence,
not wall-time allocation or predicted speedup. The small count of recorded file
events is thresholded and cannot quantify total I/O wait.270 GC events were
recorded; no causal GC or policy-strength conclusion is asserted.

Source inspection identifies duplicate conversion: EngineEvidence serializes a
JsonObject, then DurableEvidence parses that JSON and serializes it again after
adding stream metadata. A structured append overload is the next candidate;
byte-equal native tape regressions must verify any repair before adoption.
The old timeout's exact CPU/strategy breakdown remains unmeasured. Current
evidence shows substantial recorder cost and continuing natural progress.

`profile_natural_game.py` preserves an exclusive attempt claim and process CPU,
memory, logs and post-run input checks. It never interprets process success as
game or rules approval. Tests reject changed inputs and repeated attempts and
retain failed exits. `analyze_jfr_profile.py` reports observed stacks with explicit
scope. Pilot A's native fixture is independently checkpointed; Pilot B remains
experimental and receives no unapproved outcomes.
