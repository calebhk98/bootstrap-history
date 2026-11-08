"""A store of the market memory as a dict-like view of one column of a market table.

`MarketMemory.prices`, `.trade_age`, `.wages` and the rest are `MarketStore`s: they answer `get`, `[]`, `in`, `pop`, `items`,
`sorted(store)` and so on by market name (`good|area`) exactly as the dicts did, and list their markets in the order the
markets entered the store (the table's `order_*` column). The figures live in the table, so a compiled phase reads or writes the
whole column; a phase that adds or removes members must keep `MarketTables.next_order` / `member_count` (the kernels do).

A float store holds NaN for "none", so a NaN cannot be stored (`ValueError`). Values read back are plain Python numbers."""
from collections.abc import MutableMapping
from itertools import repeat
from typing import Iterator, List, Mapping, Optional, Sequence, Tuple

import numpy

from .market_table_specs import HELD_QUOTE_KIND, QUOTE_KINDS, WAGES
from .market_tables import MarketTables

_MISSING = object()


class MarketStore(MutableMapping):
    """The shared behaviour: lookup by name, order, iteration. A subclass says how a row's figure is read, written and removed."""

    def __init__(self, tables: MarketTables, store: int, column: str, labour: bool = False) -> None:
        self._tables = tables
        self._store = store
        self._column = column
        self._order_column = "order_" + column
        self._labour = labour
        self._table_attr = "labour_table" if labour else "goods_table"
        self._cached: Optional[tuple] = None      # (stamp, rows, keys) of the members in entry order
        self._seen = None                          # the table `_values` and `_held` are columns of (a replaced table is noticed by identity)
        self._values = None
        self._held = None

    def _attach(self):
        """Take the columns of the table as it is now (the table is replaced when it grows, is renumbered or is loaded)."""
        table = getattr(self._tables, self._table_attr)
        self._values = getattr(table, self._column)
        self._held = table.held if hasattr(table, "held") else None
        self._seen = table
        return table

    def _table(self):
        table = getattr(self._tables, self._table_attr)
        if table is not self._seen:
            self._attach()
        return table

    def _row(self, key: str) -> Optional[int]:
        return (self._tables.labour_numbers if self._labour else self._tables.goods_numbers).get(key)

    def _row_for_write(self, key: str) -> int:
        tables = self._tables
        return tables.labour_row_for_write(key) if self._labour else tables.goods_row_for_write(key)

    def _numbering_names(self) -> tuple:
        return (self._tables.labour_markets if self._labour else self._tables.goods_markets).names

    def _present_rows(self, table) -> numpy.ndarray:
        """Row numbers of the members, in row order."""
        raise NotImplementedError

    def _figure_at(self, table, row: int):
        raise NotImplementedError

    def _figures_at(self, table, rows: numpy.ndarray) -> list:
        raise NotImplementedError

    def _has(self, table, row: int) -> bool:
        raise NotImplementedError

    def _enter(self, table, row: int, figure) -> None:
        """Write the figure of a market that is not a member yet and count it in."""
        raise NotImplementedError

    def _leave(self, table, row: int) -> None:
        raise NotImplementedError

    def _put(self, table, row: int, figure) -> None:
        raise NotImplementedError

    def _stamp(self) -> tuple:
        tables = self._tables
        return (tables.generation, int(tables.next_order[self._store]), int(tables.member_count[self._store]))

    def _ordered(self) -> tuple:
        """(stamp, member rows, member keys) in entry order, kept until a market enters or leaves or the numbering changes."""
        stamp = self._stamp()
        cached = self._cached
        if cached is not None and cached[0] == stamp:
            return cached
        table = self._table()
        rows = self._present_rows(table)
        rows = rows[numpy.argsort(getattr(table, self._order_column)[rows], kind="stable")]
        names = self._numbering_names()
        self._cached = (stamp, rows, [names[row] for row in rows.tolist()])
        return self._cached

    def rows(self) -> numpy.ndarray:
        """Row numbers of the members in entry order (the order `items` lists them), for a reader of the table's columns. Kept until a
        market enters or leaves; the caller never changes it."""
        return self._ordered()[1]

    def __len__(self) -> int:
        return int(self._tables.member_count[self._store])

    def __iter__(self) -> Iterator[str]:
        return iter(self._ordered()[2])

    def keys(self) -> List[str]:
        return list(self._ordered()[2])

    def values(self) -> list:
        return self._figures_at(self._table(), self._ordered()[1])

    def items(self) -> List[Tuple[str, object]]:
        ordered = self._ordered()
        return list(zip(ordered[2], self._figures_at(self._table(), ordered[1])))

    def __contains__(self, key) -> bool:
        row = self._row(key)
        return row is not None and self._has(self._table(), row)

    def __getitem__(self, key: str):
        row = self._row(key)
        if row is None or not self._has(self._table(), row):
            raise KeyError(key)
        return self._figure_at(self._table(), row)

    def get(self, key: str, default=None):
        row = self._row(key)
        if row is None:
            return default
        table = self._table()
        return self._figure_at(table, row) if self._has(table, row) else default

    def _present_at(self, rows: numpy.ndarray) -> numpy.ndarray:
        """Per row (all inside the table): whether the market is in the store."""
        raise NotImplementedError

    def get_many(self, keys: Sequence[str], default=None) -> list:
        """`[self.get(key, default) for key in keys]`, read from the column in one pass."""
        if not len(keys):
            return []
        numbers = self._tables.labour_numbers if self._labour else self._tables.goods_numbers
        found = numpy.fromiter(map(numbers.get, keys, repeat(-1)), dtype=numpy.int64, count=len(keys))
        self._table()
        inside = numpy.where(found >= 0, found, 0)
        present = ((found >= 0) & self._present_at(inside)).tolist()
        figures = self._figures_at(self._seen, inside)
        return [figure if there else default for figure, there in zip(figures, present)]

    def __setitem__(self, key: str, figure) -> None:
        self._tables.writes += 1
        row = self._row_for_write(key)
        table = self._table()
        if self._has(table, row):
            self._put(table, row, figure)
        else:
            self._enter(table, row, figure)

    def __delitem__(self, key: str) -> None:
        self._tables.writes += 1
        row = self._row(key)
        table = self._table()
        if row is None or not self._has(table, row):
            raise KeyError(key)
        self._leave(table, row)

    def pop(self, key: str, default=_MISSING):
        self._tables.writes += 1
        row = self._row(key)
        table = self._table()
        if row is None or not self._has(table, row):
            if default is _MISSING:
                raise KeyError(key)
            return default
        figure = self._figure_at(table, row)
        self._leave(table, row)
        return figure

    def clear(self) -> None:
        self._tables.writes += 1
        table = self._table()
        for row in self._present_rows(table).tolist():
            self._leave(table, row)

    def admit_keys(self, keys) -> None:
        """Number the markets among `keys` that are not numbered yet as one sorted batch, so the numbering does not follow the order
        they are written in."""
        tables = self._tables
        (tables.admit_labour_markets if self._labour else tables.admit_goods_markets)(keys)

    def replace_with(self, other) -> None:
        """Make the store hold exactly the markets of `other` (a mapping), in its order."""
        if other is self:
            return
        held = list(other.items())
        self.clear()
        self.admit_keys(key for key, _figure in held)
        for key, figure in held:
            self[key] = figure

    def __repr__(self) -> str:
        return repr(dict(self.items()))


class FloatStore(MarketStore):
    """A store of prices or wages: a float column where NaN means the market is not in the store."""

    def _present_rows(self, table) -> numpy.ndarray:
        return numpy.flatnonzero(~numpy.isnan(getattr(table, self._column)[:table.row_count[0]]))

    def _figure_at(self, table, row: int) -> float:
        return self._values.item(row)

    def _figures_at(self, table, rows: numpy.ndarray) -> list:
        return getattr(table, self._column)[rows].tolist()

    def _has(self, table, row: int) -> bool:
        figure = self._values.item(row)
        return figure == figure

    def _present_at(self, rows: numpy.ndarray) -> numpy.ndarray:
        return ~numpy.isnan(self._values[rows])

    def values_at(self, rows: numpy.ndarray, default: float) -> numpy.ndarray:
        """The figure of each market row (-1: the market is not numbered) as one array, `default` where the market has none."""
        self._table()
        rows = numpy.asarray(rows, dtype=numpy.int64)
        figures = self._values[numpy.where(rows >= 0, rows, 0)]
        return numpy.where((rows >= 0) & ~numpy.isnan(figures), figures, default)

    def values_in_slots(self, book, default: float) -> numpy.ndarray:
        """`values_at` the rows of the slots of a merchants' route book (`merchants_book.RouteBook`)."""
        return self.values_at(book.market_rows(self._tables), default)

    def get(self, key: str, default=None):
        tables = self._tables
        row = (tables.labour_numbers if self._labour else tables.goods_numbers).get(key)
        if row is None:
            return default
        if getattr(tables, self._table_attr) is not self._seen:
            self._attach()
        figure = self._values.item(row)
        return default if figure != figure else figure

    def __contains__(self, key) -> bool:
        tables = self._tables
        row = (tables.labour_numbers if self._labour else tables.goods_numbers).get(key)
        if row is None:
            return False
        if getattr(tables, self._table_attr) is not self._seen:
            self._attach()
        figure = self._values.item(row)
        return figure == figure

    def _put(self, table, row: int, figure) -> None:
        if figure != figure:
            raise ValueError("a NaN is no figure for a market: use pop to remove one")
        getattr(table, self._column)[row] = figure

    def _enter(self, table, row: int, figure) -> None:
        self._put(table, row, figure)
        tables = self._tables
        getattr(table, self._order_column)[row] = tables.next_order[self._store]
        tables.next_order[self._store] += 1
        tables.member_count[self._store] += 1

    def _leave(self, table, row: int) -> None:
        getattr(table, self._column)[row] = numpy.nan
        self._tables.member_count[self._store] -= 1


class CountStore(MarketStore):
    """A store of whole numbers (trade ages, years without bids or offers): a bit of `held` says the market is in it."""

    def __init__(self, tables: MarketTables, store: int, column: str, bit: int) -> None:
        super().__init__(tables, store, column)
        self._bit = bit

    def _present_rows(self, table) -> numpy.ndarray:
        return numpy.flatnonzero(table.held[:table.row_count[0]] & self._bit)

    def get(self, key: str, default=None):
        tables = self._tables
        row = tables.goods_numbers.get(key)
        if row is None:
            return default
        if tables.goods_table is not self._seen:
            self._attach()
        return self._values.item(row) if self._held.item(row) & self._bit else default

    def __contains__(self, key) -> bool:
        tables = self._tables
        row = tables.goods_numbers.get(key)
        if row is None:
            return False
        if tables.goods_table is not self._seen:
            self._attach()
        return self._held.item(row) & self._bit != 0

    def _figure_at(self, table, row: int) -> int:
        return self._values.item(row)

    def _figures_at(self, table, rows: numpy.ndarray) -> list:
        return getattr(table, self._column)[rows].tolist()

    def _has(self, table, row: int) -> bool:
        return self._held.item(row) & self._bit != 0

    def _present_at(self, rows: numpy.ndarray) -> numpy.ndarray:
        return (self._held[rows] & self._bit) != 0

    def _put(self, table, row: int, figure) -> None:
        getattr(table, self._column)[row] = figure

    def _enter(self, table, row: int, figure) -> None:
        self._put(table, row, figure)
        table.held[row] |= self._bit
        tables = self._tables
        getattr(table, self._order_column)[row] = tables.next_order[self._store]
        tables.next_order[self._store] += 1
        tables.member_count[self._store] += 1

    def _leave(self, table, row: int) -> None:
        table.held[row] &= ~self._bit
        self._tables.member_count[self._store] -= 1


class KindStore(CountStore):
    """The quote kind of a market, as the text the memory has always held; the table keeps the kind's number."""

    def __init__(self, tables: MarketTables) -> None:
        super().__init__(tables, QUOTE_KINDS, "quote_kind", HELD_QUOTE_KIND)

    def get(self, key: str, default=None):
        figure = super().get(key, _MISSING)
        return default if figure is _MISSING else self._tables.kinds.name(figure)

    def _figure_at(self, table, row: int) -> str:
        return self._tables.kinds.name(table.quote_kind.item(row))

    def _figures_at(self, table, rows: numpy.ndarray) -> list:
        names = self._tables.kinds.names
        return [names[number] for number in table.quote_kind[rows].tolist()]

    def _put(self, table, row: int, figure) -> None:
        table.quote_kind[row] = self._tables.kind_number(figure)


def labour_wage_store(tables: MarketTables) -> FloatStore:
    """The remembered wages: a float store over the labour table."""
    return FloatStore(tables, WAGES, "wage", labour=True)


def figures_for(figures: Mapping[str, float], keys: Sequence[str], default) -> list:
    """`figures.get(key, default)` for each key: one pass over a market store's column, a plain lookup for any other mapping."""
    if isinstance(figures, MarketStore):
        return figures.get_many(keys, default)
    return list(map(figures.get, keys, repeat(default)))
