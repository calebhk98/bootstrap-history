"""Node revenue against solved costs.

Each node with authored revenue is one of:
- "output": it gates production entries and the data gives it a physical yearly
  output (`node_output`); it earns that output at solved prices less what it buys.
- "knowledge": a science that makes nothing; it earns nothing.
- "authored": equipment, institutions and services whose product the tree does not
  yet state (what each would physically earn: fees from the people served, a share
  of the trade it enables, the work its machine does). The authored figure stays,
  held under a payback floor so that cheaper solved inputs cannot turn it into a
  money pump.
"""
from typing import Iterable, Mapping

from sim.constants import declare

from . import node_output

MINIMUM_PAYBACK_YEARS = declare(
    "MINIMUM_PAYBACK_YEARS", 0.25, kind="temporary_heuristic", unit="years", source=None,
    confidence="D",
    why="Authored revenue hours were written against older, higher material costs. "
        "A node whose revenue is neither derived from output nor nil is held to at "
        "most its whole cost divided by this payback, standing for competitors "
        "entering any activity that repays its cost faster. It goes when the tree "
        "states what services, institutions and equipment produce.")


def apply_revenue(nodes: Iterable[dict], goods: Mapping[str, float],
                  wages: Mapping[str, float], money_per_labour_hour: float) -> None:
    """Set each node's `rev_hours` and `_revenue_basis`."""
    from sim.world.labour_market import production_data
    production = production_data()
    for node in nodes:
        authored = node.get("_rev_hours_authored", node.get("rev_hours", 0.0))
        node["_rev_hours_authored"] = authored
        if authored <= 0.0:
            continue
        gated = node_output.entries_gated_by(node["id"], production)
        baskets = node_output.output_baskets(node, production, goods) if gated else None
        if baskets is not None:
            outputs, purchases = baskets
            sold = sum(quantity * goods[material] for material, quantity in outputs.items())
            bought = sum(quantity * goods.get(material, 0.0) for material, quantity in purchases.items())
            node["_output_per_year"], node["_purchases_per_year"] = outputs, purchases
            node["rev_hours"] = max(0.0, sold - bought) / money_per_labour_hour
            node["_revenue_basis"] = "output"
        elif node.get("kind") == "SCIENCE" and not gated:
            node["rev_hours"] = 0.0
            node["_revenue_basis"] = "knowledge"
        else:
            node["_revenue_basis"] = "authored"
            node["rev_hours"] = _held_under_floor(node, authored, wages, money_per_labour_hour)


def _held_under_floor(node: dict, authored: float, wages: Mapping[str, float],
                      money_per_labour_hour: float) -> float:
    cost_hours = (sum(wages[trade] * hours for trade, hours in node["lab"].items())
                  / money_per_labour_hour + node["_material_hours"] + node["cap_hours"])
    if cost_hours <= 0.0:
        return authored
    return min(authored, cost_hours / MINIMUM_PAYBACK_YEARS * (1.0 - 1e-9))
