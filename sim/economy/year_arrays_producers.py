"""The producers' numeric fields as columns, one row per producer in sorted id order.

`ProducerColumns.build(producers, matrices, tiles)` reads every record once. `stale_rows` says which rows no longer
hold the record the table holds (producers are frozen records replaced through producer_table, so a replaced record is a
different object), and `refresh` re-reads those rows, or the whole table when the ids changed (entry or exit)."""
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Tuple

import numpy as np

from .practice import practised_multiplier
from .year_arrays_recipes import NO_SLOT, Names, RecipeMatrices


_MANY_ROWS = 64     # from this many rows a column is read in one pass
_COPIED = ("capacity_runs", "yield_factor", "years_of_loss", "cash_target", "expected_sales", "last_runs", "land_rent_per_run",
           "workshops", "idle_years")      # the columns that are a producer field of the same name
_PER_ROW = ("recipe_row", "tile_row", "capacity_runs", "yield_factor", "years_of_loss", "cash_target", "expected_sales", "last_runs",
            "land_rent_per_run", "land_run_cap", "workshops", "idle_years", "staffed_runs", "history_count", "expected_prices", "hours_scale")


@dataclass
class ProducerColumns:
    ids: Tuple[str, ...]
    row: Dict[str, int]
    records: List[object]
    recipe_row: np.ndarray
    tile_row: np.ndarray
    capacity_runs: np.ndarray
    yield_factor: np.ndarray
    years_of_loss: np.ndarray
    cash_target: np.ndarray
    expected_sales: np.ndarray
    last_runs: np.ndarray
    land_rent_per_run: np.ndarray
    land_run_cap: np.ndarray          # NaN: no limit
    workshops: np.ndarray
    idle_years: np.ndarray
    staffed_runs: np.ndarray          # NaN: unknown
    earnings_history: np.ndarray      # producer by year, oldest first, padded after `history_count`
    revenue_history: np.ndarray
    history_count: np.ndarray
    expected_prices: np.ndarray       # producer by the recipe's good slot; NaN: no expectation held
    hours_scale: np.ndarray           # producer by trade column: what its crew's practice multiplies the booked hours by (one: at the floor)
    matrices: RecipeMatrices = field(repr=False, default=None)
    tiles: Names = field(repr=False, default=None)

    @classmethod
    def _empty(cls, ids: Tuple[str, ...], records: List[object], history_width: int, matrices: RecipeMatrices,
               tiles: Names) -> "ProducerColumns":
        count = len(ids)
        return cls(
            ids, {each: position for position, each in enumerate(ids)}, records,
            np.zeros(count, dtype=np.int64), np.zeros(count, dtype=np.int64), np.zeros(count), np.zeros(count),
            np.zeros(count, dtype=np.int64), np.zeros(count), np.zeros(count), np.zeros(count), np.zeros(count),
            np.full(count, np.nan), np.zeros(count, dtype=np.int64), np.zeros(count, dtype=np.int64), np.full(count, np.nan),
            np.zeros((count, history_width)), np.zeros((count, history_width)), np.zeros(count, dtype=np.int64),
            np.full((count, matrices.good_slots), np.nan), np.ones((count, len(matrices.trades.ids))), matrices, tiles)

    @classmethod
    def build(cls, producers: Mapping[str, object], matrices: RecipeMatrices, tiles: Names) -> "ProducerColumns":
        ids = tuple(sorted(producers))
        history_width = max(1, max((len(producers[each].net_earnings_history) for each in ids), default=0),
                            max((len(producers[each].revenue_history) for each in ids), default=0))
        columns = cls._empty(ids, [producers[each] for each in ids], history_width, matrices, tiles)
        columns._read_many(list(range(len(ids))))
        return columns

    def _rebuilt(self, producers: Mapping[str, object]) -> "ProducerColumns":
        """The columns for a changed set of ids: a row whose record is the very one this table holds is copied, the others
        (entered or replaced) are read."""
        ids = tuple(sorted(producers))
        records = [producers[each] for each in ids]
        kept_new, kept_old, fresh = [], [], []
        for position, record in enumerate(records):
            old = self.row.get(ids[position])
            if old is not None and self.records[old] is record:
                kept_new.append(position)
                kept_old.append(old)
            else:
                fresh.append(position)
        width = max(self.earnings_history.shape[1], 1, max((len(records[each].net_earnings_history) for each in fresh), default=0),
                    max((len(records[each].revenue_history) for each in fresh), default=0))
        columns = ProducerColumns._empty(ids, records, width, self.matrices, self.tiles)
        kept_new, kept_old = np.array(kept_new, dtype=np.int64), np.array(kept_old, dtype=np.int64)
        for name in _PER_ROW:
            getattr(columns, name)[kept_new] = getattr(self, name)[kept_old]
        for name in ("earnings_history", "revenue_history"):
            getattr(columns, name)[kept_new, :self.earnings_history.shape[1]] = getattr(self, name)[kept_old]
        columns._read_many(fresh)
        return columns

    def read_scale(self, position: int) -> None:
        """The row's hours multipliers from its record's crew practice (`practice.recipe_for`'s multipliers, one where the crew is at the floor)."""
        self.hours_scale[position, :] = 1.0
        for trade, units in self.records[position].crew_runs.items():
            column = self.matrices.trades.row.get(trade)
            if column is not None:
                self.hours_scale[position, column] = practised_multiplier(units)

    def _read(self, position: int) -> None:
        producer = self.records[position]
        matrices = self.matrices
        recipe = matrices.recipes.row[producer.recipe_id]
        self.recipe_row[position] = recipe
        self.tile_row[position] = self.tiles.row[producer.tile]
        self.capacity_runs[position] = producer.capacity_runs
        self.yield_factor[position] = producer.yield_factor
        self.years_of_loss[position] = producer.years_of_loss
        self.cash_target[position] = producer.cash_target
        self.expected_sales[position] = producer.expected_sales
        self.last_runs[position] = producer.last_runs
        self.land_rent_per_run[position] = producer.land_rent_per_run
        self.land_run_cap[position] = np.nan if producer.land_run_cap is None else producer.land_run_cap
        self.workshops[position] = producer.workshops
        self.idle_years[position] = producer.idle_years
        self.staffed_runs[position] = np.nan if producer.staffed_runs is None else producer.staffed_runs
        for history, column in ((producer.net_earnings_history, self.earnings_history),
                                (producer.revenue_history, self.revenue_history)):
            column[position, :len(history)] = history
        self.history_count[position] = len(producer.net_earnings_history)
        slots = matrices.slot_goods[recipe]
        self.expected_prices[position, :] = np.nan
        self.read_scale(position)
        goods = matrices.goods.row
        held = producer.expected_prices
        for slot, good_row in enumerate(slots):
            if good_row == NO_SLOT:
                break
            price = held.get(matrices.goods.ids[good_row])
            if price is not None:
                self.expected_prices[position, slot] = price

    def _read_many(self, positions: List[int]) -> None:
        """`_read` for each position, a column at a time when there are many (one pass over the records per column)."""
        if len(positions) < _MANY_ROWS:
            for position in positions:
                self._read(position)
            return
        rows = np.array(positions, dtype=np.int64)
        records = [self.records[position] for position in positions]
        matrices = self.matrices
        recipe_rows, tile_rows = matrices.recipes.row, self.tiles.row
        self.recipe_row[rows] = recipe_rows_of = [recipe_rows[each.recipe_id] for each in records]
        self.tile_row[rows] = [tile_rows[each.tile] for each in records]
        for name in _COPIED:
            getattr(self, name)[rows] = [getattr(each, name) for each in records]
        self.land_run_cap[rows] = [np.nan if each.land_run_cap is None else each.land_run_cap for each in records]
        self.staffed_runs[rows] = [np.nan if each.staffed_runs is None else each.staffed_runs for each in records]
        self.history_count[rows] = [len(each.net_earnings_history) for each in records]
        width = self.earnings_history.shape[1]
        for column, attribute in ((self.earnings_history, "net_earnings_history"), (self.revenue_history, "revenue_history")):
            column[rows] = 0.0
            for position, each in zip(positions, records):
                history = getattr(each, attribute)
                if history:
                    column[position, :len(history)] = history
        self.expected_prices[rows] = np.nan
        self.hours_scale[rows] = 1.0
        for position, each in zip(positions, records):
            if each.crew_runs:
                self.read_scale(position)
        slot_goods = matrices.slot_goods
        goods_ids = matrices.goods.ids
        row_of, slot_of, price_of = [], [], []
        for position, each, recipe in zip(positions, records, recipe_rows_of):
            held = each.expected_prices
            if held:
                for slot, good_row in enumerate(slot_goods[recipe]):
                    if good_row == NO_SLOT:
                        break
                    price = held.get(goods_ids[good_row])
                    if price is not None:
                        row_of.append(position)
                        slot_of.append(slot)
                        price_of.append(price)
        self.expected_prices[row_of, slot_of] = price_of

    def stale_rows(self, producers: Mapping[str, object]) -> List[int]:
        """The rows whose record the table has replaced; None-like `[-1]` when the ids themselves changed."""
        if len(producers) != len(self.ids):
            return [-1]
        stale = []
        for position, each in enumerate(self.ids):
            record = producers.get(each)
            if record is None:
                return [-1]
            if record is not self.records[position]:
                stale.append(position)
        return stale

    def refresh(self, producers: Mapping[str, object]) -> "ProducerColumns":
        """Columns in step with the table: the same object with the replaced rows re-read, or a rebuilt one when producers
        entered or left."""
        stale = self.stale_rows(producers)
        if stale == [-1]:
            return self._rebuilt(producers)
        for position in stale:
            self.records[position] = producers[self.ids[position]]
        self._read_many(stale)
        return self
