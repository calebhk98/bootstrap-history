"""Complaints/532: the engine's opening herds are the head the agent economy's herd producers keep (one figure)."""
import json
import os

from .harness import *  # noqa: F401,F403

from sim.economy import api as economy_api
from sim.engine.data import ROOT
from sim.geography.api import pasture_capacity_kg, tiles_held
from sim.labour.api import production_data

HERD_STOCKS = ("sheep_kg", "goat_kg", "cattle_kg")
production = production_data()


def head_of_producers(game):
    """{stock material: units} the herd producers keep: runs a year times the stock one run holds."""
    held = {}
    for producer in economy_api.all_producers(game.economy.agent.economy()):
        for material, units in (production[producer.recipe_id].get("herd_stock") or {}).items():
            held[material] = held.get(material, 0.0) + producer.capacity_runs * units
    return held


rome = sim(civ="rome_100ad", capital=1e6)
kept = head_of_producers(rome)
capacity = sum(pasture_capacity_kg(tile, rome.state.economy.wild_stock, rome.world_map)
               for tile in tiles_held(rome.civ, rome.world_map))
check("the herd producers keep sheep", kept.get("sheep_kg", 0.0) > 0.0, kept)
total_kg = sum(kept.values())
for material in HERD_STOCKS:
    wanted = kept.get(material, 0.0)
    check("%s held at the opening equals the producers' head (pasture permitting)" % material,
          abs(rome.stock_held(material) - wanted) <= 1e-6 * max(1.0, wanted) or total_kg > capacity,
          (rome.stock_held(material), wanted))
check("the opening herds stand within the pasture the held tiles carry",
      sum(rome.stock_held(material) for material in HERD_STOCKS) <= capacity, capacity)

mexica = sim(civ="mexica_1500", capital=1e6)
for material in HERD_STOCKS:
    check("a civilisation with no herd node holds no %s" % material, mexica.stock_held(material) == 0.0,
          mexica.stock_held(material))

for name in ("rome_100ad", "han_china_100ad", "england_1300", "norse_900ad"):
    with open(os.path.join(ROOT, "data", "civilizations", name + ".json"), encoding="utf-8") as handle:
        opening = json.load(handle).get("opening_stock") or {}
    check("%s states no herd in opening_stock" % name, not set(opening) & set(HERD_STOCKS), opening)
