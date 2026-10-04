# The silver per tonne of lead rests on one deposit's byproduct figure

**Status:** partly - silver per tonne of lead is now an assay per lead deposit and no silver is counted twice; the assays are still generic or unverified, and the joint-cost split is in 305

The lead recipe's silver yield now equals what the single lead deposit that carries a silver byproduct implies (`britannia_lead`, a conf D worked example). The other lead deposits carry none, so a lead-output-weighted average over all of them would be about a third of the recipe's figure. Which is right is not settled: the empire totals in `data/world/resources.json` favour the higher figure, attested British lead is leaner in silver than the deposit's grade, and the recipe has one yield for all galena.

Silver also became much cheaper to produce (139), so money anchored to silver is worth much less in labour hours. Measure with `python3 sim/engine/solve_prices.py --civ rome_100ad --why silver_kg`.

## What it would take

Give each lead deposit an assay (silver grade, or none) from sources, make the recipe's byproduct the output-weighted mean, and reconcile that with the empire totals; then cost ore dressing and split the joint batch by physical effort rather than demand-anchored value (see 139).

## Progress

- [x] Lead deposits in Italy, Hispania and Laurion now carry the silver grade of the silver deposit in the same district (the same galena); the Gaul and Germania deposit has no assay and counts as none. The output-weighted assay is about 4.0 kg of silver per tonne of lead contained, and the recipe takes 0.90 of it to the bullion and 0.92 through the cupel, 3.33 kg (the recipe's earlier figure, so no price moved from this). `sim/tests/test_silver_chain_physics.py` pins the agreement. The empire totals in `data/world/resources.json` give 2.5 kg per tonne, the same order.
- Still open: the assays are district grades, not measurements of each deposit; the joint-cost split is an accounting choice (see 305).

Related: 284, 333, 342, 343, 344, 349.

## Update (silver-gold-data-fixes)

- Each lead deposit carries its own assay in kg of silver per tonne of lead (`kg_per_tonne_of_primary_metal` in `data/world/deposits.json`): Wood 2022's 0.2 wt% galena (opened) for the Iberian, British and Italian deposits, Laurion 2.0 from a search figure (not verified, conf D), Gaul and Germania none. The recipe is the output-weighted assay times the recoveries; `python3 -c "from sim.engine.prices import _default_production_entries as e; print(e()['lead_kg']['outputs'])"` prints it.
- The silver the lead raises is subtracted once from the empire total (`deposits.empire_output_net_of_byproducts_tonnes_per_year`); the silver-only deposits split the remainder, and the solver's rent for silver is set against that remainder. Pinned in `sim/tests/test_silver_gold_routes.py`.
- Still open: no working is assayed (the Iberian, British and Italian figure is the generic galena value); Laurion's 2.0 needs the Wood et al. text; the silver-only deposits keep their old district grades and the shares of the silver-only total are placeholders; the joint-cost split (305).
