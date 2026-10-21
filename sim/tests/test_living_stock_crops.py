"""Sourced living-stock rows for pepper, dairy cattle, tea, coffee and sugar cane (Complaints/366, 365).

Each row states its rates and cites a source with a confidence grade; a node grants the stock, so a
society reaches it by completing that node; and a year breeds and loses by the stated rates.
"""
import json

from .harness import *  # noqa: F401,F403

from sim.engine.data import ROOT

QUICK_TOPIC = True

# Complaint 640: the reach of a grant into the ledger and the yearly rate are test_living_stock_scenario and
# test_living_stock_trade (the year turns the held stock); this file reads the data only.
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
