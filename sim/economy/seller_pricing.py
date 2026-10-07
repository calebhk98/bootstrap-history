"""A seller that moves the clearing price chooses its reservation against the rest of the market's book.

The market clears at one price where the buyers' schedules meet the sellers' reservations, so a seller's
reservation decides how much it sells and at what price. A seller whose removal or withdrawal changes that
price faces a residual demand (the buyers' schedules less what its rivals offer) and picks the reservation
that maximises (price - the value of one more unit to it) * what it sells. Whether it matters is read off
the book: it is the change in the clearing price when it adds its offer, and a seller who moves nothing
keeps the price-taking rule (`best_reservation` returns None). Dominant-firm pricing against a competitive
fringe; nothing here names a good, a recipe or an actor.
"""
import math
from dataclasses import replace
from typing import List, Optional, Sequence, Tuple

from sim.constants import declare

from . import goods_market
from .accounts import ROUNDING_SHARE
from .types import Bid, Offer

SEARCH_POINTS = declare(
    "SEARCH_POINTS", 48, kind="temporary_heuristic", unit="reservation prices tried per seller per market",
    source=None, confidence="D",
    why="The best reservation is searched on a geometric grid of prices around the rivals' asks and the "
        "last price, plus the rivals' own asks, because the residual demand has steps and no closed form; "
        "a finer grid costs time per market and moves the answer by less than the grid's spacing.")
SEARCH_SPAN = declare(
    "SEARCH_SPAN", 8.0, kind="temporary_heuristic", unit="multiple of the reference price either way",
    source=None, confidence="D",
    why="How far from the market's price a seller looks for its best reservation; a profit-maximiser "
        "facing a steep schedule could ask more, but a seller does not extrapolate beyond what it has seen.")
JUST_BELOW = 1.0 - 1e-6     # an ask a hair under a rival's, so it sells first


def _clear(bids: Sequence[Bid], rivals: Sequence[Offer], offer: Offer, reservation: Optional[float],
           last_price: Optional[float]):
    offers = list(rivals)
    if reservation is not None:
        offers.append(replace(offer, reservation_price=reservation))
    return goods_market.clear(bids, offers, offer.good, offer.area, "", last_price)


def sold_and_price(bids: Sequence[Bid], rivals: Sequence[Offer], offer: Offer, reservation: float,
                   last_price: Optional[float]) -> Tuple[float, float]:
    """What the seller sells, and the clearing price, if it offers its quantity at `reservation`."""
    result = _clear(bids, rivals, offer, reservation, last_price)
    sold = math.fsum(fill.quantity for fill in result.fills if fill.agent == offer.seller and fill.side == "sell")
    return sold, result.price


def profit_at(bids: Sequence[Bid], rivals: Sequence[Offer], offer: Offer, reservation: float,
              unit_value: float, last_price: Optional[float]) -> float:
    """(clearing price - unit value) * what it sells; `unit_value` is what a unit is worth to it unsold."""
    sold, price = sold_and_price(bids, rivals, offer, reservation, last_price)
    return (price - unit_value) * sold


def moves_the_price(bids: Sequence[Bid], rivals: Sequence[Offer], offer: Offer,
                    last_price: Optional[float]) -> bool:
    """True when adding the seller's whole offer, at the lowest ask, changes the clearing price."""
    without = _clear(bids, rivals, offer, None, last_price).price
    with_it = _clear(bids, rivals, offer, 0.0, last_price).price
    return abs(with_it - without) > ROUNDING_SHARE * max(abs(with_it), abs(without))


def _candidates(rivals: Sequence[Offer], last_price: Optional[float], unit_value: float) -> List[float]:
    reference = last_price if last_price and last_price > 0.0 else max(
        [offer.reservation_price for offer in rivals if offer.reservation_price > 0.0] + [unit_value, 1e-9])
    asks = sorted({offer.reservation_price for offer in rivals if offer.reservation_price > 0.0})
    low, high = reference / SEARCH_SPAN, reference * SEARCH_SPAN
    grid = [low * (high / low) ** (step / (SEARCH_POINTS - 1)) for step in range(SEARCH_POINTS)]
    return sorted({0.0, *asks, *(ask * JUST_BELOW for ask in asks), *grid})


def best_reservation(bids: Sequence[Bid], rivals: Sequence[Offer], offer: Offer, unit_value: float,
                     last_price: Optional[float], ceiling: float = math.inf, floor: float = 0.0) -> Optional[float]:
    """The reservation, between `floor` and `ceiling`, that maximises the seller's profit against the book, or
    None when the seller does not move the price or nothing beats offering at the ceiling."""
    if not moves_the_price(bids, rivals, offer, last_price):
        return None
    start = ceiling if math.isfinite(ceiling) else 0.0
    best, best_profit = None, profit_at(bids, rivals, offer, start, unit_value, last_price)
    for reservation in _candidates(rivals, last_price, unit_value):
        if reservation >= ceiling or reservation < floor:
            continue
        profit = profit_at(bids, rivals, offer, reservation, unit_value, last_price)
        if profit > best_profit + ROUNDING_SHARE * max(abs(best_profit), 1e-300):
            best, best_profit = reservation, profit
    return best
