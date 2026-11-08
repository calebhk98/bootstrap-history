"""One clearing of the credit market for one currency over a requests table and an offers table: the base rate, who is lent what by
whom, and what is left unmet (`credit.clear_with_cause` before it ran over tables is the Python this follows).

`clear_loans` fills the new-loans table and the requests' output columns and returns `CLEARED`, a cause code, or `TABLE_FULL` when the
loans table has no room (the caller reserves more and runs again: the kernel writes only its own outputs). The base rate and whether
there is one come back in `scalars` = [rate, rate is valid]. Heuristics inside are the declared ones passed in `constants`."""
import numpy

from sim.compiled_tables.growth import NO_ROOM, claim_row
from sim.compiled_tables.sums import python_sum
from sim.jit import njit

from .clearing_tables import CLEARED, NO_BORROWER_AT_ASK, NO_OFFER_AT_RATE
from .order_kernel import allocate_in_order, base_rate_target, sorted_pairs
from .risk_kernel import ADJUSTMENT_SHARE, MATERIAL_SHARE, default_probability, fundable_amount, risk_premium

TABLE_FULL = -1
TINY = 1e-12            # a piece, or a remainder, this small is rounding
UNMET_TINY = 1e-9       # a request is left unmet only by more than this


@njit
def price_requests(requests, offers, lowest_ask, constants):
    """Fill each request's funded amount (the amount asked, cut to what its collateral bears), premium, ceiling and default
    probability. `lowest_ask` is the lowest rate any lender asks."""
    floor = max(0.0, lowest_ask)
    for row in range(requests.row_count[0]):
        debt, collateral = requests.existing_debt[row], requests.collateral_value[row]
        taken = fundable_amount(requests.amount[row], debt, collateral, requests.arrears_history[row], requests.maximum_rate[row],
                                floor, constants)
        funded = taken if 0.0 < taken < requests.amount[row] else requests.amount[row]
        requests.funded_amount[row] = funded
        requests.premium[row] = risk_premium(debt + funded, collateral, requests.arrears_history[row], constants)
        requests.default_probability[row] = default_probability(debt, funded, collateral, constants)
        requests.ceiling[row] = requests.maximum_rate[row] - requests.premium[row]


@njit
def lowest_rate(offers):
    lowest = offers.minimum_rate[0]
    for row in range(offers.row_count[0]):
        lowest = min(lowest, offers.minimum_rate[row])
    return lowest


@njit
def able_to_borrow(requests, entry_floor):
    """A flag per request: its ceiling reaches the lowest ask, so it can borrow at a rate the market could clear at."""
    count = requests.row_count[0]
    able = numpy.zeros(count, dtype=numpy.bool_)
    for row in range(count):
        able[row] = requests.ceiling[row] >= entry_floor
    return able


@njit
def target_rate(requests, offers, able, constants):
    """The base rate the market aims at (credit_rate.base_rate_target over the offers and the requests that are able to borrow)."""
    offer_count, request_count = offers.row_count[0], requests.row_count[0]
    caps = numpy.empty(request_count)
    cap_amounts = numpy.empty(request_count)
    used = 0
    for row in range(request_count):
        if able[row]:
            caps[used] = requests.ceiling[row]
            cap_amounts[used] = requests.funded_amount[row]
            used += 1
    return base_rate_target(offers.minimum_rate, offers.amount, offer_count, caps, cap_amounts, used, constants[MATERIAL_SHARE])


@njit
def requested_at(requests, able, rate, only_able):
    """The funded amounts of the requests whose ceiling reaches `rate` (only those that are able, when `only_able`), summed as
    Python's `sum` does."""
    amounts = numpy.empty(requests.row_count[0])
    used = 0
    for row in range(requests.row_count[0]):
        if (able[row] or not only_able) and requests.ceiling[row] >= rate:
            amounts[used] = requests.funded_amount[row]
            used += 1
    return python_sum(amounts, used)


@njit
def offered_at(offers, rate):
    """The funds of the lenders who take `rate` or less."""
    amounts = numpy.empty(offers.row_count[0])
    used = 0
    for row in range(offers.row_count[0]):
        if offers.minimum_rate[row] <= rate:
            amounts[used] = offers.amount[row]
            used += 1
    return python_sum(amounts, used)


@njit
def settled_rate(requests, offers, able, last_rate, has_last_rate, target, lowest_ask, constants):
    """The base rate after the sticky move from the last one toward `target`, pulled to the lowest ask, or to the target, where
    holding the old rate would leave funds idle or borrowers turned away."""
    rate = target if not has_last_rate else last_rate + max(0.0, min(1.0, constants[ADJUSTMENT_SHARE])) * (target - last_rate)
    highest_ceiling = -numpy.inf
    for row in range(requests.row_count[0]):
        highest_ceiling = max(highest_ceiling, requests.ceiling[row])
    if rate < lowest_ask <= highest_ceiling:
        return lowest_ask
    if rate > target and funds_idle_above(requests, offers, able, rate, target):
        return target
    if rate < target and borrowers_rationed_below(requests, offers, able, rate):
        return target
    return rate


@njit
def funds_idle_above(requests, offers, able, held_rate, clearing_rate):
    """Some borrower would pay the clearing rate and, at the held rate above it, lenders still have funds left over."""
    if requested_at(requests, able, clearing_rate, True) <= 0.0:
        return False
    return offered_at(offers, held_rate) > requested_at(requests, able, held_rate, False)


@njit
def borrowers_rationed_below(requests, offers, able, held_rate):
    """At the held rate, borrowers who would pay it ask for more than the lenders asking no more than it hold."""
    return requested_at(requests, able, held_rate, True) > offered_at(offers, held_rate)


@njit
def queue_before(rate_a, rank_a, amount_a, rate_b, rank_b, amount_b):
    """Whether lender a is served strictly before lender b: cheaper first, then by name, then by the smaller share."""
    if rate_a != rate_b:
        return rate_a < rate_b
    if rank_a != rank_b:
        return rank_a < rank_b
    return amount_a < amount_b


@njit
def borrower_before(requests, a, b):
    """Whether request a is lent to strictly before request b: higher ceiling first, then by name, then by row."""
    if requests.ceiling[a] != requests.ceiling[b]:
        return requests.ceiling[a] > requests.ceiling[b]
    if requests.borrower_rank[a] != requests.borrower_rank[b]:
        return requests.borrower_rank[a] < requests.borrower_rank[b]
    return a < b


@njit
def lenders_lending(offers, base_rate):
    """The rows of the offers whose lender takes `base_rate` or less, in offer order."""
    rows = numpy.empty(offers.row_count[0], dtype=numpy.int64)
    used = 0
    for row in range(offers.row_count[0]):
        if offers.minimum_rate[row] <= base_rate:
            rows[used] = row
            used += 1
    return rows[:used]


@njit
def borrowers_asking(requests, base_rate):
    """The rows of the requests whose ceiling reaches `base_rate`, in request order."""
    rows = numpy.empty(requests.row_count[0], dtype=numpy.int64)
    used = 0
    for row in range(requests.row_count[0]):
        if requests.ceiling[row] >= base_rate:
            rows[used] = row
            used += 1
    return rows[:used]


@njit
def lenders_supply(offers, lending):
    """What the lending lenders hold, added in order of (name, amount)."""
    ranks = offers.lender_rank[lending].astype(numpy.float64)
    amounts = offers.amount[lending]
    order = sorted_pairs(ranks, amounts, len(lending), False)
    return python_sum(amounts[order], len(lending))


@njit
def borrowers_demand(requests, asking):
    return python_sum(requests.funded_amount[asking], len(asking))


@njit
def lender_queue(offers, lending, shares):
    """The lending lenders that were allotted something, as a queue (offer row, amount left) cheapest first."""
    kept = numpy.nonzero(shares > 0)[0]
    order = numpy.arange(len(kept))
    for place in range(1, len(kept)):
        mover = order[place]
        slot = place
        while slot > 0 and queue_before(offers.minimum_rate[lending[kept[mover]]], offers.lender_rank[lending[kept[mover]]], shares[kept[mover]],
                                        offers.minimum_rate[lending[kept[order[slot - 1]]]],
                                        offers.lender_rank[lending[kept[order[slot - 1]]]], shares[kept[order[slot - 1]]]):
            order[slot] = order[slot - 1]
            slot -= 1
        order[slot] = mover
    return lending[kept[order]], shares[kept[order]]


@njit
def borrower_queue(requests, asking):
    """The asking requests in the order they are lent to."""
    order = asking.copy()
    for place in range(1, len(order)):
        mover = order[place]
        slot = place
        while slot > 0 and borrower_before(requests, mover, order[slot - 1]):
            order[slot] = order[slot - 1]
            slot -= 1
        order[slot] = mover
    return order


@njit
def lend_down_the_queues(requests, offers, base_rate, rationed_by_risk, new_loans):
    """Share what can be lent among the lenders lending and the borrowers asking, then lend lender by lender, cheapest first, to the
    borrowers in order of ceiling; a lender with a risk capacity refuses whole any piece whose value at risk exceeds what it has left
    and keeps the rest for smaller pieces. Writes `granted` and the new loans; returns CLEARED or TABLE_FULL."""
    lending, asking = lenders_lending(offers, base_rate), borrowers_asking(requests, base_rate)
    lent = min(lenders_supply(offers, lending), borrowers_demand(requests, asking))
    lender_shares = numpy.zeros(len(lending))
    allocate_in_order(offers.minimum_rate[lending], offers.lender_rank[lending], offers.amount[lending], len(lending), lent, False,
                      lender_shares)
    limits = requests.premium[asking] if rationed_by_risk else requests.ceiling[asking]
    borrower_shares = numpy.zeros(len(asking))
    allocate_in_order(limits, requests.borrower_rank[asking], requests.funded_amount[asking], len(asking), lent, not rationed_by_risk,
                      borrower_shares)
    queue_offers, queue_left = lender_queue(offers, lending, lender_shares)
    capacity = offers.risk_capacity[queue_offers].copy()
    owed_by_row = numpy.zeros(requests.row_count[0])
    for place in range(len(asking)):
        owed_by_row[asking[place]] = borrower_shares[place]
    for row in borrower_queue(requests, asking):
        owed = owed_by_row[row]
        for place in range(len(queue_offers)):
            if owed <= TINY:
                break
            piece = min(owed, queue_left[place])
            if piece <= TINY:
                continue
            if offers.has_capacity[queue_offers[place]]:
                piece_at_risk = requests.default_probability[row] * piece
                if piece_at_risk > capacity[place] + TINY:
                    continue
                capacity[place] -= piece_at_risk
            new_row = claim_row(new_loans)
            if new_row == NO_ROOM:
                return TABLE_FULL
            record_loan(requests, new_loans, new_row, row, queue_offers[place], piece, base_rate)
            owed -= piece
            queue_left[place] -= piece
            requests.granted[row] += piece
    return CLEARED


@njit
def record_loan(requests, new_loans, new_row, row, offer, piece, base_rate):
    """The loan of `piece` to request `row` from offer `offer`: the base rate plus its premium, and the share of the collateral
    the piece is of the funded amount."""
    new_loans.request[new_row] = row
    new_loans.offer[new_row] = offer
    new_loans.principal[new_row] = piece
    new_loans.rate[new_row] = base_rate + requests.premium[row]
    new_loans.collateral_value[new_row] = requests.collateral_value[row] * piece / requests.funded_amount[row]
    new_loans.collateral_share[new_row] = requests.collateral_share[row] * piece / requests.funded_amount[row]


@njit
def leave_unmet(requests):
    """What each request asked and did not get, where that is more than rounding."""
    for row in range(requests.row_count[0]):
        left = requests.amount[row] - requests.granted[row]
        requests.unmet[row] = left if left > UNMET_TINY else 0.0


@njit
def hold_rate(scalars, last_rate, has_last_rate):
    """Nothing cleared: the rate stays at the last one, if there was one."""
    scalars[0] = last_rate
    scalars[1] = 1.0 if has_last_rate else 0.0


@njit
def clear_loans(requests, offers, constants, last_rate, has_last_rate, rate_ceiling, has_ceiling, expected_inflation, new_loans,
                scalars):
    """Clear the market. Fills the requests' output columns and the new loans; returns CLEARED, NO_BORROWER_AT_ASK, NO_OFFER_AT_RATE
    or TABLE_FULL, and the base rate (and whether there is one) in `scalars`."""
    requests.granted[:requests.row_count[0]] = 0.0
    lowest_ask = lowest_rate(offers)
    price_requests(requests, offers, lowest_ask, constants)
    able = able_to_borrow(requests, max(0.0, lowest_ask))
    _found, target = target_rate(requests, offers, able, constants)
    if not able.any():
        hold_rate(scalars, last_rate, has_last_rate)
        return NO_BORROWER_AT_ASK
    base_rate = settled_rate(requests, offers, able, last_rate, has_last_rate, target, lowest_ask, constants)
    nominal_ceiling = rate_ceiling + max(0.0, expected_inflation)
    rationed_by_risk = has_ceiling and base_rate > nominal_ceiling
    if rationed_by_risk:
        if lowest_ask > nominal_ceiling:       # no lender accepts the bound: hold the rate, lend nothing
            scalars[0] = max(0.0, last_rate if has_last_rate else lowest_ask)
            scalars[1] = 1.0
            return NO_OFFER_AT_RATE
        base_rate = nominal_ceiling
    base_rate = max(0.0, base_rate)
    scalars[0], scalars[1] = base_rate, 1.0
    status = lend_down_the_queues(requests, offers, base_rate, rationed_by_risk, new_loans)
    if status == CLEARED:
        leave_unmet(requests)
    return status
