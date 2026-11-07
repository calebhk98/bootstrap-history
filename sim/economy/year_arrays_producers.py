"""The producers' numeric fields as columns, one row per producer in sorted id order.

`ProducerColumns.build(producers, matrices, tiles)` reads every record once. `stale_rows` says which rows no longer
hold the record the table holds (producers are frozen records replaced through producer_table, so a replaced record is a
different object), and `refresh` re-reads those rows, or the whole table when the ids changed (entry or exit)."""
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Tuple

import numpy as np

from .year_arrays_recipes import NO_SLOT, Names, RecipeMatrices


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
    matrices: RecipeMatrices = field(repr=False, default=None)
    tiles: Names = field(repr=False, default=None)

    @classmethod
    def build(cls, producers: Mapping[str, object], matrices: RecipeMatrices, tiles: Names) -> "ProducerColumns":
        ids = tuple(sorted(producers))
        count = len(ids)
        history_width = max(1, max((len(producers[each].net_earnings_history) for each in ids), default=0),
                            max((len(producers[each].revenue_history) for each in ids), default=0))
        columns = cls(
            ids, {each: position for position, each in enumerate(ids)}, [producers[each] for each in ids],
            np.zeros(count, dtype=np.int64), np.zeros(count, dtype=np.int64), np.zeros(count), np.zeros(count),
            np.zeros(count, dtype=np.int64), np.zeros(count), np.zeros(count), np.zeros(count), np.zeros(count),
            np.full(count, np.nan), np.zeros(count, dtype=np.int64), np.zeros(count, dtype=np.int64), np.full(count, np.nan),
            np.zeros((count, history_width)), np.zeros((count, history_width)), np.zeros(count, dtype=np.int64),
            np.full((count, matrices.good_slots), np.nan), matrices, tiles)
        for position in range(count):
            columns._read(position)
        return columns

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
        goods = matrices.goods.row
        held = producer.expected_prices
        for slot, good_row in enumerate(slots):
            if good_row == NO_SLOT:
                break
            price = held.get(matrices.goods.ids[good_row])
            if price is not None:
                self.expected_prices[position, slot] = price

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
            return ProducerColumns.build(producers, self.matrices, self.tiles)
        for position in stale:
            self.records[position] = producers[self.ids[position]]
            self._read(position)
        return self
