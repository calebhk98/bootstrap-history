"""`Bid` and `Offer` objects made from table rows: set field by field into the object, as `goods_market_fills.make_fill` does for
fills, because thousands are made from rows a year. Any other shape of the dataclass goes through its own constructor."""
from dataclasses import fields

from .types import Bid, Offer

_BID_FIELDS = ("buyer", "good", "area", "tile", "floor_quantity", "flexible_quantity", "reference_price", "elasticity", "budget",
               "priority", "maximum_price")
_OFFER_FIELDS = ("seller", "good", "area", "tile", "quantity", "reservation_price")
_BID_DIRECT = tuple(field.name for field in fields(Bid)) == _BID_FIELDS
_OFFER_DIRECT = tuple(field.name for field in fields(Offer)) == _OFFER_FIELDS
_new = object.__new__


def make_bid(*values) -> Bid:
    """A `Bid` of these field values, set directly (thousands are made from rows a year); any other shape of `Bid` goes through
    its own constructor."""
    if not _BID_DIRECT:
        return Bid(*values)
    bid = _new(Bid)
    bid.__dict__.update(zip(_BID_FIELDS, values))
    return bid


def make_offer(*values) -> Offer:
    """An `Offer` of these field values, set directly."""
    if not _OFFER_DIRECT:
        return Offer(*values)
    offer = _new(Offer)
    offer.__dict__.update(zip(_OFFER_FIELDS, values))
    return offer
