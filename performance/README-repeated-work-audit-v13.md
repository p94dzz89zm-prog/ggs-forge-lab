# DragonMind repeated-work audit on v13

October 2, 2026. Two isolated diagnostic games of Commander seed 20261012,
GGS_Layered_v1 / Jaymie_Ezio / Gabe_Food / Destyn_Turtles, stock Default policy.
No production optimization was adopted. The accepted v13 runtime remains active.

## Findings

| Target | Calls | Observed repeats or empty reconstructions | Instrumented time |
|---|---:|---:|---:|
| Combat survival forecasts | 42,515 | 2,597 tracked-state repeats (6.1%) | 0.373 s in repeated bodies |
| Hypothetical stack reconstruction | 34,671 | 33,168 added no options (95.7%) | 9.669 s in all stack bodies |
| Live restoration after hypothetical hosts | 34,745 | Not a repeat counter | 7.115 s in restoration bodies |

There were 221,595 alternative-cost queries, with zero repeated input identities
inside the instrumented discovery scopes. This narrow count cannot rule out
reconstruction of equivalent inputs as fresh SpellAbility objects, repeats across
separate discovery scopes, or calls outside those scopes. Stack rebuilds added
1,503 alternatives, one per productive rebuild in this workload.

Combat repetitions had no observed boolean disagreements. The tracked signature
includes card identity, face, timestamp, power/toughness, damage, counters,
controller, zone, tapped/phased/commander flags, AI life, combat identity and
revision, flags, and the existing replacement inspection invalidation generation.
It does not include every global effect, mutable ability parameter, mana resource,
stack change or trigger dependency. Matching this signature is not proof of safe
result reuse. Forecast calls can themselves prepare or mutate ability objects.

The demonstrated combat repeat work is small. Do not implement final combat
result memoization on this evidence. The stronger target is reconstruction that
adds no options: investigate a conservative way to determine when stack ability
grants could apply before rebuilding hypothetical and live static state.

## Architectural implications

The current GameAction.hasStaticAbilityAffectingZone guard asks whether any active
continuous ability affects the stack ability layer. GameActionUtil then rebuilds
for each basic spell candidate, even when that candidate gains no alternative.
The existing retired v8 candidate guard already tried narrowing this world scan
and did not reduce rebuild counts; repeating that approach is not justified.

A useful next prototype needs an indexed applicability description for stack
ability grants and their dependencies, maintained when source effects change.
It must preserve type, control, text, copied/granted effects, layer ordering,
hypothetical cast context, and hidden-zone sources. Unknown or potentially
changing dependencies must take the original reconstruction path. Checking only
printed creature types, or remembering that a previous query produced nothing,
is insufficient. First validate any proposed eligibility filter in shadow mode
against the original full rebuild; then benchmark a separate candidate.

This audit selects that target; it does not deliver the index or a speedup.
The 16.783 seconds across reconstruction and restoration are instrumented work,
not demonstrated obtainable savings. Restoration includes some non-stack
hypothetical hosts. These values cannot be added to earlier overlapping profiles,
and a real change may move costs elsewhere. This one workload does not establish
an engine-wide optimization ceiling or forecast instantaneous games.

## Validation and reproduction

Both games completed and each matched all 1,103 tracked Turn, Phase, Add To Stack,
Resolve Stack, Damage, Combat and Life events from the accepted v13 control.
Combat diagnostic engine time was 54.385 seconds; reconstruction diagnostic time
was 51.147 seconds. These are not paired speed measurements. Java 17 compiled
both isolated overlays; Python compilation and git whitespace checks passed.
No production regression suite or full Maven build was rerun for diagnostic-only
changes. All 48 managed sources still match the verified v13 checkpoint, and the
active archive still matches the accepted v13 SHA-256.

Build either overlay using its diagnostics/build_*_profile.py script with
SOURCE, accepted v13 JAR, and OUTPUT_DIRECTORY arguments. Run classes before the
jar on the classpath, with dragonmind.combatProfile or
 dragonmind.reconstructionProfile set to the CSV destination. JVM options:
-Xmx1536m -XX:+UseParallelGC -XX:-TieredCompilation -XX:CompileThreshold=1000
-XX:-UsePerfData -Djava.awt.headless=true. Simulator arguments: sim -D DECK_DIRECTORY
-d GGS_Layered_v1.dck Jaymie_Ezio.dck Gabe_Food.dck Destyn_Turtles.dck -f Commander
-seeds 20261012 -c 180 -a Default Default Default Default. Use the Forge resource
working directory. Overlays leave source and packaged jars unchanged.

Diagnostic references are held only in thread-local search scopes, removed when
the outer scope closes; process totals retain scalar counters. No diagnostic
result is used to serve engine queries. CSV counters and trace/log hashes are
retained in diagnostics/*-v13.csv and repeated-work-audit-v13.json.
