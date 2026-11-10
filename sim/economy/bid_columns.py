"""A market's bids as six columns, for the entry rules that read what the year's buyers would take at a price (entry_trial, entry_margin,
entry_backed): no `Bid` object is made for the sum.

`BidColumns` is the six figures of every bid of one market, in the order the bids reached the book and then the bids later respend rounds
added (the order a `Bid` list had), as float arrays:
    floor       units the buyer needs at any price                                 units
    flexible    units it takes beyond the floor at the reference price               units
    reference   price the flexible units are quoted at                                currency per unit
    elasticity  how fast the flexible units fall as the price rises                   pure number
    budget      money the bid may spend                                               currency units
    maximum     highest price the bid accepts                                          currency per unit

`MarketBids` is what `YearLedger.bids_by_market` holds per market: the columns (made when first read) and, for a rule still written over
`Bid` objects, a sequence of the objects (built when first read). `columns_of` gives the columns of either that or a plain list of `Bid`.
"""
import math
from collections import namedtuple
from typing import Callable, Optional, Sequence

import numpy

from sim.jit import njit

from .year_ledger_note_kernels import exact_sum

BidColumns = namedtuple("BidColumns", ("floor", "flexible", "reference", "elasticity", "budget", "maximum"))

_EXPONENT_CEILING = 700.0         # entry_trial.demand_at: the exponent of the price ratio is capped so exp cannot overflow


def columns_of_bids(bids: Sequence) -> BidColumns:
    """The columns of a list of `Bid` objects."""
    figures = numpy.array([(bid.floor_quantity, bid.flexible_quantity, bid.reference_price, bid.elasticity, bid.budget, bid.maximum_price)
                           for bid in bids], dtype=numpy.float64).reshape(-1, 6)
    return BidColumns(*(figures[:, column].copy() for column in range(6)))


def order_of_bids(bids: Sequence) -> numpy.ndarray:
    """The indexes of `Bid` objects in clearing order (`goods_market.Buyers` sorts by priority, buyer and tile; a stable sort)."""
    return numpy.array(sorted(range(len(bids)), key=lambda place: (bids[place].priority, bids[place].buyer, bids[place].tile)),
                       dtype=numpy.int64)


def clearing_order_of(bids) -> numpy.ndarray:
    """The clearing order of a market's bids: the stored one of a `MarketBids`, else worked out from the `Bid` objects."""
    return bids.clearing_order if isinstance(bids, MarketBids) else order_of_bids(list(bids))


def joined(first: BidColumns, second: BidColumns) -> BidColumns:
    """The columns of `first`'s bids followed by `second`'s."""
    return BidColumns(*(numpy.concatenate((one, other)) for one, other in zip(first, second)))


@njit
def demand_at_columns(floor, flexible, reference, elasticity, budget, maximum, price, price_now):
    """What the bids, made at `price_now`, would take at `price` (`entry_trial.demand_at`): a bid's floor whatever the price, plus the
    smaller of its leftover budget over the price and its own schedule's reach; a bid with no budget or a ceiling below the price takes
    nothing. The bids are added in their order, one float at a time. `price` must be above zero."""
    total = 0.0
    for place in range(len(floor)):
        if budget[place] <= 0.0 or price > maximum[place]:
            continue
        surplus = max(0.0, budget[place] - floor[place] * price_now)
        reach = 0.0
        if flexible[place] > 0.0 and reference[place] > 0.0 and price > 0.0:
            reach = flexible[place] * math.exp(min(_EXPONENT_CEILING, -elasticity[place] * math.log(price / reference[place])))
        total += floor[place] + min(surplus / price, reach)
    return total


@njit
def taken_at_columns(floor, flexible, reference, elasticity, budget, maximum, price):
    """The units each bid takes at a price (`goods_market.quantity_at`): none without a budget or above the bid's ceiling, floor plus
    flexible at a price of zero or less, else the schedule capped by what the budget buys."""
    taken = numpy.zeros(len(floor))
    for place in range(len(floor)):
        if budget[place] <= 0.0 or price > maximum[place]:
            continue
        if price <= 0.0:
            taken[place] = floor[place] + flexible[place]
            continue
        wanted = floor[place]
        if flexible[place] > 0.0 and reference[place] > 0.0:
            wanted += flexible[place] * (price / reference[place]) ** -elasticity[place]
        taken[place] = min(wanted, budget[place] / price)
    return taken


@njit
def sum_taken_at_columns(floor, flexible, reference, elasticity, budget, maximum, price):
    """`math.fsum` of the units each bid takes at the price (`entry_backed.unfilled_quantity` before the traded volume is taken off)."""
    taken = taken_at_columns(floor, flexible, reference, elasticity, budget, maximum, price)
    return exact_sum(taken, len(taken))


def demand_at(columns: BidColumns, price: float, price_now: float) -> float:
    """`demand_at_columns` of a market's columns."""
    return demand_at_columns(*columns, price, price_now)


def sum_taken_at(columns: BidColumns, price: float) -> float:
    """`sum_taken_at_columns` of a market's columns."""
    return sum_taken_at_columns(*columns, price)


class MarketBids(Sequence):
    """One market's bids for the entry rules: columns first, `Bid` objects only when a rule asks for them (see the module docstring)."""

    def __init__(self, make_columns: Callable[[], BidColumns], make_objects: Callable[[], list], count: int,
                 make_order: Optional[Callable[[], numpy.ndarray]] = None):
        self._make_columns, self._make_objects, self._count, self._make_order = make_columns, make_objects, count, make_order
        self._columns = self._items = self._order = None

    @property
    def columns(self) -> BidColumns:
        if self._columns is None:
            self._columns = self._make_columns()
        return self._columns

    @property
    def clearing_order(self) -> numpy.ndarray:
        """The bids' places in the order a market clears them (priority, buyer name, tile name; ties in the bids' own order), as the
        indexes of the columns."""
        if self._order is None:
            self._order = self._make_order() if self._make_order is not None else order_of_bids(self._list())
        return self._order

    def _list(self) -> list:
        if self._items is None:
            self._items = self._make_objects()
        return self._items

    def __len__(self) -> int:
        return self._count

    def __bool__(self) -> bool:
        return self._count > 0

    def __getitem__(self, index):
        return self._list()[index]

    def __iter__(self):
        return iter(self._list())

    def __eq__(self, other) -> bool:
        """Equal to any sequence holding the same bids (builds the objects: a test, an edge)."""
        return isinstance(other, Sequence) and self._list() == list(other)

    __hash__ = None


def columns_of(bids) -> BidColumns:
    """The columns of a market's bids: the stored columns of a `MarketBids`, else those of the `Bid` objects in the sequence."""
    found = getattr(bids, "columns", None)
    return found if found is not None else columns_of_bids(list(bids))
