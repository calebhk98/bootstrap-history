# The engine does not pass active mods to the map

**Status:** closed - `economy_reads_map_through_geography` opens the map with a temporary mod that edits a tile and finds the edit in the engine's map and the economy's tiles.

A mod can ship a map overlay in `mods/<id>/data/world/geography/` (new resources such as a namespaced unobtainium, animals, route modes, layer patches, or a whole replacement map), and `sim/geography/map_source.load_map(overlays)` merges it under the same add, override and remove rules as the rest of the mod system (tested in `sim/tests/test_geography_map_source.py`). The engine never calls it with the active mods, so in a game the map is always the base map. `mods/README.md` still says world geography is not an extension point.

Evidence: `grep -rn load_map sim/engine` finds nothing.

What it would take: where the engine orders the active mods (`sim/engine/mods.py` `get_ordered_mods`), hand `(mod_id, mod_root)` pairs to the geography package when it opens the map (through `sim/engine/geography_port.py`), and document the geography folder in `mods/README.md`.
