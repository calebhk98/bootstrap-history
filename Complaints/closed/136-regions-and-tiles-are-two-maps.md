# Regions and tiles are two maps

**Status:** closed - a civilisation holds tiles, and every region-level copy of tile data is gone: mineral output sits on named deposits (each placed by position, with a source and a declared share), the home mineral scale and material freight read the deposits' tiles by per-tile reach, located materials name sourced places read by tile reach, and a region record keeps only its name and note

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
- The reach bands moved: a region's level is the days of the fastest route from the held tiles over the modes held, banded on a ladder derived from the carriers' own days per tile (`reach_bands.ladder`), so civilisations that hold sea or cart techniques sit nearer, and a place no route joins is the farthest level (Complaints/328, 378).

## Done on the second-path sweep

- Farm land (`land.cultivable_land_for_civilization`), the weather cells (`Sim._compute_farm_weather_cells`), crop climate (`prices._climate_allows`) and the cast (`cast.profile_from_civilisation`) already read `tiles_held`; the earlier status line was stale. `sim/tests/test_civilisations_hold_tiles.py` now shows a civilisation with only `home_tiles` gets farm land, a crop climate and a placed cast country.
- A foreign economy's mined capacity summed the shares of its `home_regions`; it now sums each region's share by the fraction of that region's tiles the civilisation holds (`foreign_capacity.held_mineral_share`). `sim/tests/test_foreign_capacity_from_tiles.py`.
- The remaining `home_regions` mentions in code are comments, display (`cli_interactive.py`, `screen_divergence.py`, `screen_map.py`), cache keys (`economy_port.py`, `geography.py`) and the resolver itself (`tile_holdings.py`, `land._tiles_held_in` for a caller-supplied geography). Measure with `grep -rnE "home_regions|region_to_tiles" sim --include=*.py`.

## Done on the civilisation files and mineral readers

- Each shipped civilisation (`data/civilizations/*.json`) lists `home_tiles`, generated with the resolver from its old labels (each holds the same tiles as before) and spot-checked by latitude and longitude. `home_regions` is gone from them. `sim.geography.api.regions_of_tiles` gives the labels of held tiles; `cmd_civs`, the map screen and the divergence screen show those.
- Decision on dropping `home_regions` from the resolver: kept, as a shorthand a mod civilisation may use (`mods/README.md`, `data/civilizations/_SCHEMA.md`). Evidence: with the shipped files on tiles, every reader goes through `tiles_held`, so the label path costs one line and no second source remains in shipped data; but the sample mod civilisation, many fixtures and a patch that adds one mod tile to a civilisation all read more simply with labels, and removing it would touch many tests (measure: grep -rn home_regions sim/tests). `home_tiles` wins when both are present. `sim/tests/test_civilisations_hold_tiles.py` fails if a shipped file lists labels or no tiles.
- `mineral_shares.held_share` is what a holder can draw on: the deposits sitting on its tiles, exactly, plus each region's table remainder by the fraction of that region's tiles held. `foreign_capacity.held_mineral_share` uses it, so a deposit on a tile not held no longer counts because its region is. `sim/tests/test_held_mineral_share.py` (fixtures) and `sim/tests/test_foreign_capacity_from_tiles.py`.

## Done on the deposit, reach and located-material step

- Every mineral share that had no deposit behind it is now a named deposit placed by `lat`/`lon` in `data/world/geography/deposits/` (new rows in `reference_output_sites.json`, plus `share_of_reference_output` on catalogue rows that were already real districts: coal basins, Falun, Potosi, Chuquicamata and others). Each carries its source and confidence. The region `minerals` tables are deleted, and so is the derived `minerals` view in `regions.region_records`.
- `share_of_reference_output` is a district's share of the reference civilisation's output of that resource and never enters the Roman supply curve (that stays `share_of_empire_output`). Each is declared a `temporary_heuristic` by `mineral_shares.share_rows`: no district-level production series is read, so the figure is the rough relative abundance the old region table gave, sited at one district. Replace it with production or reserves per district (`python3 sim/constants.py --burndown` lists them).
- `sim/geography/mineral_shares.py` (moved from `sim/world/`) gives shares by tile; a resource is tracked when some row carries the reference-share field, so gold and mercury stay untracked.
- `reach_bands.tile_levels` gives a reach level per tile from the same route search as the region levels; `Geography.tile_reach`. `_compute_mineral_scale` fades each deposit by the reach of its own tile, `economy_freight` hauls from the nearest deposit tile (`Geography.source_tiles`, `route_km_to` takes tiles), and `foreign_capacity` counts the deposits on the tiles held.
- Located materials list `places` (a position with a source, or a catalogued deposit by id) instead of `regions`; `sim/geography/located_places.py` resolves them to tiles and `material_reach` compares the tile reach with the reference civilisation's reach of the same tile.
- The display mentions of region names (`cli_interactive.py`, `demo_commodities.py`, the map and divergence screens) are labels of the tiles held and stay.
- Tests: `sim/tests/test_mineral_access_from_tiles.py` (no region carries minerals or a located material, shares sourced and declared, scale and freight follow deposit tiles, material reach follows place tiles), `test_tiles_replace_regions.py` (a region record is only a label; a share is stored once), `test_held_mineral_share.py`.
- Known limits: the map grid is coarse, so a deposit snaps to the nearest tile (some fall on tiles no shipped civilisation holds, which is why their share is reached only by trade); the fall in a civilisation's own mineral scale where a region's old share now sits on one tile is intended.
- Related: Complaints/289 (no place names or towns).
