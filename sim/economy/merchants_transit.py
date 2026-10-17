"""Goods on the road and news on the road (Complaints/517).

A haul takes the days the route takes (`CarriageTable.days_between`). The economy steps in years, so a
haul is held for as many whole years as its days span, at least one: the year every merchant already
holds its goods between buying and selling. Goods that need more than that wait on the road in the
transit account (an edge, so a save keeps them) and reach the destination tile in the year their days
put them in. Each year on the road costs the good's spoilage and the interest on the money tied up, which
the merchant weighs when it chooses the route (merchants.py) and pays through its loans.
News of a distant market travels the same way: the merchant hears a price as many years late as the haul
to that market is held beyond the first.
"""
import math
from dataclasses import dataclass
from typing import List, Mapping, Tuple

from sim.unit_conversions import CIVIL_DAYS_PER_YEAR

from .types import EDGE_SPOILAGE, GoodId, GoodsMove, GoodSpec, TileId

EDGE_TRANSIT = "edge:transit"        # goods on the road between a merchant's purchase and its destination tile


@dataclass(frozen=True)
class Shipment:
    good: GoodId
    quantity: float
    destination_tile: TileId       # where the goods wait in the transit account
    years_left: int                # year-ends before they reach the destination


def years_held(days: float) -> int:
    """Whole years a haul of `days` is held between purchase and sale: one for any haul inside a year."""
    if days == math.inf:
        return 10 ** 6
    return max(1, math.ceil(days / CIVIL_DAYS_PER_YEAR))


def lost_share(spoilage_per_year: float, years: int) -> float:
    """The share of a good that spoils over `years` of holding."""
    return 1.0 - (1.0 - min(1.0, max(0.0, spoilage_per_year))) ** years


def advance(merchant, specs: Mapping[GoodId, GoodSpec]) -> Tuple[GoodsMove, ...]:
    """A year passes for the merchant's shipments: each spoils for the year on the road, and those whose
    years are done reach their destination tile. Returns the moves to book; updates `merchant.in_transit`."""
    moves: List[GoodsMove] = []
    remaining: List[Shipment] = []
    for shipment in merchant.in_transit:
        spec = specs.get(shipment.good)
        lost = shipment.quantity * lost_share(spec.spoilage_per_year if spec else 0.0, 1)
        if lost > 0.0:
            moves.append(GoodsMove(EDGE_TRANSIT, EDGE_SPOILAGE, shipment.good, shipment.destination_tile, lost, "spoilage"))
        quantity = shipment.quantity - lost
        if shipment.years_left <= 1:
            if quantity > 0.0:
                moves.append(GoodsMove(EDGE_TRANSIT, merchant.agent_id, shipment.good, shipment.destination_tile, quantity,
                                       "arrived from the road"))
        else:
            remaining.append(Shipment(shipment.good, quantity, shipment.destination_tile, shipment.years_left - 1))
    merchant.in_transit = remaining
    return tuple(moves)


def news_lag(carriage, from_tile: TileId, to_tile: TileId) -> int:
    """Years a price at `to_tile` is old when it reaches `from_tile`, beyond the year every price is
    already old when the merchant acts on it: the years the haul between them is held, less the first."""
    return years_held(carriage.days_between(from_tile, to_tile)) - 1


def heard(merchant, key, price: float, lag: int):
    """The price the merchant hears this year from the market `key` (good, area) `lag` years of news away:
    the price of `lag` years ago, or None while the first news has not arrived."""
    if lag <= 0:
        return price
    history = merchant.price_history.setdefault(key, [])
    history.append(price)
    del history[:-(lag + 1)]
    return history[0] if len(history) > lag else None
