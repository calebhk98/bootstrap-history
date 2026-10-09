"""What it costs a year to keep an output-derived node running.

Revenue is what the node sells less the materials and energy it buys, so the
running costs left to state are its staff and the upkeep of its plant:
- staff: the hours its lines need, at the civilisation's wages for each trade
  (the same hours the solver charges into the price of what the node makes);
- plant: a share of what its plant cost to build each year, by kind of node. The plant is the
  capital goods its production entries state, with the build bills they state; an entry that
  states none is capital-light by the data's own judgement, the solved price carries no capital
  charge for it, and so none is kept up here.
Nothing here reads an authored upkeep figure.
"""
from typing import Iterable, Mapping, Optional, Tuple

from sim.constants import declare
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

PLANT_MAINTENANCE_SHARE_PER_YEAR = {
    "INFRASTRUCTURE": declare(
        "PLANT_MAINTENANCE_SHARE_INFRASTRUCTURE", 0.02, kind="temporary_heuristic",
        unit="share of build cost per year", source=None, confidence="D",
        why="Yearly upkeep of earthworks, masonry and channels as a share of what they cost to "
            "build. It goes when each plant states the parts it renews and their lives "
            "(the `capital` entries of the production data already do for some)."),
    "ENGINEERING": declare(
        "PLANT_MAINTENANCE_SHARE_ENGINEERING", 0.04, kind="temporary_heuristic",
        unit="share of build cost per year", source=None, confidence="D",
        why="Yearly upkeep of machinery and workshop plant as a share of what it cost to build; "
            "moving parts wear faster than masonry. Replaced by per-part lives as above."),
    "RESOURCE": declare(
        "PLANT_MAINTENANCE_SHARE_RESOURCE", 0.03, kind="temporary_heuristic",
        unit="share of build cost per year", source=None, confidence="D",
        why="Yearly upkeep of workings and held resources (shoring, drainage, fences) as a share "
            "of what they cost to open."),
}
DEFAULT_MAINTENANCE_SHARE = declare(
    "PLANT_MAINTENANCE_SHARE_DEFAULT", 0.03, kind="temporary_heuristic",
    unit="share of build cost per year", source=None, confidence="D",
    why="Yearly upkeep share for a node whose kind has no share of its own.")


def maintenance_hours(node: Mapping, build_cost_hours: float, wear_hours: Optional[float] = None) -> float:
    """Labour hours a year to maintain the plant: a share of what it cost to build, by kind of node, and
    never more than the wear the solved price already charges for the same plant (maintenance is part
    of keeping a plant to its service life, not a charge on top of it)."""
    share = PLANT_MAINTENANCE_SHARE_PER_YEAR.get(node.get("kind"), DEFAULT_MAINTENANCE_SHARE)
    kept = share * build_cost_hours
    return kept if wear_hours is None else min(kept, wear_hours)


def staff_hours_cost(labour_hours_by_trade: Mapping[str, float], wages: Mapping[str, float],
                     money_per_labour_hour: float) -> float:
    """Labour hours (of unskilled work) a year the lines' staff are paid."""
    return sum(wages[trade] * hours for trade, hours in labour_hours_by_trade.items()) / money_per_labour_hour


def _capital_build_hours(capital: Mapping, goods: Mapping[str, float], wages: Mapping[str, float],
                         money_per_labour_hour: float) -> float:
    money = sum(goods.get(material, 0.0) * quantity
                for material, quantity in (capital.get("build_materials") or {}).items())
    money += sum(wages[trade] * hours for trade, hours in (capital.get("build_labour_hours") or {}).items())
    return money / money_per_labour_hour


def plant_build_hours(plant: Iterable[Tuple[Mapping, float]], goods: Mapping[str, float],
                      wages: Mapping[str, float], money_per_labour_hour: float) -> float:
    """Labour hours it takes to build one of each capital good the lines run in: its materials at solved
    prices and its labour at wages (the build bill each production entry states)."""
    return sum(_capital_build_hours(capital, goods, wages, money_per_labour_hour) for capital, _used in plant)


def plant_wear_hours(plant: Iterable[Tuple[Mapping, float]], goods: Mapping[str, float],
                     wages: Mapping[str, float], money_per_labour_hour: float) -> float:
    """Labour hours a year the plant wears out at the share of its capacity the lines use: its build
    bill over its service life, which the solved price of what it makes charges per unit."""
    return sum(_capital_build_hours(capital, goods, wages, money_per_labour_hour)
               / capital["service_life_years"] * used for capital, used in plant if capital.get("service_life_years"))



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
