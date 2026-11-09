"""`market_curves_rows.summarize_columns` as it was before `market_curves_kernel` (two `lexsort`s and a dozen small numpy calls), kept so
the kernel is tested against it."""
import numpy


def _same_as_previous(order, *keys):
    same = numpy.zeros(len(order), dtype=bool)
    if len(order) > 1:
        same[1:] = True
        for key in keys:
            sorted_key = key[order]
            same[1:] &= sorted_key[1:] == sorted_key[:-1]
    return same


def _group_sums(order, first, second, third, same_as_previous):
    runs = int((~same_as_previous).sum())
    sums = numpy.zeros((runs, 3))
    run = -1
    for place, row in enumerate(order.tolist()):
        if not same_as_previous[place]:
            run += 1
        sums[run, 0] += first[row]
        sums[run, 1] += second[row]
        sums[run, 2] += third[row]
    return sums


def plain_summarize_columns(floor, flexible, reference_price, elasticity, budget, maximum_price, bid_external, price, quantity, offer_external):
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
    sums = _group_sums(order, floor, flexible, budget, same)
    first = order[numpy.flatnonzero(~same)]
    bids = [[floors, flexibles, ref, shape_of, budgets, None if unbound else cap]
            for (floors, flexibles, budgets), ref, shape_of, unbound, cap in zip(
                sums.tolist(), reference[first].tolist(), shape[first].tolist(), unbounded[first].tolist(), ceiling[first].tolist())]
    kept = ~offer_external & (quantity > 0.0)
    offered, reservation = quantity[kept], price[kept]
    by_price = numpy.argsort(reservation, kind="stable")
    same = _same_as_previous(by_price, reservation)
    totals = _group_sums(by_price, offered, offered, offered, same)[:, 0]
    offers = [[level, units] for level, units in zip(reservation[by_price[numpy.flatnonzero(~same)]].tolist(), totals.tolist())]
    return {"bids": bids, "offers": offers}
