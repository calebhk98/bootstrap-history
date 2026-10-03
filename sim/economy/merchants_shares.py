"""What merchants have already promised to carry this year, so one merchant's routes and its rivals' routes share the markets.

A merchant sizes the cargo it bids for against what the destination usually trades and what the source
usually sells. What it has bid for already, from other sources into the same destination, counts
against the destination; what merchants have bid for out of a source counts against that source, so
no bid is made for goods another merchant has bid for or that the source does not sell. Merchants
size one after another and each sees what the earlier ones have taken.
"""
import math
from typing import Dict, Mapping, Tuple

from sim.constants import declare

from .types import AreaId, GoodId

Key = Tuple[GoodId, AreaId]

MERCHANT_GROUP_SHARE = declare(
    "MERCHANT_GROUP_SHARE", 2.0, kind="temporary_heuristic",
    unit="share of the destination's expected yearly volume", source=None, confidence="D",
    why="All merchants together stop bidding for a destination once their cargo would equal this "
        "share of what it usually trades; a market taking much more than it usually does sells below "
        "what the cargo cost. Real merchants watch each other's ships; the economy has no such "
        "view, so the order merchants size in stands in. Not yet fitted.")


MERCHANT_SOURCE_SHARE = declare(
    "MERCHANT_SOURCE_SHARE", 1.0, kind="temporary_heuristic",
    unit="share of the source's expected yearly volume", source=None, confidence="D",
    why="Merchants together bid for no more than this share of what a source area usually sells; a bid "
        "for more than the area has to sell only ties up the room the destination could take from "
        "other sources. A merchant sees what the area sold last year, not what is on offer now; not yet fitted.")


class RouteShares:
    """Units committed so far into each (good, destination area) and out of each (good, source area)."""

    def __init__(self) -> None:
        self.into: Dict[Key, float] = {}
        self.out_of: Dict[Key, float] = {}

    def commit(self, good: GoodId, source: AreaId, destination: AreaId, quantity: float) -> None:
        self.into[(good, destination)] = self.into.get((good, destination), 0.0) + quantity
        self.out_of[(good, source)] = self.out_of.get((good, source), 0.0) + quantity


def room_left(expected_volumes: Mapping[Key, float], good: GoodId, source: AreaId, destination: AreaId,
              own_share: float, own: RouteShares, group: RouteShares, held: float) -> float:
    """Units a merchant may still bid for on a route: into the destination, its own share of the market's
    expected volume less what it holds there and has bid already, and the group's share less what
    merchants have bid already; out of the source, the group's share of what it usually sells less
    what merchants have bid already. A market whose volume has never been seen sets no limit."""
    room = math.inf
    into_volume = expected_volumes.get((good, destination))
    if into_volume is not None:
        mine = own_share * into_volume - held - own.into.get((good, destination), 0.0)
        everyone = MERCHANT_GROUP_SHARE * into_volume - group.into.get((good, destination), 0.0)
        room = min(mine, everyone)
    out_volume = expected_volumes.get((good, source))
    if out_volume is not None:
        room = min(room, MERCHANT_SOURCE_SHARE * out_volume - group.out_of.get((good, source), 0.0))
    return max(0.0, room)
