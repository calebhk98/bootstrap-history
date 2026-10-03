"""What merchants have already promised to carry this year, so one merchant's route and its rivals' routes share a market.

A merchant sizes the cargo it bids for against the destination's usual volume, and what it has already
bid for from other sources counts against that same destination. Merchants together are limited the
same way, in the order they size: each sees what the earlier ones have taken.
"""
import math
from typing import Dict, Mapping, Tuple

from sim.constants import declare

from .types import AreaId, GoodId

Key = Tuple[GoodId, AreaId]

MERCHANT_GROUP_SHARE = declare(
    "MERCHANT_GROUP_SHARE", 1.0, kind="temporary_heuristic",
    unit="share of the destination's expected yearly volume", source=None, confidence="D",
    why="All merchants together stop bidding for a destination once their cargo would equal this "
        "share of what it usually trades; a market taking much more than it usually does sells below "
        "what the cargo cost. Real merchants watch each other's ships; the economy has no such "
        "view, so the order merchants size in stands in. Not yet fitted.")


class RouteShares:
    """Units committed so far into each (good, destination area)."""

    def __init__(self) -> None:
        self.into: Dict[Key, float] = {}

    def commit(self, good: GoodId, destination: AreaId, quantity: float) -> None:
        self.into[(good, destination)] = self.into.get((good, destination), 0.0) + quantity


def room_left(expected_volumes: Mapping[Key, float], key: Key, own_share: float,
              own: RouteShares, group: RouteShares, held: float) -> float:
    """Units a merchant may still bid for into `key`: its own share of the market's expected volume
    less what it holds there and has bid already, and the group's share less what merchants have
    bid already. Unlimited when no volume has been seen there."""
    volume = expected_volumes.get(key)
    if volume is None:
        return math.inf
    mine = own_share * volume - held - own.into.get(key, 0.0)
    everyone = MERCHANT_GROUP_SHARE * volume - group.into.get(key, 0.0)
    return max(0.0, min(mine, everyone))
