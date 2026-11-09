"""The producers' numeric fields as the year's columns, one row per producer in sorted id order.

`ProducerColumns.of(store, matrices, tiles)` reads the producer table's columns (producer_store.py) in blocks: a name is turned
into the year's numbering (recipe row, tile row) through a lookup array, the expected prices are laid out by the recipe's good
slot, and the crew's practice becomes the hours multiplier of each trade. No `Producer` is built. The table is the store: a phase
that changes producers writes the store, and `refresh` reads the store again when its `version` rose (the same object when
nothing was written). `rows` says which store row each column row is, valid until the store is compacted."""
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Tuple

import numpy as np

from .practice import practised_multiplier
from .producer_blocks import crews_of
from .producer_store import ProducerStore
from .year_arrays_recipes import NO_SLOT, Names, RecipeMatrices


def _lookup(names: List[str], row_of: Mapping[str, int], used: np.ndarray, what: str) -> np.ndarray:
    """For each store number, its row in the year's numbering (-1 for a name the year has no row for); a name in `used` with no row
    is a KeyError, as a producer on a tile or recipe the arrays do not know has always been."""
    found = np.array([row_of.get(name, -1) for name in names], dtype=np.int64)
    if len(used) and (found[used] < 0).any():
        raise KeyError("no %s row for %s" % (what, names[int(used[found[used] < 0][0])]))
    return found


@dataclass
class ProducerColumns:
    ids: Tuple[str, ...]
    row: Dict[str, int]
    rows: np.ndarray                  # the store row of each row here
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
    owner_number: np.ndarray = None   # the owner's number in the store's `owners` names
    tile_number: np.ndarray = None    # the tile's number in the store's `tiles` names
    crews: Dict[int, Dict[str, float]] = field(repr=False, default_factory=dict)   # row here -> the crew's practice, for a producer that has one
    store: ProducerStore = field(repr=False, default=None)
    version: int = -1                 # the store's `version` when these were read
    layout: int = -1                  # the store's `layout` when these were read: `rows` mean the same rows while it is the same
    matrices: RecipeMatrices = field(repr=False, default=None)
    tiles: Names = field(repr=False, default=None)

    @classmethod
    def build(cls, producers: Mapping[str, object], matrices: RecipeMatrices, tiles: Names) -> "ProducerColumns":
        """The columns of a producer table (a plain mapping of records is made a store first)."""
        store = producers if isinstance(producers, ProducerStore) else ProducerStore(producers)
        return cls.of(store, matrices, tiles)

    @classmethod
    def of(cls, store: ProducerStore, matrices: RecipeMatrices, tiles: Names) -> "ProducerColumns":
        """Every column read from the store's table in sorted id order (the store is compacted first)."""
        order = store.order()
        table = store.table
        ids = tuple(map(store.ids.__getitem__, order.tolist()))
        recipe_numbers, tile_numbers = table.recipe[order], table.tile[order]
        recipe_row = _lookup(store.names["recipes"].name_list, matrices.recipes.row, np.unique(recipe_numbers), "recipe")[recipe_numbers]
        tile_row = _lookup(store.names["tiles"].name_list, tiles.row, np.unique(tile_numbers), "tile")[tile_numbers]
        counts = table.earnings_count[order]
        width = max(1, int(counts.max()) if len(counts) else 0, int(table.revenue_count[order].max()) if len(order) else 0)
        earnings = _padded(table.earnings_history, order, width)
        revenue = _padded(table.revenue_history, order, width)
        columns = cls(ids, {each: position for position, each in enumerate(ids)}, order, recipe_row, tile_row,
                      table.capacity_runs[order], table.yield_factor[order], table.years_of_loss[order], table.cash_target[order],
                      table.expected_sales[order], table.last_runs[order], table.land_rent_per_run[order], table.land_run_cap[order],
                      table.workshops[order], table.idle_years[order], table.staffed_runs[order], earnings, revenue, counts.copy(),
                      _expected_prices(store, order, recipe_row, matrices), _hours_scale(store, order, matrices),
                      table.owner[order], tile_numbers, _crews(store, order), store, store.version, store.layout, matrices, tiles)
        return columns

    def owners(self) -> List[str]:
        """Each producer's owner, by row."""
        return self.store.name_of("owners", self.owner_number)

    def tile_names(self) -> List[str]:
        """Each producer's tile, by row."""
        return self.store.name_of("tiles", self.tile_number)

    def refresh(self, producers: Mapping[str, object]) -> "ProducerColumns":
        """Columns in step with the table: this object when nothing was written since it was read, else read again."""
        store = producers if isinstance(producers, ProducerStore) else ProducerStore(producers)
        if store is self.store and store.version == self.version and not store._dead:
            return self
        return ProducerColumns.of(store, self.matrices, self.tiles)


def _padded(column: np.ndarray, rows: np.ndarray, width: int) -> np.ndarray:
    """The rows of a history column, `width` places wide (zero past what the row holds)."""
    taken = column[rows]
    if taken.shape[1] >= width:
        return taken[:, :width].copy()
    return np.concatenate([taken, np.zeros((len(rows), width - taken.shape[1]))], axis=1)


def _expected_prices(store: ProducerStore, rows: np.ndarray, recipe_row: np.ndarray, matrices: RecipeMatrices) -> np.ndarray:
    """producer by the recipe's good slot: the price the producer expects for the slot's good, NaN where it holds none. A price for
    a good outside the recipe's slots is not a column."""
    table = store.table
    prices = np.full((len(rows), matrices.good_slots), np.nan)
    held = table.price_count[rows]
    if not len(rows) or not held.max():
        return prices
    names, held_goods = store.names["goods"].name_list, table.price_good[rows]
    column_of = np.full(len(names) + 1, -1, dtype=np.int64)
    places = np.arange(table.price_good.shape[1])[None, :] < held[:, None]
    for number in np.nonzero(np.bincount(held_goods[places]))[0].tolist():          # only the goods some producer holds a price for
        if number < len(names):
            column_of[number] = matrices.goods.row.get(names[number], -1)
    goods = np.where(places, column_of[held_goods], -1)          # the year's good column of each held price
    values = table.price_value[rows]
    slots = matrices.slot_goods[recipe_row]
    match = (goods[:, :, None] == slots[:, None, :]) & (slots != NO_SLOT)[:, None, :]      # producer by held price by slot, all slots at once
    has = match.any(axis=1)
    first = match.argmax(axis=1)                  # the first held price that is the slot's good
    chosen = np.take_along_axis(values, first, axis=1)
    prices[has] = chosen[has]
    return prices


def _crews(store: ProducerStore, rows: np.ndarray) -> Dict[int, Dict[str, float]]:
    """{row here: the crew's practice} for the producers that have a crew."""
    crewed = np.nonzero(store.table.crew_count[rows] > 0)[0]
    return dict(zip(crewed.tolist(), crews_of(store, rows[crewed])))


def _hours_scale(store: ProducerStore, rows: np.ndarray, matrices: RecipeMatrices) -> np.ndarray:
    """producer by trade column: `practice.practised_multiplier` of the crew's runs at the trade, one for a trade with no practice figure."""
    table = store.table
    scale = np.ones((len(rows), len(matrices.trades.ids)))
    crewed = np.nonzero(table.crew_count[rows] > 0)[0]
    if not len(crewed):
        return scale
    trade_names = store.names["trades"].name_list
    multiplier: Dict[float, float] = {}
    for position in crewed.tolist():
        row = int(rows[position])
        for number, units in zip(table.crew_trade[row, :table.crew_count[row]].tolist(), table.crew_units[row, :table.crew_count[row]].tolist()):
            column = matrices.trades.row.get(trade_names[number])
            if column is not None:
                if units not in multiplier:
                    multiplier[units] = practised_multiplier(units)
                scale[position, column] = multiplier[units]
    return scale
