"""The price a producer's own additions leave: capacity is judged at the price expected after it exists.

A producer that adds output to a market its buyers' schedules do not absorb at the same price expects less
for every unit, its own as well as the rest. The residual price is read off the market's book as the year
cleared it: the buyers' schedules against the quantity traded, and against that quantity plus the addition,
both offered at any price. A market whose book was not kept, or that traded nothing, shows no price to
move, and the share is one."""
import math
from typing import Callable, Mapping, Optional, Sequence, Tuple

from . import goods_market
from .types import AreaId, Bid, GoodId, Offer, TileId

SELLER = "expansion:price"
PriceShare = Callable[[GoodId, float], float]     # (good, units added a year) -> share of the price that stays


def price_with_supply(bids: Sequence[Bid], good: GoodId, area: AreaId, quantity: float) -> float:
    """The price at which the buyers take exactly `quantity`, all of it offered at no reservation."""
    offer = Offer(SELLER, good, area, "", quantity, 0.0)
    return goods_market.clear(bids, [offer], good, area, "", None).price


def share_after_addition(bids: Sequence[Bid], good: GoodId, area: AreaId, traded: float, added: float) -> float:
    """The share of the market's price that remains when `added` more units a year are offered beyond the
    `traded` quantity the year cleared; one when nothing is added or the book shows no price."""
    if not bids or not traded > 0.0 or not added > 0.0:
        return 1.0
    before = price_with_supply(bids, good, area, traded)
    if not before > 0.0:
        return 1.0
    after = price_with_supply(bids, good, area, traded + added)
    return max(0.0, min(1.0, after / before)) if math.isfinite(after) else 1.0


def price_share_of(bids_by_market: Mapping[Tuple[GoodId, AreaId], Sequence[Bid]],
                   traded_by_market: Mapping[Tuple[GoodId, AreaId], float],
                   area_of: Callable[[GoodId, TileId], AreaId], tile: TileId) -> PriceShare:
    """For a producer on `tile`: the share of its market's price that stays after it adds units of a good,
    from the year's bids and traded quantities."""
    def share(good: GoodId, added: float) -> float:
        area = area_of(good, tile)
        key = (good, area)
        return share_after_addition(bids_by_market.get(key, ()), good, area, traded_by_market.get(key, 0.0), added)
    return share
