"""Complaint 409: regions, located materials and the tile grid live in the map folder, so a mod's map
overlay covers them and `load_geography` is the one reader."""

QUICK_TOPIC = True

import json
import os
import tempfile

from .harness import *  # noqa: F401,F403

from sim.geography import api

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
check("the standalone geography file is gone", not os.path.exists(os.path.join(root, "data", "world", "geography.json")))

base = api.load_geography()
check("the base geography has regions, reach levels, located materials and tiles",
      all(base.get(key) for key in ("regions", "reach_levels", "located_materials", "land_tiles")))
check("a region's tiles are grouped from the tiles' own labels",
      all(base["land_tiles"]["tiles"][tile_id]["old_region"] == region_id
          for region_id, tile_ids in base["land_tiles"]["region_to_tiles"].items() for tile_id in tile_ids))

with tempfile.TemporaryDirectory() as mods_dir:
    folder = os.path.join(mods_dir, "isle_mod_q7", "data", "world", "geography")
    for name in ("regions", "tiles", "located_materials"):
        os.makedirs(os.path.join(folder, name))
    with open(os.path.join(folder, "regions", "isle.json"), "w", encoding="utf-8") as handle:
        json.dump([{"id": "isle_mod_q7:isle", "name": "Isle"}], handle)
    with open(os.path.join(folder, "tiles", "isle.json"), "w", encoding="utf-8") as handle:
        json.dump([{"id": "isle_mod_q7:isle_01", "lat": 0.0, "lon": 0.0, "land_area_km2": 1000.0, "coastal": True,
                    "borders": [], "old_region": "isle_mod_q7:isle", "koppen_class": "Af"}], handle)
    first_material = next(iter(base["located_materials"]))
    with open(os.path.join(folder, "located_materials", "patch.json"), "w", encoding="utf-8") as handle:
        json.dump([{"id": first_material, "override": True, "cost_multiplier": 777}], handle)
    modded = api.load_geography(api.open_map([("isle_mod_q7", os.path.join(mods_dir, "isle_mod_q7"))]))
check("a mod's overlay adds a region", "isle_mod_q7:isle" in modded["regions"] and "isle_mod_q7:isle" not in base["regions"])
check("a mod's tile joins its region", modded["land_tiles"]["region_to_tiles"].get("isle_mod_q7:isle") == ["isle_mod_q7:isle_01"])
check("the tile count follows the tiles", modded["land_tiles"]["tile_count"] == base["land_tiles"]["tile_count"] + 1)
check("a mod's override patches a located material", modded["located_materials"][first_material]["cost_multiplier"] == 777)
check("the base is untouched by the overlay", base["located_materials"][first_material].get("cost_multiplier") != 777)
