"""The rest of every labour market's year over arrays, after the heads (`clearing_kernel.market_heads`): the employers a wage
leaves with hours wanted and the hours each keeps from last year (`clearing.eligible_bids`, `retain`), the ceilings their offers rise
to (`offer_ceilings`), the hiring jobs for `hiring_kernel.hire_markets`, and after the rounds the wage paid, the hours sold at it,
poaching (`clearing.poach`) and the ask moved for next year (`asks.record`).

Bids sit end to end by market (`bid_offsets`), within a market in order of employer position, then highest maximum wage, then
hours, so an employer's bids are together and a sum over them runs as the plain code's did. Employers of a market with hours on
offer sit in slots end to end (`slot_offsets`), in the order of their positions (sorted ids). Sums run left to right where the plain
code used Python's compensated `sum`."""
import numpy as np

from sim.jit import njit

from .clearing_kernel import FIRST, HEAD_BASE, HEAD_CEILING, HEAD_GOAL, HEAD_LOWEST, HEAD_OFFERED, HEAD_RESERVATION, HEAD_WAGE, LAST, STATUS
from .sold_hours_kernel import sold_hours_range


@njit
def count_slots(heads, bid_offsets, bid_employer, caps, counts):
    """Per market, the employers with a bid at or above the wage, where the market has hours on offer; else none."""
    for market in range(counts.shape[0]):
        counts[market] = 0
        if heads[market, STATUS] == 0.0 or not heads[market, HEAD_OFFERED] > 0.0:
            continue
        wage = heads[market, HEAD_WAGE]
        found = 0
        previous = -1
        for index in range(bid_offsets[market], bid_offsets[market + 1]):
            if caps[index] < wage:
                continue
            if bid_employer[index] != previous:
                found += 1
                previous = bid_employer[index]
        counts[market] = found


@njit
def _store(slot, employer, employer_wanted, employer_rank, lowest_cap, previous_hours, slot_employer, wanted, rank, kept, ceilings):
    slot_employer[slot] = employer
    wanted[slot] = employer_wanted
    rank[slot] = employer_rank
    ceilings[slot] = lowest_cap
    kept[slot] = previous_hours


@njit
def fill_slots(heads, bid_offsets, bid_employer, caps, bid_hours, bid_previous, slot_offsets, slot_employer, wanted, rank, kept,
               hired, offers, ceilings, pools, asks, floors, has_job, wanted_total):
    """The jobs of the markets with hours on offer (employers in slots: what each wants, ranks, holds and may offer), and for
    every market the hours wanted in all (`wanted_total`)."""
    for market in range(wanted_total.shape[0]):
        wanted_total[market] = 0.0
        has_job[market] = False
        if heads[market, STATUS] == 0.0:
            continue
        wage = heads[market, HEAD_WAGE]
        offered = heads[market, HEAD_OFFERED]
        job = offered > 0.0
        has_job[market] = job
        slot = slot_offsets[market] - 1
        previous = -1
        previous_hours = 0.0
        employer_wanted = 0.0
        employer_rank = 0.0
        lowest_cap = np.inf
        total_wanted = 0.0
        for index in range(bid_offsets[market], bid_offsets[market + 1]):
            if caps[index] < wage:
                continue
            if bid_employer[index] != previous:
                if previous >= 0:
                    total_wanted += employer_wanted
                    if job:
                        _store(slot, previous, employer_wanted, employer_rank, lowest_cap, previous_hours, slot_employer, wanted,
                               rank, kept, ceilings)
                previous = bid_employer[index]
                previous_hours = bid_previous[index]
                slot += 1
                employer_wanted = 0.0
                employer_rank = 0.0
                lowest_cap = np.inf
            employer_wanted += bid_hours[index]
            if caps[index] > employer_rank:
                employer_rank = caps[index]
            if caps[index] < lowest_cap:
                lowest_cap = caps[index]
        if previous >= 0:
            total_wanted += employer_wanted
            if job:
                _store(slot, previous, employer_wanted, employer_rank, lowest_cap, previous_hours, slot_employer, wanted, rank,
                       kept, ceilings)
        wanted_total[market] = total_wanted
        if not job:
            continue
        first = slot_offsets[market]
        last = slot_offsets[market + 1]
        total = 0.0
        for position in range(first, last):
            held = kept[position]
            kept[position] = wanted[position] if held - wanted[position] > 0.0 else held
            total += kept[position]
        scale = offered / total if total > offered else 1.0
        held_total = 0.0
        market_ceiling = min(heads[market, HEAD_CEILING], heads[market, HEAD_GOAL])
        for position in range(first, last):
            kept[position] *= scale
            hired[position] = kept[position]
            held_total += hired[position]
            offers[position] = wage
            top = ceilings[position] if ceilings[position] < market_ceiling else market_ceiling
            ceilings[position] = top if top > wage else wage
        pools[market] = max(0.0, offered - held_total)
        asks[market] = heads[market, HEAD_RESERVATION]
        floors[market] = heads[market, HEAD_LOWEST]


@njit
def _loss_share(rank_of_other, rank_of_employer, elasticity, search_share):
    """`clearing.on_the_job_loss_share(rank_of_other, rank_of_employer)`."""
    if rank_of_employer <= rank_of_other:
        return 0.0
    factor = 1.0
    if rank_of_other > 0.0:
        factor = (rank_of_employer / rank_of_other) ** elasticity
    return min(1.0, search_share * factor)


@njit
def _poach(first, last, hired, wanted, rank, elasticity, search_share, order, capacity):
    """`clearing.poach` for the employers in slots `first` up to `last`."""
    count = last - first
    for position in range(count):
        place = position
        while place > 0 and rank[first + order[place - 1]] < rank[first + position]:
            order[place] = order[place - 1]
            place -= 1
        order[place] = position
    for turn in range(count):
        employer = first + order[turn]
        short = wanted[employer] - hired[employer]
        total = 0.0
        for other in range(first, last):
            capacity[other - first] = -1.0
            if rank[other] < rank[employer] and hired[other] > 0.0:
                capacity[other - first] = hired[other] * _loss_share(rank[other], rank[employer], elasticity, search_share)
                total += capacity[other - first]
        if short <= 0.0 or total <= 0.0:
            continue
        moved = short if short < total else total
        for other in range(first, last):
            if capacity[other - first] >= 0.0:
                hired[other] -= moved * capacity[other - first] / total
        hired[employer] += moved


@njit
def finish_markets(heads, market_area, market_trade, cells, offers_matrix, exponent, constant, scale, slot_offsets, wanted, rank,
                   hired, offers, taken_amount, taken_flag, wanted_total, has_job, elasticity, search_share, ask_adjustment,
                   rounds, cut, wage_out, offered_out, hired_total, scale_out):
    """After the hiring rounds: each market's wage (what the hours taken on were paid), the hours sold at it, the hours poached
    between employers, the hours hired, and the ask moved (`asks.record`)."""
    longest = 1
    for market in range(wage_out.shape[0]):
        if slot_offsets[market + 1] - slot_offsets[market] > longest:
            longest = slot_offsets[market + 1] - slot_offsets[market]
    order = np.empty(longest, np.int64)
    capacity = np.empty(longest)
    year_cut = 1.0 - (1.0 - cut) ** rounds
    for market in range(wage_out.shape[0]):
        wage_out[market] = np.nan
        offered_out[market] = np.nan
        hired_total[market] = 0.0
        scale_out[market] = np.nan
        if heads[market, STATUS] == 0.0:
            continue
        area = market_area[market]
        trade = market_trade[market]
        wage = heads[market, HEAD_WAGE]
        offered = heads[market, HEAD_OFFERED]
        first = slot_offsets[market]
        last = slot_offsets[market + 1]
        if has_job[market]:
            new_hours = 0.0
            for position in range(first, last):
                if taken_flag[position]:
                    new_hours += taken_amount[position]
            if new_hours > 0.0:
                paid = 0.0
                for position in range(first, last):
                    if taken_flag[position]:
                        paid += taken_amount[position] * offers[position]
                wage = paid / new_hours
            if not constant:
                offered = sold_hours_range(wage, offers_matrix, exponent, int(cells[FIRST, area, trade]),
                                           int(cells[LAST, area, trade]))
            _poach(first, last, hired, wanted, rank, elasticity, search_share, order, capacity)
        total = 0.0
        for position in range(first, last):
            if hired[position] > 0.0:
                total += hired[position]
        hired_total[market] = total
        wage_out[market] = wage
        offered_out[market] = offered
        reservation = heads[market, HEAD_BASE]
        before = scale[area, trade]
        moved = before
        if offered > 0.0:
            if wanted_total[market] >= offered:
                moved = before * (1.0 + ask_adjustment * min(1.0, (wanted_total[market] - offered) / offered))
            else:
                moved = before * (1.0 - year_cut * (offered - wanted_total[market]) / offered)
        if moved > before and reservation > 0.0:
            if wage <= reservation * before * (1.0 + ask_adjustment):
                moved = min(moved, max(before, wage / reservation))
            else:
                moved = before
        if reservation > 0.0:
            moved = max(moved, heads[market, HEAD_LOWEST] / reservation)
        scale_out[market] = moved
