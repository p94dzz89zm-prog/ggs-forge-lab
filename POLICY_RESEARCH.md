# Bounded policy research and card evidence

`DecisionWeights` exposes six bounded coefficients in the existing ninjutsu
heuristic. Without overrides, it reproduces each legacy profile's coefficients.
Commander-preservation, already-lethal connections, legal costs and timing
guards stay outside this score. This is not a general action learner.

`policy_search.py` evaluates vectors against common seeds and seat rotations.
It explores a bounded vector, then mutates a parent selected from completed,
integrity-passing outcome feedback. Withheld feedback cannot influence the
posterior. The tested pilot is never replaced automatically by a search winner.
Small paired samples cannot prove strength or coverage of all tactics.

`research_tools.py search` queries a pinned full Oracle snapshot. Its full-text
index stores both faces, legality, color identity and definition coverage. A
matching engine definition establishes presence, not correct implementation.
Regex role tags are retrieval aids, not gameplay scores. Cards without engine
definitions remain visible as untested candidates.

`research_tools.py watch` appends observations from complete canonical records
with one selected-seat audit. It deduplicates repeated priority snapshots within
a turn, retains engine provenance and separates deck variants. Empty boards,
held cards and absent commanders are observations, not causal card-cut verdicts.
The first MAIN1 snapshot can precede a perfectly reasonable deployment.

The October 15 snapshot contains 38,751 Oracle records; 18,563 are marked legal
for Commander in Grixis identity. The evaluated 100-card list resolves fully.
There are 84 eligible records with no exact/front-face engine definition match.
These figures describe that snapshot and installed engine, not every future
release. Knowing rules text is not equivalent to having played every card.

The first three-vector comparison produced the same loss/win pattern on both
paired seeds. No vector was promoted. Further work should emphasize positions
that distinguish legal alternatives and diagnose decisions before attributing
losses to card slots. Current opponents remain archived deck proxies and stock
Forge pilots; this does not establish error-free piloting of any pod deck.
