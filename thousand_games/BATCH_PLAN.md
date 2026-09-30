# 1,000-game comparison

Status: running; do not interpret partial results as the final comparison.

Exactly 1,000 scheduled attempts: 232 current-deck baseline attempts plus 48 attempts for each of the 16 trial lists in manifest.json. Four seats per seed; trial comparisons use 12 fresh seeds each, starting at 20300930. Every trial seed/seat has a corresponding baseline attempt. Baseline alone also has 46 additional seeds. Jobs interleave versions before additional baseline games. The engine performs its normal shuffling. Matched seeds do not guarantee identical draws after changing deck contents.

Engine: installed Forge 2.0.15; four workers; 240-second engine timeout plus 90-second outer allowance. Existing deck and engine hashes are recorded in run_metadata.json. Deck files are unchanged. Nine runner tests passed.

Primary comparison: paired differences in GGS victory indicators for games where both versions complete. Timeout and error frequencies, all-attempt bounds, candidate card exposure and commander recast/trigger observations are reported separately. A larger sample cannot fix poor AI play or unknown opponent upgrades. Fifty-eight baseline seed blocks and twelve seed blocks per trial are not equivalent to 1,000 independent measurements per card. Missing outcomes can bias comparisons. No human-pod win rates are inferred.

The supplied Jaymie list is used; Gabe and Destyn remain stock precon proxies. Trial swaps are diagnostic; none becomes an approved mainboard change merely from a partial tally.

A duration parser bug was corrected before this batch: engine_ms now retains the full logged integer. Old winner classifications were unaffected.
