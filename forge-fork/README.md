# DragonMind native integration

Forge remains the rules engine. Source is pinned upstream to
`4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676` (Forge2.0.15).
`build_bridge.py` clones that source into a new directory, checks the pin,
applies the restored build patches and invokes Maven. It requires network
access and Maven dependencies; this recovery has not rerun that full build.

The independently reproducible readiness overlay builds from the exact private
Stage47 JAR using `build_readiness_trace.py`. It changes PhaseHandler and adds
ReadinessTrace while checking byte equality for other original entries. See the
root README for the base hash and command. Builders keep input executables intact.

Compile/run `StateReadinessRegression.java` with the private runtime JAR, pinned
AITest helper classes and TestNG7.10.2 on the classpath. Compile RegressionLauncher
with it and invoke `RegressionLauncher StateReadinessRegression` from the Forge
resource cwd, using a fresh isolated user.home. The helper class SHA256 is
`627896571a72011a000891d05cb7a6b17b62b206ee103c94150b104c5084671d`.
Completion requires its explicit PASS marker, matching hashes and sealed evidence
when tracing is enabled. Missing markers or timeout never pass by exit status alone.

The external bridge exposes timing-eligible candidates and delegates additional
cost/target work to Forge. It is not a complete legal-action catalogue. Opponent
private audit information must remain unavailable to pilot policies. The two new
Python pilot architectures still require native integration.

Private executable resources, decks, prior histories, models and results are
supplied separately and remain absent from this source-only branch. Native
constructed regression success does not approve a complete natural game.
