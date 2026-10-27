"""Capital a node needs beyond the labour and materials it states.

What the data states is the plant the node's production entries run in (their `capital` build bills)
and the staff places the node names (`sch` and `art`). Each staff place needs tooling and a bench; a node
that states no staff and no plant needs nothing beyond its own labour and materials. A node may still
state its own `cap_hours` (a mod does); that figure is kept and labelled authored.
"""
from typing import Any, Mapping, Tuple

from sim.constants import declare
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

WORKPLACE_TOOLING_PERSON_YEARS_PER_PLACE = declare(
    "WORKPLACE_TOOLING_PERSON_YEARS_PER_PLACE", 1.0, kind="temporary_heuristic",
    unit="person-years of work per staff place", source=None, confidence="D",
    why="Tools, bench and fittings for one staff place cost about the hours that place works in a year "
        "(a kit that lasts a few years is a few months of its owner's work). It goes when the tree states "
        "tools per trade, the way production entries state their `capital`.")


def staff_places(node: Mapping[str, Any]) -> float:
    return float(node.get("sch") or 0.0) + float(node.get("art") or 0.0)


def tooling_hours(node: Mapping[str, Any]) -> float:
    """Labour hours of tooling for the staff places the node names."""
    return staff_places(node) * WORKPLACE_TOOLING_PERSON_YEARS_PER_PLACE * HOURS_PER_PERSON_YEAR


def capital_hours(node: Mapping[str, Any], plant_build_hours: float = 0.0) -> float:
    """Labour hours of capital: the plant the entries state plus tooling for the staff places."""
    return plant_build_hours + tooling_hours(node)


def resolve(node: Mapping[str, Any], plant_build_hours: float = 0.0) -> Tuple[float, str]:
    """(capital in labour hours, "authored" or "derived") for a node."""
    stated = node.get("_cap_hours_authored", node.get("cap_hours"))
    if stated is not None:
        return float(stated), "authored"
    return capital_hours(node, plant_build_hours), "derived"
