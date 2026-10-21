"""Living stock is bought from a partner, breeds and dies each year (Complaints/366, 365).

A player buys held stock through `buy living_stock`, priced at the partner's price plus the merchants'
terms and freight and paid through the one goods market; the quote is the charge. A partner that will
not sell refuses with the reason. Held stock grows by its natural increase once the herd is large
enough to breed and falls by its losses; each rate is data with a stated basis.
"""
import json

from .harness import *  # noqa: F401,F403

from sim.engine.data import ROOT
from sim.world import stock_dynamics

QUICK_TOPIC = True

HERD = "draught_animal_kg"

# --- the yearly rule: increase only from a herd that can breed, loss always.
check("a herd at or above the breeding minimum grows by its natural increase less its loss",
      abs(stock_dynamics.next_units(100.0, 0.2, 0.05, 10.0) - 115.0) < 1e-9, None)
check("a herd below the breeding minimum cannot grow, and still falls by its loss",
      abs(stock_dynamics.next_units(5.0, 0.2, 0.05, 10.0) - 4.75) < 1e-9, None)
check("stock never goes negative", stock_dynamics.next_units(1.0, 0.0, 1.5, 0.0) == 0.0, None)

with open(os.path.join(ROOT, "data", "world", "living_stock.json"), encoding="utf-8") as handle:
    rates = json.load(handle)["materials"]
for material, row in sorted(rates.items()):
    check("%s: increase is not negative, loss is a fraction of the herd and the minimum is not negative" % material,
          0.0 <= row["natural_increase"] and 0.0 <= row["annual_loss"] <= 1.0
          and row["breeding_minimum_units"] >= 0.0, row)
    check("%s: each rate states its basis" % material, len(row.get("basis", "")) > 40, row.get("basis"))


# --- the stock nodes converted from research: each holds a stock material, a venture brings it.
for consumer, material in (("tx2_cashmere", "cashmere_goat_kg"), ("tx2_mohair", "angora_goat_kg"),
                           ("tx2_jute_fibre", "jute_seed_kg"), ("ag2_hopping", "hop_rhizome_kg"),
                           ("ag2_pyrethrum", "pyrethrum_stock_kg")):
    node = NODES[consumer]
    check("%s holds %s and names no stand-in stock node" % (consumer, material),
          material in (node.get("holds") or {}) and not any(pre.endswith("_stock") for pre in node["pre"]),
          (node.get("holds"), node["pre"]))
    brought_by = [node_id for node_id, other in NODES.items() if material in (other.get("grants") or {})]
    check("%s is brought back by a venture that grants it" % material, bool(brought_by), None)
    check("%s breeds under a stated rule" % material, material in rates, None)

