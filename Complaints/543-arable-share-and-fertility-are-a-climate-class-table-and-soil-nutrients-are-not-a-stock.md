# Arable share and fertility are a climate-class table, and soil nutrients are not a stock

**Status:** open

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
