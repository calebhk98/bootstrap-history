# The tile food model and the farm model disagree, and most soils, crops and tools are unused

**Status:** partly done. The tile crop capacity and the farm model's land and quality now read one yield (stage 1 and 2 below); the economy's land base, soils, crops and tile weather are still apart (what is left, below).

Reference (an outside design note, not code-aware): carrying capacity is arable land times the
planted share (fallow by rotation, none under flood silt) times gross yield (soil and crop) net of
seed and storage loss, in calories; tools set the hectares one farmer works, not the yield per hectare.

## What the code did before the stages below (historical; "What is left" is the current state)

There were two models, and they did not read each other (re-check each bullet before acting; stages 1 to 3 changed the tile and farm yield, land and quality):

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
- Crops: `RICE` is defined but no tree node adopts it; there is no maize and no
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
- Related: 603 (population per region), 513 (staple price near satiation).

## Second note from the same source

- Irrigation on a river strip is free and permanent (`food_irrigation_*` in
  `data/world/geography/parameters/food.json`); no canals silt up or need clearing labour, so a
  state that stops maintaining them loses nothing.

## Measured before the change (historical; rome_100ad, `PYTHONPATH=. python3 -W ignore` probe of the opened game)

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
- Effect on rome_100ad (`PYTHONPATH=. python3 -W ignore`, six years of `run_year`): the farm's quality at opening goes from
  0.989 to 1.050 (the cleared best ground includes flood-watered land) and the farm share of hours from 0.367 to 0.340, so
  the pinned figures in `test_farm_edges.py` `test_ordinary_land_is_farmed_as_before` were re-recorded (tolerance unchanged).
  Norse ground is poor (mean yield factor about 0.25 of the reference field over its cropland): its opening is not yet
  checked beyond the farm topics.
- CPU per year (Complaint 497), same probe, loaded 4-core machine: 7.29 s before, 7.51 s after (noise; the first year of each run
  is dearer).
- Bounds in `test_geography_food_gaps.py` that were calibrated on the deleted parameters were restated (fishing against crops:
  0.15 to 0.25 of the crop energy, because crops now follow the farm model's yield and two-field share; the two rainforest tests
  now read `crop_site`, which does not depend on seed). Review these.

- Stage 3 (the agent economy): `tile_costs.tiles_from_map(world_map, tile_ids, open_field_cropped_share)` builds each `TileSpec` from
  geography's `crop_site`: `cropped_fraction` (cropped hectares over land, zero where the ground yields nothing; was
  `arable_fraction`, raw) and `fertility` (the yield factor of a cropped hectare; was soil only). `TileSpec.cropland_hectares` is the
  land market's supply, the title value's land and the tenancies' land (`land_market.arable_hectares` deleted;
  `tile_costs.tiles_from_geography`, the parsed-document path with a third reading of the land, deleted). The share comes from the
  society's rotation in `economy_port_setup.build_setup`, as `Sim.farm_sites()` does, so the economy's cropland equals the farm
  model's ceiling for the home tiles. Households' own plots and the shortfall hours read `tile.fertility`, so they now follow the
  tile's climate and water too (no change to `households_own.py`).
- Farm producers: `setup.yield_factor_by_recipe_tile` (a seam that was never filled) holds the tile's yield factor for every recipe
  whose entry says `extracted_from: "arable land"` (pasture, forest and mines are not read through the crop yield). New entrants are
  sited and costed on it (`location`, `entry_year`); each year `economy_port_sites.crop_yields` gives every land producer
  weather times its tile's factor, and the hidden spin-up years apply the tile factor without weather. The opening itself is still
  sized at each recipe's own yield (national runs are quantity over output, in `opening_runs`), so its inputs-have-suppliers
  identity holds; the tile yield shows from the first hidden year.
- Test: `sim/tests/test_economy_reads_tile_yield.py` (cropland equals geography's and the farm ceiling, the site yield is geography's
  factor, a producer on a better-watered tile yields more per run, the year's yield is weather times the tile factor);
  `test_economy_land_market.py` rent follows the yield factor. `test_economy_tile_costs`, `test_economy_market_areas` and
  `test_economy_reads_map_through_geography` changed to read `tiles_from_map` / cropland (subject kept); `test_spin_up_measure`
  stubs the new yield call (subject is the call order).
- Effect on rome_100ad (probe: open the economy, then five `run_year`): wheat price at opening 0.0889 to 0.0804 (economy units),
  farm share of worker-years at opening 0.233 to 0.190 and in year five 0.124 to 0.105, mean land rent per hectare 14.4 to 20.6 at
  opening. CPU per year 8.7, 7.3, 6.5, 6.3, 7.7 before; 9.0, 6.6, 6.2, 6.0, 6.6 after (loaded 4-core machine). Norse: farm share 0.63 to
  0.54, wheat price 0.0083 to 0.0045; the opening is not checked beyond the topics listed in the commit.
- `test_opening_herds_follow_producers` "Rome's opening flock supplies its opening wool demand within a tenth" fails identically
  before and after this change (6.91 million made against 5.94 million used); it is not from this stage.

## What is left

- `land.py`'s rent margin (`margin_outcome_for_civilization`, `cultivable_land_for_civilization`) is still a third land ladder on raw
  arable ground. It is not dead: `sim/engine/rent_standin.py` uses it for the price solver's opening stand-in rent, and about seven
  test topics pin it. Moving the stand-in to `territory_cropland` changes the opening prices of every civilisation, so it is its own step.
- The land market pools arable, pasture and forest producers on one cropland supply per tile; separate supplies per land class need
  pasture and timber hectares from geography.
- Soils beyond the climate-class fertility (heavy clay a plough cannot open, podzol, alluvium: Complaint 543), the engine's
  single `DEFAULT_SOIL`, rice and maize adoption, a hoe toolkit, per-tile weather applied to each tile's harvest (the economy
  and farm still take one pooled draw), irrigation as a work that silts up.
- The farm model still runs nationally for labour, clearing and the granary; demography eats what households ate (Complaint 549).

## Done: the economy follows the rotation and the soil (item 3)

- `sim/engine/economy_port_cropland.py` `follow_farm_sites` runs at the start of each agent-economy year: each held tile's
  cropped share and fertility, and the yield of every crop recipe on it, are read again from `Sim.farm_sites()`
  (`tile_costs.following_site`). A rotation adopted mid-game reaches the land market's cropland, and the soil nitrogen stock
  reaches the farm producers' yield. The farm's own ceiling follows the rotation through `Sim.refresh_farm_territory` (Complaint 543).
- Test: `sim/tests/test_economy_follows_rotation.py`.

## Done: the opening is sized at the tile yield (item 2)

- `opening_runs.mean_yields` gives each crop recipe the yield its runs are counted at: the people-weighted harmonic mean of the
  tile factors of the tiles it can run on (a tile's people eat what the tile grows); `required_runs`, `unit_costs` and
  `choose_recipes` take it, so the national run counts, the inputs they pull (nightsoil) and the income settle all know the yield.
  Placement scales each area's runs to its own tiles' mean yield, gives every crop producer its tile's factor, puts none on a tile
  that yields nothing, and shares the runs of an area where the crop cannot grow over the areas where it can (wine was 11 percent
  short of its demand otherwise).
- Test: `sim/tests/test_opening_crops_at_tile_yield.py`; `opening_inputs_have_suppliers` passes (the arithmetic mean left
  nightsoil 7 percent short, the harmonic mean over the tiles the crop grows on closes it).
- Effect on rome_100ad (probe: open the economy, hidden years included): wheat price 0.0870 to 0.0911 (economy units), farm share
  of worker-years 0.1033 to 0.0867. `opening_floor_and_thin_trades` "household floors cost a small multiple of the food floor"
  fails before this change (10.36) and after (11.40).
