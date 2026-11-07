"""The market memory as arrays: prices by (good, area), wages by (trade, tile), the base rate by (good, area), and the
index of each (good, tile) pair's area.

`AreaIndex` says which area each tile is in for each good (the area map does not change inside a year). `MemoryArrays`
holds what the memory remembers, read once with `build`; an array is read with `at_tiles`, which turns (good, tile) into
the (good, area) cell. The memory is read through its stores' keys exactly as `MarketMemory.price_kind` and
`offered_price` read them (`test_year_arrays` checks the two against each other)."""
from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .market_memory import KEY_SEPARATOR, MarketMemory
from .planning_price import BARE_QUOTES
from .types import QUOTE_LOWEST_UNFILLED_ASK, QUOTE_OPENING_ESTIMATE
from .year_arrays_recipes import Names

NO_AREA = -1


@dataclass(frozen=True)
class AreaIndex:
    areas: Names
    of_good_tile: np.ndarray        # good by tile: the area's column, NO_AREA where the good has no market there

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
        return cls(areas, grid)


@dataclass(frozen=True)
class MemoryArrays:
    price: np.ndarray        # good by area: the remembered price, NaN where none
    offered: np.ndarray      # good by area: the price on offer (MarketMemory.offered_price), NaN where none
    cleared: np.ndarray      # good by area: the price the market cleared at last year, NaN where it did not
    bare_quote: np.ndarray   # good by area: whether the remembered price is a bid ceiling or an ask, not a trade
    rate: np.ndarray         # area: the base lending rate of the area's currency, NaN where none
    wage: np.ndarray         # trade by tile: the wage rule's wage

    @classmethod
    def build(cls, memory: MarketMemory, goods: Names, trades: Names, tiles: Names, area_index: AreaIndex,
              own_currency: str, wage_of) -> "MemoryArrays":
        """`wage_of(trade, tile_id)` is the wage rule (trade_wages.wage_in_view through a view); called for every trade and tile."""
        areas = area_index.areas
        shape = (len(goods.ids), len(areas.ids))
        price, cleared = np.full(shape, np.nan), np.full(shape, np.nan)
        offered, bare = np.full(shape, np.nan), np.zeros(shape, dtype=bool)

        def cell(key: str):
            good, _separator, area = key.partition(KEY_SEPARATOR)
            good_row, area_column = goods.row.get(good), areas.row.get(area)
            return None if good_row is None or area_column is None else (good_row, area_column)
        for key, value in memory.prices.items():
            found = cell(key)
            if found is None:
                continue
            price[found] = value
            age = memory.trade_age.get(key)
            kind = memory.quote_kinds.get(key)
            if age is not None and age <= 0:
                offered[found] = value
            elif kind is None:
                if age is None:            # an opening estimate no clearing has replaced
                    offered[found] = value
            else:
                if kind in (QUOTE_LOWEST_UNFILLED_ASK, QUOTE_OPENING_ESTIMATE):
                    offered[found] = value
                bare[found] = kind in BARE_QUOTES
        for key, value in memory.cleared_prices.items():
            found = cell(key)
            if found is not None:
                cleared[found] = value
        rate = np.full(len(areas.ids), np.nan)
        for column, area in enumerate(areas.ids):
            found = memory.rates.get(memory.currency_of_area.get(area, own_currency))
            if found is not None:
                rate[column] = found
        wage = np.array([[wage_of(trade, tile) for tile in tiles.ids] for trade in trades.ids], dtype=np.float64).reshape(
            len(trades.ids), len(tiles.ids))
        return cls(price, offered, cleared, bare, rate, wage)


def at_tiles(grid: np.ndarray, area_of_good_tile: np.ndarray, good_row: int, tile_row: int) -> float:
    """The (good, area) cell of the area `good_row` has on `tile_row`; NaN where it has no market."""
    column = area_of_good_tile[good_row, tile_row]
    return np.nan if column == NO_AREA else grid[good_row, column]
