# Regions and tiles are two maps

**Status:** partly - a civilisation holds tiles (`tiles_held`: its `home_tiles`, else the tiles its region labels name) and settlement, frontier and roads, the economy's tiles, foreign routes, reach, mineral access and the forest ceiling read them; region records are labels with no position, coast, distance or land. Farm land, weather cells, crop climate and the cast still resolve region labels

The world has two land systems: 21 named regions and the land tiles inside
them. Soil fertility and arable land now come from tiles (Complaints/130),
and regions derive theirs from their tiles, but civilisations still hold
regions, and other data and code still work at region grain (located
materials, deposits, weather pooling, transport, geography screens).

## Why it matters

Two maps drift apart and have already disagreed (Complaints/45, 130). Every
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
- `python3 -m sim.tests.fingerprint check --quick` against a baseline made before the change: all four scenarios byte-identical.
- Region land is a sum over tiles (`land.load_region_lands`); region records in `data/world/geography.json` carry no `land` block; the weather cells no longer fall back to a region centroid. `sim/geography/regions.py` is the derived region view (label record plus mineral shares completed from deposits); `Sim._regions` is built from it. `sim/tests/test_region_view_from_tiles.py`.
- Deposits are placed by `lat`/`lon` and resolve to the holding tile at load (`sim/geography/tile_lookup.py`); see 281 and 282.

## Done on the tile-holding step

- `sim.geography.api.tiles_held(civilisation)` is the one answer to "which tiles does this civilisation hold": a listed `home_tiles`, else the tiles its `home_regions` labels name. `settlement`, `territory.holdings`, `labour_settlement`, `economy_port_setup`, `foreign_routes` and `economy_mining.home_land_area_km2` read it; `sim/tests/test_civilisations_hold_tiles.py`.
- A region record keeps `name`, `minerals` (shares not yet tied to a deposit) and `note`; `route_difficulty`, `coastal` and `reach_from_italia` are deleted. A region's reach and a material's freight distance come from geography's route over the tiles held (Complaint 416). `sim/tests/test_tiles_replace_regions.py` fails if a region record carries a field the tiles carry.
- The region anchor point is no longer read for reach or freight; `regions.region_anchor` (derived from tiles) remains only for placing a cast actor's location.
- The reach bands moved: a region's level is the days of the fastest route from the held tiles over the modes held, banded by `reach_band_first_days` and `reach_band_ratio`, so civilisations that hold sea or cart techniques sit nearer, and a place no route joins is the farthest level (Complaints/328, 378).

## What remains

Measure the region-layer readers with
`grep -rnE "home_regions|region_to_tiles|\.regions\b" sim --include=*.py`.

- `sim/world/land.py` and `sim/engine/core.py` (farm land, weather cells per region, `home_regions` pooling) and `sim/engine/prices.py` with `crop_climate` (growing-season check by region) still resolve region labels; `sim/agents/cast.py` places a country by a region label. A civilisation that lists `home_tiles` and no labels would hold no farm land until these read tiles.
- Civilisation files still name their starting claim by region labels; none lists `home_tiles`.
- `cli_interactive.py` and `demo_commodities.py` print region names, which is what a label is for.
- Related: Complaints/289 (no place names or towns).
