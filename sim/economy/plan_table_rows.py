"""The rows of a `PlanTable` (plan_table.py), read from the plan kernel's answer and from the `Plan` objects `producers.plan` gives the
producers the kernel leaves out, then merged into producer order.

A block is `(bid position, bid good, bid tile, bid area, bid priority, bid figures, labour position, labour trade, labour area,
labour hours, labour maximum wage)`; goods, tiles, areas and trades are places in the `LocalNames` lists (a name the kernel's arrays
did not hold is appended)."""
from typing import Dict, List

import numpy as np

from .plan_table import BidColumns, LabourColumns
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
    for good_place, tile_place in sorted({(good[row], tile[row]) for row in missing.tolist()}):
        place = names.place(2, view.area_of(names.goods[good_place], names.tiles[tile_place]))
        area[missing[(good[missing] == good_place) & (tile[missing] == tile_place)]] = place


def _labour_areas(trade: np.ndarray, tile: np.ndarray, view, trade_names, names: LocalNames) -> np.ndarray:
    """The place in the area names of the labour area of each labour bid, asked of the view once per distinct (trade, tile)."""
    area_of: Dict[tuple, int] = {}
    found = []
    for pair in zip(trade.tolist(), tile.tolist()):
        area = area_of.get(pair)
        if area is None:
            area = area_of[pair] = names.place(2, view.area_of(trade_names[pair[0]], names.tiles[pair[1]]))
        found.append(area)
    return np.array(found, dtype=np.int64)


def kernel_rows(columns, matrices, area_index, view, names: LocalNames, rows: np.ndarray, running: np.ndarray, hours, ceilings,
                quantity, bid_price, budget, worth) -> tuple:
    """The block of the rows the kernel planned: an input bid for each input slot with a positive quantity and a labour bid for each
    hired trade slot of every running row, rows in order and slots in slot order."""
    recipe_rows = columns.recipe_row[rows]
    bought = (matrices.slot_goods >= 0) & matrices.slot_is_input
    owner, slot = np.nonzero(bought[recipe_rows] & (quantity > 0.0) & running[:, None])
    position = rows[owner]
    good = matrices.slot_goods[recipe_rows[owner], slot]
    tile = columns.tile_row[position]
    area = area_index.of_good_tile[good, tile]
    _areas_of_missing(area, good, tile, view, names)
    figures = np.zeros((len(owner), _BID_FIGURES))
    figures[:, 0], figures[:, 2] = quantity[owner, slot], bid_price[owner, slot]
    figures[:, 4], figures[:, 5] = budget[owner, slot], worth[owner, slot]
    trade_columns = np.where(matrices.slot_trades >= 0, matrices.slot_trades, 0)
    hired = (matrices.slot_trades >= 0) & (np.take_along_axis(matrices.labour_hours, trade_columns, axis=1) > 0.0)
    labour_owner, labour_slot = np.nonzero(hired[recipe_rows] & running[:, None])
    labour_position = rows[labour_owner]
    labour_trade = matrices.slot_trades[recipe_rows[labour_owner], labour_slot]
    labour_area = _labour_areas(labour_trade, columns.tile_row[labour_position], view, matrices.trades.ids, names)
    labour_trade_place = np.array([names.place(3, matrices.trades.ids[trade]) for trade in labour_trade.tolist()], dtype=np.int64)
    return (position, good, tile, area, np.zeros(len(owner), dtype=np.int64), figures, labour_position, labour_trade_place, labour_area,
            hours[labour_owner, labour_slot], ceilings[labour_owner, labour_slot])


def object_rows(position: int, plan, names: LocalNames) -> tuple:
    """The block of one producer planned by `producers.plan`: its `Bid`s and `LabourBid`s read into rows (every other producer's go
    through `kernel_rows`; a few producers have recipes the kernel leaves out)."""
    bids = plan.bids
    figures = np.array([(bid.floor_quantity, bid.flexible_quantity, bid.reference_price, bid.elasticity, bid.budget, bid.maximum_price)
                        for bid in bids], dtype=np.float64).reshape(-1, _BID_FIGURES)
    labour = plan.labour_bids
    return (np.full(len(bids), position, dtype=np.int64), np.array([names.place(0, bid.good) for bid in bids], dtype=np.int64),
            np.array([names.place(1, bid.tile) for bid in bids], dtype=np.int64),
            np.array([names.place(2, bid.area) for bid in bids], dtype=np.int64),
            np.array([bid.priority for bid in bids], dtype=np.int64), figures, np.full(len(labour), position, dtype=np.int64),
            np.array([names.place(3, bid.trade) for bid in labour], dtype=np.int64),
            np.array([names.place(2, bid.area) for bid in labour], dtype=np.int64), np.array([bid.hours for bid in labour], dtype=np.float64),
            np.array([bid.maximum_wage for bid in labour], dtype=np.float64))


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
