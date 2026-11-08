"""What a year's table clearing reads again and again, worked out once: name ranks, the producers' rows in the year arrays by
agent id, the band multiple of each tile, the lending rate of each area, and which goods the batch may clear."""
import math

import numpy

from .ask_adjust import ASK_BAND_CEILING
from .goods_table_group import name_ranks


class ClearingContext:
    """The year's clearing: the records, the order tables (`orders`), the year arrays and the sellers' costs."""

    def __init__(self, setup, record, view, orders, arrays, costs):
        self.setup, self.record, self.view = setup, record, view
        self.orders, self.arrays, self.costs = orders, arrays, costs
        self._agent_ranks = self._tile_ranks = None
        self._rates = {}
        self._producer_rows = None
        self._multiples = numpy.zeros(0)

    @property
    def book(self):
        return self.record.book

    def agent_rank(self) -> numpy.ndarray:
        """Per agent id: its place when all agent names are sorted (made again when agents have been admitted since)."""
        names = self.book.agent_ids.name_list
        if self._agent_ranks is None or len(self._agent_ranks) != len(names):
            self._agent_ranks = name_ranks(names)
        return self._agent_ranks

    def tile_rank(self) -> numpy.ndarray:
        names = self.book.tile_ids.name_list
        if self._tile_ranks is None or len(self._tile_ranks) != len(names):
            self._tile_ranks = name_ranks(names)
        return self._tile_ranks

    def rate_in(self, area: str) -> float:
        """The lending rate of the area's currency; NaN where there is none."""
        found = self._rates.get(area, False)
        if found is False:
            rate = self.view.interest_rate(self.view.currency_of(area))
            found = self._rates[area] = math.nan if rate is None else rate
        return found

    def good_is_batchable(self, good: str) -> bool:
        """The good is in the year arrays (ground has a rent to hold for, read off the land record: `goods_table_clear._ground_values`)."""
        return self.arrays is not None and good in self.arrays.matrices.goods.row

    def producer_rows(self, sellers: numpy.ndarray) -> numpy.ndarray:
        """Per seller agent id: the producer's row in the year arrays, -1 for a seller that is not a producer."""
        if self._producer_rows is None:
            agent_number = self.book.agent_number
            numbers = {agent_number(name): row for name, row in self.arrays.producers.row.items()}
            self._producer_rows = numpy.full(len(self.book.agent_ids), -1, dtype=numpy.int64)
            for agent, row in numbers.items():
                self._producer_rows[agent] = row
        if len(sellers) and int(sellers.max()) >= len(self._producer_rows):
            grown = numpy.full(len(self.book.agent_ids), -1, dtype=numpy.int64)
            grown[:len(self._producer_rows)] = self._producer_rows
            self._producer_rows = grown
        return self._producer_rows[sellers]

    def band_multiples(self, tiles: numpy.ndarray) -> numpy.ndarray:
        """Per tile id: the most, as a multiple of a unit's cost, an ask may be there (the substitution markup, never past
        ASK_BAND_CEILING)."""
        names = self.book.tile_ids.name_list
        if len(self._multiples) < len(names):
            grown = numpy.full(len(names), numpy.nan)
            grown[:len(self._multiples)] = self._multiples
            self._multiples = grown
        for tile in numpy.unique(tiles[numpy.isnan(self._multiples[tiles])]).tolist():
            elasticity = self.setup.basket_for(names[tile]).substitution
            self._multiples[tile] = min(elasticity / (elasticity - 1.0) if elasticity > 1.0 else ASK_BAND_CEILING, ASK_BAND_CEILING)
        return self._multiples[tiles]
