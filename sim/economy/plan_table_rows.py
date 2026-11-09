"""The rows of a `PlanTable` (plan_table.py), read from the plan kernel's answer, then merged into producer order.

A block is `(bid position, bid good, bid tile, bid area, bid priority, bid figures, labour position, labour trade, labour area,
labour hours, labour maximum wage)`; goods, tiles, areas and trades are places in the `LocalNames` lists (a name the kernel's arrays
did not hold is appended)."""
from typing import List

import numpy as np

from .plan_table import BidColumns, LabourColumns
from .view_areas import areas_of_pairs
from .year_arrays_memory import NO_AREA

_BID_FIGURES = 6


class LocalNames:
    """The good, tile and area names the table's index columns point into: the year arrays' own, with any other name appended."""

    def __init__(self, goods, tiles, areas, trades=()):
        self.goods, self.tiles, self.areas, self.trades = list(goods), list(tiles), list(areas), list(trades)
        self._found = tuple({name: place for place, name in enumerate(names)} for names in (self.goods, self.tiles, self.areas, self.trades))

    def place(self, kind: int, name: str) -> int:
        """The place of `name` among the goods (kind 0), tiles (1), areas (2) or trades (3)."""
        found, names = self._found[kind], (self.goods, self.tiles, self.areas, self.trades)[kind]
        place = found.get(name)
        if place is None:
            place = found[name] = len(names)
            names.append(name)
        return place


def _areas_of_missing(area: np.ndarray, good: np.ndarray, tile: np.ndarray, view, names: LocalNames) -> None:
    """Fill the bids whose (good, tile) the year arrays hold no area for (`NO_AREA`) from the view, one call per distinct pair."""
    missing = np.flatnonzero(area == NO_AREA)
    if not len(missing):
        return
    asked = sorted({(good[row], tile[row]) for row in missing.tolist()})
    areas = areas_of_pairs(view, [names.goods[good_place] for good_place, _tile in asked], [names.tiles[tile_place] for _good, tile_place in asked])
    for (good_place, tile_place), area_name in zip(asked, areas):
        place = names.place(2, area_name)
        area[missing[(good[missing] == good_place) & (tile[missing] == tile_place)]] = place


def _labour_areas(trade: np.ndarray, tile: np.ndarray, view, trade_names, names: LocalNames) -> np.ndarray:
    """The place in the area names of the labour area of each labour bid, asked of the view once per distinct (trade, tile)."""
    if not len(trade):
        return np.empty(0, dtype=np.int64)
    pairs, inverse = np.unique(np.stack([trade, tile], axis=1), axis=0, return_inverse=True)
    asked = areas_of_pairs(view, [trade_names[pair_trade] for pair_trade, _tile in pairs.tolist()],
                           [names.tiles[pair_tile] for _trade, pair_tile in pairs.tolist()])
    areas = np.array([names.place(2, area) for area in asked], dtype=np.int64)       # numbered in the order of the pairs
    return areas[inverse.reshape(-1)]


def kernel_rows(columns, matrices, area_index, view, names: LocalNames, rows: np.ndarray, running: np.ndarray, hours, ceilings,
                bid_good, quantity, bid_price, budget, worth) -> tuple:
    """The block of the rows the kernel planned: an input bid for each need of every running row (`bid_good` is the good's column, -1 where
    there is no such bid) and a labour bid for each trade slot with hours (NaN: none) of every running row, rows in order and the bids of a
    row in the order the plan made them."""
    owner, place = np.nonzero((bid_good >= 0) & running[:, None])
    position = rows[owner]
    good = bid_good[owner, place]
    tile = columns.tile_row[position]
    area = area_index.of_good_tile[good, tile]
    _areas_of_missing(area, good, tile, view, names)
    figures = np.zeros((len(owner), _BID_FIGURES))
    figures[:, 0], figures[:, 2] = quantity[owner, place], bid_price[owner, place]
    figures[:, 4], figures[:, 5] = budget[owner, place], worth[owner, place]
    recipe_rows = columns.recipe_row[rows]
    labour_owner, labour_slot = np.nonzero(~np.isnan(hours) & running[:, None])
    labour_position = rows[labour_owner]
    labour_trade = matrices.slot_trades[recipe_rows[labour_owner], labour_slot]
    labour_area = _labour_areas(labour_trade, columns.tile_row[labour_position], view, matrices.trades.ids, names)
    labour_trade_place = labour_trade        # the names' trades start as the matrices' trades, in the same order
    return (position, good, tile, area, np.zeros(len(owner), dtype=np.int64), figures, labour_position, labour_trade_place, labour_area,
            hours[labour_owner, labour_slot], ceilings[labour_owner, labour_slot])


def merged(blocks: List[tuple]) -> tuple:
    """(`BidColumns`, `LabourColumns`) of all the blocks together, rows sorted by producer position with the order inside a producer
    kept (a stable sort)."""
    bid_order = np.argsort(np.concatenate([block[0] for block in blocks]), kind="stable")
    labour_order = np.argsort(np.concatenate([block[6] for block in blocks]), kind="stable")
    bids = BidColumns(np.concatenate([block[0] for block in blocks])[bid_order], np.concatenate([block[1] for block in blocks])[bid_order],
                      np.concatenate([block[2] for block in blocks])[bid_order], np.concatenate([block[3] for block in blocks])[bid_order],
                      np.concatenate([block[4] for block in blocks])[bid_order], np.concatenate([block[5] for block in blocks])[bid_order])
    labour = LabourColumns(np.concatenate([block[6] for block in blocks])[labour_order],
                           np.concatenate([block[7] for block in blocks])[labour_order], np.concatenate([block[8] for block in blocks])[labour_order],
                           np.concatenate([block[9] for block in blocks])[labour_order], np.concatenate([block[10] for block in blocks])[labour_order])
    return bids, labour
