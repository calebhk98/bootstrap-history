"""A merchant's figures by market (what it expects a market to pay, what it expects it to trade) as one column of numbers.

`MarketFigures` is a column of floats indexed by the market memory's goods-market numbering (`MarketTables.goods_markets`, the
rows of `goods_table`): entry `r` is the figure for the market the numbering calls `r`, NaN where the merchant has none. It is
also a dict-like view keyed by `(good, area id)`, for readers that ask one market at a time (the UI, tests, mods): `get`, `[]`,
`in`, `items`, `update` and `==` against a dict behave as the dict of the same keys did; iteration lists the markets in
numbering order. A kernel or a whole-column reader takes `values`, `take(rows)` or `put(rows, figures)`.

A merchant in a record shares the record's numbering (`bind`); one made alone has a numbering of its own, made when it is first
read. A save stores the figures by market name (`sorted_named`) and a load hands them back by name (`hold_named`), so a loaded
merchant is indexed once, by the record's numbering. Writing a figure for a
market the numbering has not yet numbered numbers it (`MarketTables.admit_goods_markets`), as a store of the market memory does.
When the areas are redrawn the numbering is replaced: the column follows it by `follow` (`market_areas_follow`), and a read before
that raises, since the rows would mean other markets."""
from collections.abc import MutableMapping
from typing import Iterable, Iterator, Mapping, Optional, Tuple

import numpy

from .market_table_specs import KEY_SEPARATOR
from .market_tables import MarketTables

Key = Tuple[str, str]       # (good, area id)

FIRST_CAPACITY = 64


def market_name(key: Key) -> str:
    """The name the market memory gives the market of a (good, area id)."""
    return key[0] + KEY_SEPARATOR + key[1]


class MarketFigures(MutableMapping):
    """One figure per goods market, in a column; see the module docstring. A subclass keyed otherwise than by (good, area id) replaces
    `name_of_key` and `key_of_name` (`goods_market_column.MarketColumn`: keyed by the market's name)."""

    @staticmethod
    def name_of_key(key) -> str:
        """The market's name (`good|area`) of a key of this mapping."""
        return market_name(key)

    @staticmethod
    def key_of_name(name: str):
        """The key of this mapping of a market's name."""
        good, _separator, area = name.partition(KEY_SEPARATOR)
        return (good, area)

    def __init__(self, tables: Optional[MarketTables] = None, items: Iterable = ()) -> None:
        self._tables = tables
        self._pending: Optional[Tuple[list, list]] = None      # (market names, figures) held until a numbering is chosen
        pairs = [(key, figure) for key, figure in (items.items() if isinstance(items, Mapping) else items) if figure is not None]
        if tables is None:
            self._numbering = self._column = None
            self._pending = ([self.name_of_key(key) for key, _figure in pairs], [figure for _key, figure in pairs])
        else:
            self._start(tables)
            self.update(pairs)

    def _start(self, tables: MarketTables) -> None:
        self._tables = tables
        self._numbering = tables.goods_markets
        self._column = numpy.full(max(FIRST_CAPACITY, len(self._numbering)), numpy.nan)

    def _chosen(self) -> MarketTables:
        """The numbering, a numbering of its own made now if none was chosen, with the figures held for it."""
        if self._tables is None:
            self.bind(MarketTables())
        return self._tables

    @property
    def tables(self) -> MarketTables:
        """The numbering this column is indexed by."""
        return self._chosen()

    def _current(self) -> numpy.ndarray:
        """The column, as long as the numbering (grown with NaN if markets were numbered since)."""
        if self._tables is None:
            self._chosen()
        if self._tables.goods_markets is not self._numbering:
            raise RuntimeError("the goods markets were renumbered and this merchant's figures were not carried over (follow)")
        size = len(self._numbering)
        if len(self._column) < size:
            grown = numpy.full(max(size, 2 * len(self._column)), numpy.nan)
            grown[:len(self._column)] = self._column
            self._column = grown
        return self._column

    @property
    def values(self) -> numpy.ndarray:
        """The column itself: entry `r` is the figure for goods market `r` (NaN: none). Write through `put`."""
        return self._current()

    def take(self, rows: numpy.ndarray) -> numpy.ndarray:
        """The figures at these market rows (a row of -1 has none): a new array, NaN where there is none."""
        column = self._current()
        found = numpy.full(len(rows), numpy.nan)
        known = (rows >= 0) & (rows < len(self._numbering))
        found[known] = column[rows[known]]
        return found

    def put(self, rows: numpy.ndarray, figures: numpy.ndarray) -> None:
        """Set the figures at market rows that are numbered (a figure that is NaN is a refusal: use `pop` to remove one)."""
        if numpy.isnan(figures).any():
            raise ValueError("a NaN cannot be stored as a merchant's figure")
        self._current()[rows] = figures

    def rows_of(self, names: Iterable[str]) -> numpy.ndarray:
        """The rows of these market names (`good|area`), numbering the ones not yet numbered."""
        names = list(names)
        tables = self._chosen()
        numbers = tables.goods_numbers
        if any(name not in numbers for name in names):
            tables.admit_goods_markets(names)
            numbers = tables.goods_numbers
        return numpy.array([numbers[name] for name in names], dtype=numpy.int64)

    def follow(self, old_to_new: numpy.ndarray, new_rows: numpy.ndarray, old_rows: numpy.ndarray) -> None:
        """Carry the column over to the numbering that replaced the old one (the maps `market_memory_follow.follow_goods_markets`
        returns): a market that survives keeps its figure at its new row, then new market `new_rows[p]` takes the figure of old
        market `old_rows[p]` (-1: the old one was never numbered)."""
        old = numpy.full(len(old_to_new), numpy.nan)
        shared = min(len(old), len(self._column))
        old[:shared] = self._column[:shared]
        column = numpy.full(max(FIRST_CAPACITY, len(self._tables.goods_markets)), numpy.nan)
        survives = old_to_new >= 0
        column[old_to_new[survives]] = old[survives]
        copies = old_rows >= 0
        column[new_rows[copies]] = old[old_rows[copies]]
        self._column = column
        self._numbering = self._tables.goods_markets

    def bind(self, tables: MarketTables) -> None:
        """Index this column by another numbering (a record's), keeping the figures of the markets it holds."""
        if tables is self._tables:
            return
        if self._tables is None:
            names, figures = self._pending
            self._pending = None
        else:
            names, figures = self.named()
        self._start(tables)
        self.hold_named(names, figures)

    def hold_named(self, names: list, figures: list) -> None:
        """Set the figures of these markets (by `good|area` name); a column with no numbering yet holds them until it has one."""
        if self._tables is None:
            self._pending[0].extend(names)
            self._pending[1].extend(figures)
        elif names:
            self.put(self.rows_of(names), numpy.array(figures, dtype=numpy.float64))

    def named(self) -> Tuple[list, list]:
        """(market names, figures) of the markets it holds, in numbering order."""
        rows = self._present_rows()
        names = self._numbering.name_list
        return [names[row] for row in rows.tolist()], self._current()[rows].tolist()

    def sorted_named(self) -> dict:
        """{market name: figure} in the order of the (good, area id) keys, as a save writes it."""
        names, figures = self.named()
        return dict(sorted(zip(names, figures), key=lambda pair: pair[0].replace(KEY_SEPARATOR, "\x00")))

    def replace_all(self, items: Iterable) -> None:
        """Hold exactly these figures."""
        held = [(key, figure) for key, figure in (items.items() if isinstance(items, Mapping) else items) if figure is not None]
        if self._tables is None:
            self._pending = ([self.name_of_key(key) for key, _figure in held], [figure for _key, figure in held])
            return
        self._current()[:] = numpy.nan
        self.update(held)

    def _row(self, key: Key) -> Optional[int]:
        return self._chosen().goods_numbers.get(self.name_of_key(key))

    def get(self, key, default=None):
        column = self._current()
        row = self._row(key)
        if row is None:
            return default
        figure = column[row]
        return default if figure != figure else float(figure)

    def __getitem__(self, key: Key) -> float:
        figure = self.get(key)
        if figure is None:
            raise KeyError(key)
        return figure

    def __contains__(self, key) -> bool:
        return self.get(key) is not None

    def __setitem__(self, key: Key, figure: Optional[float]) -> None:
        self.update(((key, figure),))

    def __delitem__(self, key: Key) -> None:
        if key not in self:
            raise KeyError(key)
        self._current()[self._row(key)] = numpy.nan

    def update(self, items: Iterable = ()) -> None:   # type: ignore[override]
        """Set many figures at once; a None removes the market's figure."""
        pairs = list(items.items() if isinstance(items, Mapping) else items)
        names, figures, removed = [], [], []
        for key, figure in pairs:
            if figure is None:
                removed.append(key)
            else:
                names.append(self.name_of_key(key))
                figures.append(figure)
        self._chosen()
        for key in removed:
            self.pop(key, None)
        if names:
            self.hold_named(names, figures)

    def _present_rows(self) -> numpy.ndarray:
        column = self._current()[:len(self._numbering)]
        return numpy.flatnonzero(~numpy.isnan(column))

    def __iter__(self) -> Iterator[Key]:
        rows = self._present_rows().tolist()
        names = self._numbering.name_list
        for row in rows:
            yield self.key_of_name(names[row])

    def items(self) -> list:
        """[(key, figure)] in iteration order, read from the column in one pass (the keys with a figure, as `[(key, self[key]) for key in self]`)."""
        names, figures = self.named()
        return [(self.key_of_name(name), figure) for name, figure in zip(names, figures)]

    def __len__(self) -> int:
        return int(self._present_rows().size)

    def __repr__(self) -> str:
        return "MarketFigures(%r)" % dict(self.items())
