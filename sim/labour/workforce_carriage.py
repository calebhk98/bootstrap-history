"""Crew hours to carry one tonne a typical haul, by trade: carriage as a labour need (carters, sailors).

The goods households and producers use are moved, and the movers are sailors and carriers. The
hours per tonne-km are geography's (the physical inputs the route search prices a haul with), for the
carriage modes the society's technologies unlock; this module turns them into hours per tonne of goods
by trade for `workforce_spinup.need_shares_by_trade`.
"""
import collections
from typing import Dict, Iterable

import sim.geography.api as geography
from sim.constants import declare

MEAN_HAUL_KM = declare(
    "MEAN_HAUL_KM", 150.0, kind="temporary_heuristic",
    unit="km a tonne of goods travels between the place made and the place used",
    source=None, confidence="D",
    why="One distance for every good, standing for the spread of real hauls (ore to furnace, grain to "
        "town, goods to market). A haul length per good from the tiles that make and use it would replace "
        "it; measure with the need shares for a civilisation with and without carriage.")


def _carriage_group(edge_classes: Iterable[str]) -> str:
    return "land" if "land" in edge_classes else "water"


def carriage_hours_per_tonne_by_trade(reached_nodes: Iterable[str]) -> Dict[str, float]:
    """{trade: crew hours to carry one tonne a mean haul}. [temporary_heuristic] Land and water carriage
    carry equal shares of the tonnage where both are usable, each by its least-hours mode, until
    haul shares come from the geography of where goods are made and used."""
    rates = geography.carriage_rates(geography.usable_modes([frozenset(reached_nodes)]))
    best_by_group: Dict[str, Dict[str, object]] = {}
    for rate in rates.values():
        group = _carriage_group(rate["edge_classes"])
        held = best_by_group.get(group)
        if held is None or rate["crew_hours_per_tonne_km"] < held["crew_hours_per_tonne_km"]:
            best_by_group[group] = rate
    hours: Dict[str, float] = collections.defaultdict(float)
    for rate in best_by_group.values():
        hours[rate["crew_trade"]] += (MEAN_HAUL_KM * rate["crew_hours_per_tonne_km"]
                                      / len(best_by_group))
    return dict(hours)
