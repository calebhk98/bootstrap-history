# Located materials such as pozzolana are not freighted from their sites

**Status:** closed - source_tiles places a located material through its entry goods; pozzolana is freighted from its nearest site and its multiplier is gone

`Geography.source_tiles` (`sim/geography/geography.py`) returns tiles only for the tracked mineral deposits
(`_shares_by_tile`), so `material_freight_distance_km` in `sim/engine/economy_freight.py` returns nothing for a
located material such as `pozzolana`, and `pozzolana_kg` is priced as if dug where the buyer stands. The only
distance effect is the `cost_multiplier` in `data/world/geography/located_materials/located_materials.json`,
which `Geography.material_cost_factor` applies to the unlocking tech node's project cost, not to the good. For
pozzolana that multiplier is a labelled freight stand-in (`retire: Complaints/563`).

What it would take: have `source_tiles` also return the tiles of a located material (`_material_tiles`), so that
the freight charge on `pozzolana_kg` (heavy, bulk, sea or river) follows from the route to the nearest of its
places; then drop pozzolana's `cost_multiplier` to 1 (or remove it) and re-measure the price of
`concrete_pozzolanic_kg` at the Rome, Han and Norse openings. Engine and geography code; not a data change.

## Resolution

`Geography.source_tiles` now also returns the places of the located material whose entry lists the good in a
`goods` field (`pozzolana` lists `pozzolana_kg`), so `material_freight_distance_km`, the freight cost and
`material_carriage_per_tonne` charge the route from the nearest site, as for a tracked mineral. Pozzolana's
`cost_multiplier` is 1 and its heuristic label is removed. A buyer holding a site (Rome) pays no freight; Norse
and Han buyers pay carriage per kilogram that follows the route length. Test:
`sim/tests/test_located_material_freight.py`. Measure with
`python3 -c "from sim.tests.harness import sim; s=sim(civ='norse_900ad'); print(s.material_freight_distance_km('pozzolana_kg'))"`.
