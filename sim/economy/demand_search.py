"""Sellers that sell out with buyers turned away raise their asks within the year's clearing, the mirror of the unsold
search (unsold_search.py): that one lowers asks to the highest common level at which everything sells, this one raises
them to the highest common level at which the buyers still ask for all that is offered. Beyond it the buyers' money (or their ceilings)
no longer buys the stock, so the ask is where demand equals what is offered. Lengnick 2013, Caiani et al. 2016 and
Peters 2020 raise a firm's price when its inventory runs short as they cut it when stock is left; in a fair or a harvest
market the sold-out seller does so on the spot, since buyers are standing there with money unspent. Without it the
buyers' unspent money was involuntary saving and the price the market remembered stayed below the crossing.
"""
import math
from typing import List, Mapping, Optional, Sequence

from sim.book import ROUNDING_SHARE

from . import goods_market
from .types import Offer

SEARCH_PRECISION = 1e-4     # numerical tolerance of the bisection on the ask level, not a model number


def _lifted(offers: Sequence[Offer], raisable: Sequence[int], level: float,
            limits: Optional[Mapping[int, float]] = None) -> List[Offer]:
    """`offers` with each raisable ask at `level`, no higher than its own limit (an ask already above its limit stays)."""
    chosen = set(raisable)
    limits = limits or {}
    return [Offer(each.seller, each.good, each.area, each.tile, each.quantity,
                  max(each.reservation_price, min(level, limits.get(index, math.inf))))
            if index in chosen else each for index, each in enumerate(offers)]


def _demand_covers(buyers: goods_market.Buyers, offers: Sequence[Offer]) -> bool:
    """True when the buyers ask for at least what is on offer at these asks: the stock sells out, bar what the
    clearing's two rounds of choice (goods_market_logit.py) leave with a seller whose buyers went to others."""
    supply = math.fsum(offer.quantity for offer in offers if offer.quantity > 0.0)
    return goods_market.requested_by_buyers(buyers, offers) >= supply * (1.0 - ROUNDING_SHARE)


def price_ceiling(buyers: goods_market.Buyers, supply: float) -> float:
    """The highest price at which the buyers could still take `supply`: the dearest ceiling any of them has, and the money
    they hold for the good over the units (infinite when neither is finite)."""
    money = math.fsum(max(0.0, bid.budget) for bid in buyers.bids)
    highest = max((bid.maximum_price for bid in buyers.bids), default=0.0)
    return min(highest, money / supply if supply > 0.0 else math.inf)


def raise_asks(buyers: goods_market.Buyers, offers: Sequence[Offer], raisable: Sequence[int],
               limits: Optional[Mapping[int, float]] = None) -> List[Offer]:
    """`offers` with the asks of the `raisable` indices (nothing moves unless the buyers ask for the whole stock now) lifted to the highest
    common level at which the buyers still ask for the whole stock (an ask above the level stays), no higher than the buyers could pay for the stock.
    `limits` (index -> the most that seller may ask, the band above its cost) hold a seller below the common level."""
    offers = list(offers)
    if not raisable or not _demand_covers(buyers, offers):
        return offers
    lowest = min(offers[index].reservation_price for index in raisable)
    supply = math.fsum(offer.quantity for offer in offers if offer.quantity > 0.0)
    ceiling = price_ceiling(buyers, supply)
    if lowest <= 0.0 or not math.isfinite(ceiling) or ceiling <= lowest:
        return offers
    if limits:
        ceiling = min(ceiling, max(limits.get(index, math.inf) for index in raisable))
        if ceiling <= lowest:
            return offers
    low, high = lowest, ceiling
    if not _demand_covers(buyers, _lifted(offers, raisable, lowest * (1.0 + SEARCH_PRECISION), limits)):
        return offers
    while high / low - 1.0 > SEARCH_PRECISION:
        middle = math.sqrt(low) * math.sqrt(high)
        if _demand_covers(buyers, _lifted(offers, raisable, middle, limits)):
            low = middle
        else:
            high = middle
    return _lifted(offers, raisable, low, limits)
