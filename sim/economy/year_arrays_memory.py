"""The market memory as arrays: prices by (good, area), wages by (trade, tile), the base rate by (good, area), and the
index of each (good, tile) pair's area.

`AreaIndex` says which area each tile is in for each good (the area map does not change inside a year). `MemoryArrays`
holds what the memory remembers, read once with `build`; an array is read with `at_tiles`, which turns (good, tile) into
the (good, area) cell. The memory's goods market table is read whole by kernels
(`market_table_kernels`), with the same meaning as `MarketMemory.price_kind` and `offered_price` (`test_year_arrays` checks the
two against each other)."""
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

from .market_memory import MarketMemory, written_stamp
from .market_table_kernels import (KIND_BARE, KIND_OFFERED, KIND_OTHER, bare_quotes, market_of_good_tile, offered_prices,
                                   scatter_flags, scatter_values)
from .planning_price import BARE_QUOTES
from .types import QUOTE_LOWEST_UNFILLED_ASK, QUOTE_OPENING_ESTIMATE
from .year_arrays_recipes import Names

NO_AREA = -1


@dataclass(frozen=True)
class AreaIndex:
    areas: Names
    of_good_tile: np.ndarray        # good by tile: the area's column, NO_AREA where the good has no market there
    stores: Dict[str, tuple] = field(default_factory=dict, compare=False, repr=False)   # reads kept for this index: "cells" -> (numbering stamp, goods, good row, area column of each goods market)

    @classmethod
    def build(cls, area_map, goods: Names, tiles: Names) -> "AreaIndex":
        known = set(area_map.goods())
        ids = set()
        for good in goods.ids:
            if good in known:
                ids.update(area.area_id for area in area_map.areas(good))
        areas = Names.of(ids)
        grid = np.full((len(goods.ids), len(tiles.ids)), NO_AREA, dtype=np.int64)
        for good_row, good in enumerate(goods.ids):
            if good not in known:
                continue
            for area in area_map.areas(good):
                column = areas.row[area.area_id]
                for tile in area.tiles:
                    tile_row = tiles.row.get(tile)
                    if tile_row is not None:
                        grid[good_row, tile_row] = column
        return cls(areas, grid, {})


_KIND_BITS = {QUOTE_LOWEST_UNFILLED_ASK: KIND_OFFERED | KIND_BARE, QUOTE_OPENING_ESTIMATE: KIND_OFFERED,
              **{kind: KIND_BARE for kind in BARE_QUOTES if kind != QUOTE_LOWEST_UNFILLED_ASK}}


def market_cells(memory: MarketMemory, goods: Names, area_index: AreaIndex):
    """(good row, area column) of each goods market of the memory's table, -1 where the market's good or area is not one these arrays
    hold. Worked out once per numbering of the markets and kept on the area index."""
    tables = memory.tables
    markets = tables.goods_table
    stamp = (id(tables), tables.generation)
    kept = area_index.stores.get("cells")
    if kept is not None and kept[0] == stamp and kept[1] is goods:
        return kept[2], kept[3]
    count = int(markets.row_count[0])
    good_row_of_number = np.array([goods.row.get(name, -1) for name in tables.goods.names], dtype=np.int64)
    area_column_of_number = np.array([area_index.areas.row.get(name, -1) for name in tables.areas.names], dtype=np.int64)
    good_rows = good_row_of_number[markets.first[:count]] if count else np.empty(0, dtype=np.int64)
    area_columns = area_column_of_number[markets.area[:count]] if count else np.empty(0, dtype=np.int64)
    area_index.stores["cells"] = (stamp, goods, good_rows, area_columns)
    return good_rows, area_columns


def markets_by_good_tile(memory: MarketMemory, goods: Names, area_index: AreaIndex) -> np.ndarray:
    """Good row by tile row: the memory's goods market row for the good's area on that tile, -1 where there is none (the array a
    compiled phase reads in place of `area_of(good, tile)` followed by a key lookup)."""
    good_rows, area_columns = market_cells(memory, goods, area_index)
    market_of_good_area = np.full((len(goods.ids), max(1, len(area_index.areas.ids))), -1, dtype=np.int64)
    found = (good_rows >= 0) & (area_columns >= 0)
    market_of_good_area[good_rows[found], area_columns[found]] = np.flatnonzero(found)
    return market_of_good_tile(area_index.of_good_tile, market_of_good_area)


def class_of_kind(memory: MarketMemory) -> np.ndarray:
    """By the memory's quote kind number: the KIND_* bits of the kind (`_KIND_BITS`; a kind it does not know is KIND_OTHER)."""
    return np.array([_KIND_BITS.get(kind, KIND_OTHER) for kind in memory.tables.kinds.names], dtype=np.int64)


def price_grid(memory: MarketMemory, goods: Names, area_index: AreaIndex) -> np.ndarray:
    """The remembered prices alone (`MemoryArrays.price`), for a reader that needs no other part of the memory."""
    price = np.full((len(goods.ids), len(area_index.areas.ids)), np.nan)
    good_rows, area_columns = market_cells(memory, goods, area_index)
    markets = memory.tables.goods_table
    scatter_values(price, markets.price, good_rows, area_columns, int(markets.row_count[0]))
    return price


@dataclass(frozen=True)
class MemoryArrays:
    price: np.ndarray        # good by area: the remembered price, NaN where none
    offered: np.ndarray      # good by area: the price on offer (MarketMemory.offered_price), NaN where none
    cleared: np.ndarray      # good by area: the price the market cleared at last year, NaN where it did not
    bare_quote: np.ndarray   # good by area: whether the remembered price is a bid ceiling or an ask, not a trade
    rate: np.ndarray         # area: the base lending rate of the area's currency, NaN where none
    wage: np.ndarray         # trade by tile: the wage rule's wage
    stamp: Optional[tuple] = None    # what the memory was when these were read (`is_current`)

    def is_current(self, memory: MarketMemory) -> bool:
        """Whether nothing has been written to this memory since these arrays were read."""
        return self.stamp is not None and self.stamp == (id(memory), written_stamp())

    @classmethod
    def build(cls, memory: MarketMemory, goods: Names, trades: Names, tiles: Names, area_index: AreaIndex,
              own_currency: str, wage_of, wage_grid: Optional[np.ndarray] = None) -> "MemoryArrays":
        """`wage_of(trade, tile_id)` is the wage rule (trade_wages.wage_in_view through a view); called for every trade and tile.
        A caller that has worked the wages out already hands the (trade by tile) grid as `wage_grid`."""
        areas = area_index.areas
        shape = (len(goods.ids), len(areas.ids))
        price, cleared = np.full(shape, np.nan), np.full(shape, np.nan)
        offered, bare = np.full(shape, np.nan), np.zeros(shape, dtype=bool)
        markets = memory.tables.goods_table
        good_rows, area_columns = market_cells(memory, goods, area_index)
        count = int(markets.row_count[0])
        kind_classes = class_of_kind(memory)
        scatter_values(price, markets.price, good_rows, area_columns, count)
        scatter_values(offered, offered_prices(markets, kind_classes), good_rows, area_columns, count)
        scatter_flags(bare, bare_quotes(markets, kind_classes), good_rows, area_columns, count)
        scatter_values(cleared, markets.cleared_price, good_rows, area_columns, count)
        rate = np.full(len(areas.ids), memory.rates.get(own_currency, np.nan))      # every area is in the economy's own currency but those the memory names
        for area, currency in memory.currency_of_area.items():
            if area in areas.row:
                rate[areas.row[area]] = memory.rates.get(currency, np.nan)
        wage = wage_grid if wage_grid is not None else np.array(
            [[wage_of(trade, tile) for tile in tiles.ids] for trade in trades.ids], dtype=np.float64).reshape(
            len(trades.ids), len(tiles.ids))
        return cls(price, offered, cleared, bare, rate, wage, (id(memory), written_stamp()))


def at_tiles(grid: np.ndarray, area_of_good_tile: np.ndarray, good_row: int, tile_row: int) -> float:
    """The (good, area) cell of the area `good_row` has on `tile_row`; NaN where it has no market."""
    column = area_of_good_tile[good_row, tile_row]
    return np.nan if column == NO_AREA else grid[good_row, column]
