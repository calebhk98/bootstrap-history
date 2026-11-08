"""`market_curves.summarize` over the columns of a market's rows in the order tables: the same summary of the market's own book, with no
`Bid` or `Offer` made.

`summarize_columns` takes the first round's bids as columns and the offers as columns, with a flag for each that the external edge made
(`EDGE_EXTERNAL`: left out), and answers the summary `market_curves.summarize` gives: bids merged where they share a reference price,
elasticity and ceiling (their units and budgets added in arrival order) sorted by those three, offers merged by price and sorted by
price. `of_rows` reads the columns from the order tables for a cleared market."""
import numpy

from sim.jit import njit

from .types import EDGE_EXTERNAL


@njit
def group_sums(order, first, second, third, same_as_previous):
    """For rows taken in `order`, the sums of `first`, `second` and `third` over each run of rows that `same_as_previous` marks as a
    continuation, each added left to right; one row of sums per run."""
    runs = 0
    for place in range(len(order)):
        if not same_as_previous[place]:
            runs += 1
    sums = numpy.zeros((runs, 3))
    run = -1
    for place in range(len(order)):
        row = order[place]
        if not same_as_previous[place]:
            run += 1
        sums[run, 0] += first[row]
        sums[run, 1] += second[row]
        sums[run, 2] += third[row]
    return sums


def _same_as_previous(order, *keys):
    """Per place in `order`, whether the row has the same keys as the one before it."""
    same = numpy.zeros(len(order), dtype=bool)
    if len(order) > 1:
        same[1:] = True
        for key in keys:
            sorted_key = key[order]
            same[1:] &= sorted_key[1:] == sorted_key[:-1]
    return same


def summarize_columns(floor, flexible, reference_price, elasticity, budget, maximum_price, bid_external, price, quantity, offer_external):
    """`market_curves.summarize` of bids and offers given as columns (arrays of one length for each side)."""
    taken = ~bid_external & (budget > 0.0)
    floor, flexible, budget = floor[taken], flexible[taken], budget[taken]
    flexing = flexible > 0.0
    reference = numpy.where(flexing, reference_price[taken], 0.0)
    shape = numpy.where(flexing, elasticity[taken], 0.0)
    ceiling = maximum_price[taken]
    unbounded = ~numpy.isfinite(ceiling)
    sort_ceiling = numpy.where(unbounded, -1.0, ceiling)
    order = numpy.lexsort((sort_ceiling, shape, reference))
    same = _same_as_previous(order, reference, shape, sort_ceiling)
    sums = group_sums(order, floor, flexible, budget, same)
    first = order[numpy.flatnonzero(~same)]
    bids = [[floors, flexibles, ref, shape_of, budgets, None if unbound else cap]
            for (floors, flexibles, budgets), ref, shape_of, unbound, cap in zip(
                sums.tolist(), reference[first].tolist(), shape[first].tolist(), unbounded[first].tolist(), ceiling[first].tolist())]
    kept = ~offer_external & (quantity > 0.0)
    offered, reservation = quantity[kept], price[kept]
    by_price = numpy.argsort(reservation, kind="stable")
    same = _same_as_previous(by_price, reservation)
    totals = group_sums(by_price, offered, offered, offered, same)[:, 0]
    offers = [[level, units] for level, units in zip(reservation[by_price[numpy.flatnonzero(~same)]].tolist(), totals.tolist())]
    return {"bids": bids, "offers": offers}


def of_rows(orders, bid_rows, offer_rows):
    """`market_curves.summarize` of the market with these bid and offer rows (arrays of rows in the order tables)."""
    bids, offers = orders.tables()
    external = orders.book.agent_ids.numbers.get(EDGE_EXTERNAL, -1)
    return summarize_columns(
        bids.floor_quantity[bid_rows], bids.flexible_quantity[bid_rows], bids.reference_price[bid_rows], bids.elasticity[bid_rows],
        bids.budget[bid_rows], bids.maximum_price[bid_rows], bids.buyer[bid_rows] == external, offers.reservation_price[offer_rows],
        offers.quantity[offer_rows], offers.seller[offer_rows] == external)
