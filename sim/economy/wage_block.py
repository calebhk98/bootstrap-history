"""The one wage rule (`trade_wages`) for a block of trades and labour areas, read from the market memory's labour table in one kernel call.

`wage_rule_block(setup, memory, trades, areas)` is `trade_wages.wage_in_area` for every trade and area given, as a (trade by area) grid
with the same values bit for bit. `WageRuleTable` keeps such a block for every trade of the setup and a set of areas until the memory
is written to (`price_grid.memory_stamp`), and answers one cell from it."""
import weakref
from typing import Callable, Dict, Optional, Sequence

import numpy as np

from .price_grid import memory_stamp
from .market_memory import market_key
from .trade_wages import known_trade, trade_premium
from .wage_block_kernels import labour_market_matrix, market_rows_of, wage_rule_grid

_matrix_of: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def _market_matrix(tables) -> np.ndarray:
    """(trade number, area number) to labour market row, worked out once per numbering of the labour markets."""
    kept = _matrix_of.get(tables)
    stamp = (tables.generation, len(tables.trades), len(tables.areas))
    if kept is None or kept[0] != stamp:
        table = tables.labour_table
        kept = _matrix_of[tables] = (stamp, labour_market_matrix(table.first, table.area, int(table.row_count[0]), len(tables.trades),
                                                                 len(tables.areas)))
    return kept[1]


def wage_rule_block(setup, memory, trades: Sequence[str], areas: Sequence[str]) -> np.ndarray:
    """`trade_wages.wage_in_area(setup, memory, trade, area)` for each trade and area, as a (trade by area) grid. A trade the setup
    does not know is a KeyError, as in the per-cell rule."""
    from .trade_wages import priced_trade_wage
    tables = memory.tables
    matrix = _market_matrix(tables)
    trade_numbers = np.array([tables.trades.numbers.get(trade, -1) for trade in trades], dtype=np.int64)
    area_numbers = np.array([tables.areas.numbers.get(area, -1) for area in areas], dtype=np.int64)
    rows = market_rows_of(matrix, trade_numbers, area_numbers)
    unskilled_number = tables.trades.numbers.get(setup.unskilled_trade, -1)
    unskilled_rows = market_rows_of(matrix, np.array([unskilled_number], dtype=np.int64), area_numbers)[0]
    for trade in trades:
        known_trade(setup, trade)
    level = memory.opening_wage_level(setup.currency_id)
    opening_wages = np.array([setup.opening_wages.get(trade, np.nan) for trade in trades], dtype=np.float64)
    opening_of_unskilled = setup.opening_wages.get(setup.unskilled_trade)
    grid = wage_rule_grid(
        rows, tables.labour_table.wage, unskilled_rows, np.array([memory.holds_wage_for(trade) for trade in trades], dtype=np.bool_),
        opening_wages, np.array([trade_premium(setup, trade) for trade in trades], dtype=np.float64), level,
        np.nan if opening_of_unskilled is None else opening_of_unskilled * level)
    if len(grid) and np.isnan(grid).any():       # nothing to price some cell from: the per-cell rule refuses with its own message
        for row, trade in enumerate(trades):
            for column, area in enumerate(areas):
                if grid[row, column] != grid[row, column]:
                    grid[row, column] = priced_trade_wage(setup, trade, memory.wages.get(market_key(trade, area)),
                                                          memory.wages.get(market_key(setup.unskilled_trade, area)), level,
                                                          memory.holds_wage_for(trade))
    return grid


class WageRuleTable:
    """The wage rule for every trade of the setup in each of some labour areas, kept until the memory is written to."""

    def __init__(self, setup, memory, areas: Callable[[], Sequence[str]]) -> None:
        self._setup = setup
        self._memory = memory
        self._areas = areas
        self._stamp: Optional[tuple] = None
        self._grid: Optional[np.ndarray] = None
        self._trade_row: Dict[str, int] = {}
        self._area_column: Dict[str, int] = {}
        self.refreshes = 0

    def _current(self) -> np.ndarray:
        stamp = memory_stamp(self._memory)
        if stamp != self._stamp:
            trades = sorted(self._setup.trades)
            areas = tuple(self._areas())
            self._grid = wage_rule_block(self._setup, self._memory, trades, areas)
            self._trade_row = {trade: row for row, trade in enumerate(trades)}
            self._area_column = {area: column for column, area in enumerate(areas)}
            self._stamp = stamp
            self.refreshes += 1
        return self._grid

    def wage(self, trade: str, area: str) -> Optional[float]:
        """The rule's wage, None for a trade or an area the table does not hold (the per-cell rule then answers)."""
        grid = self._current()
        row = self._trade_row.get(trade)
        column = self._area_column.get(area)
        return None if row is None or column is None else grid.item(row, column)
