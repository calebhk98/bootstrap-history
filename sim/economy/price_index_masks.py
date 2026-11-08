"""Which markets of a price-index layout a country's national figures count, as whole-array reads of the area map and the layout, with no
per-market function call.

A national price counts the markets of a good whose area touches one of the country's tiles, and every market whose area the area map
does not hold for that good (`country_figures._prices` before it moved here); a national wage counts the labour markets of the country's own
tiles. Both masks are by the layout's place order (`price_index.MarketLayout`)."""
import weakref
from typing import Iterable, Optional

import numpy as np

from .setup import LABOUR_AREA_PREFIX

_arrays_of: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()
_places_of: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def _table_arrays(table) -> tuple:
    """`AreaTileTable` as numpy arrays (goods, good partition, areas, area partition, entry area, entry tile), kept for the table."""
    kept = _arrays_of.get(table)
    if kept is None:
        kept = _arrays_of[table] = (np.array(table.goods, dtype=str), np.array(table.good_partition, dtype=np.int64),
                                    np.array(table.areas, dtype=str), np.array(table.area_partition, dtype=np.int64),
                                    np.array(table.entry_area, dtype=np.int64), np.array(table.entry_tile, dtype=str))
    return kept


def _row_of(sorted_names: np.ndarray, names: np.ndarray) -> np.ndarray:
    """Per name: its row in the sorted unique `sorted_names`, -1 for a name not in it."""
    if not len(sorted_names):
        return np.full(len(names), -1, dtype=np.int64)
    found = np.minimum(np.searchsorted(sorted_names, names), len(sorted_names) - 1)
    return np.where(sorted_names[found] == names, found, -1)


def _place_areas(layout, table) -> np.ndarray:
    """Per place of the layout: the row in the table's areas of the place's market area when the map holds that area for the place's good,
    else -1 (a good the map has no market for, or an area of another partition or of no partition). Kept for the layout and table."""
    kept = _places_of.get(layout)
    if kept is not None and kept[0] is table:
        return kept[1]
    goods, good_partition, areas, area_partition, _entry_area, _entry_tile = _table_arrays(table)
    good_of_place = _row_of(goods, np.array(layout.good_of_place, dtype=str))
    area_of_place = _row_of(areas, np.array(layout.areas, dtype=str))
    held = (good_of_place >= 0) & (area_of_place >= 0)
    same = held & (good_partition[np.maximum(good_of_place, 0)] == area_partition[np.maximum(area_of_place, 0)])
    rows = np.where(same, area_of_place, -1)
    _places_of[layout] = (table, rows)
    return rows


def areas_touching(table, tiles: Iterable[str]) -> np.ndarray:
    """Per area of the table: whether any of its tiles is among `tiles`."""
    _goods, _good_partition, areas, _area_partition, entry_area, entry_tile = _table_arrays(table)
    inside = np.isin(entry_tile, np.array(sorted(tiles), dtype=str))
    return np.bincount(entry_area[inside], minlength=len(areas)) > 0


def country_price_mask(layout, table, tiles: Iterable[str]) -> np.ndarray:
    """Per place of the layout: whether the market's area touches `tiles` or is not an area the map holds for its good."""
    rows = _place_areas(layout, table)
    touching = areas_touching(table, tiles)
    return (rows < 0) | touching[np.maximum(rows, 0)]


def labour_area_mask(layout, tiles: Iterable[str]) -> np.ndarray:
    """Per place of the layout: whether the market's area is the labour area of one of `tiles`."""
    wanted = np.array([LABOUR_AREA_PREFIX + tile for tile in sorted(tiles)], dtype=str)
    return np.isin(np.array(layout.areas, dtype=str), wanted)


def mask_for(layout, area_map, tiles: Iterable[str]) -> Optional[np.ndarray]:
    """`country_price_mask` for an area map that lays itself out as a table; None for any other, whose caller takes the per-market rule."""
    table_of = getattr(area_map, "tile_table", None)
    return None if table_of is None else country_price_mask(layout, table_of(), tiles)
