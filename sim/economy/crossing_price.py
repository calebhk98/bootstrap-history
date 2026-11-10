"""The crossing price of a market's buyers against a book of offers, from columns: the price `goods_market.crossing` finds, without
the `Bid` objects, the `Buyers` and the `DemandSchedule`.

`price_at_levels` is the end of `crossing` (the search and the ceiling rule) for supply given as levels. `single_supply_price` is
the whole of `crossing` for the one book a producer's expansion is judged against: one offer of a quantity at no reservation, with
no last price held (`expansion_price.price_with_supply`). `ColumnDemand` prepares a market's `BidColumns` once for any number of
quantities. A figure the kernels do not reproduce (see `crossing_demand.FALLBACK`) raises `NeedsObjects`, and the caller runs the
Python on objects.
"""
from typing import Optional

import numpy

from sim.book import ROUNDING_SHARE
from sim.jit import njit

from .bid_columns import BidColumns
from .crossing_columns import DemandColumns, demand_columns
from .crossing_demand import KERNEL, total_at
from .crossing_solve import at_a_ceiling, solve_levels
from .year_ledger_note_kernels import exact_sum

CHEAP_PASSES_PER_BID = 10     # the cheap pass over the uncapped demand is used when groups times this are at most the bids


class NeedsObjects(Exception):
    """The columns hold a figure the kernels do not reproduce; the price is found on `Bid` objects."""


@njit(**KERNEL)
def price_at_levels(level_price, level_supply, demand_at_first, lowest, demand, flags):
    """The crossing price of the buyers against supply in levels (ascending reservations, cumulative quantities), where
    `demand_at_first` is demand at the first level and `lowest` the lowest reservation: the search, then a ceiling of a buyer's
    own where demand falls off one."""
    use_uncapped = len(demand.group_reference) * CHEAP_PASSES_PER_BID <= demand.bid_count
    price = solve_levels(level_price, level_supply, demand_at_first, use_uncapped, demand, flags)
    if demand.capped:
        price = at_a_ceiling(price, level_price, level_supply, lowest, demand, flags)
    return price


@njit(**KERNEL)
def minimum_price_of(reference, share):
    """(found, price): `share` of the mean of the positive reference prices (`goods_market.Buyers.minimum_price` with no last
    price held); not found when no bid quotes a reference price."""
    positive = numpy.empty(len(reference))
    used = 0
    for bid in range(len(reference)):
        if reference[bid] > 0.0:
            positive[used] = reference[bid]
            used += 1
    if used == 0:
        return False, 0.0
    return True, share * (exact_sum(positive, used) / used)


@njit(**KERNEL)
def single_supply_price(demand, has_minimum, minimum_price, quantity, flags):
    """(found, price) of `goods_market.crossing` for one offer of `quantity` at a reservation of zero and no last price held; not
    found where the Python reports no price (nothing offered, residue only, or no price scale to search from)."""
    if not quantity > 0.0:
        return False, 0.0
    reservation = minimum_price if has_minimum else 0.0       # the token price a zero reservation is raised to
    demand_at_first = total_at(reservation, demand, flags)
    if quantity <= ROUNDING_SHARE * demand_at_first:
        return False, 0.0
    if demand_at_first <= 0.0:
        return True, reservation
    if not reservation > 0.0:
        return False, 0.0
    level_price, level_supply = numpy.array([reservation]), numpy.array([quantity])
    return True, price_at_levels(level_price, level_supply, demand_at_first, reservation, demand, flags)


class ColumnDemand:
    """A market's buyers prepared from their columns and clearing order, asked the price at which they take exactly a quantity
    offered at no reservation."""

    def __init__(self, columns: BidColumns, order: numpy.ndarray, minimum_share: float):
        self.demand: Optional[DemandColumns] = demand_columns(columns, order)
        self.has_minimum, self.minimum_price = minimum_price_of(columns.reference, minimum_share)

    def price_with_supply(self, quantity: float) -> Optional[float]:
        """The price at which the buyers take `quantity`; None when the book shows no price. Raises `NeedsObjects`."""
        if self.demand is None:
            raise NeedsObjects()
        flags = numpy.zeros(1, dtype=numpy.int64)
        found, price = single_supply_price(self.demand, self.has_minimum, self.minimum_price, quantity, flags)
        if flags[0]:
            raise NeedsObjects()
        return price if found else None
