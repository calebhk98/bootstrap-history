"""One basket at one tile's prices as blocks of the packed arrays of `households_orders_pack`, made from the columns of its `PricedNeeds`.

The goods of the priced needs are rows of the answer's column lists; a template takes them as slices and gathers by row number in numpy:
the row floats (price, effect, share, ceiling, quality, service life, spoilage, limit), the good numbers local to the pass (in the order the pass
first meets a good), the priority and the order of the rows by good name. What does not change with the prices (the names of a template's
goods, their areas, the book's numbers of the goods and of their markets) is kept by tile and goods (`StaticRows`), so a basket on a tile
that another template already met is not looked up again."""
from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from . import opening_demand_kernel as opening_kernel
from .priced_need_list import PricedNeeds
from .priced_need_tables import GOODS


def selected_rows(first: np.ndarray, stop: np.ndarray) -> np.ndarray:
    """The rows `first[i]` to `stop[i]` of each i, joined in order."""
    counts = stop - first
    total = int(counts.sum())
    if total == 0:
        return np.zeros(0, dtype=np.int64)
    offsets = np.cumsum(counts) - counts
    return np.arange(total) - np.repeat(offsets - first, counts)


class LocalGoods:
    """Goods numbered 0, 1, 2 ... in the order a pass first meets them (the packed arrays refer to a good by this number)."""

    def __init__(self) -> None:
        self.local = np.full(len(GOODS.names), -1, dtype=np.int64)
        self.count = 0

    def of(self, numbers: np.ndarray) -> np.ndarray:
        """The local number of each good number (numbers in GOODS), giving a number to those not met before in order of first appearance."""
        if len(numbers) == 0:
            return np.zeros(0, dtype=np.int64)
        if len(self.local) <= int(numbers.max()):
            grown = np.full(len(GOODS.names), -1, dtype=np.int64)
            grown[:len(self.local)] = self.local
            self.local = grown
        found = self.local[numbers]
        unseen = found < 0
        if unseen.any():
            fresh, first_at = np.unique(numbers[unseen], return_index=True)
            fresh = fresh[np.argsort(first_at)]
            self.local[fresh] = np.arange(self.count, self.count + len(fresh))
            self.count += len(fresh)
            found = self.local[numbers]
        return found


@dataclass(frozen=True)
class StaticRows:
    """What a template's rows have of a tile and a list of goods, whatever the prices: kept by (tile, goods)."""
    goods: List[str]
    areas: List[str]
    good_ids: List[int]          # the order book's number of each good
    market_ids: List[int]        # the memory's goods market row of each (good, area)


def static_rows(cache: Dict[tuple, StaticRows], goods: List[str], key: tuple, tile: str, view, orders) -> StaticRows:
    """The `StaticRows` of the goods on the tile, made on the first template that has them (`key` names the goods)."""
    found = cache.get(key)
    if found is None:
        areas = [view.area_of(good, tile) for good in goods]
        found = cache[key] = StaticRows(goods, areas, [orders.good_id(good) for good in goods], orders.market_ids(goods, areas))
    return found


def first_unit_of_goods(basket_goods: List[int], need_of_row: List[int]) -> np.ndarray:
    """For each good number: the position in the basket of the first need that names it (-1 for none), indexed by good number."""
    first = np.full(len(GOODS.names), -1, dtype=np.int64)
    first[np.array(basket_goods[::-1], dtype=np.int64)] = np.array(need_of_row[::-1], dtype=np.int64)       # the earliest need is written last
    return first


@dataclass(frozen=True)
class TemplateRows:
    """The rows of one template, by priced good (rows of the `PricedNeeds` columns, in the needs' order)."""
    floats: np.ndarray           # opening_kernel.RF_COUNT columns per row
    local_goods: np.ndarray      # pass-local good number per row
    first_unit: np.ndarray       # position in the basket of the first need naming the row's good (-1 for none)
    priority: np.ndarray         # 0 for a need with a floor, 1 for the others
    order: np.ndarray            # row numbers in the order of (good name, row)
    good_numbers: np.ndarray
    counts: np.ndarray           # priced goods per priced need


def template_rows(priced: PricedNeeds, floors_positive: List[bool], first_unit_by_good: np.ndarray, life: np.ndarray, spoilage: np.ndarray,
                  local: LocalGoods) -> TemplateRows:
    """The rows of the priced needs. `life` and `spoilage` are the goods' service life and spoilage by good number (0 for a good with no spec)."""
    arrays = priced.columns.arrays
    positions = np.array(priced.positions, dtype=np.int64)
    first, stop = arrays.start[positions], arrays.stop[positions]
    rows = selected_rows(first, stop)
    good_numbers = arrays.good[rows]
    floats = np.empty((len(rows), opening_kernel.RF_COUNT))
    floats[:, 0] = arrays.price[rows]
    floats[:, 1] = arrays.effect[rows]
    floats[:, 2] = arrays.share[rows]
    floats[:, 3] = arrays.ceiling[rows]
    floats[:, 4] = arrays.quality[rows]
    floats[:, 5] = 0.0
    floats[:, 6] = life[good_numbers]
    floats[:, 7] = spoilage[good_numbers]
    floats[:, 8] = 0.0
    floats[:, 9] = arrays.limit[rows]
    counts = stop - first
    priority = np.repeat(np.where(np.array(floors_positive, dtype=bool), 0, 1), counts)
    return TemplateRows(floats, local.of(good_numbers), first_unit_by_good[good_numbers], priority,
                        np.argsort(GOODS.rank_array()[good_numbers], kind="stable"), good_numbers, counts)
