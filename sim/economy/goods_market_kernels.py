"""The goods market's clearing as numba kernels over arrays: the logit allocation of a market's buyers over its sellers
(goods_market_logit.py is the packing), the quantity buyers want at a price, and the searches that move asks within the
year (demand_search.py, unsold_search.py). Every function takes and returns numpy arrays and numbers only.

Buyers are columns, packed in clearing order (tiers contiguous): `floors`, `flexibles`, `budgets`, the schedule's
`references` and `exponents` (negated elasticity) and `maximums` (DemandSchedule.kernel_arrays). Sellers are rows in
ascending ask order. Sums run left to right in a fixed order.
"""
import numpy

from sim.book import ROUNDING_SHARE
from sim.jit import njit

from .price_setting import LOGIT_INTENSITY
from .stock_residue import STOCK_RESIDUE_UNITS

SEARCH_PRECISION = 1e-4     # numerical tolerance of the bisection on the ask level, not a model number
KERNEL = {"error_model": "numpy"}


@njit(**KERNEL)
def pack_demand(table):
    """The kernel arrays of a market's bids from their table (a row per bid: floor, flexible, reference price, elasticity,
    budget, maximum price, priority tier): a bid with no budget wants nothing, one with no flexible part or no reference
    price does not move with price (reference one, exponent zero). Returns floors, flexibles, budgets, references,
    exponents, whether any bid has a ceiling, and where each priority tier starts, with the count at the end."""
    count = len(table)
    floors = numpy.zeros(count)
    flexibles = numpy.zeros(count)
    budgets = numpy.zeros(count)
    references = numpy.ones(count)
    exponents = numpy.zeros(count)
    bounds = numpy.zeros(count + 1, dtype=numpy.int64)
    tiers = 0
    capped = False
    for bid in range(count):
        if table[bid, 4] > 0.0:
            floors[bid] = table[bid, 0]
            budgets[bid] = table[bid, 4]
            if table[bid, 1] > 0.0 and table[bid, 2] > 0.0:
                flexibles[bid] = table[bid, 1]
                references[bid] = table[bid, 2]
                exponents[bid] = -table[bid, 3]
        if table[bid, 5] < numpy.inf:
            capped = True
        if bid > 0 and table[bid, 6] != table[bid - 1, 6]:
            tiers += 1
            bounds[tiers] = bid
    if count > 0:      # no bids: no tier, and the bounds are the start alone
        tiers += 1
        bounds[tiers] = count
    return floors, flexibles, budgets, references, exponents, capped, bounds[:tiers + 1].copy()


@njit(**KERNEL)
def pack_demand_many(table, bid_ptr):
    """`pack_demand` of each market's rows (`bid_ptr` cuts the table by market), joined: the columns for all bids, whether
    each market has a ceiling, and the tier starts of each market joined, cut by the returned pointers."""
    markets = len(bid_ptr) - 1
    total = len(table)
    floors = numpy.zeros(total)
    flexibles = numpy.zeros(total)
    budgets = numpy.zeros(total)
    references = numpy.ones(total)
    exponents = numpy.zeros(total)
    capped = numpy.zeros(markets, dtype=numpy.bool_)
    tier_ptr = numpy.zeros(markets + 1, dtype=numpy.int64)
    tier_values = numpy.zeros(total + markets, dtype=numpy.int64)
    used = 0
    for market in range(markets):
        first, last = bid_ptr[market], bid_ptr[market + 1]
        market_floors, market_flexibles, market_budgets, market_references, market_exponents, ceiling, bounds = pack_demand(
            table[first:last])
        floors[first:last] = market_floors
        flexibles[first:last] = market_flexibles
        budgets[first:last] = market_budgets
        references[first:last] = market_references
        exponents[first:last] = market_exponents
        capped[market] = ceiling
        for position in range(len(bounds)):
            tier_values[used] = bounds[position]
            used += 1
        tier_ptr[market + 1] = used
    return floors, flexibles, budgets, references, exponents, capped, tier_ptr, tier_values[:used].copy()


@njit(**KERNEL)
def want_at(price, floor, flexible, budget, reference, exponent, maximum, capped):
    """One buyer's quantity at a price (goods_market.quantity_at, with the budget cap and the buyer's ceiling)."""
    if price <= 0.0:
        wanted = floor + flexible
    else:
        wanted = floor
        if flexible > 0.0:
            wanted += flexible * (price / reference) ** exponent
        cap = budget / price
        if cap < wanted:
            wanted = cap
    if capped and price > maximum:
        return 0.0
    return wanted


@njit(**KERNEL)
def total_wanted(price, floors, flexibles, budgets, references, exponents, maximums, capped):
    """Everything the buyers want at a price."""
    total = 0.0
    for bid in range(len(floors)):
        total += want_at(price, floors[bid], flexibles[bid], budgets[bid], references[bid], exponents[bid],
                         maximums[bid], capped)
    return total


@njit(**KERNEL)
def affordable_units(price, budget_left):
    """What a buyer's budget left buys at an ask; a free or paid-to-take good (ask at or below zero) costs it nothing, so
    any quantity is affordable."""
    return budget_left / price if price > 0.0 else numpy.inf


@njit(**KERNEL)
def choice_weights(asks, stocked):
    """Each offer's weight in a buyer's choice among the offers in stock (relative to the cheapest in stock), and the
    running total of weights over the offers in ascending order, with a leading zero."""
    count = len(asks)
    weights = numpy.zeros(count)
    running = numpy.zeros(count + 1)
    cheapest = 0.0
    found = False
    for offer in range(count):
        if stocked[offer] and not found:
            cheapest = asks[offer]
            found = True
    if found:
        for offer in range(count):
            if stocked[offer]:
                if offer > 0 and stocked[offer - 1] and asks[offer] == asks[offer - 1]:      # the same ask weighs the same
                    weights[offer] = weights[offer - 1]
                elif cheapest > 0.0:
                    weights[offer] = numpy.exp(-LOGIT_INTENSITY * numpy.log(asks[offer] / cheapest))
                elif asks[offer] <= cheapest:
                    weights[offer] = 1.0
    for offer in range(count):
        running[offer + 1] = running[offer] + weights[offer]
    return weights, running


@njit(**KERNEL)
def weight_sum(running, asks, ceiling):
    """The sum of weights a buyer with this ceiling chooses among (1 when it has no choice)."""
    total = running[numpy.searchsorted(asks, ceiling, side="right")]
    return total if total > 0.0 else 1.0


@njit(**KERNEL)
def requested_round_one(asks, quantities, floors, flexibles, budgets, references, exponents, maximums, capped):
    """What the buyers ask for at the asks before any seller runs out: the first round's requests, in all."""
    stocked = quantities >= STOCK_RESIDUE_UNITS      # a seller of residue size is no seller
    weights, running = choice_weights(asks, stocked)
    requested = 0.0
    for bid in range(len(floors)):
        total = weight_sum(running, asks, maximums[bid])
        want = 0.0
        for offer in range(len(asks)):
            if offer == 0 or asks[offer] != asks[offer - 1]:      # the same price wants the same
                want = want_at(asks[offer], floors[bid], flexibles[bid], budgets[bid], references[bid], exponents[bid],
                               maximums[bid], capped)
            requested += want * weights[offer] / total
    return requested


@njit(**KERNEL)
def serve(requests, left, tier_bounds, served, short):
    """Every offer (a row) meets the requests sent to it: all are served if it holds enough, else tiers in turn, a tier
    that cannot be served in full pro rata. Fills `served` and `short` (the requests not served) and updates `left`."""
    offers, bids = requests.shape
    for offer in range(offers):
        total = 0.0
        for bid in range(bids):
            total += requests[offer, bid]
        if total > left[offer]:
            remaining = left[offer]
            for tier in range(len(tier_bounds) - 1):
                start, end = tier_bounds[tier], tier_bounds[tier + 1]
                tier_total = 0.0
                for bid in range(start, end):
                    tier_total += requests[offer, bid]
                enough = remaining >= tier_total
                share = 0.0
                if tier_total > 0.0:
                    share = 1.0 if enough else remaining / tier_total
                for bid in range(start, end):
                    served[offer, bid] = requests[offer, bid] * share
                remaining = remaining - tier_total if enough else 0.0
            left[offer] = 0.0
            for bid in range(bids):
                gap = requests[offer, bid] - served[offer, bid]
                short[offer, bid] = gap if gap > ROUNDING_SHARE * requests[offer, bid] else 0.0
        else:
            left[offer] = left[offer] - total
            for bid in range(bids):
                served[offer, bid] = requests[offer, bid]
                short[offer, bid] = 0.0


@njit(**KERNEL)
def allocate_arrays(asks, quantities, floors, flexibles, budgets, references, exponents, maximums, capped, tier_bounds):
    """Rounds of choice among the offers (ascending asks) by the bids: (quantity bought and cost per bid, quantity sold per
    offer, the quantity the bids asked for in all (taken and still unmet when the rounds ended), and the quantity each offer (row)
    sold each bid (column) over all rounds)."""
    offers, bids = len(asks), len(floors)
    wants = numpy.zeros((offers, bids))
    for offer in range(offers):
        if offer > 0 and asks[offer] == asks[offer - 1]:      # the same price wants the same: copy the row
            wants[offer, :] = wants[offer - 1, :]
            continue
        for bid in range(bids):
            wants[offer, bid] = want_at(asks[offer], floors[bid], flexibles[bid], budgets[bid], references[bid],
                                        exponents[bid], maximums[bid], capped)
    left = quantities.copy()
    stocked = left > ROUNDING_SHARE * quantities
    weights, running = choice_weights(asks, stocked)
    sums = numpy.zeros(bids)
    for bid in range(bids):
        sums[bid] = weight_sum(running, asks, maximums[bid])
    requests = numpy.zeros((offers, bids))
    for offer in range(offers):
        for bid in range(bids):
            requests[offer, bid] = wants[offer, bid] * weights[offer] / sums[bid]
    served = numpy.zeros((offers, bids))
    short = numpy.zeros((offers, bids))
    serve(requests, left, tier_bounds, served, short)
    flow = served.copy()
    taken = numpy.zeros(bids)
    cost = numpy.zeros(bids)
    unmet = numpy.zeros(bids)
    for offer in range(offers):
        for bid in range(bids):
            taken[bid] += served[offer, bid]
            cost[bid] += asks[offer] * served[offer, bid]
            unmet[bid] += short[offer, bid]
    # each further round sends the share of its choice the last could not serve (the unserved quantity at each offer as a share of
    # what the buyer wants at that ask) on among the offers still holding stock, by the same weights, so a seller short of stock
    # is replaced by the others in proportion; a round that leaves requests short has emptied an offer, so the loop ends within
    # one round per offer
    for _round in range(offers):
        stocked = left > ROUNDING_SHARE * quantities
        anyone_short = False
        for bid in range(bids):
            if unmet[bid] > 0.0:
                anyone_short = True
        if not stocked.any() or not anyone_short:
            break
        unserved_share = numpy.zeros(bids)
        for offer in range(offers):
            for bid in range(bids):
                if short[offer, bid] > 0.0 and wants[offer, bid] > 0.0:
                    unserved_share[bid] += short[offer, bid] / wants[offer, bid]
        weights, running = choice_weights(asks, stocked)
        for bid in range(bids):
            sums[bid] = weight_sum(running, asks, maximums[bid])
        for offer in range(offers):
            for bid in range(bids):
                again = 0.0
                if unserved_share[bid] > 0.0:
                    budget_left = budgets[bid] - cost[bid]
                    if budget_left < 0.0:
                        budget_left = 0.0
                    affordable = affordable_units(asks[offer], budget_left)
                    again = unserved_share[bid] * wants[offer, bid] * weights[offer] / sums[bid]
                    if affordable < again:
                        again = affordable
                requests[offer, bid] = again
        serve(requests, left, tier_bounds, served, short)
        for bid in range(bids):
            unmet[bid] = 0.0
        for offer in range(offers):
            for bid in range(bids):
                flow[offer, bid] += served[offer, bid]
                taken[bid] += served[offer, bid]
                cost[bid] += asks[offer] * served[offer, bid]
                unmet[bid] += short[offer, bid]
    # what buyers asked for: what they got and what they were still short of when the rounds ended, so a seller with no
    # stock to give is not counted in their choice
    requested = 0.0
    for bid in range(bids):
        requested += taken[bid] + unmet[bid]
    sold = quantities - left
    return taken, cost, sold, requested, flow


@njit(**KERNEL)
def ordered_asks(reservations, lifted, minimum, has_minimum, order):
    """The effective asks (reservation, lifted where flagged, held to the token minimum) in ascending order; fills `order`
    with the offers' positions in that order (ties keep their given order)."""
    asks = reservations.copy()
    for offer in range(len(asks)):
        if lifted[offer] >= 0.0 and lifted[offer] > asks[offer]:
            asks[offer] = lifted[offer]
    order[:] = numpy.argsort(asks, kind="mergesort")
    result = numpy.zeros(len(asks))
    for position in range(len(asks)):
        ask = asks[order[position]]
        if has_minimum and ask < minimum:
            ask = minimum
        result[position] = ask
    return result


@njit(**KERNEL)
def covers_at(reservations, quantities, lifted, minimum, has_minimum, floors, flexibles, budgets, references, exponents,
              maximums, capped):
    """True when, with the asks of the offers flagged in `lifted` (>= 0) at that level, the buyers ask for at least what is
    on offer (demand_search._demand_covers: the book trades and the first round's requests reach the stock)."""
    order = numpy.zeros(len(reservations), dtype=numpy.int64)
    asks = ordered_asks(reservations, lifted, minimum, has_minimum, order)
    supply = 0.0
    for offer in range(len(quantities)):
        supply += quantities[offer]
    if len(asks) == 0:
        return supply >= supply * (1.0 - ROUNDING_SHARE)
    wanted = total_wanted(asks[0], floors, flexibles, budgets, references, exponents, maximums, capped)
    requested = 0.0
    if wanted > 0.0 and supply > ROUNDING_SHARE * wanted:
        requested = requested_round_one(asks, quantities[order], floors, flexibles, budgets, references, exponents,
                                        maximums, capped)
    return requested >= supply * (1.0 - ROUNDING_SHARE)


@njit(**KERNEL)
def raise_search(reservations, quantities, raisable, limits, lowest, ceiling, minimum, has_minimum, floors, flexibles,
                 budgets, references, exponents, maximums, capped):
    """The highest common ask level in [lowest, ceiling] at which the buyers still ask for all that is offered (each
    raisable ask lifted to the level, held to its limit), by bisection on the geometric mean; -1 when not even a level
    just above `lowest` is covered. Offers are the positive-quantity ones in seller-and-tile order."""
    count = len(reservations)
    lifted = numpy.full(count, -1.0)

    for offer in range(count):
        if raisable[offer]:
            lifted[offer] = min(lowest * (1.0 + SEARCH_PRECISION), limits[offer])
    if not covers_at(reservations, quantities, lifted, minimum, has_minimum, floors, flexibles, budgets, references,
                     exponents, maximums, capped):
        return -1.0
    low, high = lowest, ceiling
    while high / low - 1.0 > SEARCH_PRECISION:
        middle = numpy.sqrt(low) * numpy.sqrt(high)
        for offer in range(count):
            if raisable[offer]:
                lifted[offer] = min(middle, limits[offer])
        if covers_at(reservations, quantities, lifted, minimum, has_minimum, floors, flexibles, budgets, references,
                     exponents, maximums, capped):
            low = middle
        else:
            high = middle
    return low


@njit(**KERNEL)
def unsold_at(level, reservations, quantities, searched, floors, keys, key_count, minimum, has_minimum, floors_b,
              flexibles, budgets, references, exponents, maximums, capped, tier_bounds):
    """True when, with every searched ask held to no more than max(its floor, `level`), some searched offer is left
    with unsold stock above its floor (unsold_search.search_asks's trial). `keys` number each offer's (seller, tile);
    what a key sells is compared with each of its offers' own quantity."""
    count = len(reservations)
    raw = reservations.copy()
    for offer in range(count):
        if searched[offer]:
            raw[offer] = min(reservations[offer], max(floors[offer], level))
    order = numpy.zeros(count, dtype=numpy.int64)
    asks = ordered_asks(raw, numpy.full(count, -1.0), minimum, has_minimum, order)
    key_sold = numpy.zeros(key_count)
    supply = 0.0
    for offer in range(count):
        supply += quantities[offer]
    if count > 0:
        wanted = total_wanted(asks[0], floors_b, flexibles, budgets, references, exponents, maximums, capped)
        if wanted > 0.0 and supply > ROUNDING_SHARE * wanted:
            taken, cost, sold, requested, flow = allocate_arrays(asks, quantities[order], floors_b, flexibles, budgets,
                                                                 references, exponents, maximums, capped, tier_bounds)
            for position in range(count):
                key_sold[keys[order[position]]] += sold[position]
    for offer in range(count):
        if searched[offer] and raw[offer] > floors[offer] and key_sold[keys[offer]] < quantities[offer] * (1.0 - ROUNDING_SHARE):
            return True
    return False


@njit(**KERNEL)
def search_level(reservations, quantities, searched, floors, keys, key_count, minimum, has_minimum, floors_b, flexibles,
                 budgets, references, exponents, maximums, capped, tier_bounds):
    """The highest common level at which every searched ask held to no more than max(its floor, level) sells out or sits
    at its floor, by bisection from the lowest floor up to the highest searched ask (unsold_search.search_asks)."""
    low = numpy.inf
    high = 0.0
    for offer in range(len(reservations)):
        if searched[offer]:
            low = min(low, floors[offer])
            high = max(high, reservations[offer])
    ceiling = high
    while high - low > SEARCH_PRECISION * (high if low > 0.0 else ceiling):
        middle = numpy.sqrt(low) * numpy.sqrt(high) if low > 0.0 else 0.5 * (low + high)
        if unsold_at(middle, reservations, quantities, searched, floors, keys, key_count, minimum, has_minimum, floors_b,
                     flexibles, budgets, references, exponents, maximums, capped, tier_bounds):
            high = middle
        else:
            low = middle
    return low
