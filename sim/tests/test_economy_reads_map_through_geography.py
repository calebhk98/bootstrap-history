"""Complaints 409 and 410: the economy's setup reads tiles through geography's api, and the map the
game opens carries the active mods' map overlays."""
import json
import os
import tempfile

from .harness import *  # noqa: F401,F403

from sim.engine import economy_port_setup, geography_port

with open(economy_port_setup.__file__, encoding="utf-8") as handle:
    check("the economy setup does not open the geography file by path", "geography.json" not in handle.read())

game = sim()
base_tiles, _base_map = economy_port_setup.civilisation_tiles(game.civ, game.world_map)
check("the civilisation holds tiles on the engine's map", len(base_tiles) > 1, len(base_tiles))
edited = base_tiles[0]
base_setup = economy_port_setup.build_setup(game)
check("the base map gives the tile its shipped arable fraction",
      base_setup.tiles[edited].arable_fraction != 0.123, base_setup.tiles[edited].arable_fraction)

with tempfile.TemporaryDirectory() as mods_dir:
    mod_root = os.path.join(mods_dir, "tile_edit_k3f9")
    os.makedirs(os.path.join(mod_root, "data", "world", "geography", "tiles"))
    with open(os.path.join(mod_root, "mod.json"), "w", encoding="utf-8") as handle:
        json.dump({"id": "tile_edit_k3f9", "name": "Tile edit", "version": "1.0.0", "dependencies": [], "conflicts": []}, handle)
    with open(os.path.join(mod_root, "data", "world", "geography", "tiles", "edit.json"), "w", encoding="utf-8") as handle:
        json.dump([{"id": edited, "override": True, "arable_fraction": 0.123}], handle)
    saved = geography_port.MODS_DIR
    geography_port.MODS_DIR = mods_dir
    try:
        modded = sim()
        check("the engine's map is the base map with the active mod's overlay",
              modded.world_map.tiles[edited]["arable_fraction"] == 0.123)
        modded_setup = economy_port_setup.build_setup(modded)
        check("the economy's tiles come from that map", modded_setup.tiles[edited].arable_fraction == 0.123)
        check("the setup names the map its tiles lie on", modded_setup.world_map is modded.world_map)
    finally:
        geography_port.MODS_DIR = saved
check("without the mod the base map is unchanged", sim().world_map.tiles[edited]["arable_fraction"] != 0.123)
