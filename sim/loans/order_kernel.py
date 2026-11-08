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
def clearing_point(floors, floor_funds, floor_count, caps, cap_amounts, cap_count):
    """(found, price): where the quantity asked at or above a floor meets the quantity bid at or below a cap; `found` is false when
    no entry has a positive quantity (order_book.clearing_point)."""
    live_floors = numpy.empty(floor_count)
    live_floor_funds = numpy.empty(floor_count)
    floors_live = 0
    for index in range(floor_count):
        if floor_funds[index] > 0:
            live_floors[floors_live] = floors[index]
            live_floor_funds[floors_live] = floor_funds[index]
            floors_live += 1
    live_caps = numpy.empty(cap_count)
    live_cap_amounts = numpy.empty(cap_count)
    caps_live = 0
    for index in range(cap_count):
        if cap_amounts[index] > 0:
            live_caps[caps_live] = caps[index]
            live_cap_amounts[caps_live] = cap_amounts[index]
            caps_live += 1
    if floors_live == 0 and caps_live == 0:
        return False, 0.0
    floor_order = sorted_pairs(live_floors, live_floor_funds, floors_live, False)
    cap_order = sorted_pairs(live_caps, live_cap_amounts, caps_live, True)
    if floors_live == 0:
        return True, live_caps[cap_order[0]]
    if caps_live == 0:
        return True, live_floors[floor_order[0]]
    return True, meeting_price(live_floors[floor_order], live_floor_funds[floor_order], live_caps[cap_order], live_cap_amounts[cap_order])


@njit
def meeting_price(floors, floor_funds, caps, cap_amounts):
    """The price at which sorted sellers (cheapest first) and sorted buyers (keenest first) meet: midway across the range no one left
    out would break; midway between the cheapest seller and the keenest buyer when none can trade."""
    seller, buyer = 0, 0
    seller_left, buyer_left = floor_funds[0], cap_amounts[0]
    last_floor = last_cap = 0.0
    matched_any = False
    while seller < len(floors) and buyer < len(caps):
        if floors[seller] > caps[buyer]:
            break
        last_floor, last_cap = floors[seller], caps[buyer]
        matched_any = True
        matched = min(seller_left, buyer_left)
        seller_left -= matched
        buyer_left -= matched
        if seller_left <= 0:
            seller += 1
            seller_left = floor_funds[seller] if seller < len(floors) else 0.0
        if buyer_left <= 0:
            buyer += 1
            buyer_left = cap_amounts[buyer] if buyer < len(caps) else 0.0
    if not matched_any:
        return (floors[0] + caps[0]) / 2.0
    next_floor = floors[seller] if seller < len(floors) else numpy.inf
    next_cap = caps[buyer] if buyer < len(caps) else -numpy.inf
    low, high = max(last_floor, next_cap), min(last_cap, next_floor)
    if low > high:
        return (last_floor + last_cap) / 2.0
    return (low + high) / 2.0


@njit
def positive_total(values, count):
    """`sum(value for value in values if value > 0.0)` as Python adds it."""
    kept = numpy.empty(count)
    used = 0
    for index in range(count):
        if values[index] > 0.0:
            kept[used] = values[index]
            used += 1
    return python_sum(kept, used)


@njit
def base_rate_target(floors, floor_funds, floor_count, caps, cap_amounts, cap_count, material_share):
    """(found, rate): the plain clearing point, lowered to the dearest ask of the lenders with a worthwhile sum when borrowers who
    would pay it ask for more than those lenders hold (credit_rate.base_rate_target)."""
    found, rate = clearing_point(floors, floor_funds, floor_count, caps, cap_amounts, cap_count)
    if not found or floor_count == 0 or cap_count == 0:
        return found, rate
    total_funds = positive_total(floor_funds, floor_count)
    lending_funds = numpy.empty(floor_count)
    lending_asks = numpy.empty(floor_count)
    lending = 0
    for index in range(floor_count):
        if floors[index] <= rate + 1e-12 and floor_funds[index] > 0.0:
            lending_funds[lending] = floor_funds[index]
            lending_asks[lending] = floors[index]
            lending += 1
    demanded = numpy.empty(cap_count)
    asking = 0
    for index in range(cap_count):
        if caps[index] >= rate - 1e-12 and cap_amounts[index] > 0.0:
            demanded[asking] = cap_amounts[index]
            asking += 1
    if python_sum(demanded, asking) <= python_sum(lending_funds, lending) * (1.0 + 1e-9):
        return True, rate
    dearest = -numpy.inf
    for index in range(lending):
        if lending_funds[index] >= material_share * total_funds and lending_asks[index] > dearest:
            dearest = lending_asks[index]
    return True, (dearest if dearest != -numpy.inf else rate)


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
