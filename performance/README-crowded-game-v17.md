# Crowded-board investigation and audit enrichment

A Java Flight Recorder diagnostic reproduced Apex seed 20261021 on accepted v16.
It completed with Destyn winning after 88 global turns, taking 270.439 seconds.
The earlier fully audited run finished at turn 75, so these are different traces;
the profiled time is not a speed comparison with that earlier run.

Of 19,830 execution samples, 13,312 included spell-ability discovery (67.1%),
10,067 included static-ability rebuilding (50.8%), 3,218 included block search
(16.2%), and 2,951 included attack search (14.9%). Inclusive counts overlap and
are not exclusive CPU durations. Source inspection confirms that uncertain
stack grants and dependencies retain hypothetical rebuilding. The profile
supports investigating those dependencies next, not blindly broadening rebuild
exclusions. No CPU shortcut was adopted in this pass.

Reviewing the earlier ten games found both accepted and rejected ninjutsu plans.
Priority snapshots lacked combat relationships, and evaluations did not identify
the host card. That limited attribution of missed fresh-creature connections.
V17 adds public combat IDs/status to snapshots and host identity plus an
is_ninjutsu flag to private evaluations. Hidden identities retain existing guards;
private records are kept in saved archives and excluded from public exports.

Both decklists and pilot weights are unchanged. V17 is an audit improvement, not
a demonstrated strategy or speed improvement. The new twenty-game collection
uses seeds 20261024–33, the same seats and pod, one JVM per game, one worker,
and a 600-second allowance. A seed-19 control exactly preserved all 887 tracked
events from the earlier v16 audited game.

## Additional timeout evidence from the new collection

The initial Apex seed-28 attempt declared a win, but the runner invalidated it
because an AI evaluation exceeded the engine's five-second decision allowance.
The timeout stack ran through PumpAllAi, attack planning, a nested next-combat
forecast, blocker assignment, removeUnpayableBlocks, available mana estimation,
additional-cost checking and CostAdjustment.adjust. At the sampled point it was
assembling battlefield card collections. The same-seed retry under unchanged
settings completed cleanly and is explicitly labeled in the accepted sample.
The failed attempt remains separate; its declared win is not counted.

CostAdjustment.adjust currently collects battlefield, stack and command cards,
then adds the host with the existing deduplication priority and reads current
static abilities. Sharing conservative source discovery inside a read-only
forecast is a concrete follow-up experiment. It must preserve those zones,
ordering, host/LKI priority, face-down changes, live modifier conditions and
invalidation. No cost outcomes or mana affordability results should be cached.
This evidence supports a candidate to test; it does not establish a speedup.
