"""Sellers that sell out with buyers turned away raise their asks within the year's clearing, the mirror of the unsold
search (unsold_search.py): that one lowers asks to the highest common level at which everything sells, this one raises
them to the highest common level at which the buyers still ask for all that is offered. Beyond it the buyers' money (or their ceilings)
no longer buys the stock, so the ask is where demand equals what is offered. Lengnick 2013 and Caiani et al. 2016
raise a firm's price when its inventory runs short as they cut it when stock is left; Peters 2022 (arXiv 2205.00752) sets
its price rule by output against the demand since the last strategy change, with a NAIRU and an average-price condition,
not by inventory. In a fair or a harvest
market the sold-out seller does so on the spot, since buyers are standing there with money unspent. Without it the
buyers' unspent money was involuntary saving and the price the market remembered stayed below the crossing.
"""
import math
from typing import List, Mapping, Optional, Sequence

import numpy

from . import goods_market, goods_market_kernels
from .goods_market_kernels import SEARCH_PRECISION
from .types import Offer


def _lifted(offers: Sequence[Offer], raisable: Sequence[int], level: float,
            limits: Optional[Mapping[int, float]] = None) -> List[Offer]:
    """`offers` with each raisable ask at `level`, no higher than its own limit (an ask already above its limit stays)."""
    chosen = set(raisable)
    limits = limits or {}
    return [Offer(each.seller, each.good, each.area, each.tile, each.quantity,
                  max(each.reservation_price, min(level, limits.get(index, math.inf))))
            if index in chosen else each for index, each in enumerate(offers)]


class _Book:
    """The offers with units to sell, in seller-and-tile order, as the kernels read them: asks, quantities, which
    asks may be raised and by how far."""

    def __init__(self, buyers: goods_market.Buyers, offers: Sequence[Offer], raisable: Sequence[int],
                 limits: Optional[Mapping[int, float]]):
        positions = sorted((index for index, offer in enumerate(offers) if offer.quantity > 0.0),
                           key=lambda index: (offers[index].seller, offers[index].tile))
        chosen = set(raisable)
        self.reservations = numpy.array([offers[index].reservation_price for index in positions], dtype=float)
        self.quantities = numpy.array([offers[index].quantity for index in positions], dtype=float)
        self.raisable = numpy.array([index in chosen for index in positions], dtype=bool)
        self.limits = numpy.array([(limits or {}).get(index, math.inf) for index in positions], dtype=float)
        minimum = buyers.minimum_price
        self.minimum = 0.0 if minimum is None else minimum
        self.has_minimum = minimum is not None
        self.buyer_arrays = buyers.arrays.kernel_arrays()

    def covered(self) -> bool:
        """True when the buyers ask for at least what is on offer at these asks: the stock sells out, bar what the
        clearing's rounds of choice (goods_market_logit.py) leave with a seller whose buyers went to others."""
        return bool(goods_market_kernels.covers_at(self.reservations, self.quantities, numpy.full(len(self.quantities), -1.0),
                                                   self.minimum, self.has_minimum, *self.buyer_arrays))

    def highest_covered_level(self, lowest: float, ceiling: float) -> float:
        """The highest common level in [lowest, ceiling] at which every raisable ask lifted to it (to its limit) is
        still covered; -1 when not even a level just above `lowest` is."""
        return float(goods_market_kernels.raise_search(self.reservations, self.quantities, self.raisable, self.limits,
                                                       lowest, ceiling, self.minimum, self.has_minimum, *self.buyer_arrays))


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
    if not raisable:
        return offers
    book = _Book(buyers, offers, raisable, limits)
    if not book.covered():
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
    level = book.highest_covered_level(lowest, ceiling)
    return offers if level < 0.0 else _lifted(offers, raisable, level, limits)
