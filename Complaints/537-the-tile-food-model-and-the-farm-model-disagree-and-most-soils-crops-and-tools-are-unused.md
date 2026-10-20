# The tile food model and the farm model disagree, and most soils, crops and tools are unused

**Status:** partly done. The tile crop capacity and the farm model's land and quality now read one yield (stage 1 and 2 below); the economy's land base, soils, crops and tile weather are still apart (what is left, below).

Reference (an outside design note, not code-aware): carrying capacity is arable land times the
planted share (fallow by rotation, none under flood silt) times gross yield (soil and crop) net of
seed and storage loss, in calories; tools set the hectares one farmer works, not the yield per hectare.

## What the code does

There are two models, and they do not read each other:

- **Tile model** (`sim/geography/food_capacity.py`, `food_crops.py`, parameters in
  `data/world/geography/parameters/food.json`): a calorie ceiling per tile from arable area, a fixed
  cropped share, a reference yield times climate and tile fertility, a river irrigation multiplier,
  seed and loss fractions. Only settlement spread reads it; it does not cap population.
- **Farm model** (`sim/world/agriculture*.py`, `farming_technique.py`, run from the engine): national
  rotation, crop, soil and toolkit, with spoilage and granaries in `agriculture_storage.py`.

Within the farm model:

- Soils (`agriculture.py`): chernozem, desert, arctic and mountain are defined, but the engine uses
  only `DEFAULT_SOIL` (`agriculture_labour.py`), so soil never varies. There is no alluvial, podzol or
  steppe soil and no heavy clay that needs a heavy plough.
- Rotations: `NILE_FLOOD_RECESSION` (near-zero fallow) is defined in `agriculture.py`, but outside
  tests nothing selects it, and nothing ties it to floodplain land. The tile model gives river land no
  fallow on its own. Each model handles the Nile its own way.
- Crops: `RICE` is defined but no tree node adopts it; there is no maize (Complaint 489) and no
  irrigated wheat separate from dry wheat.
- Tools: yield per hectare and hectares per worker are separate (`agriculture_yield.py`,
  `agriculture_labour.py`), which is right. The toolkits run from the ard and oxen to the mechanical
  reaper; there is no hoe tier below the ard (Mexica, early societies) and no tractor above.
- Weather: one draw per weather cell, correlated in space (`core.py`), but pooled to one national
  multiplier before farming and demography read it, and with the default soil's spread only.

## What it would take

- One food model: the farm model run per tile (or per the land classes of 536), with rotation,
  soil and irrigation from the tile, and the tile ceiling as its output, not a second estimate.
- Soils from map data with a heavy-clay class that only a heavy plough opens.
- Crops adopted by the tree for rice and maize; a hoe toolkit.
- Tile weather applied to the tile's own harvest.
- Related: 489 (population national, food check partial), 513 (farm labour sized exactly).

## Second note from the same source

- Irrigation on a river strip is free and permanent (`food_irrigation_*` in
  `data/world/geography/parameters/food.json`); no canals silt up or need clearing labour, so a
  state that stops maintaining them loses nothing.

## Measured before the change (rome_100ad, `PYTHONPATH=. python3 -W ignore` probe of the opened game)

- Tile view, crops, over the 88 held tiles: about 115 thousand giga-kcal a year. Farm model's gross harvest on its own cleared
  land: about 57 thousand giga-kcal. Per tile, the tile view over the farm model's harvest on the same arable hectares
  ranged from 0.77 to 1.29 (the two disagreed on yield per hectare, 1000 kg against 742 kg gross, and on the cropped share,
  0.6 against the rotation's 0.5).
- Land the two models counted: 105 million hectares of arable ground in the tile view (slope and forest limits applied)
  against a farm ceiling of 136 million (raw arable share), and the farm ceiling counted cropped hectares against held
  hectares, ignoring fallow. Farm quality was fertility only (mean 0.989): climate and river water never reached it.

## What was done

- Stage 1: `sim/geography/food_crops.py` keeps only the tile's side: `crop_site(tile, open_field_cropped_share)` gives the
  hectares cropped in a year (fallow rotation, shifting cultivation on cleared forest, flood land) and the mean yield factor
  of a cropped hectare (soil fertility, temperature and rain suitability, river water) against the reference field. What a
  cropped hectare gives (harvest, seed, storage loss, energy) comes from the farm model through
  `sim/world/agriculture_tile.py` `crop_technique(technique)`, so the actor's crop, tools and rotation all reach the tile
  view. Deleted: the parameters `food_crop_reference_yield`, `food_crop_cropped_share`, `food_crop_seed_fraction`,
  `food_crop_loss_fraction`, `food_crop_grain_kcal_per_tonne`. Seed is now kilograms per hectare sown, not a share of the
  harvest, so land that yields less than its seed nets nothing. Without a technique the tile view has no crop source.
  Technique-free views (`settlement`: where people live, what a colony can feed) use the default technique, set once in
  `sim/engine/geography_port.py`.
- Stage 2: the farm model's ladder and ceiling come from the same `crop_site` (`land.territory_cropland`; `territory_farmland`
  deleted). The ceiling is cropped hectares, quality is the yield factor, so soil, climate and river water vary the farm per
  tile. `Sim.farm_sites()` (`sim/engine/food_supply.py`) is the seam tests replace.
- Test: `sim/tests/test_one_food_model.py` checks every held tile's crop kcal against `agriculture.gross_harvest_kg` on the
  tile's own cropped hectares and yield factor, under the default, a better plough and a three-field rotation.
- Bounds in `test_geography_food_gaps.py` that were calibrated on the deleted parameters were restated (fishing against crops:
  0.15 to 0.25 of the crop energy, because crops now follow the farm model's yield and two-field share; the two rainforest tests
  now read `crop_site`, which does not depend on seed). Review these.

## What is left

- The agent economy's own land base: `sim/economy/land_market.py` counts `land_area * arable_fraction` (raw, no slope or forest)
  and `TileSpec.fertility` (`sim/economy/tile_costs.py`, built in `sim/engine/economy_port_setup.py`) is soil fertility only,
  used for households' own plots and rent. Giving `TileSpec` geography's `arable_hectares` and the crop yield factor would make
  the economy's farms read the same land; market farm producers still get only the pooled weather as their `yield_factor`.
- `land.py`'s rent margin (`margin_outcome_for_civilization`, `cultivable_land_for_civilization`) is a third land ladder on raw
  arable ground.
- Soils beyond the climate-class fertility (heavy clay a plough cannot open, podzol, alluvium: Complaint 543), the engine's
  single `DEFAULT_SOIL`, rice and maize adoption, a hoe toolkit, per-tile weather applied to each tile's harvest (the economy
  and farm still take one pooled draw), irrigation as a work that silts up.
- The farm ceiling is set once from the starting rotation; a rotation that fallows less does not raise it.
- The farm model still runs nationally for labour, clearing and the granary; demography eats what households ate (Complaint 549).
