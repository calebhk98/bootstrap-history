# Forests are land rent, not a stock that burning uses up

**Status:** open

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
