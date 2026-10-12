"""The price a producer's own additions leave: capacity is judged at the price expected after it exists.

A producer that adds output to a market its buyers' schedules do not absorb at the same price expects less
for every unit, its own as well as the rest. The residual price is read off the market's book as the year
cleared it: the buyers' schedules against the quantity traded, and against that quantity plus the addition,
both offered at any price. A market whose book was not kept, or that traded nothing, shows no price to
move, and the share is one."""
import math
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple

from . import goods_market
from .types import AreaId, Bid, GoodId, Offer, TileId

SELLER = "expansion:price"
PriceShare = Callable[[GoodId, float], float]     # (good, units added a year) -> share of the price that stays


class PreparedMarket:
    """One market's buyers prepared once, with the prices already found for quantities offered to them."""

    def __init__(self, bids: Sequence[Bid]):
        self.buyers = goods_market.Buyers(bids, None)
        self.prices: Dict[Tuple[GoodId, AreaId, float], float] = {}

    def price_with_supply(self, good: GoodId, area: AreaId, quantity: float) -> float:
        key = (good, area, quantity)
        price = self.prices.get(key)
        if price is None:
            price = self.prices[key] = price_with_supply(None, good, area, quantity, self.buyers)
        return price


def price_with_supply(bids: Optional[Sequence[Bid]], good: GoodId, area: AreaId, quantity: float,
                      buyers: Optional[goods_market.Buyers] = None) -> float:
    """The price at which the buyers take exactly `quantity`, all of it offered at no reservation.
    `buyers` is the market's bids prepared once, when the caller has them."""
    if buyers is None:
        buyers = goods_market.Buyers(bids, None)
    offer = Offer(SELLER, good, area, "", quantity, 0.0)
    # the crossing is the price `goods_market.clear` reports; the fills it would also build are not needed
    return goods_market._crossing(buyers, goods_market.in_clearing_order([offer]), with_wants=False)[0]


def share_after_addition(bids: Sequence[Bid], good: GoodId, area: AreaId, traded: float, added: float,
                         prepared: Optional[PreparedMarket] = None) -> float:
    """The share of the market's price that remains when `added` more units a year are offered beyond the
    `traded` quantity the year cleared; one when nothing is added or the book shows no price."""
    if not bids or not traded > 0.0 or not added > 0.0:
        return 1.0
    if prepared is None:
        prepared = PreparedMarket(bids)
    before = prepared.price_with_supply(good, area, traded)
    if not before > 0.0:
        return 1.0
    after = prepared.price_with_supply(good, area, traded + added)
    return max(0.0, min(1.0, after / before)) if math.isfinite(after) else 1.0


def price_share_of(bids_by_market: Mapping[Tuple[GoodId, AreaId], Sequence[Bid]],
                   traded_by_market: Mapping[Tuple[GoodId, AreaId], float],
                   area_of: Callable[[GoodId, TileId], AreaId], tile: TileId,
                   prepared: Optional[Dict[Tuple[GoodId, AreaId], PreparedMarket]] = None) -> PriceShare:
    """For a producer on `tile`: the share of its market's price that stays after it adds units of a good,
    from the year's bids and traded quantities. `prepared` keeps each market's prepared buyers across producers."""
    if prepared is None:
        prepared = {}

    def share(good: GoodId, added: float) -> float:
        area = area_of(good, tile)
        key = (good, area)
        bids = bids_by_market.get(key, ())
        if not bids or not added > 0.0:
            return 1.0
        market = prepared.get(key)
        if market is None:
            market = prepared[key] = PreparedMarket(bids)
        return share_after_addition(bids, good, area, traded_by_market.get(key, 0.0), added, market)
    return share
