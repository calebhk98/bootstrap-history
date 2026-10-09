"""Complaint 103: a concern that declares no `annual_output_t` still puts goods on the market: what its staff and plant
turn out, derived from the production data (the node's baskets), reaches the market through the same supply rule."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import supply
from sim.labour.api import production_data

# a node that declares nothing, and one that declares a total
bare = {"id": "bare"}
declared = {"id": "declared", "annual_output_t": 100.0}

check("with nothing declared and nothing derived, a concern supplies nothing",
      supply.concern_output_tonnes(bare, "bare", "iron_bar_kg", 1.0, 1.0) == 0.0)
check("what the staff and plant can turn out, derived from the data, is the supply scaled by ramp and staffing",
      abs(supply.concern_output_tonnes(bare, "bare", "iron_bar_kg", 0.5, 0.8, derived_tonnes=50.0) - 20.0) < 1e-9)

# ---- a node that runs a technique (operated_by) makes the materials of that technique ---------------------
production = production_data()
operated = {}
for entry in production.values():
    for node_id in entry.get("operated_by") or ():
        operated.setdefault(node_id, set()).update(entry.get("outputs") or {})
check("the data names nodes that operate techniques", len(operated) > 0, len(operated))
node_id = sorted(operated)[0]
check("such a node is counted as making what its technique outputs", set(operated[node_id]) <= set(supply.materials_made_by(node_id)),
      (node_id, operated[node_id], supply.materials_made_by(node_id)))
material = sorted(operated[node_id])[0]
check("and is found among the concerns that make the material", node_id in supply.nodes_making(material))
