# Coal undercuts firewood per kilogram at the Rome opening, though Rome holds no coal

**Status:** open

Found while closing 534. Measured at the Rome opening:

    python3 -c "from sim.tests.harness import sim; s=sim(civ='rome_100ad'); print({g: s._material_price_per_kg(g) for g in ('coal_kg','firewood_kg','lime_kg','lime_wood_kg','pozzolana_kg')})"

(takes about two minutes). Coal came out near 0.0007 per kg and firewood near 0.0034, about five times dearer, so
per megajoule coal is roughly an order of magnitude cheaper than firewood.

Trace (`data/production/30_fuel_stone.json`): `coal_kg` is labour only (miner and labourer hours, a small shaft
capital), priced at the pit head with no seam rent and no haul to the buyer. `firewood_kg` is nine labourer
hours plus `land_hectare_years` of forest at the solved rent, and that land term is about six times its
labour. The forest rent is itself a labelled temporary heuristic (see the LAND note on `wood_kg`). So neither
input is a data error in itself; the gap comes from (a) forest rent being large and heuristic, and (b) coal
carrying neither a seam land or royalty term nor freight from a coalfield Rome does not hold.

What it would take: price coal's seam land/royalty from the deposit, and freight tracked minerals to the buyer
in the recipe price (`material_freight_cost_per_kg` exists in `sim/engine/economy_freight.py` but the recipe
price does not use it for a good not produced where the buyer holds ground); then re-measure the command above.
Both are engine or economy changes, outside the data-only scope of 534.
