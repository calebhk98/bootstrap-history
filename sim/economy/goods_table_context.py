"""What a year's table clearing reads again and again, worked out once: name ranks, the producers' rows in the year arrays by
agent id, the band multiple of each tile, the lending rate of each area, and which goods the batch may clear."""
import math

import numpy

from sim.compiled_tables.growth import reserve_rows

from .ask_ceiling import AskAlternatives
from .goods_table_group import name_ranks

PAIRS_PER_ROW = 12        # room reserved for pairs, per bid and offer row: a guess that only saves growing the table again (`reserve_cleared_rows`)


class ClearingContext:
    """The year's clearing: the records, the order tables (`orders`), the year arrays and the sellers' costs."""

    def __init__(self, setup, record, view, orders, arrays, costs):
        self.setup, self.record, self.view = setup, record, view
        self.orders, self.arrays, self.costs = orders, arrays, costs
        self._agent_ranks = self._tile_ranks = None
        self._rates = {}
        self._area_rates, self._area_rates_known = numpy.zeros(0), numpy.zeros(0, dtype=numpy.bool_)
        self._producer_rows = None
        self._multiples = {}
        self.alternatives = AskAlternatives(setup, record)
        self._scratch = None
        self._room_reserved = False

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

    def area_rates(self) -> tuple:
        """(rate, known) per area id: the lending rates asked for so far (`note_area_rate` adds one), for the packing kernel."""
        count = len(self.orders.memory_tables.areas.name_list)
        if len(self._area_rates) != count:
            grown = numpy.full(count, math.nan)
            grown[:len(self._area_rates)] = self._area_rates
            known = numpy.zeros(count, dtype=numpy.bool_)
            known[:len(self._area_rates)] = self._area_rates_known
            self._area_rates, self._area_rates_known = grown, known
        return self._area_rates, self._area_rates_known

    def note_area_rate(self, area_id: int) -> None:
        """Ask for the lending rate of an area the packing kernel found missing from `area_rates`."""
        rate, known = self.area_rates()
        rate[area_id] = self.rate_in(self.orders.memory_tables.areas.name_list[area_id])
        known[area_id] = True

    def ask_known_areas_and_tiles(self) -> None:
        """Ask now for the lending rate of every area numbered so far, so the packing kernel does not find them missing and run again. It
        is a read of the memory that does not change within the year, so asking early gives the figure asking late would; an area numbered
        later is still asked when found missing. A good's band multiples are asked when its markets clear (`band_multiple_table`)."""
        for area_id in range(len(self.orders.memory_tables.areas.name_list)):
            self.note_area_rate(area_id)

    def scratch(self, areas: int, tiles: int) -> tuple:
        """(areas, tiles, room) the fused clearing kernel marks what it needs answered in: all false and zero between calls."""
        if self._scratch is None or len(self._scratch[0]) != areas or len(self._scratch[1]) != tiles:
            self._scratch = (numpy.zeros(areas, dtype=numpy.bool_), numpy.zeros(tiles, dtype=numpy.bool_), numpy.zeros(4, dtype=numpy.int64))
        return self._scratch

    def reserve_cleared_rows(self) -> None:
        """Once a year, on the first good cleared: room in the tables the clearing appends to for the rows the tables hold now (a good's
        clearing appends at most one row per bid, per offer and per market, and pairs by the dozen), so the goods after it rarely
        find a table full (`goods_clear_fused` reserves again when one is)."""
        if self._room_reserved:
            return
        self._room_reserved = True
        orders = self.orders
        bids, offers = orders.tables()
        rows = int(bids.row_count[0]) + int(offers.row_count[0])
        for name, extra in (("bid_order", int(bids.row_count[0])), ("offer_order", int(offers.row_count[0])), ("pairs", PAIRS_PER_ROW * rows),
                            ("results", rows)):
            setattr(orders, name, reserve_rows(getattr(orders, name), extra))

    def good_is_batchable(self, good: str) -> bool:
        """The good is in the year arrays (ground has a rent to hold for, read off the land record: `goods_table_clear._ground_values`)."""
        return self.arrays is not None and good in self.arrays.matrices.goods.row

    def producer_row_table(self) -> numpy.ndarray:
        """Per agent id: the producer's row in the year arrays, -1 for an agent that is not a producer (agents admitted since the table was
        made are not producers)."""
        if self._producer_rows is None:
            agent_number = self.book.agent_number
            numbers = {agent_number(name): row for name, row in self.arrays.producers.row.items()}     # numbering an agent may admit it
            self._producer_rows = numpy.full(len(self.book.agent_ids), -1, dtype=numpy.int64)
            for agent, row in numbers.items():
                self._producer_rows[agent] = row
        if len(self._producer_rows) < len(self.book.agent_ids):
            grown = numpy.full(len(self.book.agent_ids), -1, dtype=numpy.int64)
            grown[:len(self._producer_rows)] = self._producer_rows
            self._producer_rows = grown
        return self._producer_rows

    def band_multiple_table(self, good: str) -> numpy.ndarray:
        """Per tile id: the most, as a multiple of a unit's cost, an ask for `good` may be there (`ask_ceiling.band_multiple`: what its
        buyers' cheapest alternative costs, else the substitution markup, else the stated multiple); NaN for a tile not asked about
        yet (`note_band_multiple` fills one in)."""
        count = len(self.book.tile_ids.name_list)
        table = self._multiples.get(good)
        if table is None or len(table) < count:
            grown = numpy.full(count, numpy.nan)
            if table is not None:
                grown[:len(table)] = table
            table = self._multiples[good] = grown
        return table

    def note_band_multiple(self, tile: int, good: str) -> None:
        """Work out the band multiple of `good` on a tile the decision kernel found missing from `band_multiple_table`."""
        self.band_multiple_table(good)[tile] = self.alternatives.multiple(good, self.book.tile_ids.name_list[tile])
