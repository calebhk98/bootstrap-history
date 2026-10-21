"""A merchant's fleet: the carts, saddles, barges and animals it holds bound what it can carry in a year.

A held unit of a carrier good bears `1 / service life` units of wear a year, and a tonne hauled wears
`units_per_tonne` of each carrier good it uses (carriage_wear, from geography's carrier-days per tonne-km and the
route's days). So a fleet bears `capacity[good]` units of wear a year and carries, on a haul, the tonnes its scarcest
carrier good allows. Pure arithmetic: the book-facing parts (what is held, leases, the opening endowment) are in
carriage_fleet_book.
"""
import math
from dataclasses import dataclass
from typing import Callable, Dict, Mapping

GoodId = str
TileId = str


@dataclass(frozen=True)
class FleetLimit:
    """What bounds one merchant's dispatch: `units_per_tonne(source, destination)` is the wear a tonne puts on each
    carrier good on that haul, `capacity` the units of wear a year each fleet good can bear (held and hired); a
    carrier good absent from `capacity` (a feed that is eaten, not held) does not limit."""
    units_per_tonne: Callable[[TileId, TileId], Mapping[GoodId, float]]
    capacity: Mapping[GoodId, float]


def capacity_of(held: Mapping[GoodId, float], lives: Mapping[GoodId, float]) -> Dict[GoodId, float]:
    """Units of wear a year the units `held` of each fleet good can bear: what they lose to age in a year."""
    return {good: units / lives[good] for good, units in held.items() if lives.get(good, 0.0) > 0.0}


def tonnes_within(spare: Mapping[GoodId, float], per_tonne: Mapping[GoodId, float]) -> float:
    """The tonnes a haul wearing `per_tonne` units of each carrier good a tonne can carry on the `spare` wear."""
    limits = [max(0.0, spare[good]) / units for good, units in per_tonne.items() if good in spare and units > 0.0]
    return min(limits) if limits else math.inf


def wanted_fleet(wanted_wear: Mapping[GoodId, float], lives: Mapping[GoodId, float]) -> Dict[GoodId, float]:
    """Units of each fleet good to hold to bear `wanted_wear` units of wear a year."""
    return {good: units * lives[good] for good, units in wanted_wear.items() if lives.get(good, 0.0) > 0.0}
