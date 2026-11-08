"""Every market of the year cleared in a few kernel calls from one pack: the heads (`clearing_kernel.market_heads`), the employers and
their jobs (`clearing_tail_kernel.fill_slots`), the hiring rounds of all markets (`hiring_kernel.hire_markets`) and the finish
(`finish_markets`); then the state's tables written (clearing_write.py). The plain functions of `clearing.py` (`_prepare`,
`_finish`) stay for a caller whose fetched-hands search or hours schedule the kernels do not stand in for."""
import numpy as np

from . import asks, clearing_arrays, clearing_tail_kernel as kernel, clearing_write, hiring_kernel
from .applications import APPLICATIONS_PER_ROUND, SEPARATION_SHARE_PER_ROUND
from .clearing_pack import previous_hours
from .clearing_results import Clearings
from .market_state import MarketState


def clear_packed(state: MarketState, packed, elasticity: float, search_share: float) -> Clearings:
    """The clearings of the packed markets with a stated outside option, in the packed order; the state's tables move as the plain
    `_finish` leaves the dicts."""
    heads = clearing_arrays.run_heads(packed)
    count = packed.markets
    market_of_bid = np.repeat(np.arange(count), np.diff(packed.bid_offsets))
    held = state.hired_table
    held_rows = int(held.row_count[0])
    previous = previous_hours(state.market_table.hired_count, held.employer[:held_rows], held.hours[:held_rows], len(state.ids.employers),
                              packed.market_row[market_of_bid], packed.bid_employer)
    by_name = np.lexsort((packed.bid_hours, packed.caps, state.ids.employers.rank[packed.bid_employer], market_of_bid))   # market, employer by name, maximum wage, hours
    s_employer, s_caps, s_hours, s_previous = packed.bid_employer[by_name], packed.caps[by_name], packed.bid_hours[by_name], previous[by_name]
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
    cells = packed.arguments[0]
    kernel.finish_markets(heads, packed.market_area, packed.market_trade, cells, packed.arguments[1], packed.arguments[2], packed.arguments[3],
                          packed.arguments[6], slot_offsets, wanted, rank, hired, offers, taken_amount, taken_flag, wanted_total, has_job,
                          elasticity, search_share, asks.ASK_ADJUSTMENT_SHARE_PER_YEAR, asks.SEARCH_ROUNDS_PER_YEAR,
                          asks.RESERVATION_CUT_PER_ROUND, wage_out, offered_out, hired_total, scale_out)
    cleared = heads[:, 0] != 0.0
    clearing_write.write_clearing(state, packed.market_row, cleared, wage_out, scale_out, slot_offsets, slot_employer, hired)
    return Clearings((state.ids.areas.names, state.ids.trades.names), state.ids.employers.table.names, packed.market_area,
                     packed.market_trade, heads, wage_out, offered_out, wanted_total, hired_total, packed.bid_offsets, packed.caps,
                     packed.bid_hours, slot_offsets, slot_employer, hired)
