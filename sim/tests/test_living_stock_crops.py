"""Sourced living-stock rows for pepper, dairy cattle, tea, coffee and sugar cane (Complaints/366, 365).

Each row states its rates and cites a source with a confidence grade; a node grants the stock, so a
society reaches it by completing that node; and a year breeds and loses by the stated rates.
"""
import json

from .harness import *  # noqa: F401,F403

from sim.engine.data import ROOT
from sim.world import stock_dynamics

HOME = "rome_100ad"
WIRING = {
    "pepper_vine_stock_kg": "fud_pepper_cultivation",
    "dairy_cattle_kg": "fud_livestock_selective_cattle",
    "tea_plant_stock_kg": "ag2_tea_voyage",
    "coffee_seedling_kg": "ag2_coffee_voyage",
    "sugar_cane_sett_kg": "ag2_sugar_voyage",
}

with open(os.path.join(ROOT, "data", "world", "living_stock.json"), encoding="utf-8") as handle:
    rows = json.load(handle)["materials"]

for material, node_id in sorted(WIRING.items()):
    row = rows.get(material)
    check("%s has a living-stock row" % material, row is not None, None)
    if row is None:
        continue
    check("%s: increase is not negative, loss is a fraction and the minimum is not negative" % material,
          0.0 <= row["natural_increase"] and 0.0 <= row["annual_loss"] <= 1.0
          and row["breeding_minimum_units"] >= 0.0, row)
    check("%s names a source with a confidence grade" % material,
          len(row.get("source", "")) > 40 and row.get("confidence") in ("A", "B", "C"), row)
    check("%s: the node %s grants it" % (material, node_id),
          (NODES[node_id].get("grants") or {}).get(material, 0) > 0, NODES[node_id].get("grants"))

    # reachable: the node's grant is what completing it adds to the ledger
    founder = sim(civ=HOME, capital=1e6)
    check("%s is not held before the node" % material, founder.stock_held(material) == 0.0, None)
    founder.grant_stock(material, NODES[node_id]["grants"][material])
    held = founder.stock_held(material)
    check("%s is held once the node's grant lands" % material, held > 0.0, held)

    # a year breeds and loses by the stated rates
    herd = max(held, row["breeding_minimum_units"])
    founder.grant_stock(material, herd - held)
    founder.step_living_stock()
    expected = stock_dynamics.next_units(herd, row["natural_increase"], row["annual_loss"],
                                         row["breeding_minimum_units"])
    check("%s: a year moves the holding by the stated rates" % material,
          abs(founder.stock_held(material) - expected) < 1e-6, (founder.stock_held(material), expected))
    check("%s: the holding is not constant over a year" % material,
          abs(founder.stock_held(material) - herd) > 1e-9, None)
