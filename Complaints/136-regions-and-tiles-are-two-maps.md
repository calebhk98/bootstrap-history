# Regions and tiles are two maps

**Status:** partly - a civilisation holds tiles: every shipped civilisation file lists `home_tiles` and no `home_regions`, and every reader of a civilisation's territory goes through `tiles_held`. A foreign economy's mined share counts the deposits on its tiles. Remaining: region records still carry mineral shares with no deposit behind them (listed below), the home mineral scale and material freight still read region shares, and located materials still name regions

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

## Done on the second-path sweep

- Farm land (`land.cultivable_land_for_civilization`), the weather cells (`Sim._compute_farm_weather_cells`), crop climate (`prices._climate_allows`) and the cast (`cast.profile_from_civilisation`) already read `tiles_held`; the earlier status line was stale. `sim/tests/test_civilisations_hold_tiles.py` now shows a civilisation with only `home_tiles` gets farm land, a crop climate and a placed cast country.
- A foreign economy's mined capacity summed the shares of its `home_regions`; it now sums each region's share by the fraction of that region's tiles the civilisation holds (`foreign_capacity.held_mineral_share`). `sim/tests/test_foreign_capacity_from_tiles.py`.
- The remaining `home_regions` mentions in code are comments, display (`cli_interactive.py`, `screen_divergence.py`, `screen_map.py`), cache keys (`economy_port.py`, `geography.py`) and the resolver itself (`tile_holdings.py`, `land._tiles_held_in` for a caller-supplied geography). Measure with `grep -rnE "home_regions|region_to_tiles" sim --include=*.py`.

## Done on the civilisation files and mineral readers

- Each shipped civilisation (`data/civilizations/*.json`) lists `home_tiles`, generated with the resolver from its old labels (each holds the same tiles as before) and spot-checked by latitude and longitude. `home_regions` is gone from them. `sim.geography.api.regions_of_tiles` gives the labels of held tiles; `cmd_civs`, the map screen and the divergence screen show those.
- Decision on dropping `home_regions` from the resolver: kept, as a shorthand a mod civilisation may use (`mods/README.md`, `data/civilizations/_SCHEMA.md`). Evidence: with the shipped files on tiles, every reader goes through `tiles_held`, so the label path costs one line and no second source remains in shipped data; but the sample mod civilisation, many fixtures and a patch that adds one mod tile to a civilisation all read more simply with labels, and removing it would touch many tests (measure: grep -rn home_regions sim/tests). `home_tiles` wins when both are present. `sim/tests/test_civilisations_hold_tiles.py` fails if a shipped file lists labels or no tiles.
- `mineral_shares.held_share` is what a holder can draw on: the deposits sitting on its tiles, exactly, plus each region's table remainder by the fraction of that region's tiles held. `foreign_capacity.held_mineral_share` uses it, so a deposit on a tile not held no longer counts because its region is. `sim/tests/test_held_mineral_share.py` (fixtures) and `sim/tests/test_foreign_capacity_from_tiles.py`.

## What remains

- Region mineral shares with no deposit behind them (measure: print each region's `minerals` from `load_geography()` against `mineral_shares.deposit_shares_by_tile`): every non-zero table entry is such a case. Coal in all seven regions that list it, saltpetre in India, Persia and China, and iron, copper, lead, silver and tin in the non-Roman regions (Scandinavia, Arabia, India, Persia, China, West Africa, Southeast Asia, East Africa, Siberia, the Americas, Australia, Greenland). The deposit catalogue only holds Roman-world metals (iron, copper, lead, silver, tin, gold, mercury). No deposits are invented here; each needs a sourced deposit entry (Complaint 416).
- The home mineral scale (`Geography._compute_mineral_scale`) and `economy_freight` (regions that produce a material) still read region shares by region reach. Moving the deposit part to the reach of the deposit's tile needs a per-tile reach level; geography only banks reach per region.
- Located materials (`data/world/geography/located_materials/located_materials.json`, read by `Geography.material_reach`) name regions. Translating them mechanically to every tile of those regions would keep behaviour and add no information; a real move needs a sourced tile (or latitude and longitude) per material, like deposits, and a per-tile reach level.
- `cli_interactive.py` and `demo_commodities.py` print region names, which is what a label is for.
- Related: Complaints/289 (no place names or towns).
