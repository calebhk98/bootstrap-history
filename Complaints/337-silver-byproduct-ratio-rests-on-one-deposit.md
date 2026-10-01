# The silver per tonne of lead rests on one deposit's byproduct figure

**Status:** open

The lead recipe's silver yield now equals what the single lead deposit that carries a silver byproduct implies (`britannia_lead`, a conf D worked example). The other lead deposits carry none, so a lead-output-weighted average over all of them would be about a third of the recipe's figure. Which is right is not settled: the empire totals in `data/world/resources.json` favour the higher figure, attested British lead is leaner in silver than the deposit's grade, and the recipe has one yield for all galena.

Silver also became much cheaper to produce (143), so money anchored to silver is worth much less in labour hours. Measure with `python3 sim/solve_prices.py --civ rome_100ad --why silver_kg`.

## What it would take

Give each lead deposit an assay (silver grade, or none) from sources, make the recipe's byproduct the output-weighted mean, and reconcile that with the empire totals; then cost ore dressing and split the joint batch by physical effort rather than demand-anchored value (see 143).
