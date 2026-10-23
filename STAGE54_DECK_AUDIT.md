# Independent Commander deck construction audit

All twelve frozen historical decks pass construction checks against the
October23,2026 external Oracle mirror and Wizards' current Commander ban list.
The reports resolve329 distinct requested identities and retain Oracle IDs,
selected printing IDs, source hashes, original deck hashes and every result.
The frozen deck files were not modified.

The verifier independently checks100cards, commander eligibility/pairing,
combined color identity, basic-land-type restrictions, canonical singleton
counts, basic-land and explicit copy exceptions, paper-format legality and the
42named Commander bans. Split/adventure/DFC faces bind to physical card identity;
full card names take precedence over coincidentally named alternate faces.
Non-playable art cards cannot shadow actual cards. Leonardo's activated ability
contributes all five colors to his color identity. Legendary Vehicles/Spacecraft
with power/toughness boxes follow CR903.3 in the September25,2026 rules.

A newly verified punctuation binding connects the frozen Ratonhnhaké:ton name
to the catalog's modifier-letter-colon spelling under its canonical Oracle ID.
Future selected reprint dates are not mistaken for the first release of an
existing card. These repairs affect the independent audit, not Forge gameplay.

The data source is Scryfall's full public Oracle mirror, downloaded with GET and
matched locally. An attempted name-derived batch lookup was rejected by approval
review before a response; it was not retried. No private deck names were sent
through the successful catalog-download workflow. Initial dependency/schema and
catalog-resolution failures are retained with the private evidence.

Current-snapshot construction passes do not establish a publisher-verified
historical Oracle/banned-list snapshot for October20. Historical deck legality,
opening-state causality and complete-game certification remain unapproved.
Zero historical events gain complete independent certification from these
construction checks. No game or training was run. Stage47/48 remain unchanged.

Primary rules sources:
[Comprehensive Rules](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt),
[Commander ban list](https://magic.wizards.com/en/banned-restricted-list),
[TMNT partner/color rulings](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes),
[Ratonhnhaké:ton](https://magic.wizards.com/en/news/feature/assassins-creed-release-notes).
