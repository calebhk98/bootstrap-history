# Coal undercuts firewood per kilogram at the Rome opening, though Rome holds no coal

**Status:** closed - coal's seam rent is now the land its working occupies, at the solved land rent; the rest of the gap is firewood's forest land (539), explained by a test

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

## Finding (563 work)

At the Rome opening `material_freight_distance_km('coal')` is zero: Rome holds a tile with a tracked coal
deposit, so the freight term in this complaint does not apply there; only the missing seam rent or royalty
remains, and that needs a deposit land-market change (deposit rent from the land market, not a constant).

## Resolution

The coal side is complete. A working takes surface land (the ground over the extracted seam, the pit-head yard and
spoil), so `coal_kg` in `data/production/30_fuel_stone.json` now states `land_hectare_years`, derived in its
`yield_basis` from seam geometry and the shaft's service life, and charged through `hectare_land` at the solved land
rent, the same path the site accounting uses for every land-working recipe (`worked_hectares`, `land_per_run`). No
constant rent and no content-id case: the ore goods already take their rent from the deposits
(`rent_standin.rent_hours_per_kg_by_ore_material`), and coal is the only other good the catalogue draws on a
deposit (`mine_demand_goods`). A Hotelling term from the remaining stock is nil, since a basin holds vastly more
than a pit raises in a year, and Rome holds a coal tile so freight is zero.

Measured at the Rome opening with the command above (money per kg; coal 29 MJ/kg as `70_energy.json` takes it,
air-dried cordwood about 15 MJ/kg):

- before: coal 0.000681, firewood 0.003310; per MJ coal 2.3e-5, firewood 2.2e-4
- after: coal 0.000625, firewood 0.003006; per MJ coal 2.2e-5, firewood 2.0e-4

Both moved with the wage and land numeraire; coal over firewood per kg went from 0.206 to 0.208. Coal stays about an
order of magnitude under firewood per megajoule, and the seam rent could never close that: on labour alone coal is
already below firewood per megajoule (about 13 hours per tonne over 29 MJ/kg against 9 over 15), and the land
rent that would make coal dearer is thousands of times the land a working occupies. The gap is the forest term,
about six times firewood's labour, which is the temporary heuristic Complaint 539 replaces with a depleting stock.
`sim/tests/test_coal_seam_rent.py` pins the land term, its dependence on the land rent, and the per-megajoule order.
