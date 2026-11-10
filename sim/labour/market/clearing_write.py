"""The year's clearing written into the state's tables: wages, asks and the hours each employer was hired for, per market."""
import numpy as np

from sim.jit import njit

from .market_state import MarketState


@njit
def count_hired(slot_offsets, hired, counts):
    """Per market: the employers with hours hired (the slots with more than zero hired)."""
    for market in range(counts.shape[0]):
        counts[market] = 0
        for slot in range(slot_offsets[market], slot_offsets[market + 1]):
            if hired[slot] > 0.0:
                counts[market] += 1


@njit
def fill_hired(market_row, cleared, slot_offsets, slot_employer, slot_hired, new_first, old_first, old_count, old_employer,
               old_hours, rewritten, out_employer, out_hours):
    """The HIRED rows after the year: the markets that were not cleared keep their rows, the cleared ones hold their slots with hours
    hired, in slot order (employers by name)."""
    for row in range(old_count.shape[0]):
        if not rewritten[row]:
            for held in range(old_count[row]):
                out_employer[new_first[row] + held] = old_employer[old_first[row] + held]
                out_hours[new_first[row] + held] = old_hours[old_first[row] + held]
    for market in range(market_row.shape[0]):
        if not cleared[market]:
            continue
        target = new_first[market_row[market]]
        for slot in range(slot_offsets[market], slot_offsets[market + 1]):
            if slot_hired[slot] > 0.0:
                out_employer[target] = slot_employer[slot]
                out_hours[target] = slot_hired[slot]
                target += 1


def write_clearing(state: MarketState, market_row: np.ndarray, cleared: np.ndarray, wage: np.ndarray, scale: np.ndarray,
                   slot_offsets: np.ndarray, slot_employer: np.ndarray, slot_hired: np.ndarray) -> None:
    """Write the cleared markets (those with `cleared` set; `market_row` is their grid rows) into the state: the wage the hours were
    paid, the ask moved for next year and the employers' hours, in the order the markets run."""
    rows = market_row[cleared]
    markets = state.market_table
    trades = len(state.ids.trades)
    for column, order, values in (("wage", "wage_order", wage[cleared]), ("ask", "ask_order", scale[cleared])):
        stored = getattr(markets, column)
        state.stamp_pairs(getattr(markets, order), rows[np.isnan(stored[rows])])
        state.stamp_areas("wages" if column == "wage" else "asks", rows // trades)
        stored[rows] = values
    counts = np.zeros(len(market_row), np.int64)
    count_hired(slot_offsets, slot_hired, counts)
    new_count = markets.hired_count.copy()
    new_count[rows] = counts[cleared]
    new_first = np.cumsum(new_count) - new_count
    rewritten = np.zeros(len(new_count), np.bool_)
    rewritten[rows] = True
    old = state.hired_table
    total = int(new_count.sum())
    out_employer, out_hours = np.zeros(total, np.int64), np.zeros(total)
    fill_hired(market_row, cleared, slot_offsets, slot_employer, slot_hired, new_first, markets.hired_first, markets.hired_count,
               old.employer, old.hours, rewritten, out_employer, out_hours)
    state.replace_hired(new_count, out_employer, out_hours)
    state.stamp_pairs(markets.hired_order, rows[~markets.hired_present[rows]])
    markets.hired_present[rows] = True
    state.stamp_areas("hired", rows // trades)
