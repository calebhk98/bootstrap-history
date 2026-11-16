"""Run the close kernel over the year's producers: pack, run, price the shares the kernel asked for, run those rows again.

`close_producers(setup, record, view, ledger, arrays, pack, price_shares_of)` -> `CloseAnswer`, one row per producer in the
year arrays' order. Nothing is written to the record here; `year_close_apply.py` does that."""
from dataclasses import dataclass, fields

import numpy as np

from . import close_kernel, firm_finance
from .close_pack import ClosePack, constants_array
from .year_arrays import YearArrays


@dataclass
class CloseAnswer:
    new_capacity: np.ndarray
    new_losses: np.ndarray
    new_target: np.ndarray
    new_expected: np.ndarray
    written: np.ndarray
    exited: np.ndarray
    dividend: np.ndarray
    request_kind: np.ndarray
    request_amount: np.ndarray
    request_rate: np.ndarray
    request_term: np.ndarray
    request_collateral: np.ndarray
    expansion_runs: np.ndarray
    replacement_runs: np.ndarray
    new_earnings: np.ndarray
    new_revenues: np.ndarray
    new_count: np.ndarray
    state: np.ndarray
    write_off: np.ndarray
    new_idle: np.ndarray
    new_expected_sales: np.ndarray
    new_last_runs: np.ndarray
    new_staffed: np.ndarray
    demand_runs: np.ndarray
    needs_share: np.ndarray
    added: np.ndarray

    @classmethod
    def empty(cls, columns) -> "CloseAnswer":
        count, width = columns.expected_prices.shape
        history = columns.earnings_history.shape[1]
        history = max(history, firm_finance.HISTORY_YEARS, 1)
        shapes = {"new_expected": (count, width), "written": (count, width), "new_earnings": (count, history),
                  "new_revenues": (count, history), "added": (count, width)}
        kinds = {"written": bool, "exited": bool, "needs_share": bool, "new_losses": np.int64, "request_kind": np.int64,
                 "new_count": np.int64, "state": np.int64, "new_idle": np.int64}
        return cls(**{each.name: np.zeros(shapes.get(each.name, (count,)), dtype=kinds.get(each.name, np.float64))
                      for each in fields(cls)})


def _kernel_arguments(rows, arrays: YearArrays, pack: ClosePack, market_capacity, share, answer: CloseAnswer):
    matrices, columns, memory = arrays.matrices, arrays.producers, arrays.memory
    return (rows, constants_array(),
            matrices.slot_goods, matrices.slot_trades, matrices.slot_is_input, matrices.slot_is_output, matrices.slot_is_plant,
            matrices.inputs, matrices.outputs, arrays.revenue_outputs, matrices.plant_goods, matrices.labour_hours, matrices.plant_labour_hours,
            matrices.plant_life_years, matrices.idle_wear_share,
            columns.recipe_row, columns.tile_row, columns.capacity_runs, columns.yield_factor, columns.years_of_loss,
            columns.cash_target, columns.expected_sales, columns.last_runs, columns.land_rent_per_run,
            columns.earnings_history, columns.revenue_history, columns.history_count, columns.expected_prices, pack.ask_multiple,
            arrays.area_index.of_good_tile, memory.price, memory.offered, memory.cleared, memory.bare_quote, memory.wage,
            pack.clearing, pack.unmet, market_capacity, pack.spoilage, pack.ground,
            pack.rate_of, pack.cash_in_currency, pack.cash_in_money, pack.revenue, pack.running_costs, pack.stock, pack.sold,
            pack.made, pack.hours_hired, pack.interest, pack.commitments, pack.arrears, pack.debt, pack.held_start,
            pack.held_good, pack.held_quantity, share,
            answer.new_capacity, answer.new_losses, answer.new_target, answer.new_expected, answer.written, answer.exited,
            answer.dividend, answer.request_kind, answer.request_amount, answer.request_rate, answer.request_term,
            answer.request_collateral, answer.expansion_runs, answer.replacement_runs, answer.new_earnings,
            answer.new_revenues, answer.new_count, answer.state, answer.write_off, answer.new_idle, answer.new_expected_sales,
            answer.new_last_runs, answer.new_staffed, answer.demand_runs, answer.needs_share, answer.added, arrays.tools)


def close_producers(arrays: YearArrays, pack: ClosePack, price_shares_of=None) -> CloseAnswer:
    """The close of every producer not idle. `price_shares_of(rows, added)` -> the share of the price that stays, rows by slots,
    for the rows whose growth the kernel flagged and the units each adds per slot (None: no share is priced, every share is one)."""
    columns = arrays.producers
    count = len(columns.ids)
    answer = CloseAnswer.empty(columns)
    share = np.ones(columns.expected_prices.shape)
    capacity = close_kernel.market_capacity_of(
        arrays.matrices.slot_goods, arrays.matrices.outputs, arrays.area_index.of_good_tile, columns.recipe_row,
        columns.tile_row, columns.capacity_runs, columns.yield_factor, columns.idle_years, count,
        len(arrays.matrices.goods.ids), len(arrays.area_index.areas.ids))
    rows = np.nonzero(columns.idle_years <= 0)[0].astype(np.int64)
    close_kernel.close_rows(*_kernel_arguments(rows, arrays, pack, capacity, share, answer))
    flagged = np.nonzero(answer.needs_share)[0].astype(np.int64)
    if len(flagged) and price_shares_of is not None:
        share[flagged] = price_shares_of(flagged, answer.added[flagged])
        close_kernel.close_rows(*_kernel_arguments(flagged, arrays, pack, capacity, share, answer))
    return answer
