# Food potential: shelf zones overlap, cold pasture is high, no slope, no competition

**Status:** closed - every gap is built: the shelf layer is partitioned by nearest land (it sums to the physical shelf), cold pasture follows a growing season with winter fodder, slope and forest limit cropland, wild grazers share the grass, land cleared from forest is cropped in a shifting-cultivation rotation, a saved wild stock is drawn by hunting and regrows, and fishers and hunters bound the food from the water and from game by their hours (`sim/labour/food_gathering.py`). Tests: `sim/tests/test_geography_food_gaps.py`, `test_geography_wild_stock.py`, `test_food_gathering_labour_cap.py`; `test_wild_stock_whole_game.py` is a slow topic. Measure with `python3 -c "from sim.geography import api; print(api.food_potential('<tile>'))"`.

`sim/geography/food_capacity.py` gives each tile's sustainable food by source from physical layers. Known gaps, each measurable with `python3 -c "from sim.geography import api; print(api.food_potential('<tile>'))"`:

- Marine fishing reads `shelf_area_km2`, which is the shelf within a zone of the tile's cell plus one cell side around its land, so neighbouring zones overlap and are not additive. A small-land coastal tile can get more marine food per km2 of land than its crops (cold North Sea and Baltic tiles; desert coasts on the Red Sea and Gulf). A shelf layer partitioned between tiles, or a fishing-grounds cap per tile, would fix it.
- Herding on subarctic and tundra tiles (Koppen Dfc, ET) comes out near one person per km2: the grass formula ignores the short season and winter fodder. It needs a growing-season or snow-cover layer.
- No slope or ruggedness limit on arable or pasture land; `ruggedness_index` and `elevation_std_m` exist and are unused by food.
- Wild grazers and herds draw on the same grass without competing; hunting does not deplete its stock; forest is not subtracted from cropland.
- Tropical rainforest cropping (Af) is low next to savanna (Aw): the crop water envelope's wet side and the class arable fraction.
- No labour cap: a fisher or hunter feeds a bounded number of people, which belongs to the labour model once food reads geography.
- Most coefficients are labelled heuristic in `data/world/geography/parameters/food.json` (measure with `python3 -c "from sim.geography import map_source, parameters; print(len(parameters.heuristics(map_source.load_map())))"`).

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 412 (`closed/412-deposits-have-no-geology-layer.md`): deposits have no geology layer; needs external data (owner decision on source).
- 413 (`closed/413-sea-routes-have-no-land-mask-and-few-lanes.md`): sea routes have no land mask and few lanes.
- 378 (`closed/378-reach-bands-not-calibrated-against-tile-geometry.md`): reach bands are not calibrated against tile geometry; re-deriving them moves fingerprints.
