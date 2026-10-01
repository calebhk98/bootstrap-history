# Regions and tiles are two maps

**Status:** partly - land rent, forest area and mineral deposits read tiles; civilisations still hold region labels and region records remain for the readers listed below

The world has two land systems: 21 named regions and the land tiles inside
them. Soil fertility and arable land now come from tiles (Complaints/134),
and regions derive theirs from their tiles, but civilisations still hold
regions, and other data and code still work at region grain (located
materials, deposits, weather pooling, transport, geography screens).

## Why it matters

Two maps drift apart and have already disagreed (Complaints/46, 134). Every
new mechanism has to choose one, and mods have to edit both.

## What it would take

- Civilisations hold tiles (a region becomes an optional label over tiles).
- Move remaining region-level data (materials, deposits, weather) to tiles or
  derive it from them, and delete region-level copies.
- A test that no region-level field duplicates a tile-level one.
See `docs/architecture/MAP_AND_WEATHER.md`.

## Done

- Land rent's extensive margin was already tile-keyed (`cultivable_land_for_civilization`); `docs/architecture/MAP_AND_WEATHER.md` section 2.2 is stale on this.
- `Sim.home_land_area_km2` (the forest ceiling) sums the land area of the tiles the home regions resolve to, not the region record's own `land_area_km2` (`land.territory_land_area_km2`). Tile area runs a few percent above the coarse region records, so a civilisation's forest ceiling is larger by about that much; no quick-fingerprint scenario reaches the ceiling.
- A named deposit sits on a tile (`tile` in `data/world/deposits.json`) and carries its own share of output, moved unchanged out of the region mineral tables. `load_deposits` no longer opens `geography.json`. `sim/world/mineral_shares.py` gives a region's total as its remaining table plus the deposits on its tiles, which keeps `mineral_scale` and material freight unchanged.
- `sim/tests/test_tiles_replace_regions.py` fails if any of these goes back to the region layer, or if a share is stored on both a region and a deposit.
- `python3 sim/perf_fingerprint.py check --quick` against a baseline made before the change: all four scenarios byte-identical.

## What remains

Measure the region-layer readers with
`grep -rnE "\[\"regions\"\]|get\(\"regions\"\)|self\._regions" sim --include=*.py`.
Each remaining reader and what would move it:

- Civilisations hold region labels (`home_regions`); every tile list comes from `region_to_tiles`. Holding tiles directly is the real fix and the biggest change.
- `sim/engine/geography.py` and `economy_freight.py`: region centroids and `reach_from_italia` for reach and freight, and the region `minerals` table for `mineral_scale` and material source regions. Reach would come from tile positions; the unlocated mineral shares have no tile yet.
- `sim/engine/core.py` weather cells: falls back to a region centroid for a region with no tiles.
- `sim/world/land.py` `load_region_lands` and each region's `land` block (area, arable share, fertility): only tests and the weather fallback read them, and they duplicate what the tiles hold. Deleting them needs those tests and the fallback moved first.
- `cli_interactive.py` and `demo_commodities.py`: region names for display, which is what a label is for.
- Related: Complaints/285 (deposit tiles are a coarse hand assignment) and Complaints/286 (regenerating tiles drops references to them).
