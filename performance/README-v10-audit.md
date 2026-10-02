# DragonMind v10: batch throughput and correctness audit

2026-10-02. Baseline v9; local v10 runtime and batch-runner fixes.

## Result

Use two independent Java workers with warm seed batches on this host. Four workers
provided only 1.3% more throughput in this workload while nearly doubling peak
memory. One-worker throughput was 1.40 games/minute; two workers achieved 2.53.
This is batch throughput, not sub-second individual games.

| Workers | Four-game wall time | Games/minute | Peak combined RSS | Completed |
|---|---:|---:|---:|---:|
| 1 | 171.13 s | 1.40 | 1.20 GiB | 4/4 |
| 2 | 94.71 s | 2.53 | 2.27 GiB | 4/4 |
| 4 | 93.49 s | 2.57 | 4.09 GiB | 4/4 |

Host limits: eight CPU cores, 8 GiB memory. Each JVM has a 1536 MiB heap cap.
The workload repeats seeds 20261011 and 20261012 twice at rotation zero, using
stock AI in GGS / Ezio / Food / Turtles. One/two workers use two warm two-game
processes; four workers use four single-game processes. Startup, warm-up, and job
layout are included, so this is a workload comparison rather than pure worker
scaling. Configurations were measured once, sequentially, with no concurrent
tests or simulation profilers. Memory was sampled approximately every 0.5 second.
All 12 games completed and 12,876 ordered tracked events matched the reference.

## Confirmed fixes

1. **Completed-game retention:** Forge's global AI decision cache retains Player
   and Game references until the next decision clears it. The initial two-game
   weak-reference probe retained one completed game after explicit collection;
   no evaluator threads survived. v10 clears this cache after successful
   simulations. The repeated probe retained zero of two games and zero evaluator
   threads. Post-collection used heap fell from 299,777,880 to 184,275,440 bytes.
   This demonstrates last-game retention in this workload, not unbounded growth.
2. **Interrupted timeout helper:** interruption of the waiting caller previously
   left its task uncancelled. It now cancels the task, restores the interrupt flag,
   and shuts down its executor in finally. Cooperative tasks stop; uncooperative
   work still needs the existing outer JVM timeout. Normal results/exceptions and
   game rules are unchanged.
3. **Log memory:** the batch runner now parses file lines incrementally instead of
   reading, splitting, and accumulating whole game transcripts. Retained parser
   state consists of result rows and an error flag; raw logs remain on disk.
4. **Untrusted results:** trailing exceptions invalidate final completions;
   malformed JSON/fields/durations become recorded batch failures rather than
   aborting the entire run. Winners must identify registered seats. Performance
   output includes status counts and completed games/minute.
5. **Replay fabrication:** the replay builder previously injected hardcoded life
   changes and six Dragons from a particular historical game. Final outcome text
   now requires matching four-player outcome/result records from the current log.
   It preserves the last observed board and does not infer final damage or tokens.
6. **Batch configuration:** default workers becomes two on cgroup hosts with at
   least four CPU cores and 4 GiB memory, otherwise one. An explicit --workers
   overrides this choice; the existing warm-batch default remains four seeds.

## Verification

- 32 engine optimization tests, 19 commander pilot tests, 12 bridge tests:
  all passed against the accepted v9 source overlay/v10 runtime.
- 31 Python tests passed, including new parsing, malformed-output, resource-limit,
  and replay tests. Python sources compiled; git diff whitespace check passed.
- Four lifecycle scenarios passed: normal result, original exception propagation,
  caller interruption with task cancellation, and timeout with task cancellation.
- The fixed memory probe completed both pod games and all 2,146 tracked events
  matched the original controls. Separate diagnostic classes insert only weak
  references and forced collection after simulation; they are excluded from jars.
- Twelve ordered patches reproduced all 41 patch-managed source files byte for
  byte from the pinned upstream checkout. The packaged v10 jar passes ZIP
  integrity checks and excludes test/profiler classes. Its two changed production
  classes are SimulateMatch and TimeLimitedCodeBlock.
- Packaged v10 runner completed seed 20261011 in 26.076 engine seconds /
  31.459 wall seconds; all 1,043 tracked events matched. Stable dragonmind.jar
  was updated only after this verification. This is not a separate timing pair.
- Changed Java production/test classes were compiled with Java 17. The entire
  Maven source build was not rerun.

## Audit coverage and outstanding gaps

The audit covered DragonMind's patch-managed source changes, batch scheduling and
classification, bridge/replay code, added caches and invalidation hooks, global
AI cache references, task lifecycle, syntax/conflict-marker checks, source/package
reproduction, and representative completed games. It is not exhaustive proof that
upstream Forge or every Magic card interaction is correct or leak-free.

Known limits remain:
- Commander inference recognizes the GGS fresh-creature Dragon trigger family.
  General commander-plan inference is not implemented.
- Two opponent lists remain stock proxies rather than verified current pod lists.
- The replay is recorded playback, not a live spectator stream.
- The supplied rules baseline explicitly states targeted, non-exhaustive rules
  conformance. Draconic Visitor uses the installed upcoming-card script and still
  needs separate Oracle/script scrutiny.
- Upstream AI evaluation still contains a last-resort Thread.stop fallback after
  timeout. Failed evaluations are rejected by result classification; this audit
  does not certify that cancellation is safe for every uncooperative engine path.
- Larger and more varied warm batches are needed to establish long-term heap
  stability and generalize worker selection. No universal no-leak claim is made.

The next performance work should profile block-search internals and static-layer
rebuilds; parallel games improve throughput but do not remove those per-game costs.
