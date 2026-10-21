# Arable share and fertility are a climate-class table, and soil nutrients are not a stock

**Status:** partly done: the soil nitrogen stock (below); arable share and fertility from the water balance, slope and silt, and tillage resistance, remain open

Reference (an outside design note, not code-aware): soil should be derived from the physical inputs a
tile already has, not looked up. Plant growth is limited by the scarcer of heat and water; rain far
beyond evaporation leaches a hot soil (rainforest), rain near evaporation on flat ground builds deep
humus (steppe black earth), river floods lay down silt. Each harvest removes nitrogen from a soil pool
that manure, legumes, silt or rest restore, so fallow becomes a choice rather than a typed share. Heavy
soils resist tillage until the tool and team can pull hard enough.

## What the code does

- Crop yield on a tile already takes the minimum of a temperature and a water suitability built from
  WorldClim layers (`sim/geography/food_crops.py`, `content_rules.suitability`), which is the
  climate half of the note.
- `arable_fraction` and `fertility_quality_multiplier` come from one table keyed by Koppen class
  (`tools/generate_geography_tiles.py`, "THE CLIMATE TABLE"), with the Mediterranean class anchored
  at the Roman wheat yield and the rest set by agronomic judgement (confidence D). The tile has slope,
  ruggedness, precipitation, temperature and river layers (`data/world/geography/layers/`) that the
  table does not read.
- Nitrogen appears only as the reason a rotation's typed fallow share exists (`sim/world/agriculture.py`);
  no tile holds a nutrient pool that harvests draw down.
- No soil resists tillage; the toolkit changes labour per hectare everywhere alike (537).

## What it would take

- Arable share from slope, forest, wetness and the land-cover layer; fertility from the water
  balance (precipitation against evaporation from temperature), slope and river silt, each relation
  sourced and labelled. The outside note's leaching formula has unsourced constants and is not a
  source in itself.
- A soil nitrogen stock per tile: removed by harvests, restored by manure (herds, 532), legumes,
  silt and rest, so fallow share and yield decline under overcropping emerge.
- A tillage resistance per soil and a draught force per toolkit, so heavy clay and prairie sod open
  only to a heavy plough (537).
- The table kept only as a test reference: the derived values should land near it for the classes it
  covers, as a validation under 4.2.

## Done: soil nitrogen stock

- `sim/geography/soil_nutrients.py`: the share of a tile's native nitrogen pool left, saved as `state.economy.soil_nitrogen`
  (a tile with no entry is native). Each year the harvest's grain nitrogen draws it down; a grain legume's net fixation,
  the humus share of applied manure and the natural input (equal to a native soil's loss, so untouched ground holds still)
  build it. A crop's yield against the reference field follows the year's mineral supply (pool mineralisation, plus nitrate
  that the fallow hectares of the holding leave, plus the manure's available share) with a saturating response, normalised
  to native soil under the two-field rotation. Rates are declared with sources (most recalled, marked) in that module.
- Geography only multiplies: `crop_site(..., nutrient_factor)` and `food_potential(..., nutrient_factors)`.
  `sim/engine/soil_nitrogen_year.py` owns the yearly step (phase `soil_nitrogen`) and feeds the factors to the tile food view
  and `Sim.farm_sites()`. `Rotation` gained `legume_share_of_holding` (three-field: half the spring field).
- Manure is a transitional rule (`MANURE_COLLECTED_SHARE`, `sim/geography/soil_nutrients.py`): the society's draught herd's collected
  dung is spread over the held cropland. Dung is made by herd and draught recipes (544, closed: `data/production/95_herds.json`) but the only
  recipe that takes it as an input is the nitre bed (`data/production/60_nitrogen.json`); no farm recipe buys it. The constant's `retire`
  still names 544, which is closed: it should name this complaint (the retirement is a farm recipe with manure as an input).
- Tests: `sim/tests/test_soil_nitrogen.py`, `test_soil_nitrogen_whole_game.py`.

## Done: the farm model reads the stock

- `Sim.refresh_farm_territory()` (`sim/engine/soil_nitrogen_year.py`) rebuilds the farm's ladder, ceiling and the cleared
  ground's quality from `farm_sites()` at the start of each year (and after a load), so national farm yield follows the soil
  nitrogen stock and the society's rotation. `THREE_FIELD_SOIL_FERTILITY_YIELD_MULTIPLIER` is deleted: the three-field
  rotation's edge is its smaller fallow (more cropped hectares) and its legumes' gain to the stock.
- Tests: `sim/tests/test_farm_follows_soil.py` (continuous cropping lowers the ladder's harvest weight and the cleared
  ground's quality over thirty years; three-field with legumes holds a higher stock and harvest than without; the ceiling
  follows a rotation change). The Nile rotation keeps its own silt multiplier until silt is an input.

## Left

- Per-tile manure from market purchase (a farm recipe with manure as an input, so 544's dung reaches the soil); silt as an input on flooded tiles (then the Nile multiplier goes); arable share and
  fertility derivation; tillage resistance.
