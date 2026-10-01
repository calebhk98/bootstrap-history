"""The cheapest route between two sets of regions over a graph of links, each
leg carried by the cheapest mode both ends can use.

Standalone: a caller supplies the network (data/world/trade_routes.json), what
each mode costs per tonne-km, the techs held at each end and a distance
function. The result keeps its legs so a player can see the route on the map.
"""
import heapq
import json
import os
from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, Iterable, Optional, Tuple

ROUTES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "world", "trade_routes.json")


@dataclass(frozen=True)
class Leg:
    origin: str
    destination: str
    mode: str
    distance_km: float
    cost_per_tonne: float
    travel_days: float = 0.0


@dataclass(frozen=True)
class Route:
    legs: Tuple[Leg, ...]

    @property
    def cost_per_tonne(self):
        return sum(leg.cost_per_tonne for leg in self.legs)

    @property
    def distance_km(self):
        return sum(leg.distance_km for leg in self.legs)

    @property
    def travel_days(self):
        return sum(leg.travel_days for leg in self.legs)

    def describe(self):
        return " > ".join("%s -%s-> %s" % (leg.origin, leg.mode, leg.destination)
                          for leg in self.legs)


def load_network(path=ROUTES_PATH):
    """{"modes": {...}, "links": [...]} as authored."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def usable_modes(network, technologies_of_each_end: Iterable[Iterable[str]]) -> FrozenSet[str]:
    """Modes whose node every end holds."""
    held = [frozenset(technologies) for technologies in technologies_of_each_end]
    return frozenset(mode for mode, rule in network["modes"].items()
                     if all(rule.get("requires_node") in end for end in held))


def _leg_choice(link, mode_rules, regions, modes, held_by_either, distance_km,
                cost_per_tonne_km, handling_per_tonne, difficulty):
    """(cost per tonne, mode, km, difficulty factor) of the cheapest usable mode on a link, or None."""
    if link.get("requires_node") and link["requires_node"] not in held_by_either:
        return None
    origin, destination = regions.get(link["from"]), regions.get(link["to"])
    if origin is None or destination is None:
        return None
    km = link.get("km") or distance_km(origin["lat"], origin["lon"],
                                       destination["lat"], destination["lon"])
    best = None
    for mode in link["modes"]:
        if mode not in modes or mode not in cost_per_tonne_km:
            continue
        if mode_rules[mode].get("needs_ports") and not (
                origin.get("coastal") and destination.get("coastal")):
            continue
        factor = 1.0 if mode == "sea" else difficulty(origin, destination)
        cost = km * factor * cost_per_tonne_km[mode] + handling_per_tonne.get(mode, 0.0)
        if best is None or cost < best[0]:
            best = (cost, mode, km, factor)
    return best


def cheapest_route(network, regions: Dict[str, dict], origins: Iterable[str],
                   destinations: Iterable[str], modes: FrozenSet[str],
                   held_by_either: FrozenSet[str], distance_km: Callable,
                   cost_per_tonne_km: Dict[str, float],
                   handling_per_tonne: Optional[Dict[str, float]] = None,
                   difficulty: Optional[Callable] = None,
                   days_per_km: Optional[Dict[str, float]] = None) -> Optional[Route]:
    """Least-cost chain of legs from any origin region to any destination
    region, or None when the network does not join them. A shared region
    makes a route of no legs (cost zero). `days_per_km` gives each mode's
    travel time over level ground; a leg's days are that times its length and
    difficulty."""
    handling_per_tonne = handling_per_tonne or {}
    days_per_km = days_per_km or {}
    difficulty = difficulty or (lambda origin, destination: 0.5 * (
        origin.get("route_difficulty", 1.0) + destination.get("route_difficulty", 1.0)))
    neighbours: Dict[str, list] = {}
    for link in network["links"]:
        choice = _leg_choice(link, network["modes"], regions, modes, held_by_either,
                             distance_km, cost_per_tonne_km, handling_per_tonne, difficulty)
        if choice is None:
            continue
        cost, mode, km, factor = choice
        days = km * factor * days_per_km.get(mode, 0.0)
        neighbours.setdefault(link["from"], []).append(
            (link["to"], Leg(link["from"], link["to"], mode, km, cost, days)))
        neighbours.setdefault(link["to"], []).append(
            (link["from"], Leg(link["to"], link["from"], mode, km, cost, days)))
    goals = set(destinations)
    queue = [(0.0, index, origin, ()) for index, origin in enumerate(sorted(set(origins)))]
    sequence = len(queue)
    heapq.heapify(queue)
    settled = set()
    while queue:
        cost, _order, region, legs = heapq.heappop(queue)
        if region in settled:
            continue
        settled.add(region)
        if region in goals:
            return Route(legs)
        for next_region, leg in sorted(neighbours.get(region, ()), key=lambda pair: pair[0]):
            if next_region not in settled:
                sequence += 1
                heapq.heappush(queue, (cost + leg.cost_per_tonne, sequence, next_region,
                                       legs + (leg,)))
    return None
