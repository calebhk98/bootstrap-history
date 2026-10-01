# The silver per tonne of lead rests on one deposit's byproduct figure

**Status:** partly - every lead deposit in a silver district now carries that district's assay and the recipe is the weighted mean times the recoveries; the joint-cost split is in 410

The lead recipe's silver yield now equals what the single lead deposit that carries a silver byproduct implies (`britannia_lead`, a conf D worked example). The other lead deposits carry none, so a lead-output-weighted average over all of them would be about a third of the recipe's figure. Which is right is not settled: the empire totals in `data/world/resources.json` favour the higher figure, attested British lead is leaner in silver than the deposit's grade, and the recipe has one yield for all galena.

Silver also became much cheaper to produce (143), so money anchored to silver is worth much less in labour hours. Measure with `python3 sim/solve_prices.py --civ rome_100ad --why silver_kg`.

## What it would take

Give each lead deposit an assay (silver grade, or none) from sources, make the recipe's byproduct the output-weighted mean, and reconcile that with the empire totals; then cost ore dressing and split the joint batch by physical effort rather than demand-anchored value (see 139).

## Progress

- [x] Lead deposits in Italy, Hispania and Laurion now carry the silver grade of the silver deposit in the same district (the same galena); the Gaul and Germania deposit has no assay and counts as none. The output-weighted assay is about 4.0 kg of silver per tonne of lead contained, and the recipe takes 0.90 of it to the bullion and 0.92 through the cupel, 3.33 kg (the recipe's earlier figure, so no price moved from this). `sim/tests/test_silver_chain_physics.py` pins the agreement. The empire totals in `data/world/resources.json` give 2.5 kg per tonne, the same order.
- Still open: the assays are district grades, not measurements of each deposit; the joint-cost split is an accounting choice (see 305).
