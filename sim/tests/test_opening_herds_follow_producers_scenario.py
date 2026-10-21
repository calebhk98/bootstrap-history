"""Scenario, Complaints/532: in a running game the ledger's opening herds are the head the agent economy's herd
producers keep, and the opening flock supplies the opening wool demand. The arithmetic is in
test_opening_herds_follow_producers."""
from .harness import *  # noqa: F401,F403
from .harness import unopened_sim

from sim.economy import api as economy_api
from sim.geography.api import pasture_capacity_kg, tiles_held
from sim.labour.api import production_data
from sim.economy import opening
from sim.engine.economy_port_setup import build_setup

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
check("the opening herds equal the producers' head (pasture permitting) and stand within the pasture",
      all(abs(rome.stock_held(material) - kept.get(material, 0.0)) <= 1e-6 * max(1.0, kept.get(material, 0.0))
          or total_kg > capacity for material in HERD_STOCKS)
      and sum(rome.stock_held(material) for material in HERD_STOCKS) <= capacity,
      {material: (rome.stock_held(material), kept.get(material)) for material in HERD_STOCKS})

_record, _areas, _carriage = opening.open_economy(build_setup(unopened_sim(civ="rome_100ad")))
producers = list(_record.producers.values())
wool_made = sum(p.capacity_runs * production[p.recipe_id]["outputs"].get("wool_kg", 0.0) for p in producers)
wool_used = sum(p.capacity_runs * (production[p.recipe_id].get("inputs") or {}).get("wool_kg", 0.0) for p in producers)
check("Rome's opening flock supplies its opening wool demand within a tenth",
      wool_used > 0.0 and abs(wool_made / wool_used - 1.0) <= 0.1, (wool_made, wool_used))

mexica = sim(civ="mexica_1500", capital=1e6)
check("a civilisation with no herd node holds no herds",
      all(mexica.stock_held(material) == 0.0 for material in HERD_STOCKS), [mexica.stock_held(m) for m in HERD_STOCKS])
