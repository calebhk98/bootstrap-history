"""The market memory as arrays: prices by (good, area), wages by (trade, tile), the base rate by (good, area), and the
index of each (good, tile) pair's area.

`AreaIndex` says which area each tile is in for each good (the area map does not change inside a year). `MemoryArrays`
holds what the memory remembers, read with `build` straight from the memory's own (good by area) arrays
(`market_arrays.MarketStore.gather`: this year's order of goods and areas laid over the memory's numbering, no key is
split); an array is read with `at_tiles`, which turns (good, tile) into the (good, area) cell. The kinds are read exactly
as `MarketMemory.price_kind` and `offered_price` read them (`test_year_arrays` checks the two against each other)."""
from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np

from .market_memory import MarketMemory, written_stamp
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


_KIND_OFFERED, _KIND_BARE, _KIND_OTHER = 1, 2, 4
_KIND_BITS = {None: 0, QUOTE_LOWEST_UNFILLED_ASK: _KIND_OFFERED | _KIND_BARE, QUOTE_OPENING_ESTIMATE: _KIND_OFFERED,
              **{kind: _KIND_BARE for kind in BARE_QUOTES if kind != QUOTE_LOWEST_UNFILLED_ASK}}


def price_grid(memory: MarketMemory, goods: Names, area_index: AreaIndex) -> np.ndarray:
    """The remembered prices alone (`MemoryArrays.price`), for a reader that needs no other part of the memory: the memory's
    own (good by area) array read in this year's order of goods and areas."""
    ids = memory.numbering("goods")
    return memory.prices.gather(ids.rows_of(goods.ids), ids.columns_of(area_index.areas.ids))


def _kind_bits(words) -> np.ndarray:
    """`_KIND_BITS` of each quote kind a store holds, by code, with a last entry (index -1) for no quote."""
    return np.array([_KIND_BITS.get(word, _KIND_OTHER) for word in words] + [0], dtype=np.int64)


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
        ids = memory.numbering("goods")
        rows, columns = ids.rows_of(goods.ids), ids.columns_of(areas.ids)
        price = memory.prices.gather(rows, columns)
        cleared = memory.cleared_prices.gather(rows, columns)
        ages = memory.trade_age.gather(rows, columns)
        bits = _kind_bits(memory.quote_kinds.words)[memory.quote_kinds.gather(rows, columns)]
        found = ~np.isnan(price)
        has_age = ages >= 0
        current = has_age & (ages <= 0)
        kind_free = ~current & (bits == 0)
        offered_mask = found & (current | (kind_free & ~has_age) | (~current & (bits != 0) & ((bits & _KIND_OFFERED) > 0)))
        offered = np.where(offered_mask, price, np.nan)
        bare = found & ~current & (bits != 0) & ((bits & _KIND_BARE) > 0)
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
