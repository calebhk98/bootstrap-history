# Regions and tiles are two maps

**Status:** partly - land, forest area, mineral deposits and the weather cells read tiles and no region record carries a land block; civilisations still hold region labels, and reach, freight and mineral tables still read a region anchor point (Complaints/500)

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
- Region land is a sum over tiles (`land.load_region_lands`); region records in `data/world/geography.json` carry no `land` block; the weather cells no longer fall back to a region centroid. `sim/world/regions.py` is the derived region view (label record plus mineral shares completed from deposits); `Sim._regions` is built from it. `sim/tests/test_region_view_from_tiles.py`.
- Deposits are placed by `lat`/`lon` and resolve to the holding tile at load (`sim/world/tile_lookup.py`); see 285 and 286.

## What remains

Measure the region-layer readers with
`grep -rnE "\[\"regions\"\]|get\(\"regions\"\)|self\._regions" sim --include=*.py`.

- Civilisations hold region labels (`home_regions`); every tile list comes from `region_to_tiles`. Holding tiles directly is the real fix and the biggest change.
- `sim/engine/geography.py`, `economy_freight.py`, `foreign_*`: read `Sim._regions`, the derived view, for a label anchor point, route difficulty and the unlocated mineral shares. Deriving the anchor from tile positions moves reach bands for some civilisation and region pairs (Complaints/500), so it is not behaviour-preserving.
- `cli_interactive.py`: region names for display, which is what a label is for. `demo_commodities.py` prints trade-partner region names from a report only.
- Related: Complaints/330 (no place names or towns).
