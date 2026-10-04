# Economy setup opens the geography file by path

**Status:** open

`sim/engine/economy_port_setup.py` loads `data/world/geography.json` itself (`_load("world", "geography.json")`) instead of asking the geography package. The map is meant to be replaceable (a finer grid, a fantasy map, a mod's map; `sim/geography/map_source.py`), and every reader that opens the file directly pins the map to that file and that layout. It is also why `geography.json` could not move into `data/world/geography/` with the rest of the map.

Evidence: `grep -n geography.json sim/engine/economy_port_setup.py`.

What it would take: read tiles through `sim.geography.api` (the map's tiles and layers), then move `geography.json` into the map folder and update `data/world/geography/map.json`.
