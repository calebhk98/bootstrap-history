"""What it costs a year to keep an output-derived node running.

Revenue is what the node sells less the materials and energy it buys, so the
running costs left to state are its staff and the upkeep of its plant:
- staff: the hours its lines need, at the civilisation's wages for each trade
  (the same hours the solver charges into the price of what the node makes);
- plant: a share of what its plant cost to build each year, by kind of node (the kernel, `plant_figures`). The plant is the
  capital goods its production entries state, with the build bills they state; an entry that
  states none is capital-light by the data's own judgement, the solved price carries no capital
  charge for it, and so none is kept up here.
Nothing here reads an authored upkeep figure.
"""
from typing import Mapping, Optional

from sim.unit_conversions import HOURS_PER_PERSON_YEAR
from sim.world import plant_figures


def maintenance_hours(node: Mapping, build_cost_hours: float, wear_hours: Optional[float] = None) -> float:
    """Labour hours a year to maintain the node's plant (the kernel's `maintenance_hours` for its kind of node)."""
    return plant_figures.maintenance_hours(node.get("kind"), build_cost_hours, wear_hours)


# Staffing resources a node's `sch` and `art` places fill, paid at these trades' wages.
SCHOLAR_STAFF_TRADE = "scholar"
CRAFT_STAFF_TRADE = "artisan"


def staff_places_hours_cost(node: Mapping, wages: Mapping[str, float], money_per_labour_hour: float) -> float:
    """Labour hours (of unskilled work) a year the node's named staff places are paid: `sch` scholars and
    `art` craftsmen, each working a year."""
    paid = (float(node.get("sch") or 0.0) * wages[SCHOLAR_STAFF_TRADE]
            + float(node.get("art") or 0.0) * wages[CRAFT_STAFF_TRADE])
    return paid * HOURS_PER_PERSON_YEAR / money_per_labour_hour


def programme_spending_hours(node: Mapping, goods: Mapping[str, float], wages: Mapping[str, float],
                             money_per_labour_hour: float) -> float:
    """Labour hours a year a programme costs to keep running, priced from what it buys: the hours of each trade it
    employs (`annual_labour_hours`) at wages and the materials it consumes (`annual_consumables`) at solved prices.
    The actor that opens the node pays this each year."""
    bought = sum(wages[trade] * hours for trade, hours in (node.get("annual_labour_hours") or {}).items())
    bought += sum(goods.get(material, 0.0) * quantity
                  for material, quantity in (node.get("annual_consumables") or {}).items())
    return bought / money_per_labour_hour


def is_programme(node: Mapping) -> bool:
    return bool(node.get("annual_labour_hours") or node.get("annual_consumables"))


def unstated_upkeep_hours(node: Mapping, build_bill_hours: float) -> float:
    """Upkeep of a node that states none and runs no entries: the upkeep of what it cost to build (its
    labour, materials and tooling), by kind of node."""
    return maintenance_hours(node, build_bill_hours)


def non_labour_share(node: Mapping) -> float:
    """The share of the node's upkeep that is not its crew's pay (the kernel's rule over the node's stated parts)."""
    return plant_figures.non_labour_share(node.get("_upkeep_hours_parts"), node.get("_upkeep_basis"))


def non_labour_upkeep_money(upkeep: float, node: Mapping, capacity: float, cost_scale: float) -> float:
    """Yearly upkeep money (`upkeep`, the node's stated figure) of a concern at `capacity` times its founding size, without its crew's pay (the crew is hired
    through the labour market and paid wages there)."""
    return upkeep * non_labour_share(node) * cost_scale * capacity
