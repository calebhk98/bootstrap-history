"""Node revenue against solved costs.

A node that declares a physical yearly output earns what that output sells for
at solved prices. A node without one keeps its authored `rev_hours`, held under
a payback floor so that cheaper solved inputs cannot turn authored revenue into
a money pump.
"""
from typing import Iterable, Mapping

from sim.constants import declare

MINIMUM_PAYBACK_YEARS = declare(
    "MINIMUM_PAYBACK_YEARS", 0.25, kind="temporary_heuristic", unit="years", source=None,
    confidence="D",
    why="Authored revenue hours were written against older, higher material costs. "
        "Where a node declares no physical output to derive revenue from, its revenue "
        "is held to at most its whole cost divided by this payback, standing for "
        "competitors entering any activity that repays its cost faster. It goes when "
        "every node's revenue is derived from what it produces.")


def apply_revenue(nodes: Iterable[dict], goods: Mapping[str, float],
                  wages: Mapping[str, float], money_per_labour_hour: float) -> None:
    """Set each node's `rev_hours` from its output or its capped authored figure."""
    from .actors.supply import materials_made_by
    for node in nodes:
        node["_rev_hours_authored"] = node.get("rev_hours", 0.0)
        made = [material for material in materials_made_by(node["id"]) if material in goods]
        declared = float(node.get("annual_output_t") or 0.0)
        if declared > 0.0 and made:
            kilograms = declared * 1000.0 / len(made)
            node["rev_hours"] = sum(kilograms * goods[material] for material in made) / money_per_labour_hour
            continue
        authored = node.get("rev_hours", 0.0)
        if authored <= 0.0:
            continue
        cost_hours = (sum(wages[trade] * hours for trade, hours in node["lab"].items())
                      / money_per_labour_hour + node["_material_hours"] + node["cap_hours"])
        if cost_hours <= 0.0:
            continue
        node["rev_hours"] = min(authored, cost_hours / MINIMUM_PAYBACK_YEARS * (1.0 - 1e-9))
