"""The ledger's figures as the dicts they used to be: mappings over the tables, for readers not yet on the tables.

Every view answers `[]`, `get`, `in`, `len`, `items`, `keys`, `values`, `setdefault`, assignment and removal by name exactly as
the dict did, lists its keys in the order they were first added (the close sums in that order), and compares equal to a dict
with the same items. The figures live in `LedgerTables`; a view reads and writes them with single-cell operations, so a caller
with many figures should use the ledger's array entry points instead. Reading never numbers a name: an agent, good or market
the numberings have not met is simply absent. A view first adds the pending notes its table waits on (`year_ledger_batch.py`).

    AgentFigureView    agent name -> float                       money_out, wages_in, sales_in, plant_spend, plant_worn, hours_sold,
                                                                 spare_hours
    MarketFigureView   (good, area) -> float                     delivered_by_market, unmet_demand
    PairView, NestedView, InnerView (year_ledger_pair_views.py)  the (agent, good) and (agent, trade) figures"""
import functools
from collections.abc import MutableMapping
from typing import Iterator, List, Optional, Tuple

import numpy

from sim.economy.year_ledger_kernels import add_to_figure, remove_from_figure, set_figure
from sim.economy.year_ledger_store import LedgerTables
from sim.economy.year_ledger_tables import DELIVERED, FIGURE_KIND, MEMBERS, NEXT_ENTRY, ROUNDS, UNMET


def flushed(method):
    """The method runs once the pending notes of the kind its table waits on are in the table (it reads or writes it)."""
    @functools.wraps(method)
    def flushing(self, *args, **kwargs):
        kind = self._kind
        if kind is not None:
            tables = self._tables
            if tables.pending.counts[kind]:
                tables.pending.flush(tables, kind)
        return method(self, *args, **kwargs)
    return flushing


class Show(MutableMapping):
    """What every view shares: equality with dicts comes from `Mapping`, and the text shows the items."""

    def __repr__(self) -> str:
        return repr(dict(self.items()))


def in_entry_order(orders: numpy.ndarray, count: int) -> numpy.ndarray:
    """Row numbers of the members (order above zero) among the first `count` rows, in the order they entered."""
    members = numpy.flatnonzero(orders[:count])
    return members[numpy.argsort(orders[members], kind="stable")]


class _Dense(Show):
    """A figure with one cell per row of a dense table (an agent, or a goods market), members in entry order."""

    def __init__(self, tables: LedgerTables, figure: int, column: str) -> None:
        self._tables = tables
        self._figure = figure
        self._column = column
        self._order = "order_" + column
        self._kind = self.KINDS[figure]
        self._cache = None

    # How a subclass turns a key into a row and back, and which table and counters it reads.
    def _table(self):
        raise NotImplementedError

    def _counters(self):
        raise NotImplementedError

    def _row_of(self, key) -> Optional[int]:
        raise NotImplementedError

    def _row_for_write(self, key) -> int:
        raise NotImplementedError

    def _key_of(self, row: int):
        raise NotImplementedError

    def _members(self) -> Tuple[numpy.ndarray, list]:
        table, counters = self._table(), self._counters()
        stamp = (int(counters[2 * self._figure + NEXT_ENTRY]), int(counters[2 * self._figure + MEMBERS]))
        if self._cache is None or self._cache[0] is not table or self._cache[1] != stamp:
            rows = in_entry_order(getattr(table, self._order), int(table.row_count[0]))
            self._cache = (table, stamp, rows, [self._key_of(row) for row in rows.tolist()])
        return self._cache[2], self._cache[3]

    def _read(self, key):
        """(whether the key is a member, its figure): one cell, no numbering."""
        row = self._row_of(key)
        if row is None:
            return False, 0.0
        table = self._table()
        try:
            if getattr(table, self._order).item(row):
                return True, getattr(table, self._column).item(row)
        except IndexError:        # a number the table has no room for yet
            pass
        return False, 0.0

    @flushed
    def __len__(self) -> int:
        return int(self._counters()[2 * self._figure + MEMBERS])

    @flushed
    def __iter__(self) -> Iterator:
        return iter(self._members()[1])

    @flushed
    def keys(self) -> List:
        return list(self._members()[1])

    @flushed
    def values(self) -> List[float]:
        rows, _keys = self._members()
        return getattr(self._table(), self._column)[rows].tolist()

    @flushed
    def items(self) -> List[tuple]:
        rows, keys = self._members()
        return list(zip(keys, getattr(self._table(), self._column)[rows].tolist()))

    @flushed
    def __contains__(self, key) -> bool:
        return self._read(key)[0]

    @flushed
    def __getitem__(self, key) -> float:
        found, figure = self._read(key)
        if not found:
            raise KeyError(key)
        return figure

    @flushed
    def get(self, key, default=None):
        found, figure = self._read(key)
        return figure if found else default

    @flushed
    def get_many(self, keys, default=None) -> list:
        """`[self.get(key, default) for key in keys]`."""
        found_and_figures = [self._read(key) for key in keys]
        return [figure if found else default for found, figure in found_and_figures]

    @flushed
    def __setitem__(self, key, value: float) -> None:
        row = self._row_for_write(key)
        table = self._table()
        set_figure(getattr(table, self._column), getattr(table, self._order), self._counters(), self._figure, row, float(value))

    @flushed
    def add(self, key, amount: float) -> None:
        """`self[key] = self.get(key, 0.0) + amount`."""
        row = self._row_for_write(key)
        table = self._table()
        add_to_figure(getattr(table, self._column), getattr(table, self._order), self._counters(), self._figure, row, float(amount))

    @flushed
    def __delitem__(self, key) -> None:
        if not self._read(key)[0]:
            raise KeyError(key)
        remove_from_figure(getattr(self._table(), self._order), self._counters(), self._figure, self._row_of(key))


class AgentFigureView(_Dense):
    """Agent name -> float, one cell per agent number of the book."""

    KINDS = FIGURE_KIND

    def _table(self):
        return self._tables.figures

    def _counters(self):
        return self._tables.counters

    def _row_of(self, key) -> Optional[int]:
        return self._tables.book.agent_ids.numbers.get(key)

    def _row_for_write(self, key) -> int:
        return self._tables.agent_number(key)

    def _key_of(self, row: int):
        return self._tables.book.agent_ids.name_list[row]


class MarketFigureView(_Dense):
    """(good, area) -> float, one cell per goods market of the market memory."""

    KINDS = {DELIVERED: ROUNDS, UNMET: None}

    def _table(self):
        return self._tables.market_figures

    def _counters(self):
        return self._tables.market_counters

    def _row_of(self, key) -> Optional[int]:
        return self._tables.markets.goods_numbers.get(key[0] + "|" + key[1])

    def _row_for_write(self, key) -> int:
        return self._tables.market_number(key[0], key[1])

    def _key_of(self, row: int):
        good, _separator, area = self._tables.markets.goods_markets.name_list[row].partition("|")
        return (good, area)
