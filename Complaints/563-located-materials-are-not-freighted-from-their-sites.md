# Located materials such as pozzolana are not freighted from their sites

**Status:** open

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
