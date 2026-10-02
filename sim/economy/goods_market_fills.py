"""Build the fills of a cleared market. Thousands of buyer fills are built per market, so the frozen
dataclass is filled in directly when its fields are the ones expected; any other shape of `Fill` goes
through its own constructor."""
from dataclasses import fields
from typing import Iterable, List, Tuple

from .types import AreaId, Bid, Fill, GoodId, Offer

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
