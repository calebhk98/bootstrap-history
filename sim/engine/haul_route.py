"""A haul over tiles as legs in order, each with its mode, distance, money per tonne and travel days."""
from dataclasses import dataclass
from typing import Tuple


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
    """A haul over tiles: legs in order from the partner's tiles to this society's."""
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
        return " > ".join("%s -%s-> %s" % (leg.origin, leg.mode, leg.destination) for leg in self.legs)


def route_from_geography(found):
    """A `Route` from the geography contract's answer (its handling days count as travel)."""
    return Route(tuple(
        Leg(leg["from"], leg["to"], leg["mode"], leg["km"], leg["cost_per_tonne"],
            leg["days"] + leg.get("handling_days", 0.0))
        for leg in found["legs"]))
