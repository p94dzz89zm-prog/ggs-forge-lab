# Readiness capture allocation

Base published source12a30d01aa9ab13f93e51a778ec93ba640cd074a.
Independent disabled-by-default recorder; Stage48 artifacts remain untouched.
Use frozen Stage47 engine b1521760e6448630079102e9917ecd74293300e34ab577140ccc0de67b8e8762.
Budget: one instrumentation build and at most three constructed native capture
attempts in a fresh external temporary directory. No natural game seeds or
training are allocated in this milestone. Preserve every failure and raw output.

Capture the actual native SBA and trigger-staging returns, readiness routine
entry/exit, and controller-action boundary. Link records with a monotone
sequence and seal completed traces with byte count/SHA256. Missing terminal or
receipt fails closed. These snapshots are intentionally partial: no whole-game
approval may be inferred from a complete diagnostic trace. Natural capture is
enabled only by explicit dragonmind.readinessTrace path; hypothetical games are
excluded by actual game identity. No rules or policy logic is changed.

Status: native capture and independent protocol validation completed.

The builder overlays only PhaseHandler and the new ReadinessTrace class on the
exact Stage47 base; every other existing JAR entry remains byte-identical.
Instrumentation checks the actual call graph before writing output. It records
SBA return/trigger-staging return, readiness entry/exit, and the actual controller
choice call site. Native mainGameLoop attaches/seals the recorder automatically
when explicitly enabled; exceptions leave a trace without a success receipt.

Two fresh JVM executions of the constructed four-player regression pass with
byte-identical trace bytes. Each independently audited trace has4 completed
readiness windows,5 SBA returns,5 trigger-staging returns, and1 actual priority
offer. No natural complete game was executed in this milestone. Full logs,
traces, receipts and the executable are preserved in a private immutable archive;
saved bytes were downloaded, restored and verified against all16 manifest
members. Only aggregate results and build hashes are published under
forge-fork/validation/readiness-capture-20261020. Automatic review rejected
raw evidence publication to GitHub; no raw logs/traces from this milestone were
published there. Source and tests remain independently reproducible.

The streaming reader binds the original receipt and rejects missing/reordered
SBA/trigger checks, an early priority offer, changed recorded state before the
offer, duplicate offers, missing completion, and malformed counters.277 Python
tests pass. This is an independent causal-protocol check, not a complete rules
referee: snapshots omit full layer/replacement/target and pending-trigger
inventory. Game-over early exits likewise remain explicitly unverified.

New native bytecode evidence does not alter gameplay choices or legality.
Stage48 remains untouched; Stage47 at466 choices remains the replay recovery
checkpoint. New natural games0; independently approved complete games0; trusted
training updates0. Next milestone: separately allocate one natural four-player
diagnostic with this overlay and the full private engine recorder, save its
original evidence, and inspect readiness/state/decision gaps before any approval.
