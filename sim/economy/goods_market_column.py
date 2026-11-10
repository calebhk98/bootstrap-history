"""A figure per goods market that the goods record keeps, as a column of the market memory's goods-market numbering.

`MarketColumn` is `merchant_figures.MarketFigures` keyed by the market's name (`market_key(good, area)`: `good|area`), which is how
`record.goods.volumes`, `unsold`, `unmet` and `margin_years` were keyed as dictionaries. Whole-column readers and writers take `values`,
`take(rows)`, `put(rows, figures)` and `replace_rows(rows, figures)`; a reader that asks about one market uses the mapping's `get`, `[]`,
`in`, `items`. Iteration lists the markets in (good, area) order. A column made with `integer=True` answers whole numbers (the streaks of
`margin_years`); it is stored as floats, which hold them exactly.

The column follows a redraw of the market areas by `follow` (`market_areas_follow`), and is bound to a record's numbering by `bind`
(`record.EconomyRecord`); the save writes it as `{market name: figure}` in name order (`saved`) and a load hands it back (`hold_named`)."""
from typing import Iterable, Optional

import numpy

from .merchant_figures import MarketFigures
from .market_tables import MarketTables
from .saved_name_order import in_saved_order


class MarketColumn(MarketFigures):
    """One figure per goods market keyed by the market's name; see the module docstring."""

    def __init__(self, tables: Optional[MarketTables] = None, items: Iterable = (), integer: bool = False) -> None:
        self.integer = integer
        super().__init__(tables, items)

    @staticmethod
    def name_of_key(key: str) -> str:
        return key

    @staticmethod
    def key_of_name(name: str) -> str:
        return name

    def __iter__(self):
        """The markets with a figure in the order of (good, area): the order a dictionary written market by market in sorted order had."""
        return iter([name for name, _figure in self.items()])

    def items(self) -> list:
        """[(market name, figure)] in (good, area) order, read from the column in one pass."""
        self._chosen()
        names = self._numbering.name_list
        rows = in_saved_order(self._present_rows(), names)
        figures = self._current()[rows].tolist()
        return [(names[row], int(figure) if self.integer else figure) for row, figure in zip(rows.tolist(), figures)]

    def get(self, key, default=None):
        figure = super().get(key, default)
        return int(figure) if self.integer and figure is not default and figure is not None else figure

    def get_many(self, keys, default=None) -> list:
        """`[self.get(key, default) for key in keys]`, read from the column in one pass."""
        numbers = self._chosen().goods_numbers
        found = self.take(numpy.array([numbers.get(key, -1) for key in keys], dtype=numpy.int64)).tolist()
        return [default if figure != figure else (int(figure) if self.integer else figure) for figure in found]

    def replace_rows(self, rows: numpy.ndarray, figures: numpy.ndarray) -> None:
        """Hold exactly these figures, at these market rows (numbered markets): every other market has none."""
        self._current()[:] = numpy.nan
        if len(rows):
            self.put(rows, figures)

    def saved(self) -> dict:
        """{market name: figure} in the order of the names with the area after the good, as a save writes it."""
        saved = self.sorted_named()
        return {name: int(figure) for name, figure in saved.items()} if self.integer else saved

    def copy(self) -> "MarketColumn":
        """A column with the same figures over the same numbering."""
        names, figures = self.named()
        copied = MarketColumn(self._tables, integer=self.integer)
        copied.hold_named(names, figures)
        return copied
