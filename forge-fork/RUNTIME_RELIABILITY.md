# Exception-preserving regression execution

The desktop runtime can install its own default uncaught-exception handler
during model initialization. A handler may consume a failure instead of
printing its original console traceback. That is an observability problem,
not by itself an explanation of earlier incomplete exit0 startup attempts.

`RegressionLauncher` invokes a suite's main method reflectively and catches
the original failure before it reaches that handler. It prints the original
cause and stack, flushes stderr and exits nonzero. The regression includes a
control whose deliberately discarding handler suppresses an assertion trace,
then verifies the wrapped version retains that assertion and stack. Additional
contracts test argument forwarding, static initialization, missing suite and
missing argument failures. These are constructed subprocess tests, not games.

`run_pilot_recovery.py` and `run_line_planner.py` compile this launcher with the
suites, record its source/class hashes and retain the existing exact completion
markers, timeout limits and error checks. An explicit System.exit(0), missing
marker, timeout, crash or incomplete suite is still not a pass. The launcher
cannot catch a process kill or every asynchronous worker-thread failure.

No Java policy, engine executable, card rules, deck or coefficients are changed
by this runner correction. Keep experimental engine provenance separate from
the adopted incumbent. A cleaner diagnostic is not a pilot-strength gain.
The intermittent startup-exit cause and full-game strategic reliability remain
open until separately reproduced and reviewed.

After interrupted work, recover the authoritative ledger and confirmed saved
checkpoint. Do not infer stoppage solely from an absent process in another
workspace. Record any later missing evidence as a retention gap, keep consumed
seeds reserved, and rerun reconstructed source checks on newly allocated random
conditions rather than describing lost logs as certified evidence. Persist a
completed attempt before starting more work or lengthy analysis.

## Frozen input integrity

`run_pilot_recovery.py` now verifies a closed input ZIP's CRC and SHA256 before
execution, optionally against `--expected-jar-sha256`. It checks the hash after
every suite and rejects changed/missing archives even with a valid completion
marker. Invalid inputs retain a failure manifest with zero completed checks.
Regressions include missing ZIP directories, CRC corruption, and a different
but structurally valid archive under an old frozen hash. This detects damaged
inputs; it does not establish the cause of observed workspace truncations or
explain intermittent startup exits. Verify saved checkpoint bytes again after
materialization; an upload receipt alone is insufficient for recoverability.
