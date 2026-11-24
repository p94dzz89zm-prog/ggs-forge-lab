# Independent Commander pilots, milestone 1

The executable decision window is the house opening declaration. Each of four seats can keep or take an available full seven-card redraw. The native service handles round order, the third-redraw cap, shuffling, drawing and the transition to first priority. A clean policy comparison begins with identical parameters in all four identities. Seat, deck name and pilot identity do not enter the scorer. A manually edited parameter is an engineering control.

## Architectural assessment

| Component | Reused behavior | Current limit |
| --- | --- | --- |
| Forge 2.0.15 and the private SharedOpening overlay | Real controller callback, actor-local opening features, house mulligan service, original approved deck files, first-priority stop | A broader bridge candidate can still lack complete targets or payment. General actions require independent enumeration and engine revalidation. |
| Existing Python pilot_architectures | LegalOffer presents revision, actor and opaque alternatives. Selection identifies the chosen alternative. The fixture uses step and revalidates at execution. | The generic interface alone cannot prove that an upstream offer is legal. |
| Historical decision tape, priority/payment audits, prospective opening capture | Sealed originals and existing Java RNG/permutation helpers. The new verifier handles sequential deck initialization and the complete captured mulligan round. | An opening receipt covers its named scope. Historical command-zone payment and broader full-game legality remain on the reliability track. |
| Private reliability/play, referee and native replay | Restricted four-seat producer, independent referee, prior restricted native certificates | The restricted card pool does not generalize to the approved pod. |
| Existing validation/strategic pilots, shared opening heuristic, adaptive policy and population/evaluation tooling | Existing actor projections, matched allocations, seed rotation, scoring ideas, evidence admission, prior policy scaffolds | Fixed personalities and the validation pilot are controls. This milestone has no outcome optimizer, learned value function or automatic promotion. |

## Decision interface and information flow

The trusted adapter constructs an opening LegalOffer and passes an allowlisted object down one pipe. Each worker is a fresh Python interpreter with its own seed, immutable policy version and actor history. Its only private input is a summary of its own seven cards and public commander access. The worker receives zero library identities or shuffle RNG values. The parent retains all-seat referee information in a separate directory. The threat model covers trusted pilot implementations running on one local user account. Third-party or adversarial policy code requires OS-level isolation before use.

An offer has exactly five fields: game-window name, actor seat, seat-local revision, legal tokens, and the observation. The observation contains only land-option count, cheap-spell count, and a cheap-commander flag. Seeding uses a stable SHA-256 derivation from policy, actor-visible history, mode and decision seed. Certification selects the highest score with a reproducible tie break. Exploration can sample actions within one heuristic point of the top score. Both modes score the same two alternatives exactly once, with no search or rollout. Each game uses four new workers and four dedicated pipes. Revisions are scoped to that worker session.

Only the native callback can convert a reply into a game action. It matches the window, actor, revision and token. A bad reply interrupts the run. Private referee verification compares the selections with actual native results, independently reconstructs seeded shuffle permutations, round order and seven-card hands, and separately checks the actor summaries against pinned card records. The result directory is created exclusively. Incomplete directories retain failures. Archive raw trials privately.

## Version and experience formats

Each identity has a separate SQLite version store. A content-addressed snapshot contains algorithm, schema, signed integer coefficients and parent digest. Rollback selects an existing digest for that identity. Scratch or held-out results cannot write weights. A new version may be supplied for a controlled experiment.

Each pilot records its configuration and one JSONL row per decision. Rows contain actor-visible inputs and legal choices, content hash of the policy, decision seed and mode, scores and contributing terms, exploration margin, strongest rejected action, and choice. Each verified per-seat receipt binds the journal hash and executed declarations. Outcome and retrospective assessment are nullable. The lesson renderer reconstructs the exact calculations before explaining them. Fixture branching replays a prefix and executes an alternative through the same legality gate. A divergent natural game after a rejected alternative needs a separate fork and fresh verification.

## Reproduction

On either source checkout run:

```sh
python -m unittest -v test_independent_opening_pilots
python -m pilot_m1.benchmark
```

On the private checkpoint checkout, restore the original Forge resources, four approved deck inputs, pinned reference generation, and shared-opening.jar. Apply the source-only files and keep the private reliability code. Build with Java 21 and use the frozen private allocation and new output directory.

```sh
python -m pilot_m1.build shared-opening.jar independent.jar PLAN.json
python -m pilot_m1.native --help
python -m pilot_m1.lesson RUN/workers/pilot-0
```

The private evidence contains the exact allocation, invocations, hashes, position comparisons and failure controls. The intentional first-priority stop produces an interrupted Forge game. A verified opening receipt is required for the opening evidence. A simulator exit code is insufficient.

## Measurement and roadmap

1. **Opening interface.** Replay identical native inputs, swap or roll back a single test policy, rotate all policy identities on the same opening positions, and compare journal bytes. Count distinct openings separately from rotations and repeats. Keep seed and deck provenance in the referee.
2. **Independently certified interactions (A).** Extend the same actor interface to one priority, mana-payment or attack window with complete alternatives. Reject stale capabilities, verify revision, actor, costs, targets and state changes, then verify them again with an independent checker. Bind public-card identities and conceal nonpublic state from both ranking and lookahead.
3. **Complete independent turns (B).** Add limited equal-node-budget lookahead and seat-local observable threat features. Verify a whole legal turn against Oracle, rulings, comprehensive rules and independent tests. Add counterfactual positions and label estimated and observed consequences separately.
4. **Independent four-player games (C).** Close full-pod reliability obligations through elimination, including replacement order, passes, hidden choices and SBAs. Preserve unsupported cases as failures.
5. **Independent learning (D).** Give each pilot an experience buffer and trainable policy/value head. Reopen bound verification evidence before any update or replay sampling. Quarantine illegal or incomplete trajectories, never learn from held-out openings, and maintain immutable policy histories. Opponent models use observed actions only. Freeze promotion opponents before training.
6. **Certified comparisons (E).** Compare each candidate to its predecessor, a fixed baseline, other current agents, and a diverse frozen historical population on unseen deals and multiple decks. Rotate seats and deck assignments. Report wins, placement, legal offers and execution accuracy, mulligan quality, mana use and sequencing, combat and interaction timing, threat assessment, recovery and missed lethal. For wins/placements report matched differences and intervals clustered on the independent opening, retaining failures and the number of usable blocks. Promote only after prespecified thresholds, repeatability and independent legality checks.

Apex v1.12 is one equally budgeted evaluation deck. Later fixtures should separately exercise fresh attackers and combat access, Dragon creation and conversion, entry triggers and replacement order, Treasure and Magda choices, color sequencing, extra combats, lethal and recovery through wipes. Crossing those roles in held-out positions tests when one offensive package can take over from another. Each interaction needs its own Oracle/rulings binding. Current results measure opening choices only.
