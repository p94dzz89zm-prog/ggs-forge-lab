# DragonMind source recovery

DragonMind is an experimental Magic rules-validation and Commander research
environment built around a pinned Forge runtime. Python tools use the standard
library with Python3.11 or newer. Native overlays require a Java17 JDK.

Run the source tests from this directory:

```sh
python3 -m unittest discover -v
python3 -m unittest discover -s diagnostics -p 'test_*.py' -v
python3 -m compileall -q .
```

The source tree includes engine overlay builders, synthetic regression tests,
evidence writers/readers, admission gates and two experimental Python pilot
architectures. Native pilot integration is ongoing. Complete independently
rules-approved four-player games:0. Trusted outcome training remains gated.

Provide private decks, resource/card databases, model artifacts and game histories
as external runtime inputs. They are intentionally absent from this branch.
No default deck path here establishes that a corresponding private file exists.
Keep active game outputs outside the source checkout. Use a new output directory
for every attempt and preserve failures and reserved seeds.

The verified readiness builder accepts the exact private Stage47 JAR with SHA256
`b1521760e6448630079102e9917ecd74293300e34ab577140ccc0de67b8e8762`:

```sh
python3 forge-fork/build_readiness_trace.py --base /absolute/path/base.jar \
  --output /tmp/new-isolated-attempt/engine.jar --java /absolute/path/java
```

The base JAR, Forge resources, pinned AITest helper and TestNG dependency are
external dependencies. Native checks must run with Forge's resource directory
as cwd. See `forge-fork/README.md`. This recovery verifies the overlay build
against those dependencies; a complete upstream Maven build is a separate check.

`SOURCE_PROVENANCE.json` binds restored original file bytes to the private
recovery commit. `SOURCE_RECOVERY.md` records the selected inventory and tests.
Original datasets and full recovery archives remain privately preserved.
