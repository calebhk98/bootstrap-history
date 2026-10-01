# Regenerating the tile grid breaks the ids other data points at

**Status:** closed - deposits are placed by position and resolve to a tile at load; pinned by sim/tests/test_region_view_from_tiles.py

`tools/generate_geography_tiles.py` rewrites the whole `land_tiles` section. Data that names tile ids by hand, now each deposit's `tile` in `data/world/deposits.json`, points at nothing after a regeneration at another cell size (stage 4 of `docs/architecture/MAP_AND_WEATHER.md`). `sim/tests/test_tiles_replace_regions.py` fails when a deposit's tile is missing, but nothing re-assigns it.

## Why it matters

A finer grid is meant to be a data change, not an engine change; this makes it one that has to be followed by hand edits.

## What it would take

Store a position for every hand-placed reference and resolve it to a tile at load (see Complaints/281), or have the generator carry such references over to the tile that now contains them.

## Done

Each deposit in `data/world/deposits.json` carries `lat` and `lon`, and `sim/world/tile_lookup.py` resolves the nearest tile centre at load, so a regenerated grid needs no edit to deposits. Any later hand-placed reference (a town, Complaints/289) should do the same.
