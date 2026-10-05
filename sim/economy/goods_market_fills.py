"""Build the fills of a cleared market. Thousands of buyer fills are built per market, so the frozen
dataclass is filled in directly when its fields are the ones expected; any other shape of `Fill` goes
through its own constructor."""
import math
from dataclasses import fields
from typing import Iterable, List, Tuple

from .types import AreaId, Bid, Fill, GoodId, Offer, is_edge

_EXPECTED_FIELDS = ("agent", "good", "area", "tile", "quantity", "price", "side")
_DIRECT = tuple(field.name for field in fields(Fill)) == _EXPECTED_FIELDS
_new = object.__new__


def make_fill(agent, good, area, tile, quantity, price, side) -> Fill:
    if not _DIRECT:
        return Fill(agent, good, area, tile, quantity, price, side)
    fill = _new(Fill)
    values = fill.__dict__
    values["agent"] = agent
    values["good"] = good
    values["area"] = area
    values["tile"] = tile
    values["quantity"] = quantity
    values["price"] = price
    values["side"] = side
    return fill


def buyer_fills(bids: Iterable[Bid], served: Iterable[float], good: GoodId, area: AreaId, price: float) -> List[Fill]:
    return [make_fill(bid.buyer, good, area, bid.tile, quantity, price, "buy")
            for bid, quantity in zip(bids, served) if quantity > 0.0]


def seller_fills(served: Iterable[Tuple[Offer, float]], good: GoodId, area: AreaId, price: float) -> List[Fill]:
    return [make_fill(offer.seller, good, area, offer.tile, quantity, price, "sell")
            for offer, quantity in served if quantity > 0.0]


def without_edge_self_trades(fills: List[Fill]) -> Tuple[List[Fill], float]:
    """A book edge (the mint) quoting both ways at one price would buy its own stock: take the overlap of
    its buy and sell fills out of both, and return the quantity removed."""
    bought, sold = {}, {}
    for fill in fills:
        if is_edge(fill.agent):
            side = bought if fill.side == "buy" else sold
            side[fill.agent] = side.get(fill.agent, 0.0) + fill.quantity
    wash = {agent: min(quantity, sold.get(agent, 0.0)) for agent, quantity in bought.items()}
    wash = {agent: quantity for agent, quantity in wash.items() if quantity > 0.0}
    if not wash:
        return fills, 0.0
    left = {(agent, side): quantity for agent, quantity in wash.items() for side in ("buy", "sell")}
    result = []
    for fill in fills:
        take = min(fill.quantity, left.get((fill.agent, fill.side), 0.0))
        if take > 0.0:
            left[(fill.agent, fill.side)] -= take
        if fill.quantity - take > 0.0:
            result.append(fill if take == 0.0 else make_fill(fill.agent, fill.good, fill.area, fill.tile,
                                                             fill.quantity - take, fill.price, fill.side))
    return result, math.fsum(wash.values())
