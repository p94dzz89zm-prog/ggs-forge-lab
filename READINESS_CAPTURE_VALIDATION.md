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

Status: allocated; implementation unvalidated until native compilation/run,
independent trace checks, and published evidence complete.
