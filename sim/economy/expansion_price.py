"""The price a producer's own additions leave: capacity is judged at the price expected after it exists.

A producer that adds output to a market its buyers' schedules do not absorb at the same price expects less
for every unit, its own as well as the rest. The residual price is read off the market's book as the year
cleared it: the buyers' schedules against the quantity traded, and against that quantity plus the addition,
both offered at any price. A market whose book was not kept, or that traded nothing, shows no price to
move, and the share is one."""
import math
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple

from . import bid_columns, crossing_price, goods_market
from .types import AreaId, Bid, GoodId, Offer, TileId

SELLER = "expansion:price"
PriceShare = Callable[[GoodId, float], float]     # (good, units added a year) -> share of the price that stays


class PreparedMarket:
    """One market's buyers prepared once, with the prices already found for quantities offered to them. The search runs on the
    bids' columns (crossing_price.py); only a figure the kernels do not reproduce makes `Buyers` of the `Bid` objects."""

    def __init__(self, bids: Sequence[Bid]):
        self.bids = bids
        self._demand: Optional[crossing_price.ColumnDemand] = None
        self._objects: Optional[goods_market.Buyers] = None
        self.prices: Dict[Tuple[GoodId, AreaId, float], Optional[float]] = {}

    @property
    def buyers(self) -> goods_market.Buyers:
        """The bids as objects in clearing order, built when the columns cannot answer."""
        if self._objects is None:
            self._objects = goods_market.Buyers(self.bids, None)
        return self._objects

    def price_with_supply(self, good: GoodId, area: AreaId, quantity: float) -> Optional[float]:
        key = (good, area, quantity)
        price = self.prices.get(key)
        if price is None:
            price = self.prices[key] = self._price(good, area, quantity)
        return price

    def _price(self, good: GoodId, area: AreaId, quantity: float) -> Optional[float]:
        try:
            if self._demand is None:
                self._demand = crossing_price.ColumnDemand(bid_columns.columns_of(self.bids), bid_columns.clearing_order_of(self.bids),
                                                           goods_market.MINIMUM_PRICE_SHARE_OF_REFERENCE)
            return self._demand.price_with_supply(quantity)
        except crossing_price.NeedsObjects:
            return price_with_supply(None, good, area, quantity, self.buyers)


def price_with_supply(bids: Optional[Sequence[Bid]], good: GoodId, area: AreaId, quantity: float,
                      buyers: Optional[goods_market.Buyers] = None) -> Optional[float]:
    """The price at which the buyers take exactly `quantity`, all of it offered at no reservation; None when the book
    shows no price.
    `buyers` is the market's bids prepared once, when the caller has them."""
    if buyers is None:
        buyers = goods_market.Buyers(bids, None)
    offer = Offer(SELLER, good, area, "", quantity, 0.0)
    # the crossing is the price `goods_market.clear` reports; the fills it would also build are not needed
    return goods_market.crossing(buyers, goods_market.in_clearing_order([offer]), with_wants=False)[0]


def share_after_addition(bids: Sequence[Bid], good: GoodId, area: AreaId, traded: float, added: float,
                         prepared: Optional[PreparedMarket] = None) -> float:
    """The share of the market's price that remains when `added` more units a year are offered beyond the
    `traded` quantity the year cleared; one when nothing is added or the book shows no price."""
    if not bids or not traded > 0.0 or not added > 0.0:
        return 1.0
    if prepared is None:
        prepared = PreparedMarket(bids)
    before = prepared.price_with_supply(good, area, traded)
    if before is None or not before > 0.0:
        return 1.0
    after = prepared.price_with_supply(good, area, traded + added)
    return max(0.0, min(1.0, after / before)) if after is not None and math.isfinite(after) else 1.0


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
