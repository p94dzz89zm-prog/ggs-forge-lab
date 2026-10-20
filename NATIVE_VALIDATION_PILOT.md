# Experimental native Rules-Validation Pilot A

`forge-fork/build_validation_pilot.py` overlays the exact readiness executable
with an opt-in controller factory and `RulesValidationController`. Other base
JAR entries remain byte-identical. Enable explicitly with
`-Ddragonmind.validationPilot=true -Ddragonmind.validationSeed=INTEGER`.
Remote bridge ownership and decision replay cannot be combined with this mode.
Default-off controller selection remains unchanged.

The policy ranks engine candidates by least-visited action kind, token visits
and a stable seeded tie. It enumerates its own hand/graveyard/command/battlefield
and face-up exile; library actions and permission to use opponent-owned sources
are outside this version's action enumeration. Mana abilities remain delegated
to Forge payment. Target choices use stock Forge assistance; combat, mulligans,
trigger choices and other unoverridden hooks also remain delegated. Those
heuristics' hidden-information discipline is not independently certified here.

Timing, target eligibility/counts and payment preflight use native Forge APIs.
Actual execution checks the selected object, actor, priority and current targets
again, then calls the actual Forge payment/casting routine and retains its
success result. A failed engine payment is never promoted by policy. Candidate
preflight is not a proof of a complete legal-action catalogue. Successful native
execution still needs independent rules review. A policy budget of64 actions per
turn/phase permits passing to bound repetitive zero-cost choices; it cannot end
the game or manufacture a terminal result.

`RulesValidationPilotRegression` is a constructed four-player Commander fixture.
It installs four controllers, selects/casts Sol Ring using actual Island mana,
rejects wrong-priority and consumed-selection execution, resolves the artifact,
then casts targeted Lightning Bolt using actual red mana and observes the
targeted1/1's removal through SBA. An unaffordable spell and an opposing hidden
hand card remain in hand. This does not prove comprehensive information security.

Two fresh fixture processes yield identical399-row engine tapes/199 paired
calls, with writer receipts verified and independent arithmetic checking2 mana
cost/pool transitions with0 gaps. No random requests occur in that scoped tape;
the fixture sets the actual native RNG and policy seed before game construction.
Default-off control passes. Build1 failed ASM superclass loading; the frame
resolver now uses the application loader. First fixture failed an old card-object
zone assertion; the corrected check locates current zone membership by card ID.
Failure logs remain private. A separate invocation compiled from the wrong cwd;
that failure is retained as a harness error and is not counted as a pass.

Pilot B remains the separate experimental Python offline scorer. Neither pilot
trains on these fixtures or unapproved outcomes. No complete natural game or
full-game rules approval follows. Next: separately allocate a profiled natural
diagnostic with complete input provenance and histories; obtain comprehensive
casting/stack/combat/trigger/SBA/terminal review before admitting any game.
