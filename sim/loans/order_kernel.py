"""Where a queue of lenders meets a queue of borrowers, and how a total is shared down a queue (`sim/economy/order_book.py` and
`credit_rate.base_rate_target` are the Python these follow).

A queue is parallel arrays: a limit (a rate), a quantity and, where a tie is broken by name, the rank of the name. Sorts are stable
insertion sorts on a permutation, so the order of equal entries is the order they came in."""
import numpy

from sim.compiled_tables.sums import python_sum
from sim.jit import njit


@njit
def pair_before(limit_a, quantity_a, limit_b, quantity_b, descending):
    """Whether (limit, quantity) a sorts strictly before b as tuples (after, when `descending`)."""
    if limit_a != limit_b:
        return limit_a > limit_b if descending else limit_a < limit_b
    return quantity_a > quantity_b if descending else quantity_a < quantity_b


@njit
def sorted_pairs(limits, quantities, count, descending):
    """The first `count` entries as a permutation, sorted by (limit, quantity) ascending or descending, equal entries in order."""
    order = numpy.arange(count)
    for place in range(1, count):
        mover = order[place]
        slot = place
        while slot > 0 and pair_before(limits[mover], quantities[mover], limits[order[slot - 1]], quantities[order[slot - 1]], descending):
            order[slot] = order[slot - 1]
            slot -= 1
        order[slot] = mover
    return order


@njit
def cumulative_curve(limits, quantities, count, descending):
    """(prices, totals, points): the distinct limit prices of the entries with a positive quantity, ascending, and at each the
    quantity of entries whose limit is at most that price (at least it, when `descending`), summed in the order Python sums them
    (order_book.cumulative_curve)."""
    live_limits = numpy.empty(count)
    live_quantities = numpy.empty(count)
    live = 0
    for index in range(count):
        if quantities[index] > 0:
            live_limits[live] = limits[index]
            live_quantities[live] = quantities[index]
            live += 1
    order = sorted_pairs(live_limits, live_quantities, live, descending)
    prices = numpy.empty(live)
    totals = numpy.empty(live)
    points = 0
    running = 0.0
    for place in range(live):
        running += live_quantities[order[place]]
        price = live_limits[order[place]]
        if points > 0 and prices[points - 1] == price:
            totals[points - 1] = running
        else:
            prices[points] = price
            totals[points] = running
            points += 1
    if descending:
        prices[:points] = prices[:points][::-1].copy()
        totals[:points] = totals[:points][::-1].copy()
    return prices, totals, points


@njit
def interpolated(prices, totals, points, price):
    """The curve through (price, total) points at `price`: straight between points, flat beyond the ends."""
    if price <= prices[0]:
        return totals[0]
    for index in range(points - 1):
        if price < prices[index + 1]:
            return totals[index] + (totals[index + 1] - totals[index]) * (price - prices[index]) / (prices[index + 1] - prices[index])
    return totals[points - 1]


@njit
def base_rate_target(floors, floor_funds, floor_count, caps, cap_amounts, cap_count):
    """(found, rate): where the funds offered meet the funds requested, each a curve through its cumulative points
    (order_book.supply_demand_crossing); `found` is false when no entry has a positive quantity."""
    supply_prices, supply_totals, supplies = cumulative_curve(floors, floor_funds, floor_count, False)
    demand_prices, demand_totals, demands = cumulative_curve(caps, cap_amounts, cap_count, True)
    if supplies == 0 and demands == 0:
        return False, 0.0
    if supplies == 0:
        return True, demand_prices[demands - 1]
    if demands == 0:
        return True, supply_prices[0]
    candidates = numpy.sort(numpy.concatenate((supply_prices[:supplies], demand_prices[:demands])))
    previous_price = supply_prices[0]
    previous_gap = 0.0
    first = True
    last_price = supply_prices[0]
    for index in range(len(candidates)):
        price = candidates[index]
        if price < supply_prices[0] or price > supply_prices[supplies - 1] or (not first and price == previous_price):
            continue
        gap = interpolated(supply_prices, supply_totals, supplies, price) - interpolated(demand_prices, demand_totals, demands, price)
        if gap >= 0.0:
            if first:
                return True, price
            return True, previous_price + (price - previous_price) * (0.0 - previous_gap) / (gap - previous_gap)
        previous_price, previous_gap = price, gap
        last_price = price
        first = False
    return True, last_price


@njit
def allocate_in_order(limits, ranks, quantities, count, total, descending, shares):
    """Share `total` among the first `count` entries best limit first (highest when `descending`), pro rata among equal limits at the
    margin, writing each entry's share to `shares` (order_book.allocate_in_order). Entries of one limit are served in order of (rank,
    quantity)."""
    for index in range(count):
        shares[index] = 0.0
    keys = -limits[:count] if descending else limits[:count].copy()
    by_limit = numpy.argsort(keys, kind="mergesort")
    remaining = total
    start = 0
    while start < count:
        stop = start + 1
        while stop < count and limits[by_limit[stop]] == limits[by_limit[start]]:
            stop += 1
        if remaining <= 0:
            break
        remaining = share_group(by_limit[start:stop], ranks, quantities, remaining, shares)
        start = stop


@njit
def share_group(members, ranks, quantities, remaining, shares):
    """Serve one group of equal limits from `remaining`: all of each when they all fit, else pro rata with the last member taking
    what is left. Returns what remains."""
    ordered = members[sorted_pairs(ranks[members].astype(numpy.float64), quantities[members], len(members), False)]
    group_total = python_sum(quantities[ordered], len(ordered))
    if group_total <= remaining:
        for index in ordered:
            shares[index] = quantities[index]
        return remaining - group_total
    given = 0.0
    for place in range(len(ordered) - 1):
        index = ordered[place]
        shares[index] = quantities[index] * remaining / group_total
        given += shares[index]
    shares[ordered[len(ordered) - 1]] = remaining - given
    return 0.0
