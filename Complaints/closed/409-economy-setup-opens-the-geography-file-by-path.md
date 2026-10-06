# Economy setup opens the geography file by path

**Status:** closed - `data/world/geography.json` is gone: its tile grid is `data/world/geography/tile_grid.json` (the map's tile source) and its regions, reach levels and located materials are catalogues in the map folder, so a mod's overlay covers them; `load_geography(world_map)` assembles the same dict from the map (`geography_data_in_map_folder`). The deposit loader still reads the base map's deposit records (separate).

`sim/engine/economy_port_setup.py` loads `data/world/geography.json` itself (`_load("world", "geography.json")`) instead of asking the geography package. The map is meant to be replaceable (a finer grid, a fantasy map, a mod's map; `sim/geography/map_source.py`), and every reader that opens the file directly pins the map to that file and that layout. It is also why `geography.json` could not move into `data/world/geography/` with the rest of the map.

What remains: `geography.json` still holds the regions and located materials that `load_geography` reads beside the tiles, so moving it into `data/world/geography/` means splitting those blocks from `land_tiles` first. Readers that still open the file directly: `grep -rn geography.json sim`.

The engine's foreign routes (`_foreign_route` in `sim/engine/foreign_routes.py`) now resolve tiles, usable modes and the
haul on `sim.world_map`, the mod-aware map (`economy_reads_map_through_geography`). `_freight_mode_costs` reads no
map (it prices carriers from physics and this society's prices), so nothing there needed changing. Not done: the
deposit loader (`sim/world/deposits.py` `load_deposits`) still reads the base map's deposit records.
