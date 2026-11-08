"""The rules of bondage placement (`bondage_hours.py`) as kernels over the rows of the year's labour offers and bids.

Hours are cut in the arrays they are given (the caller hands copies). A bid or an offer is a row number; a market's rows are read
through `order` arrays that list the rows of one (trade, area) or one employer in row order, with a first and a last place for each
thing that asks (the same rows, in the same order, the Python walked). Sums are Python's own (`python_sum`), and every figure is
worked out in the order and with the brackets the Python had, so the results are the same to the last digit."""
from sim.jit import njit
from sim.labour.api import python_sum

SMALL_HOURS = 1e-12      # hours below which nothing is placed (the Python's literal)


@njit
def place_held_kernel(group_of, group_available, people, bid_first, bid_last, bid_order, offer_first, offer_last, offer_order,
                      offer_hours, bid_hours, hours_per_worker, keep_rate, people_after, keep_triple, keep_offer, keep_amount,
                      take_triple, take_hours, scratch):
    """Bought bonded people work for the employer that holds them, off the market. Triple `t` is one holder's people in one
    (tile, trade); triples come in the order of (tile, trade, holder) names, those of one (tile, trade) sharing a `group_of` and
    drawing on its `group_available` people in turn. A triple's people (no more than are left in the group) want
    `people * hours_per_worker` hours of its holder's bids (rows `bid_order[bid_first[t]:bid_last[t]]`, in order). A bid with hours
    takes the least of the hours wanted, its hours and the market's hours offered (rows `offer_order[offer_first[t]:offer_last[t]]`);
    the offers give up that share of their hours, and the holder owes the keep of the hours taken from each offer.
    Writes `people_after` (the triple's people), the keep rows (`keep_triple`, `keep_offer`, `keep_amount`) and the takes
    (`take_triple`, `take_hours`), and cuts `offer_hours` and `bid_hours`. Returns (keep rows, takes)."""
    keeps = 0
    takes = 0
    group = -1
    available = 0.0
    for triple in range(people.shape[0]):
        if group_of[triple] != group:
            group = group_of[triple]
            available = group_available[group]
        held_people = min(people[triple], available)
        people_after[triple] = held_people
        available -= held_people
        want = held_people * hours_per_worker
        for position in range(bid_first[triple], bid_last[triple]):
            if want <= SMALL_HOURS:
                break
            slot = bid_order[position]
            if bid_hours[slot] <= 0.0:
                continue
            offered = _offered_hours(offer_order, offer_first[triple], offer_last[triple], offer_hours, scratch)
            taken = min(want, bid_hours[slot], offered)
            if taken <= SMALL_HOURS:
                continue
            cut = taken / offered
            for place in range(offer_first[triple], offer_last[triple]):
                row = offer_order[place]
                if offer_hours[row] > 0.0:
                    keep_triple[keeps] = triple
                    keep_offer[keeps] = row
                    keep_amount[keeps] = offer_hours[row] * cut / hours_per_worker * keep_rate[triple]
                    keeps += 1
                    offer_hours[row] = offer_hours[row] * (1.0 - cut)
            bid_hours[slot] = bid_hours[slot] - taken
            take_triple[takes] = triple
            take_hours[takes] = taken
            takes += 1
            want -= taken
    return keeps, takes


@njit
def _offered_hours(offer_order, first, last, offer_hours, scratch):
    """The hours of the offers in `offer_order[first:last]` added as Python's `sum` adds a list."""
    for place in range(first, last):
        scratch[place - first] = offer_hours[offer_order[place]]
    return python_sum(scratch, last - first)


@njit
def place_bonds_kernel(bond_first, bond_last, bond_creditor, bond_debt, worker_order, offer_hours, offer_rate, offer_bid_first,
                       offer_bid_last, market_bid_order, bid_hours, bid_owner, owed_share, debt_floor, total_hours, placed_hours,
                       placed_value, cash_share, counted, took, take_bid, take_hours, scratch):
    """Bonded cohorts work off their debt in their creditors' own works. Bond `b` is one cohort in bond order: its offers are
    rows `worker_order[bond_first[b]:bond_last[b]]`, and an offer's bids (same trade and area) are rows
    `market_bid_order[offer_bid_first[row]:offer_bid_last[row]]`. A cohort with hours owes `owed_share` of them; each offer
    places the least of that share of its hours, the hours still owed and the hours its debt buys at the offer's reservation wage,
    with each bid of the creditor's works (`bid_owner` equal to `bond_creditor`) that holds hours, until the debt, the hours owed
    or the offer is spent. Cuts `offer_hours` and `bid_hours`; writes per bond `total_hours`, `placed_hours`, `placed_value`,
    `cash_share` (the share of its market wages still owed in cash), `counted` (it had hours) and `took` (it placed some), and per
    take the bid row and hours (`take_bid`, `take_hours`). Returns how many takes."""
    takes = 0
    for bond in range(bond_first.shape[0]):
        first, last = bond_first[bond], bond_last[bond]
        total = _offered_hours(worker_order, first, last, offer_hours, scratch)
        total_hours[bond] = total
        if total <= 0.0:
            continue
        counted[bond] = True
        owed = owed_share * total
        debt_left = bond_debt[bond]
        placed = 0.0
        value_placed = 0.0
        for place in range(first, last):
            row = worker_order[place]
            hours = offer_hours[row]
            if hours <= 0.0 or owed <= SMALL_HOURS or debt_left <= debt_floor:
                continue
            wage = offer_rate[row]
            want = min(owed_share * hours, owed, debt_left / wage if wage > 0.0 else owed)
            for position in range(offer_bid_first[row], offer_bid_last[row]):
                if want <= SMALL_HOURS:
                    break
                slot = market_bid_order[position]
                if bid_hours[slot] <= 0.0 or bid_owner[slot] != bond_creditor[bond]:
                    continue
                taken = min(want, bid_hours[slot])
                bid_hours[slot] = bid_hours[slot] - taken
                offer_hours[row] = offer_hours[row] - taken
                take_bid[takes] = slot
                take_hours[takes] = taken
                takes += 1
                took[bond] = True
                placed += taken
                value = taken * wage
                value_placed += value
                debt_left -= value
                owed -= taken
                want -= taken
        placed_hours[bond] = placed
        placed_value[bond] = value_placed
        left_in_market = total - placed
        cash_share[bond] = max(0.0, owed_share * total - placed) / left_in_market if left_in_market > 0.0 else 0.0
    return takes


@njit
def payable_keep_kernel(holder, amount, balance, paid):
    """The keep rows a holder can pay: row `i` of holder number `holder[i]` pays the least of `amount[i]` and what is left of the
    holder's `balance` (never below zero), rows in order, so several rows of one holder never overdraw it. Writes `paid` and
    returns how many rows pay something (a row that pays nothing is left out). `balance` is spent in place."""
    count = 0
    for row in range(holder.shape[0]):
        pay = min(amount[row], balance[holder[row]])
        if pay > 0.0:
            paid[row] = pay
            balance[holder[row]] -= pay
            count += 1
        else:
            paid[row] = 0.0
    return count
