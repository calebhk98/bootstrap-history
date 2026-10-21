# Rome's bonded share has no ensemble check against its sourced range, and captives and imports are not a modelled supply

**Status:** partly - the births drift is fixed; the ensemble check over the sourced range is still to write, and captives and imports as a supply are not modelled (see Research needed)

Found rewriting `rome_slave_stratum` (640). Rome seeds its bonded stratum at its declared share of the people; after two
simulated years the share fell below the low end of the range its source note gives (Scheidel 2005, cited in
`data/civilizations/rome_100ad.json`).

**What was wrong and is fixed.** `BONDED_BIRTH_SHARE`, a labelled heuristic with no source, trimmed bonded births to a
fraction of the ordinary rate. Scheidel 2005 ('Human Mobility in Roman Italy, II: The Slave Population', JRS 95: 64-79, p. 75,
read in the Gwern.net copy) writes: "Bagnall and Frier have found that the average fertility of slave women was similar to
that of all women." The constant is deleted; a bonded stratum has the stratum's own birth rule (rule test in
`sim/tests/test_rome_slave_stratum.py`: a fed bonded stratum grows at the rate a fed free one does). The first-year famine
is fixed too (`true_up_keep`).

**What is left.**

1. An ensemble check over seeds of the bonded share after a few years against Scheidel's eight to fifteen per cent range
   (CLAUDE.md 4.2: validation, not a target). Measure the share with the bonded stratum's members over all strata after
   `close_years(game, 2)` on `rome_100ad`; the old single-run check was moved to a comment in `test_rome_slave_stratum.py`.
2. Captives and imports as a supply. Scheidel (pp. 77-78) gives no observed import rate: he derives imports as the output of
   attrition from the target stock (urban slaves lose 0.75 per cent a year to excess mortality, 1.25 to 1.75 per cent with
   manumission; a 1.2 million stock needs "anywhere between two and four million" imports over two centuries). A flow set from
   that would pin the share, the typed inflow CLAUDE.md 4.3 forbids, so nothing is added.
3. A residence-driven mortality difference. Scheidel draws equal fertility from Egyptian census returns and adds "Yet we cannot
   know how this compares to conditions in Roman Italy" (p. 75); p. 69 allows that "slave fertility may well have fallen below
   replacement levels", and p. 75 names "above-average mortality in cities and rural gravia loca" as the larger constraint.
   That disadvantage came from urban and malarial residence, not legal status, which the stratum model does not carry.

**Research needed.** The supply side of Roman bondage as events the model can generate: captives by campaign (which
campaigns, how many taken, what share sold), and a price-driven trade (prices of slaves by age and skill against the cost of
rearing one, sources for Roman Egypt sale contracts, Scheidel's and Harris's estimates, and how piracy and the frontier
trade supplied the market). The model aims at realism: captives come from the war mechanism (484) and trade from merchants,
not from a typed inflow. See also 644 (the owners' sale rule).
