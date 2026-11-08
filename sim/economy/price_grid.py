"""Every good's offered price on every tile as one grid, refreshed once per write to the market memory.

`PriceIndex` is what an area map fixes for a game: the goods that have markets, the tiles they are in, and each good's area on each
tile (`year_arrays_memory.AreaIndex`). `PriceGrid` is the memory's offered prices (`MarketMemory.offered_price`) laid out good by tile
through the memory's own market numbers (`year_arrays_memory.markets_by_good_tile`): `price_grid_kernels.offered_by_good_tile`
fills it in one call, and it is filled again only when a figure it reads may have changed (`memory_stamp`). A reader that wants the prices
of a basket on a tile takes the tile's column (`TilePrices`), where it used to ask `area_of` and `offered_price` once per good.

NaN in the grid is "no price", never 0.0; `TilePrices.prices` holds only goods that have one."""
import weakref
from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Tuple

import numpy as np

from .market_memory import MarketMemory, written_stamp
from .price_grid_kernels import offered_by_good_tile
from .year_arrays_memory import AreaIndex, class_of_kind, markets_by_good_tile
from .market_table_kernels import offered_prices
from .year_arrays_recipes import Names


@dataclass(frozen=True)
class PriceIndex:
    goods: Names                 # the goods the area map holds markets for
    tiles: Names                 # every tile of the area map
    area_index: AreaIndex        # each good's area on each tile
    stores: Dict[str, tuple]     # reads kept for this index

    @classmethod
    def build(cls, area_map) -> "PriceIndex":
        goods = Names.of(area_map.goods())
        tiles = Names.of(tile for good in goods.ids for area in area_map.areas(good) for tile in area.tiles)
        return cls(goods, tiles, AreaIndex.build(area_map, goods, tiles), {})


_index_of: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def price_index_of(area_map) -> Optional[PriceIndex]:
    """The `PriceIndex` of an area map, built once per map (a map never changes; a redraw makes a new one). None for a map that cannot
    list its goods and areas: its readers take the per-good path."""
    try:
        return _index_of[area_map]
    except KeyError:
        pass
    except TypeError:
        return _build_unkept(area_map)
    index = _build_unkept(area_map)
    if index is not None:
        _index_of[area_map] = index
    return index


def _build_unkept(area_map) -> Optional[PriceIndex]:
    try:
        return PriceIndex.build(area_map)
    except AttributeError:
        return None


def memory_stamp(memory: MarketMemory) -> tuple:
    """What the memory's price columns were when read: changes with every write to a figure (`MarketTables.writes`), every
    write the memory notes (`written_stamp`) and every new numbering or table (`generation`)."""
    tables = memory.tables
    return (id(tables), tables.generation, tables.writes, written_stamp())


class EveryGood:
    """The `covered` of a grid that answers for any good: a good the area map has no market for has none in the memory either."""

    def __contains__(self, good) -> bool:
        return True


EVERY_GOOD = EveryGood()


@dataclass(frozen=True)
class TilePrices:
    """The offered prices on one tile: `prices` holds the goods that have one, `covered` every good the grid answers for (a good outside it
    is read by the per-good path). A good with no market in the area map is answered "no price" when the memory holds no market of any
    good outside the area map (then `covered` is `EVERY_GOOD`): the per-good path would look for `good|labour area` and find none."""
    prices: Dict[str, float]
    covered: Mapping[str, int]

    def covers_all(self, goods) -> bool:
        """Whether the block answers for each of `goods`."""
        covered = self.covered
        return covered is EVERY_GOOD or all(good in covered for good in goods)


class PriceGrid:
    """The offered prices and the remembered prices of one memory over one `PriceIndex`, good by tile."""

    def __init__(self, memory: MarketMemory, index: PriceIndex) -> None:
        self._memory = memory
        self._index = index
        self._stamp: Optional[tuple] = None
        self._grids: Tuple[Optional[np.ndarray], Optional[np.ndarray]] = (None, None)      # offered, remembered
        self._tiles: Tuple[Dict[str, TilePrices], Dict[str, TilePrices]] = ({}, {})
        self._rows: Optional[tuple] = None      # (numbering stamp, the market row of each good and tile, whether every good the memory numbers is the index's)
        self.refreshes = 0         # how many times the grids were filled again (tests and measurements read it)

    def _current(self) -> None:
        """Fill the grids again if the memory was written to since they were filled."""
        stamp = memory_stamp(self._memory)
        if stamp == self._stamp:
            return
        index = self._index
        tables = self._memory.tables
        markets = tables.goods_table
        numbering = (id(tables), tables.generation)
        if self._rows is None or self._rows[0] != numbering:
            indexed_only = all(good in index.goods.row for good in tables.goods.name_list)
            self._rows = (numbering, markets_by_good_tile(self._memory, index.goods, index.area_index), indexed_only)
        offered = offered_by_good_tile(offered_prices(markets, class_of_kind(self._memory)), self._rows[1])
        self._grids = (offered, offered_by_good_tile(markets.price[:int(markets.row_count[0])], self._rows[1]))
        self._tiles = ({}, {})
        self._stamp = stamp
        self.refreshes += 1

    def grid(self) -> np.ndarray:
        """The good-by-tile grid of offered prices as of the memory now."""
        self._current()
        return self._grids[0]

    @property
    def tiles(self) -> tuple:
        """Every tile the grid holds, in its column order."""
        return self._index.tiles.ids

    def on_tile(self, tile: str, remembered: bool = False) -> Optional[TilePrices]:
        """The offered prices on `tile` (the remembered prices, `MarketMemory.prices`, when `remembered`), None for a tile the area map
        does not hold (the per-good path then answers, and refuses as it did)."""
        column_of = self._index.tiles.row.get(tile)
        if column_of is None:
            return None
        self._current()
        kept = self._tiles[remembered]
        found = kept.get(tile)
        if found is None:
            column = self._grids[remembered][:, column_of]
            present = np.flatnonzero(column == column)
            names = self._index.goods.ids
            found = kept[tile] = TilePrices(
                {names[row]: price for row, price in zip(present.tolist(), column[present].tolist())},
                EVERY_GOOD if self._rows[2] else self._index.goods.row)
        return found
