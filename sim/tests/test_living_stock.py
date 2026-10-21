"""Living stock is held, not researched (Complaints/365, 133).

Silkworm eggs are a material held at a place. A node that needs them (`holds`) opens by itself
once they are held, however they were got: an opening holding, a purchase from a partner that
offers them, or a grant. A country refusing to sell is that country's state deciding, from the monopolies its data starts it with.
"""

from .harness import *  # noqa: F401,F403

from sim.engine.data import load_civ

EGGS = "silkworm_eggs_kg"
HOME, PARTNER = "rome_100ad", "han_china_100ad"

QUICK_TOPIC = True

# --- the stand-ins are gone and no route node stands in for the stock.
check("the native-stock stand-in node is gone", "tx2_silkworm_native_stock" not in NODES, None)
check("the acquire-the-stock research node is gone", "tx2_silkworm_stock" not in NODES, None)
for _node_id in ("tx2_silk_fibre", "tx2_sericulture"):
    _node = NODES[_node_id]
    _options = {option for group in _node.get("req_any") or [] for option in group["options"]}
    check("%s needs the eggs held and no route node" % _node_id,
          EGGS in (_node.get("holds") or {}) and "sea_monsoon_route" not in _node["pre"]
          and "sea_monsoon_route" not in _options, _node.get("holds"))
check("the partner's starting techs name no stock node",
      not {"tx2_silkworm_stock", "tx2_silkworm_native_stock"} & set(load_civ(PARTNER)["starting_techs"]), None)

check("the partner's state starts with the eggs as a monopoly",
      EGGS in load_civ(PARTNER).get("state_monopolies", ()), load_civ(PARTNER).get("state_monopolies"))
check("the founding-herd voyage grants the herd it brings",
      (NODES["exp_import_draught_animals"].get("grants") or {}).get("draught_animal_kg", 0) > 0,
      NODES["exp_import_draught_animals"].get("grants"))
check("the ramie stock research node is gone and the fibre needs the stock held",
      "tx2_ramie_plant_stock" not in NODES
      and "ramie_stock_kg" in (NODES["tx2_ramie_fibre"].get("holds") or {}), None)
