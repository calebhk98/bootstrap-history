"""A seller left with unsold stock lowers its ask within the year's clearing until the stock sells or the ask
reaches the seller's floor, what a unit is worth to it unsold (never below what it costs to make).

Only producers whose ask is the one `producers.offers` gave them are searched: a seller that moves the price
chose its ask against the whole book (seller_offers.py) and holds units back on purpose. When any of them
is unsold, all of them are brought down to a common ask level, each to no lower than its own floor, because
a seller that undercuts leaves its rivals unsold in turn; the level is the highest at which all of them sell
out or sit at their floors, found by bisection on whole-market clears. A market with no unsold searchable
stock clears once, and a sold-out seller's ask is raised between years by ask_raise.py.
"""
import dataclasses
import math
from typing import List, Optional, Sequence, Tuple

from sim.book import ROUNDING_SHARE

from . import goods_market, seller_offers
from .types import Offer

SEARCH_PRECISION = 1e-4     # numerical tolerance of the bisection on the ask level, not a model number


def _sold_by_offer(result, offers: Sequence[Offer]) -> List[float]:
    sold = {}
    for fill in result.fills:
        if fill.side == "sell":
            key = (fill.agent, fill.tile)
            sold[key] = sold.get(key, 0.0) + fill.quantity
    return [sold.get((each.seller, each.tile), 0.0) for each in offers]


def _unsold(result, offers: Sequence[Offer], indices: Sequence[int]) -> List[int]:
    sold = _sold_by_offer(result, offers)
    return [index for index in indices if sold[index] < offers[index].quantity * (1.0 - ROUNDING_SHARE)]


def _floors(setup, record, view, offers: Sequence[Offer], original: Sequence[Offer]) -> dict:
    """Searchable offers (index -> floor): a producer's unchanged ask above what a unit is worth to it unsold."""
    floors = {}
    for index, offer in enumerate(offers):
        if offer.quantity <= 0.0 or offer.reservation_price != original[index].reservation_price:
            continue
        cost = seller_offers.unit_cost(setup, record, view, offer)
        if cost is None:
            continue
        floor = seller_offers.unit_value(offer, cost)
        if offer.reservation_price > floor:
            floors[index] = floor
    return floors


def _with_level(offers: Sequence[Offer], floors: dict, level: float) -> List[Offer]:
    return [dataclasses.replace(each, reservation_price=min(each.reservation_price, max(floors[index], level)))
            if index in floors else each for index, each in enumerate(offers)]


def clear_with_search(setup, record, view, bids, original: Sequence[Offer], offers: Sequence[Offer], good, area,
                      currency, last_price: Optional[float]) -> Tuple[List[Offer], object]:
    """(the offers after the search, the market's clearing with them). `original` are the offers before the
    sellers re-chose, `offers` after; a market with no unsold searchable stock clears once."""
    offers = list(offers)
    result = goods_market.clear(bids, offers, good, area, currency, last_price)
    floors = _floors(setup, record, view, offers, original)
    unsold = _unsold(result, offers, list(floors))
    if not unsold:
        return offers, result
    searched = list(floors)       # a seller undercut by a lower ask becomes unsold in turn: all are searched together

    def trial(level: float):
        candidate = _with_level(offers, {index: floors[index] for index in searched}, level)
        cleared = goods_market.clear(bids, candidate, good, area, currency, last_price)
        return candidate, cleared, [index for index in _unsold(cleared, candidate, searched)
                                    if candidate[index].reservation_price > floors[index]]

    low = min(floors[index] for index in searched)
    best = trial(low)         # every searched ask at its floor: nothing above a floor can stay unsold
    high = max(offers[index].reservation_price for index in searched)
    while high - low > SEARCH_PRECISION * max(high, 1e-300):
        middle = math.sqrt(low * high) if low > 0.0 else 0.5 * (low + high)
        attempt = trial(middle)
        if attempt[2]:
            high = middle
        else:
            low, best = middle, attempt
    return best[0], best[1]
