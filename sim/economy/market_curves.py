"""What a market's last clearing remembers of its own book, so a price can be quoted for extra supply or demand.

The book of a market that cleared is summarised as the buyers' schedules (merged where they share a
reference price, elasticity and ceiling) and the sellers' reservation prices (merged by price), leaving
out the external edge's own orders. A quote clears that summary again with one more offer (cargo landed in
the area) or one more floor bid (cargo taken out), through the same `goods_market.clear` the year uses, and
returns the price over what the summary alone clears at (unbounded when more is taken than the sellers hold). Merging buyers adds their budgets, so a market in
which a few buyers are held back by their budgets quotes a little off the book it summarises.
"""
import math
from typing import Dict, List, Optional, Sequence, Tuple

from . import goods_market
from .types import EDGE_EXTERNAL, Bid, Offer

CURVE_AREA = "curve"
CURVE_TILE = "curve"
EXTRA_SELLER = "extra:supply"
EXTRA_BUYER = "extra:demand"
_NO_CEILING = None     # a bid with no ceiling is saved with none, not with infinity


def port_area(area_map, port_tile: str, good: str) -> Optional[str]:
    """The market area of a good that holds the port, where cargo enters and leaves; None if it has none."""
    if area_map is None or port_tile is None:
        return None
    try:
        return area_map.area_of(good, port_tile)
    except KeyError:
        return None


def summarize(bids: Sequence[Bid], offers: Sequence[Offer]) -> Dict[str, List[List[float]]]:
    """The market's own book as plain rows: bids [floor, flexible, reference, elasticity, budget, ceiling]
    and offers [reservation, quantity]."""
    merged: Dict[Tuple[float, float, Optional[float]], List[float]] = {}
    for bid in bids:
        if bid.buyer == EDGE_EXTERNAL or bid.budget <= 0.0:
            continue
        ceiling = bid.maximum_price if math.isfinite(bid.maximum_price) else _NO_CEILING
        reference = bid.reference_price if bid.flexible_quantity > 0.0 else 0.0
        elasticity = bid.elasticity if bid.flexible_quantity > 0.0 else 0.0
        row = merged.setdefault((reference, elasticity, ceiling), [0.0, 0.0, 0.0])
        row[0] += bid.floor_quantity
        row[1] += bid.flexible_quantity
        row[2] += bid.budget
    by_price: Dict[float, float] = {}
    for offer in offers:
        if offer.seller != EDGE_EXTERNAL and offer.quantity > 0.0:
            by_price[offer.reservation_price] = by_price.get(offer.reservation_price, 0.0) + offer.quantity
    return {"bids": [[floor, flexible, reference, elasticity, budget, ceiling]
                     for (reference, elasticity, ceiling), (floor, flexible, budget) in sorted(
                         merged.items(), key=lambda item: (item[0][0], item[0][1], -1.0 if item[0][2] is None else item[0][2]))],
            "offers": [[price, quantity] for price, quantity in sorted(by_price.items())]}


def _bids(curve: Dict[str, List[List[float]]], good: str) -> List[Bid]:
    return [Bid("curve:%d" % number, good, CURVE_AREA, CURVE_TILE, floor, flexible, reference, elasticity, budget,
                0, math.inf if ceiling is None else ceiling)
            for number, (floor, flexible, reference, elasticity, budget, ceiling) in enumerate(curve["bids"])]


def _offers(curve: Dict[str, List[List[float]]], good: str) -> List[Offer]:
    return [Offer("curve:%d" % number, good, CURVE_AREA, CURVE_TILE, quantity, price)
            for number, (price, quantity) in enumerate(curve["offers"])]


def price_response(curve: Dict[str, List[List[float]]], good: str, last_price: Optional[float],
                   landed: float, taken: float) -> Optional[float]:
    """The market's price after `landed` more units are offered in it and `taken` more are bought, over the
    price its summarised book clears at; None when that book traded nothing, so the market has no price to
    move."""
    bids, offers = _bids(curve, good), _offers(curve, good)
    base = goods_market.clear(bids, offers, good, CURVE_AREA, "", last_price)
    if not base.quantity > 0.0 or not base.price > 0.0:
        return None
    if landed > 0.0:
        offers.append(Offer(EXTRA_SELLER, good, CURVE_AREA, CURVE_TILE, landed, 0.0))
    if taken > 0.0:
        bids.append(Bid(EXTRA_BUYER, good, CURVE_AREA, CURVE_TILE, taken, 0.0, 0.0, 0.0, math.inf))
    if taken >= math.fsum(offer.quantity for offer in offers):
        return math.inf    # more is wanted at any price than the sellers hold: nothing caps the price
    try:
        moved = goods_market.clear(bids, offers, good, CURVE_AREA, "", base.price)
    except OverflowError:
        return math.inf
    if not moved.quantity > 0.0:
        return None
    return moved.price / base.price
