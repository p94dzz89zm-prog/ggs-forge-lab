# Explicit split-card identity binding

The Stage52 initial-state name differences are now explained with a partial,
reviewed identity manifest. Official Wizards articles identify Dusk // Dawn;
the TMNT release notes identify Double Jump // Flying Kick and both halves.
`reviewed_split_identities.json` freezes those explicit aliases and source links.

`card_identity_index.py` rejects ambiguous shared aliases, duplicate canonical
identities and missing primary provenance. It never infers aliases by splitting
an unfamiliar name. Counts accumulate under one physical-card identity: listing
both half names still counts as two cards, so normalization cannot conceal a
duplicate. Unknown names remain literal and never gain Oracle approval.

Using this manifest, all12 initial seats across the three preserved histories
match their frozen deck card-name multisets. The six short/full-name differences
(two per game) are closed as scoped identity bindings. The private certification
ledger retains the turn0 Oracle/format legality blocker and all gameplay audit
obligations. Full color identity, singleton exceptions, commander eligibility,
partner legality and effective format restrictions have not been independently
proved. The house history remains the leading candidate, with opening draws at
turn0/call30 as the earliest recorded gameplay obligation after setup proof.

No engine rules or pilot behavior changed. No new game, complete-game approval,
strategic result or training admission occurred. Stage47/48 remain untouched.

Primary references:
[Dusk/Dawn](https://magic.wizards.com/en/news/making-magic/storm-scale-kaladesh-and-amonkhet-2019-03-25),
[aftermath context](https://magic.wizards.com/en/news/making-magic/the-history-of-two-in-ones-part-2),
[Double Jump/Flying Kick](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes).
