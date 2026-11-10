"""The share of each market's price that stays when producers add output to it, for every request of the year in one kernel call.

Markets lie one after another in the bid columns (`market_start`), each with its clearing order (indexes into its own bids) and the
quantity the year traded; the requests of a market lie together (`request_start`), each an added quantity a year. For each market the
buyers are prepared once and the price found at the traded quantity, then at the traded quantity plus each addition
(`crossing_price.single_supply_price`, the search `expansion_price.PreparedMarket` runs). A market the columns cannot hold (see
`crossing_columns._usable`, or a flag from the search) is left to the caller: its requests are marked in `needs_objects`."""
import numpy

from sim.jit import njit

from .crossing_columns import KERNEL, DemandColumns, prepare_demand
from .crossing_price import minimum_price_of, single_supply_price


@njit(**KERNEL)
def _price_at(demand, has_minimum, minimum_price, quantity):
    """(found, price, needs_objects) of the buyers at one offer of `quantity`."""
    flags = numpy.zeros(1, dtype=numpy.int64)
    found, price = single_supply_price(demand, has_minimum, minimum_price, quantity, flags)
    return found, price, flags[0] != 0


@njit(**KERNEL)
def _share_after(demand, has_minimum, minimum_price, traded, added):
    """(share, needs_objects): the share of the price at `traded` that remains at `traded + added`; one where the book shows no price."""
    found, before, needs_objects = _price_at(demand, has_minimum, minimum_price, traded)
    if needs_objects:
        return 1.0, True
    if not found or not before > 0.0:
        return 1.0, False
    found, after, needs_objects = _price_at(demand, has_minimum, minimum_price, traded + added)
    if needs_objects:
        return 1.0, True
    if not found or not numpy.isfinite(after):
        return 1.0, False
    return max(0.0, min(1.0, after / before)), False


@njit(**KERNEL)
def shares_after_additions(floor, flexible, reference, elasticity, budget, maximum, order, market_start, traded,
                           request_start, added, minimum_share, share, needs_objects):
    """Fill `share` and `needs_objects` for every request. A request that adds nothing, or in a market with no bids or no trade, keeps
    the whole price (share one)."""
    for market in range(len(traded)):
        first, last = market_start[market], market_start[market + 1]
        if last == first or not traded[market] > 0.0:
            share[request_start[market]:request_start[market + 1]] = 1.0
            continue
        (usable, group_start, row_floor, row_flexible, row_budget, row_maximum, group_reference, group_exponent, group_floor,
         group_flexible, ceilings) = prepare_demand(floor[first:last], flexible[first:last], reference[first:last],
                                                    elasticity[first:last], budget[first:last], maximum[first:last], order[first:last])
        if not usable:
            needs_objects[request_start[market]:request_start[market + 1]] = True
            continue
        demand = DemandColumns(row_floor, row_flexible, row_budget, row_maximum, group_start, group_reference, group_exponent,
                               group_floor, group_flexible, ceilings, len(ceilings) > 0, last - first)
        has_minimum, minimum_price = minimum_price_of(reference[first:last], minimum_share)
        for request in range(request_start[market], request_start[market + 1]):
            if not added[request] > 0.0:
                share[request] = 1.0
                continue
            share[request], needs_objects[request] = _share_after(demand, has_minimum, minimum_price, traded[market], added[request])
