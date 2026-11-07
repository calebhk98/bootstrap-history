"""The market memory as arrays: prices by (good, area), wages by (trade, tile), the base rate by (good, area), and the
index of each (good, tile) pair's area.

`AreaIndex` says which area each tile is in for each good (the area map does not change inside a year). `MemoryArrays`
holds what the memory remembers, read once with `build`; an array is read with `at_tiles`, which turns (good, tile) into
the (good, area) cell. The memory is read through its stores' keys exactly as `MarketMemory.price_kind` and
`offered_price` read them (`test_year_arrays` checks the two against each other)."""
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional

import numpy as np

from .market_memory import KEY_SEPARATOR, MarketMemory, written_stamp
from .planning_price import BARE_QUOTES
from .types import QUOTE_LOWEST_UNFILLED_ASK, QUOTE_OPENING_ESTIMATE
from .year_arrays_recipes import Names

NO_AREA = -1


@dataclass(frozen=True)
class AreaIndex:
    areas: Names
    of_good_tile: np.ndarray        # good by tile: the area's column, NO_AREA where the good has no market there
    located: Dict[str, int] = field(default_factory=dict, compare=False, repr=False)    # a memory key -> its good row times the area count plus its area column, -1 where it names none the arrays hold

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


_KIND_OFFERED, _KIND_BARE, _KIND_OTHER = 1, 2, 4
_KIND_BITS = {None: 0, QUOTE_LOWEST_UNFILLED_ASK: _KIND_OFFERED | _KIND_BARE, QUOTE_OPENING_ESTIMATE: _KIND_OFFERED,
              **{kind: _KIND_BARE for kind in BARE_QUOTES if kind != QUOTE_LOWEST_UNFILLED_ASK}}


def _located(area_index: AreaIndex, store: Mapping[str, float], goods: Names):
    """(the store's keys, the good row and area column of each, -1 where the key names no good or area the arrays hold). Where a
    key falls is worked out once and kept."""
    keys = tuple(store)
    kept = area_index.located
    areas = area_index.areas
    width = max(1, len(areas.ids))
    codes = np.empty(len(keys), dtype=np.int64)
    for position, key in enumerate(keys):
        code = kept.get(key)
        if code is None:
            good, _separator, area = key.partition(KEY_SEPARATOR)
            good_row, area_column = goods.row.get(good), areas.row.get(area)
            code = kept[key] = -1 if good_row is None or area_column is None else good_row * width + area_column
        codes[position] = code
    return keys, np.where(codes >= 0, codes // width, -1), np.where(codes >= 0, codes % width, -1)


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

        keys, rows, columns = _located(area_index, memory.prices, goods)
        found = rows >= 0
        values = np.fromiter(memory.prices.values(), dtype=np.float64, count=len(keys))
        price[rows[found], columns[found]] = values[found]
        ages = np.array([memory.trade_age.get(key, np.nan) for key in keys], dtype=np.float64)
        has_age = ~np.isnan(ages)
        bits = np.array([_KIND_BITS.get(memory.quote_kinds.get(key), _KIND_OTHER) for key in keys], dtype=np.int64)
        current = has_age & (ages <= 0)
        kind_free = ~current & (bits == 0)
        offered_mask = found & (current | (kind_free & ~has_age) | (~current & (bits != 0) & ((bits & _KIND_OFFERED) > 0)))
        offered[rows[offered_mask], columns[offered_mask]] = values[offered_mask]
        bare_mask = found & ~current & (bits != 0) & ((bits & _KIND_BARE) > 0)
        bare[rows[bare_mask], columns[bare_mask]] = True
        keys, rows, columns = _located(area_index, memory.cleared_prices, goods)
        found = rows >= 0
        values = np.fromiter(memory.cleared_prices.values(), dtype=np.float64, count=len(keys))
        cleared[rows[found], columns[found]] = values[found]
        rate = np.full(len(areas.ids), np.nan)
        for column, area in enumerate(areas.ids):
            found = memory.rates.get(memory.currency_of_area.get(area, own_currency))
            if found is not None:
                rate[column] = found
        wage = wage_grid if wage_grid is not None else np.array(
            [[wage_of(trade, tile) for tile in tiles.ids] for trade in trades.ids], dtype=np.float64).reshape(
            len(trades.ids), len(tiles.ids))
        return cls(price, offered, cleared, bare, rate, wage, (id(memory), written_stamp()))


def at_tiles(grid: np.ndarray, area_of_good_tile: np.ndarray, good_row: int, tile_row: int) -> float:
    """The (good, area) cell of the area `good_row` has on `tile_row`; NaN where it has no market."""
    column = area_of_good_tile[good_row, tile_row]
    return np.nan if column == NO_AREA else grid[good_row, column]
