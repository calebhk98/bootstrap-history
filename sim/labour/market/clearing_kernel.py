"""The head of every labour market's year over arrays: the wage before the hiring rounds (the kernel behind
`clearing._head`), with the price of fetched hands (`import_cost.ImportCosts.supply`, `fetch_wage.fetch_wage`) and the
searches for the wage a rising supply of hours meets the demand at (`clearing.supply_target`, `_wage_with_supply`).

The year's inputs sit in `cells[field, area, trade]` (hours the trade's workers have, hours and highest wage bid, the wage
paid at the start of the year, and the columns of the sold-hours matrix the market's offers fill), per-area and per-trade
vectors, and one list of bids per market end to end (`bid_offsets`). Areas and trades are positions in sorted id order,
so a tie by name is a tie by position. A missing wage, outside option or answer is NaN. Sums run left to right where the
plain code used Python's compensated `sum`; the rules are those of the plain functions in `clearing.py`, `import_cost.py`
and `fetch_wage.py`, which stay as the fallback when a mod replaces the fetched-hands kernel or a schedule is not packed."""
import math

import numpy as np

from sim.jit import njit

from .sold_hours_kernel import sold_hours_range

EVERYONE, WANTED, MOST, WAGE, FIRST, LAST, JOBS, CELL_FIELDS = range(8)
STATUS, HEAD_WAGE, HEAD_TARGET, HEAD_GOAL, HEAD_OFFERED, HEAD_RESERVATION, HEAD_BASE, HEAD_LOWEST, HEAD_CEILING, \
    HEAD_FULL, HEAD_FIELDS = range(11)
FETCH_BISECTION_STEPS = 40      # a numerical bound: the search for the wage at which fetched hands fill a shortage
SUPPLY_SOLVE_STEPS = 60         # a numerical bound: the bisection for the wage a rising supply meets the falling demand at


@njit
def _hours_at(cells, offers, exponent, constant, area, trade, wage):
    """The hours the trade's workers in an area sell at a wage."""
    if constant:
        return cells[EVERYONE, area, trade]
    return sold_hours_range(wage, offers, exponent, int(cells[FIRST, area, trade]), int(cells[LAST, area, trade]))


@njit
def _spare(cells, area, trade):
    spare = cells[EVERYONE, area, trade] - cells[WANTED, area, trade]
    return spare if spare > 0.0 else 0.0


@njit
def _fills(cells, offers, exponent, constant, area, trade, sources, count, wanted, wage):
    own = _hours_at(cells, offers, exponent, constant, area, trade, wage)
    to_come = 0.0
    for position in range(count):
        to_come += _spare(cells, sources[position], trade)
    slack = 1e-9 * (1.0 + abs(wanted))
    if own + to_come < wanted - slack:
        return False
    fetched = 0.0
    for position in range(count):
        other = sources[position]
        to_come -= _spare(cells, other, trade)
        more = _hours_at(cells, offers, exponent, constant, other, trade, wage) - cells[WANTED, other, trade]
        fetched += more if more > 0.0 else 0.0
        if own + fetched >= wanted:
            return True
        if own + fetched + to_come < wanted - slack:
            return False
    return own + fetched >= wanted


@njit
def _lowest_filling(cells, offers, exponent, constant, area, trade, sources, count, wanted, low, high):
    for _step in range(FETCH_BISECTION_STEPS):
        middle = (low + high) / 2.0
        if _fills(cells, offers, exponent, constant, area, trade, sources, count, wanted, middle):
            high = middle
        else:
            low = middle
    return high


@njit
def _going(cells, subsistence, risk, vol, hours, area, trade):
    paid = cells[WAGE, area, trade]
    if not math.isnan(paid):
        return paid
    if math.isnan(subsistence[area]):
        return np.nan
    return subsistence[area] / max(hours, 1e-12) * (1.0 + max(0.0, risk[trade]) * vol)


@njit
def _offer_cost(cells, subsistence, reach_other, reach_cost, hours, career_hours, area, slot, trade):
    """What an area's hands come at, for the `slot`th way out of `area`; NaN where that area has no wage for the trade."""
    other = reach_other[area, slot]
    wage = cells[WAGE, other, trade]
    if math.isnan(wage):
        return np.nan
    floor = wage
    if not math.isnan(subsistence[other]):
        floor = max(wage, subsistence[other] / max(hours, 1e-12))
    return floor + reach_cost[area, slot] / career_hours


@njit
def _sorted_offers(cells, subsistence, reach_other, reach_cost, reach_count, hours, career_hours, area, trade, costs, others):
    """The offers by (cost, area) into `costs` and `others`; how many."""
    count = 0
    for slot in range(reach_count[area]):
        cost = _offer_cost(cells, subsistence, reach_other, reach_cost, hours, career_hours, area, slot, trade)
        if math.isnan(cost):
            continue
        other = reach_other[area, slot]
        position = count
        while position > 0 and (costs[position - 1] > cost or (costs[position - 1] == cost and others[position - 1] > other)):
            costs[position] = costs[position - 1]
            others[position] = others[position - 1]
            position -= 1
        costs[position] = cost
        others[position] = other
        count += 1
    return count


@njit
def _fetch_wage(cells, offers, exponent, constant, area, trade, wanted, going, top, costs, others, count_offers, sources):
    """`fetch_wage.fetch_wage`: NaN where the bids set the wage."""
    if _hours_at(cells, offers, exponent, constant, area, trade, going) >= wanted:
        return np.nan
    count = 0
    lowest = going
    for position in range(count_offers):
        cost = costs[position]
        sources[count] = others[position]
        if _fills(cells, offers, exponent, constant, area, trade, sources, count + 1, wanted, cost):
            if _fills(cells, offers, exponent, constant, area, trade, sources, count, wanted, cost):
                return _lowest_filling(cells, offers, exponent, constant, area, trade, sources, count, wanted, lowest, cost)
            return cost
        count += 1
        lowest = cost
    if top > lowest and _fills(cells, offers, exponent, constant, area, trade, sources, count, wanted, top):
        return _lowest_filling(cells, offers, exponent, constant, area, trade, sources, count, wanted, lowest, top)
    return np.nan


@njit
def _fetched_supply(cells, offers, exponent, constant, subsistence, risk, vol, hours, career_hours, reach_other, reach_cost,
                    reach_count, area, trade, costs, others, sources, answer):
    """`ImportCosts.supply`: whether hands can be fetched, and (bound, share) in `answer`."""
    wanted = cells[WANTED, area, trade]
    going = _going(cells, subsistence, risk, vol, hours, area, trade)
    if math.isnan(going):
        return False
    shortage = wanted - _hours_at(cells, offers, exponent, constant, area, trade, going)
    if wanted <= 0.0 or shortage <= 0.0:
        return False
    count = _sorted_offers(cells, subsistence, reach_other, reach_cost, reach_count, hours, career_hours, area, trade, costs, others)
    top = cells[MOST, area, trade]
    bound = _fetch_wage(cells, offers, exponent, constant, area, trade, wanted, going, top, costs, others, count, sources)
    if math.isnan(bound):
        found = False
        dearest = 0.0
        for position in range(count):
            if costs[position] <= top and (not found or costs[position] > dearest):
                dearest = costs[position]
                found = True
        if not found:
            return False
        bound = dearest
    fetched = 0.0
    for slot in range(reach_count[area]):
        cost = _offer_cost(cells, subsistence, reach_other, reach_cost, hours, career_hours, area, slot, trade)
        if math.isnan(cost) or cost > bound:
            continue
        other = reach_other[area, slot]
        more = _hours_at(cells, offers, exponent, constant, other, trade, bound) - cells[WANTED, other, trade]
        fetched += more if more > 0.0 else 0.0
    answer[0] = bound
    answer[1] = (shortage if shortage < fetched else fetched) / wanted
    return True


@njit
def _sorted_live(reservation, caps, bid_hours, first, last, live_caps, live_hours):
    """The bids a wage of `reservation` can pay, highest maximum first (then most hours); how many."""
    count = 0
    for index in range(first, last):
        cap = caps[index]
        if cap < reservation:
            continue
        position = count
        while position > 0 and (live_caps[position - 1] < cap or (live_caps[position - 1] == cap and live_hours[position - 1] < bid_hours[index])):
            live_caps[position] = live_caps[position - 1]
            live_hours[position] = live_hours[position - 1]
            position -= 1
        live_caps[position] = cap
        live_hours[position] = bid_hours[index]
        count += 1
    return count


@njit
def _clearing_target(reservation, offered, caps, bid_hours, first, last, live_caps, live_hours):
    """`clearing.clearing_target`."""
    count = _sorted_live(reservation, caps, bid_hours, first, last, live_caps, live_hours)
    taken = 0.0
    for index in range(count):
        taken += live_hours[index]
        if taken >= offered:
            if taken <= offered and index + 1 < count:
                beyond = live_caps[index + 1]
            elif taken > offered:
                beyond = live_caps[index]
            else:
                beyond = -np.inf
            return (max(reservation, beyond) + live_caps[index]) / 2.0
    return reservation


@njit
def _hours_wanted_at(wage, caps, bid_hours, first, last):
    total = 0.0
    for index in range(first, last):
        if caps[index] >= wage:
            total += bid_hours[index]
    return total


@njit
def _pressure(last, reservation, offered, caps, bid_hours, first, last_bid):
    """`clearing.pressure`."""
    wanted = _hours_wanted_at(max(last, reservation), caps, bid_hours, first, last_bid)
    return min(1.0, abs(wanted - offered) / offered)


@njit
def _continuous_wanted_at(wage, reservation, live_caps, live_hours, count):
    """`clearing.hours_wanted_at` over the `count` distinct caps in `live_caps` (lowest first) with their hours."""
    total = 0.0
    lower = reservation
    for index in range(count):
        cap = live_caps[index]
        if wage <= lower:
            total += live_hours[index]
        elif wage < cap:
            total += live_hours[index] * ((cap - wage) / (cap - lower))
        lower = cap
    return total


@njit
def _supply_target(reservation, caps, bid_hours, first, last, cells, offers, exponent, area, trade, live_caps, live_hours):
    """`clearing.supply_target` for a market whose hours sold are its offers' (`sold_hours_range`)."""
    first_offer = int(cells[FIRST, area, trade])
    last_offer = int(cells[LAST, area, trade])
    count = 0
    for index in range(first, last):      # the distinct maximum wages the reservation can pay, lowest first, with their hours
        cap = caps[index]
        if cap < reservation:
            continue
        position = count
        while position > 0 and live_caps[position - 1] > cap:
            position -= 1
        if position > 0 and live_caps[position - 1] == cap:
            live_hours[position - 1] += bid_hours[index]
            continue
        for later in range(count, position, -1):
            live_caps[later] = live_caps[later - 1]
            live_hours[later] = live_hours[later - 1]
        live_caps[position] = cap
        live_hours[position] = bid_hours[index]
        count += 1
    low = reservation
    for index in range(count):
        high = live_caps[index]
        if sold_hours_range(high, offers, exponent, first_offer, last_offer) < _continuous_wanted_at(high, reservation, live_caps, live_hours, count):
            low = high
            continue
        if sold_hours_range(low, offers, exponent, first_offer, last_offer) >= _continuous_wanted_at(low, reservation, live_caps, live_hours, count):
            return low
        for _step in range(SUPPLY_SOLVE_STEPS):
            middle = (low + high) / 2.0
            if sold_hours_range(middle, offers, exponent, first_offer, last_offer) >= _continuous_wanted_at(middle, reservation, live_caps, live_hours, count):
                high = middle
            else:
                low = middle
        return high
    return low


@njit
def _moved(wage_now, goal, ceiling, reservation, caps, bid_hours, first, last, cells, offers, exponent, area, trade):
    """The wage now moved toward `goal` by the imbalance at it (`clearing._wage_with_supply.moved`)."""
    at = max(wage_now, reservation)
    offered = sold_hours_range(at, offers, exponent, int(cells[FIRST, area, trade]), int(cells[LAST, area, trade]))
    gap = 1.0
    if offered > 0.0:
        gap = min(1.0, abs(_hours_wanted_at(at, caps, bid_hours, first, last) - offered) / offered)
    return wage_now + gap * (min(goal, ceiling) - wage_now)


@njit
def _bid_weighted_worth(reservation, caps, bid_hours, first, last):
    total = 0.0
    worth = 0.0
    for index in range(first, last):
        if caps[index] >= reservation and bid_hours[index] > 0.0:
            total += bid_hours[index]
            worth += caps[index] * bid_hours[index]
    if total <= 0.0:
        return reservation
    return max(reservation, worth / total)


@njit
def market_heads(cells, offers, exponent, constant, subsistence, ask_floor, scale, risk, training_years, premium, fallback,
                 vol, hours, career_hours, reach_other, reach_cost, reach_count, market_area, market_trade, bid_offsets, caps,
                 bid_hours, share_closed_rise, heads):
    """For every market: its wage before the hiring rounds, where it is heading, the clearing point, the hours offered, the
    reservation wage, the wage floor and the ceiling (`heads[market, field]`); the status is zero where the area states
    no outside option. `constant` is true where every worker sells a whole year at any wage."""
    reach_width = max(reach_other.shape[1], 1)
    costs = np.empty(reach_width)
    others = np.empty(reach_width, np.int64)
    sources = np.empty(reach_width, np.int64)
    answer = np.empty(2)
    longest = 1
    for market in range(market_area.shape[0]):
        if bid_offsets[market + 1] - bid_offsets[market] > longest:
            longest = bid_offsets[market + 1] - bid_offsets[market]
    live_caps = np.empty(longest + 1)
    live_hours = np.empty(longest + 1)
    for market in range(market_area.shape[0]):
        area = market_area[market]
        trade = market_trade[market]
        first = bid_offsets[market]
        last_bid = bid_offsets[market + 1]
        count_bids = last_bid - first
        heads[market, STATUS] = 0.0
        if math.isnan(subsistence[area]):
            continue
        base = subsistence[area] / max(hours, 1e-12) * (1.0 + max(0.0, risk[trade]) * vol)
        lowest = base
        if not math.isnan(ask_floor[area]):
            lowest = ask_floor[area] / max(hours, 1e-12)
        reservation = max(base * scale[area, trade], lowest)
        if trade != fallback and not math.isnan(cells[WAGE, area, fallback]):      # `unskilled_reach.reservation_with_unskilled_option`
            option = cells[WAGE, area, fallback]
            if option > reservation:
                share = 1.0
                if cells[EVERYONE, area, trade] > 0.0:
                    share = min(1.0, max(0.0, cells[JOBS, area, fallback]) / cells[EVERYONE, area, trade])
                reservation = reservation + share * (option - reservation)
        last = cells[WAGE, area, trade]
        if trade == fallback:
            substitute = np.inf
        else:
            unskilled = subsistence[area] / max(hours, 1e-12)      # the reservation wage of a trade with no risk
            if not math.isnan(cells[WAGE, area, fallback]):
                unskilled = max(cells[WAGE, area, fallback], unskilled)
            substitute = unskilled * premium[trade] * (1.0 + risk[trade] * vol)
        long_run = max(substitute, reservation)
        imported = np.nan
        fetched_share = 0.0
        if count_bids > 0 and _fetched_supply(cells, offers, exponent, constant, subsistence, risk, vol, hours, career_hours,
                                              reach_other, reach_cost, reach_count, area, trade, costs, others, sources, answer):
            imported = answer[0]
            fetched_share = answer[1]
        # the ceiling: `scarcity.short_run_ceiling`
        if math.isinf(long_run) or training_years[trade] <= 0.0 or count_bids == 0:
            ceiling = long_run
        else:
            ceiling = _bid_weighted_worth(reservation, caps, bid_hours, first, last_bid)
        if not math.isnan(imported):
            share = min(1.0, max(0.0, fetched_share))
            if share >= 1.0:
                ceiling = min(ceiling, imported)
            elif share > 0.0:
                if math.isinf(ceiling) and count_bids > 0:
                    ceiling = _bid_weighted_worth(reservation, caps, bid_hours, first, last_bid)
                ceiling = (1.0 - share) * ceiling + share * min(ceiling, imported)
        ceiling = max(ceiling, reservation)
        highest = reservation
        any_payable = False
        for index in range(first, last_bid):
            if caps[index] > highest:
                highest = caps[index]
            if caps[index] >= reservation:
                any_payable = True
        full = cells[EVERYONE, area, trade]
        if constant:
            offered = full
            if offered <= 0.0:
                if math.isnan(last):
                    best = reservation
                    for index in range(first, last_bid):
                        if index == first or caps[index] > best:
                            best = caps[index]
                    wage = best
                else:
                    wage = last
            elif count_bids == 0:
                wage = reservation
            else:
                goal = _clearing_target(reservation, offered, caps, bid_hours, first, last_bid, live_caps, live_hours)
                if math.isnan(last):
                    wage = goal
                else:
                    closed = share_closed_rise if goal > last else 1.0
                    wage = last + closed * _pressure(last, reservation, offered, caps, bid_hours, first, last_bid) * (goal - last)
                if any_payable:
                    wage = max(wage, reservation)
                wage = min(wage, highest)
            wage = min(wage, ceiling)
            goal = wage
            target = wage
            if offered > 0.0 and count_bids > 0:
                goal = _clearing_target(reservation, offered, caps, bid_hours, first, last_bid, live_caps, live_hours)
                if math.isnan(last) or not wage < last:
                    target = wage + _pressure(wage, reservation, offered, caps, bid_hours, first, last_bid) * (min(goal, ceiling) - wage)
        else:
            if count_bids == 0:
                wage = min(reservation, ceiling)
                target = np.nan
                goal = wage
            else:
                goal = _supply_target(reservation, caps, bid_hours, first, last_bid, cells, offers, exponent, area, trade, live_caps, live_hours)
                if math.isnan(last):
                    wage = goal
                else:
                    stepped = _moved(last, goal, ceiling, reservation, caps, bid_hours, first, last_bid, cells, offers, exponent, area, trade)
                    closed = share_closed_rise if stepped > last else 1.0
                    wage = last + closed * (stepped - last)
                if any_payable:
                    wage = max(wage, reservation)
                wage = min(min(wage, highest), ceiling)
                if not math.isnan(last) and wage < last:
                    target = wage
                else:
                    target = _moved(wage, goal, ceiling, reservation, caps, bid_hours, first, last_bid, cells, offers, exponent, area, trade)
            offered = sold_hours_range(wage, offers, exponent, int(cells[FIRST, area, trade]), int(cells[LAST, area, trade]))
        if not math.isnan(target):
            target = min(target, long_run)
        heads[market, STATUS] = 1.0
        heads[market, HEAD_WAGE] = wage
        heads[market, HEAD_TARGET] = target
        heads[market, HEAD_GOAL] = goal
        heads[market, HEAD_OFFERED] = offered
        heads[market, HEAD_RESERVATION] = reservation
        heads[market, HEAD_BASE] = base
        heads[market, HEAD_LOWEST] = lowest
        heads[market, HEAD_CEILING] = ceiling
        heads[market, HEAD_FULL] = full
