"""A market's price response from the columns of its summarised book, with no `Bid`, `Offer` or `Buyers` object.

`market_curves.price_response_objects` clears the summary again with one more offer or bid through `goods_market.clear_at_one_price`, which
builds the fills, the demand schedule and the `Bid` list only for the price and whether anything traded to be read off. Here the
summary's rows are columns (`PreparedCurve`, kept against the book object like `response_memo`'s answers) and `clear_summary` is the
crossing of `goods_market.crossing` from the same search kernels (`crossing_price.price_at_levels`): the price is the same figure, and
"something traded" is `wanted > 0` and `supply > 0`, which is when `ration` serves a positive quantity (every bid of a curve is in one
priority tier). A figure the kernels do not take (`NeedsObjects`) is answered by the objects."""
import math
from typing import Dict, Optional, Tuple

import numpy

from sim.book import ROUNDING_SHARE
from sim.jit import njit

from .bid_columns import BidColumns
from .crossing_columns import demand_columns
from .crossing_demand import KERNEL, total_at
from .crossing_price import NeedsObjects, minimum_price_of, price_at_levels
from .year_ledger_note_kernels import exact_sum

CURVES_KEPT = 256
NOTHING, TRADES, OBJECTS = 0, 1, 2     # `clear_summary` statuses


@njit(**KERNEL)
def clear_summary(reservation, quantity, has_minimum, minimum, last_price, demand, flags):
    """(status, price): the crossing of buyers `demand` against offers (reservations ascending, quantities above zero), as
    `goods_market.crossing` finds it, and whether the market trades at it (`NOTHING`: no price to move; `OBJECTS`: a figure the
    kernels do not take). `last_price` is NaN when none is held; a reservation is raised to `minimum` when `has_minimum`."""
    count = len(reservation)
    effective = numpy.empty(count)
    for place in range(count):
        effective[place] = max(reservation[place], minimum) if has_minimum else reservation[place]
    demand_at_first = total_at(effective[0], demand, flags)
    if flags[0]:
        return OBJECTS, 0.0
    if exact_sum(quantity, count) <= ROUNDING_SHARE * demand_at_first or demand_at_first <= 0.0:
        return NOTHING, 0.0
    floor = last_price if last_price > 0.0 else -1.0
    for place in range(count):
        if effective[place] > 0.0:
            floor = effective[place]       # ascending: the first positive one is the least
            break
    if not floor > 0.0:
        return NOTHING, 0.0
    level_price, level_supply = numpy.empty(count), numpy.empty(count)
    levels, running, start = 0, 0.0, 0
    while start < count:
        end = start + 1
        while end < count and effective[end] == effective[start]:
            end += 1
        running += exact_sum(quantity[start:end].copy(), end - start)
        level_price[levels], level_supply[levels] = max(effective[start], floor), running
        levels += 1
        start = end
    price = price_at_levels(level_price[:levels].copy(), level_supply[:levels].copy(), demand_at_first, effective[0], demand, flags)
    if flags[0]:
        return OBJECTS, 0.0
    sold = numpy.empty(count)
    eligible = 0
    for place in range(count):
        if effective[place] <= price:
            sold[eligible] = quantity[place]
            eligible += 1
    wanted = total_at(price, demand, flags)
    if flags[0]:
        return OBJECTS, 0.0
    if wanted > 0.0 and eligible > 0 and exact_sum(sold, eligible) > 0.0:
        return TRADES, price
    return NOTHING, price


class PreparedCurve:
    """One summarised book as columns: the buyers (curve order) with their clearing order and prepared demand, and the offers by
    ascending reservation. Built once per book object."""

    def __init__(self, curve):
        rows = curve["bids"]
        figures = numpy.array([[row[0], row[1], row[2], row[3], row[4], math.inf if row[5] is None else row[5]] for row in rows],
                              dtype=numpy.float64).reshape(-1, 6)
        self.columns = BidColumns(*(figures[:, column].copy() for column in range(6)))
        count = len(rows)
        names = ["curve:%d" % number for number in range(count)]
        self.order = numpy.array(sorted(range(count), key=names.__getitem__), dtype=numpy.int64)      # clearing order: by buyer name
        offers = numpy.array(curve["offers"], dtype=numpy.float64).reshape(-1, 2)
        ascending = numpy.argsort(offers[:, 0], kind="stable")
        self.reservation, self.quantity = offers[ascending, 0].copy(), offers[ascending, 1].copy()
        self.demand = demand_columns(self.columns, self.order)
        self.minimum: Dict[Optional[float], Tuple[bool, float]] = {}

    def minimum_price(self, last_price: Optional[float], share: float) -> Tuple[bool, float]:
        """(there is one, the token price): `share` of the mean positive reference price, else of the last price held."""
        found = self.minimum.get(last_price)
        if found is None:
            found, price = minimum_price_of(self.columns.reference, share)
            if not found and last_price is not None and last_price > 0.0:
                found, price = True, share * last_price
            found = self.minimum[last_price] = (bool(found), float(price))
        return found

    def with_extra_buyer(self, taken: float):
        """The prepared demand of this book's buyers and one more that takes `taken` units at any price; None when the columns cannot be prepared."""
        extra = BidColumns(*(numpy.concatenate((column, [value])) for column, value in zip(
            self.columns, (taken, 0.0, 0.0, 0.0, math.inf, math.inf))))
        order = numpy.concatenate((self.order, [len(self.columns.floor)])).astype(numpy.int64)      # "extra:demand" sorts after every "curve:n"
        return demand_columns(extra, order)

    def with_extra_seller(self, landed: float):
        """(reservations, quantities) of the offers and one more of `landed` units at a reservation of zero."""
        place = numpy.searchsorted(self.reservation, 0.0, side="right")
        return (numpy.insert(self.reservation, place, 0.0), numpy.insert(self.quantity, place, landed))


_PREPARED: Dict[int, Tuple[object, PreparedCurve]] = {}


def prepared(curve) -> PreparedCurve:
    """The columns of `curve`, kept against the book object (which is held, so its id is not taken by another)."""
    found = _PREPARED.get(id(curve))
    if found is None or found[0] is not curve:
        if len(_PREPARED) >= CURVES_KEPT:
            _PREPARED.clear()
        found = _PREPARED[id(curve)] = (curve, PreparedCurve(curve))
    return found[1]


def _clear(book: PreparedCurve, reservation, quantity, demand, last_price: Optional[float], share: float):
    if demand is None:
        raise NeedsObjects()
    if len(reservation) == 0:
        return NOTHING, 0.0
    has_minimum, minimum = book.minimum_price(last_price, share)
    flags = numpy.zeros(1, dtype=numpy.int64)
    status, price = clear_summary(reservation, quantity, has_minimum, minimum, math.nan if last_price is None else last_price, demand, flags)
    if status == OBJECTS:
        raise NeedsObjects()
    return status, price


def price_response(curve, last_price: Optional[float], landed: float, taken: float, share: float) -> Optional[float]:
    """`market_curves.price_response_objects` of the same arguments (`share` is `goods_market.MINIMUM_PRICE_SHARE_OF_REFERENCE`).
    Raises `NeedsObjects` for a figure the kernels do not take."""
    book = prepared(curve)
    base_status, base_price = _clear(book, book.reservation, book.quantity, book.demand, last_price, share)
    if base_status != TRADES or not base_price > 0.0:
        return None
    reservation, quantity = book.with_extra_seller(landed) if landed > 0.0 else (book.reservation, book.quantity)
    if taken >= exact_sum(quantity, len(quantity)):
        return math.inf        # more is wanted at any price than the sellers hold: nothing caps the price
    status, price = _clear(book, reservation, quantity, book.with_extra_buyer(taken) if taken > 0.0 else book.demand, base_price, share)      # the one more is cleared with the base price held
    if status != TRADES:
        return None
    return price / base_price
