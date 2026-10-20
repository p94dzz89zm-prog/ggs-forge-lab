# Source-only recovery inventory

Compared immutable publishedf6dd1b0 (14 files), earlier12a30d0 (794 files),
and saved/reverifiedbdfcc89 (812 files). Current branch is a separate recovery;
the existing integration branch and original archives remain intact.

| Original recovery classification | Selected | Excluded |
| --- | ---: | ---: |
| Source code |196|4|
| Synthetic tests |150|0|
| Configuration |4|0|
| Documentation/licenses |15|63|
| Generated artifacts |0|100|
| Historical evidence |0|250|
| Private deck/research inputs |0|30|

The selected19 build patches are required by the restored native builders.
The four excluded source patches are unadopted experiments. Excluded bytes,
paths, original Git blob identities and SHA256 values are recorded privately.
No unique original source is discarded; the full private recovery bundle retains
all812 files and historical commits. The current source tree publishes no raw
game histories, private decks/models or historical datasets.

Safe current README/dashboard/native-build instructions replace historical
versions. Source inventory checks and this report are new recovery files.
`SOURCE_PROVENANCE.json` records current file hashes and original provenance.
`python3 verify_source_inventory.py` checks the ENTIRE Git index/path inventory
and every current source file, catching sparse or extra trees and changed bytes.
The manifest itself is bound by its published Git blob; self-hashing is excluded.

Validation:300 root Python tests,14 diagnostic tests, compileall, six pure-JDK
launcher checks, rebuilt readiness overlay byte-identical to the private saved
executable, and native four-player readiness fixture pass. The independent trace
protocol audit covers this constructed fixture. Full upstream Maven dependency
build and all historical native suites have not been rerun. Forge resources,
external executable/helper dependencies and private decks are not distributed.

Complete independently rules-approved games remain0. Native pilot integration,
natural-game profiling and full-game independent approval remain next work.
