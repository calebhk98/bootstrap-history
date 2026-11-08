"""The year's cleared markets as a mapping of (good, area) to `goods_respend_year.LeftMarket`, with no `LeftMarket` made until one is asked for.

Everything the year's rules read about a market is a column of the year's table (`goods_year_markets.YearMarkets`) or of the good's clearing
(`goods_good_clear.GoodClearing`); this mapping only remembers where each market's row is, so `table_columns` can hand the sorted markets'
rows to a rule that reads columns, and makes a `LeftMarket` (the market's objects) when a rule written over objects, a test or the UI asks."""
from collections.abc import Mapping
from typing import Iterator, List, Tuple

import numpy

from .goods_respend_year import LeftMarket

Market = Tuple[str, str]


class LeftMarkets(Mapping):
    """Market -> `LeftMarket`, made on first read; `keys_in_order` and `rows` are the markets in the order they cleared and their table rows."""

    def __init__(self, year_markets) -> None:
        self.year_markets = year_markets
        self._keys: List[Market] = []
        self._goods: list = []          # per good that cleared: (its `GoodClearing`, its answer from the settlement, the table row of its first market)
        self._place: dict = {}          # market -> (index in `_goods`, place in its clearing); built when first asked for
        self._made: dict = {}
        self._sorted = None

    def add_good(self, good: str, cleared, answer: list, first_row: int) -> None:
        """The markets of a good that cleared, in clearing order, with the settlement's answer for each and their first table row."""
        self._keys.extend((good, area) for area in cleared.areas)
        self._goods.append((cleared, answer, first_row))
        self._sorted = None

    def keys_in_order(self) -> List[Market]:
        return self._keys

    def sorted_keys(self) -> List[Market]:
        """The markets sorted by (good, area), made once."""
        if self._sorted is None:
            self._sorted = sorted(range(len(self._keys)), key=self._keys.__getitem__)
        return [self._keys[each] for each in self._sorted]

    def sorted_cells(self) -> numpy.ndarray:
        """The year table's row of each market in `sorted_keys()` order."""
        self.sorted_keys()
        rows = self.rows()
        return rows[numpy.array(self._sorted, dtype=numpy.int64)] if len(rows) else rows

    def rows(self) -> numpy.ndarray:
        """The year table's row of each market in clearing order."""
        return numpy.concatenate([numpy.arange(first, first + len(cleared), dtype=numpy.int64) for cleared, _answer, first in self._goods]) \
            if self._goods else numpy.zeros(0, dtype=numpy.int64)

    def _index(self) -> dict:
        if not self._place and self._keys:
            position = 0
            for number, (cleared, _answer, _first) in enumerate(self._goods):
                for place in range(len(cleared)):
                    self._place[self._keys[position]] = (number, place)
                    position += 1
        return self._place

    def __getitem__(self, market: Market) -> LeftMarket:
        found = self._made.get(market)
        if found is None:
            number, place = self._index()[market]
            cleared, answer, first = self._goods[number]
            each, delivered, bought = cleared[place], float(answer.delivered[place]), answer.bought(place)
            found = self._made[market] = LeftMarket(each.bids, each.result, each.offers_left, None, delivered, 0.0, 0, bought, each.rows,
                                                    self.year_markets, first + place)
        return found

    def __iter__(self) -> Iterator[Market]:
        return iter(self._keys)

    def __len__(self) -> int:
        return len(self._keys)

    def __contains__(self, market) -> bool:
        return market in self._index()
