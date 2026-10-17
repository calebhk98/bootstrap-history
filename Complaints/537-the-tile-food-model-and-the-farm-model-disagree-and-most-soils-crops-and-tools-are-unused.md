# The tile food model and the farm model disagree, and most soils, crops and tools are unused

**Status:** open

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
- Rotations: `NILE_FLOOD_RECESSION` (near-zero fallow) is a technique adopted by technology, never
  tied to floodplain land; outside tests nothing selects it. The tile model gives river land no
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
