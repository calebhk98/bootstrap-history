"""A haul over tiles as legs in order, each with its mode, distance, money per tonne and travel days."""
from dataclasses import dataclass
from typing import Tuple

from sim.geography.api import cargo_cost
from sim.world import trader_response


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


def domestic_cargo_cost_share(spoilage_rate_per_year, loss_per_day_by_mode, route, annual_rate):
    """The cargo's own cost over a domestic haul as a share of its price: interest at `annual_rate` while it
    travels, spoilage over that time, and the daily loss each leg's mode states (a herd on the road). No
    merchant margin."""
    years = route.travel_days / 365.0
    spoilage = cargo_cost.spoilage_share(spoilage_rate_per_year, years)
    road = cargo_cost.lost_share(*(cargo_cost.daily_loss_share(loss_per_day_by_mode.get(leg.mode, 0.0), leg.travel_days)
                                   for leg in route.legs))
    return trader_response.cost_share_of_price(0.0, cargo_cost.lost_share(spoilage, road), annual_rate, years)


def cargo_class_of(stock_row):
    """"living_stock" for stock whose living-stock row says it walks (animals), else "goods" (seed, cuttings, eggs)."""
    return "living_stock" if (stock_row or {}).get("walks") else "goods"


def domestic_haul_mode(cargo, walking_modes, goods_mode):
    """The mode a domestic haul of this class of cargo goes by: `goods_mode` (the cart) for goods, the first mode whose
    cargo walks for living stock, the goods mode when the map has none."""
    if cargo == "living_stock":
        return walking_modes[0] if walking_modes else goods_mode
    return goods_mode


def unjoined_haul_cost(rate_per_tonne_km, distance_km, dues_per_tonne):
    """Money per tonne of a haul no way joins: one leg at the mode's rate over the great-circle distance, plus the dues once."""
    return rate_per_tonne_km * distance_km + dues_per_tonne
