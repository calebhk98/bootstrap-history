# Rome's bonded share drifts below its sourced range within two years

**Status:** open

Found rewriting `rome_slave_stratum` (640). Rome seeds its bonded stratum at its declared share of the people; after
two simulated years the share is below the low end of the range its source note gives (Scheidel 2005, cited in
`data/civilizations/rome_100ad.json`). The rewrite cites bonded births and migration as the drift; not traced.

Measure: the bonded stratum's members over all strata after `close_years(game, 2)` on `rome_100ad` (the slow check in
`sim/tests/test_rome_slave_stratum.py` was moved to a comment proposing an ensemble check).

What it would take: find which rule moves the bonded share that fast (births, deaths, manumission, migration of
strata), test it as a function, and replace the old check with an ensemble baseline check over seeds against the
sourced range (CLAUDE.md 4.2).
