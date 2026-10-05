# Economy setup opens the geography file by path

**Status:** open - narrowed: the economy setup now reads tiles through `sim.geography.api` (`economy_reads_map_through_geography`); only moving `geography.json` into the map folder remains.

`sim/engine/economy_port_setup.py` loads `data/world/geography.json` itself (`_load("world", "geography.json")`) instead of asking the geography package. The map is meant to be replaceable (a finer grid, a fantasy map, a mod's map; `sim/geography/map_source.py`), and every reader that opens the file directly pins the map to that file and that layout. It is also why `geography.json` could not move into `data/world/geography/` with the rest of the map.

What remains: `geography.json` still holds the regions and located materials that `load_geography` reads beside the tiles, so moving it into `data/world/geography/` means splitting those blocks from `land_tiles` first. Readers that still open the file directly: `grep -rn geography.json sim`.
