"""The arrays `market_curves.summarize` is made of, for a market's rows in the order tables, in one kernel call (`summarize_columns`
ran two `lexsort`s, a dozen gathers and several small calls per market it kept).

`curve_arrays` takes the first round's bids and offers as columns; `curve_arrays_of_rows` reads the columns of the given rows from
the order tables first. Bids are merged where they share a reference price, elasticity and ceiling (units and budgets added in
arrival order) and sorted by those three, offers merged by price and sorted by price."""
import numpy

from sim.jit import njit

from .stable_order_kernel import stable_order


@njit
def curve_arrays(floor, flexible, reference_price, elasticity, budget, maximum_price, bid_external, price, quantity, offer_external):
    """(bid_sums, bid_reference, bid_shape, bid_unbounded, bid_ceiling, offer_levels, offer_totals): one entry per merged bid (the sums
    of floor, flexible and budget in the columns of `bid_sums`) and per merged offer (its price and its units)."""
    count = 0
    for place in range(len(budget)):
        if not bid_external[place] and budget[place] > 0.0:
            count += 1
    taken = numpy.empty(count, dtype=numpy.int64)
    found = 0
    for place in range(len(budget)):
        if not bid_external[place] and budget[place] > 0.0:
            taken[found] = place
            found += 1
    reference = numpy.where(flexible[taken] > 0.0, reference_price[taken], 0.0)
    shape = numpy.where(flexible[taken] > 0.0, elasticity[taken], 0.0)
    ceiling = maximum_price[taken]
    sort_ceiling = numpy.where(numpy.isfinite(ceiling), ceiling, -1.0)
    order = stable_order((sort_ceiling, shape, reference))
    runs = 0
    for place in range(count):
        if place == 0 or not (reference[order[place]] == reference[order[place - 1]] and shape[order[place]] == shape[order[place - 1]]
                              and sort_ceiling[order[place]] == sort_ceiling[order[place - 1]]):
            runs += 1
    sums = numpy.zeros((runs, 3))
    first = numpy.empty(runs, dtype=numpy.int64)
    run = -1
    for place in range(count):
        row = order[place]
        if place == 0 or not (reference[row] == reference[order[place - 1]] and shape[row] == shape[order[place - 1]]
                              and sort_ceiling[row] == sort_ceiling[order[place - 1]]):
            run += 1
            first[run] = row
        sums[run, 0] += floor[taken[row]]
        sums[run, 1] += flexible[taken[row]]
        sums[run, 2] += budget[taken[row]]
    offers = 0
    for place in range(len(quantity)):
        if not offer_external[place] and quantity[place] > 0.0:
            offers += 1
    kept = numpy.empty(offers, dtype=numpy.int64)
    found = 0
    for place in range(len(quantity)):
        if not offer_external[place] and quantity[place] > 0.0:
            kept[found] = place
            found += 1
    reservation = price[kept]
    by_price = stable_order((reservation,))
    levels = numpy.empty(offers)
    totals = numpy.zeros(offers)
    merged = -1
    for place in range(offers):
        row = by_price[place]
        if place == 0 or not reservation[row] == reservation[by_price[place - 1]]:
            merged += 1
            levels[merged] = reservation[row]
        totals[merged] += quantity[kept[row]]
    return (sums, reference[first], shape[first], ~numpy.isfinite(ceiling[first]), ceiling[first], levels[:merged + 1].copy(),
            totals[:merged + 1].copy())


@njit
def curve_arrays_of_rows(bids, offers, bid_rows, offer_rows, external):
    """`curve_arrays` of the market with these bid and offer rows; `external` is the agent id of the external edge (-1: none)."""
    return curve_arrays(bids.floor_quantity[bid_rows], bids.flexible_quantity[bid_rows], bids.reference_price[bid_rows],
                        bids.elasticity[bid_rows], bids.budget[bid_rows], bids.maximum_price[bid_rows], bids.buyer[bid_rows] == external,
                        offers.reservation_price[offer_rows], offers.quantity[offer_rows], offers.seller[offer_rows] == external)
