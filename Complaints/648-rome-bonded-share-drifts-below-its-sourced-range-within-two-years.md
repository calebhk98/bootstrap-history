# Rome's bonded share drifts below its sourced range within two years

**Status:** fixed for the births drift; captives and imports as a supply are not modelled (see below); the ensemble check over the sourced range is still to write

Found rewriting `rome_slave_stratum` (640). Rome seeds its bonded stratum at its declared share of the people; after
two simulated years the share is below the low end of the range its source note gives (Scheidel 2005, cited in
`data/civilizations/rome_100ad.json`). The rewrite cites bonded births and migration as the drift; not traced.

Measure: the bonded stratum's members over all strata after `close_years(game, 2)` on `rome_100ad` (the slow check in
`sim/tests/test_rome_slave_stratum.py` was moved to a comment proposing an ensemble check).

What it would take: find which rule moves the bonded share that fast (births, deaths, manumission, migration of
strata), test it as a function, and replace the old check with an ensemble baseline check over seeds against the
sourced range (CLAUDE.md 4.2).

## Update: births

The first-year famine is fixed (`true_up_keep`). The slow decline came from `BONDED_BIRTH_SHARE`, a labelled heuristic
with no source that trimmed bonded births to a fraction of the ordinary rate against the ordinary death rate. Scheidel
2005 ('Human Mobility in Roman Italy, II: The Slave Population', JRS 95: 64-79, p. 75, read in the Gwern.net copy this
session) writes: "Bagnall and Frier have found that the average fertility of slave women was similar to that of all
women." The constant is deleted; a bonded stratum now has the stratum's own birth rule (rule test in
`sim/tests/test_rome_slave_stratum.py`: a fed bonded stratum grows at the rate a fed free one does).

## Still open: captives and imports

Scheidel (same paper, pp. 77-78) does not give an observed import rate. He derives imports as the output of attrition:
urban slaves lose 0.75 per cent a year to excess mortality, 1.25 to 1.75 per cent with manumission ("For computational
purposes, I will put annual decrease in the cities at 1.75 per cent"), against a Caribbean mean natural decrease of
0.419 per cent, and a target of 1.2 million slaves needs "anywhere between two and four million" imports over two
centuries ("attrition rates of 1.5 per cent and 3.1 million imports, 2 per cent and 3.8 million"). Those attrition
rates come from urban and malarial residence, not from legal status ("This disadvantage did not arise from their legal
identity per se"), which the stratum model does not carry. An import mechanism through the foreign economies and the
merchant path needs a source for how many captives war and trade delivered, and the paper gives it only as a
back-calculation from the target total; a flow set from that would pin the share, which is the typed inflow CLAUDE.md
4.3 forbids. Nothing is added until a source for the supply side (captures by campaign, price-driven trade) is read.

What would close it: an ensemble check over seeds of the bonded share after a few years against Scheidel's eight to
fifteen per cent range (validation, not a target), and a supply mechanism once a supply-side source is opened.

Caveat on the births source (checked against the same PDF, p. 75): Scheidel draws the equal-fertility finding from the
Egyptian census returns and adds "Yet we cannot know how this compares to conditions in Roman Italy"; p. 69 allows
that "slave fertility may well have fallen below replacement levels", and p. 75 names "above-average mortality in
cities and rural gravia loca" as the larger constraint. Equal birth rates are the sourced default; a residence-driven
mortality difference is the open part.
