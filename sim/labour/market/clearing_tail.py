"""Every market of the year cleared in a few kernel calls from one pack: the heads (`clearing_kernel.market_heads`), the employers and
their jobs (`clearing_tail_kernel.fill_slots`), the hiring rounds of all markets (`hiring_kernel.hire_markets`) and the finish
(`finish_markets`); then the state and the clearings written back market by market. The plain functions of `clearing.py`
(`_prepare`, `_finish`) stay for a caller whose fetched-hands search or hours schedule the kernels do not stand in for."""
from itertools import chain
from operator import attrgetter
from typing import List

import numpy as np

from . import asks, clearing_arrays, clearing_kernel, clearing_tail_kernel as kernel, hiring_kernel
from .applications import APPLICATIONS_PER_ROUND, SEPARATION_SHARE_PER_ROUND
from .records import LabourClearing, MarketState


def _employer_columns(packed, state: MarketState):
    """The employer of every bid (a position in sorted id order), the hours that employer held in the market last year, and the ids."""
    flat = list(map(attrgetter("employer"), chain.from_iterable(packed.groups)))
    names = sorted(set(flat))
    position = {name: index for index, name in enumerate(names)}
    previous: List[float] = []
    for (trade, area), each in zip(packed.markets, packed.groups):
        held = state.hired_hours.get(area, {}).get(trade) if each else None
        previous.extend([held.get(bid.employer, 0.0) for bid in each] if held else [0.0] * len(each))
    return np.fromiter((position[name] for name in flat), np.int64, len(flat)), np.array(previous, np.float64), names


def clear_packed(state: MarketState, packed, elasticity: float, search_share: float) -> List[LabourClearing]:
    """The clearings of the packed markets with a stated outside option, in the packed order; the state moves as the plain
    `_finish` leaves it."""
    heads = clearing_arrays.run_heads(packed)
    count = len(packed.markets)
    employer, previous, names = _employer_columns(packed, state)
    market_of_bid = np.repeat(np.arange(count), np.diff(packed.bid_offsets))
    order = np.lexsort((packed.bid_hours, packed.caps, employer, market_of_bid))      # by market, then employer, then maximum wage, then hours
    s_employer, s_caps, s_hours, s_previous = employer[order], packed.caps[order], packed.bid_hours[order], previous[order]
    counts = np.zeros(count, np.int64)
    kernel.count_slots(heads, packed.bid_offsets, s_employer, s_caps, counts)
    slot_offsets = np.zeros(count + 1, np.int64)
    np.cumsum(counts, out=slot_offsets[1:])
    slots = int(slot_offsets[-1])
    slot_employer = np.zeros(slots, np.int64)
    wanted, rank, kept, hired, offers, ceilings = (np.zeros(slots) for _each in range(6))
    pools, ask, floors, wanted_total = (np.zeros(count) for _each in range(4))
    has_job = np.zeros(count, np.bool_)
    kernel.fill_slots(heads, packed.bid_offsets, s_employer, s_caps, s_hours, s_previous, slot_offsets, slot_employer, wanted, rank,
                      kept, hired, offers, ceilings, pools, ask, floors, has_job, wanted_total)
    taken_amount, taken_flag = np.zeros(slots), np.zeros(slots, np.bool_)
    hiring_kernel.hire_markets(
        slot_offsets, hired, kept, wanted, offers, ceilings, pools, ask, floors, has_job, taken_amount, taken_flag,
        asks.SEARCH_ROUNDS_PER_YEAR, APPLICATIONS_PER_ROUND, SEPARATION_SHARE_PER_ROUND, asks.RESERVATION_CUT_PER_ROUND,
        asks.WAGE_UPDATE_PER_ROUND, asks.VACANCY_SHARE_THRESHOLD)
    wage_out, offered_out, hired_total, scale_out = (np.zeros(count) for _each in range(4))
    kernel.finish_markets(heads, packed.market_area, packed.market_trade, packed.cells, packed.offers, packed.exponent, packed.constant,
                          packed.scale, slot_offsets, wanted, rank, hired, offers, taken_amount, taken_flag, wanted_total, has_job,
                          elasticity, search_share, asks.ASK_ADJUSTMENT_SHARE_PER_YEAR, asks.SEARCH_ROUNDS_PER_YEAR,
                          asks.RESERVATION_CUT_PER_ROUND, wage_out, offered_out, hired_total, scale_out)
    head_rows = heads.tolist()
    wages, offered_list, totals, scales = wage_out.tolist(), offered_out.tolist(), hired_total.tolist(), scale_out.tolist()
    wanted_list = wanted_total.tolist()
    slot_names = [names[each] for each in slot_employer.tolist()]
    slot_hired, bounds = hired.tolist(), slot_offsets.tolist()
    caps, bid_hours, bid_bounds = packed.caps.tolist(), packed.bid_hours.tolist(), packed.bid_offsets.tolist()
    clearings: List[LabourClearing] = []
    for market, (trade, area) in enumerate(packed.markets):
        row = head_rows[market]
        if not row[clearing_kernel.STATUS]:
            continue
        low, high = bounds[market], bounds[market + 1]
        hired_by_employer = {slot_names[slot]: slot_hired[slot] for slot in range(low, high) if slot_hired[slot] > 0.0}
        state.wages.setdefault(area, {})[trade] = wages[market]
        state.asks.setdefault(area, {})[trade] = scales[market]
        state.hired_hours.setdefault(area, {})[trade] = dict(hired_by_employer)
        target = row[clearing_kernel.HEAD_TARGET]
        clearings.append(LabourClearing(
            trade=trade, area=area, wage=wages[market], hours_offered=offered_list[market], hours_wanted=wanted_list[market],
            hours_hired=totals[market], hired_by_employer=hired_by_employer, target_wage=None if target != target else target,
            hours_held=row[clearing_kernel.HEAD_FULL],
            demand=tuple(zip(caps[bid_bounds[market]:bid_bounds[market + 1]], bid_hours[bid_bounds[market]:bid_bounds[market + 1]]))))
    return clearings
