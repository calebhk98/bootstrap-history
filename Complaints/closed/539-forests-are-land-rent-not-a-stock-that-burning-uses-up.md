# Forests are land rent, not a stock that burning uses up

**Status:** closed - tiles hold standing timber that wood recipes fell and growth restores; fuel cost follows the haul to standing wood

Reference (an outside design note, not code-aware): smelting, pottery, lime, glass and baking all
burned wood or charcoal drawn from finite forest, which is the energy bottleneck of an ancient economy.

## What the code does

- `firewood_kg` (`data/production/30_fuel_stone.json`) is extracted from forest with
  `land_hectare_years` per tonne: it is priced from land rent and can be made in any quantity.
  `charcoal_kg` takes wood at a fixed ratio.
- Tiles carry `forest_fraction`, but it only limits arable and pasture (`sim/geography/food_land.py`,
  `food_pasture.py`). No tile holds standing timber that is cut down or regrows.
- The founder's coppice is a flat yield per hectare (`sim/engine/economy_mining.py`,
  `economy_materials.py`), not a stock, and not tied to tiles.
- `sim/world/stock_dynamics.py` covers living stock only.

## Why it matters

Deforestation around smelting districts, rising fuel prices and the move to coal are outcomes the
model should produce. With fuel as rent on unlimited land, a large iron industry costs no forest.

## What it would take

- Standing timber per tile (from the forest layer), cut by fuel and timber recipes and regrowing by a
  physical rate; coppice as a managed regrowth on the same stock.
- Fuel priced from the stock's scarcity and the haul from the nearest standing wood.
- Related: 534 (lime has no wood route), 536 (no stored land composition).

## Resolution

- `sim/geography/forest_timber.py`: a tile's forest hectares come from `forest_fraction` less the plough's
  share; its yearly increment is net primary production times the stem share of production (parameters in
  `data/world/geography/parameters/forest.json`, each with a source and confidence); its full stock is the
  increment times the years of increment a stand holds standing. The saved ledger is
  `state.economy.forest_felled` ({tile: tonnes felled}); a missing tile is untouched.
- `sim/engine/economy_port_timber.py`, reached from `economy_port_sites.py`: a recipe whose `extracted_from`
  is `standing timber` (`wood_kg`, `firewood_kg`) is limited per tile to the runs the standing wood allows. A
  tile with no forest, or one cut bare, has no limit, so the recipe does not run there. As the felled area
  spreads the haul to standing wood lengthens (a disc around the settlement, at the cheapest land carrier's
  crew hours per tonne-km), which cuts the wood a run delivers and so raises its cost. What the firms fell is
  drawn from the tile each year and the ledger then regrows at the increment, through the same site
  mechanism the ore deposits use.
- The founder's coppice follows the same increment: `CHARCOAL_PER_HA` is now the home forest's increment over
  the wood-to-charcoal ratio, not a flat figure.
- Tests: `sim/tests/test_forest_timber_stock.py` (stock, cost and room as it runs down, no forest no firewood,
  regrowth at the sourced rate, felling drawn from a tile) and `test_forest_timber_whole_game.py` (save and
  load round trip).
- The yearly cost is one pass over the economy's tiles with per-tile figures cached on the map; measure with
  `python3 -c "import time; from sim.tests.harness import sim; g=sim(); t=time.process_time(); g.step(); print(time.process_time()-t)"`.
