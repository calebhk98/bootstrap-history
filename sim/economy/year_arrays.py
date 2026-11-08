"""The year's arrays: the producers', cohorts' and market memory's numeric fields as columns with id-to-row maps, built
once a year (`Economy._run_year`) and read by every ported phase, so a phase does not pack the records itself.

    arrays = YearArrays.build(setup, record, area_map, view)    # the year's start
    arrays.sync(record, view)                                   # before a phase reads: producers entered, left or were replaced

Rows are in sorted id order. `producers` follows the producer table through the records' identity (a producer is a
frozen record the table replaces, so a replaced row is re-read and a changed set of ids rebuilds the columns);
`cohorts` and `memory` are read again whole by `sync`. The saved record is not changed by any of this.
See year_arrays_recipes.py, year_arrays_producers.py, year_arrays_cohorts.py and year_arrays_memory.py."""
from dataclasses import dataclass

import numpy as np

from .setup import labour_area
from .year_arrays_cohorts import CohortColumns
from .year_arrays_memory import AreaIndex, MemoryArrays
from .year_arrays_producers import ProducerColumns
from .year_arrays_recipes import Names, RecipeMatrices, build_recipe_matrices


def tiles_of(record, setup=None) -> Names:
    """Every tile a producer or cohort is on, and every tile of the setup (a newcomer may be sited on a tile nobody is on yet)."""
    return Names.of([each.tile for each in record.producers.values()] + [each.tile for each in record.cohorts.values()]
                    + list(getattr(setup, "tiles", ())))


def wage_grid(setup, view, trades: Names, tiles: Names) -> np.ndarray:
    """`trade_wages.wage_in_view` for every trade and tile, as a (trade by tile) grid. A view that reads the wage rule in blocks
    (`YearView.wage_rule_block`) gives it in one kernel call; any other view is read cell by cell (`wage_grid_by_cells`)."""
    block = getattr(view, "wage_rule_block", None)
    if block is None or getattr(view, "setup", None) is not setup:
        return wage_grid_by_cells(setup, view, trades, tiles)
    return block(trades.ids, [labour_area(tile) for tile in tiles.ids]).reshape(len(trades.ids), len(tiles.ids))


def wage_grid_by_cells(setup, view, trades: Names, tiles: Names) -> np.ndarray:
    """`wage_grid` read one cell at a time: the wage rule's three cases worked out per trade (what it holds, the opening wage, the
    premium) and per tile (the unskilled wage), then applied cell by cell."""
    from .trade_wages import priced_trade_wage
    areas = [labour_area(tile) for tile in tiles.ids]
    unskilled = [view.wage(setup.unskilled_trade, area) for area in areas]
    level = view.opening_wage_level(setup.currency_id)
    grid = np.empty((len(trades.ids), len(tiles.ids)))
    for row, trade in enumerate(trades.ids):
        held = view.wage_held_anywhere(trade)
        for column, area in enumerate(areas):
            grid[row, column] = priced_trade_wage(setup, trade, view.wage(trade, area), unskilled[column], level, held)
    return grid


def _memory_arrays(setup, matrices: RecipeMatrices, tiles: Names, area_index: AreaIndex, record, view, previous=None) -> MemoryArrays:
    if previous is not None and previous.is_current(record.memory):      # nothing was written since: the same answer
        return previous
    from .trade_wages import wage_in_view
    return MemoryArrays.build(record.memory, matrices.goods, matrices.trades, tiles, area_index, setup.currency_id,
                              lambda trade, tile: wage_in_view(setup, view, trade, labour_area(tile)),
                              wage_grid(setup, view, matrices.trades, tiles))


def _held(collection) -> tuple:
    return tuple(collection.items()) if hasattr(collection, "items") else tuple((each, each) for each in collection)


def source_of(setup) -> tuple:
    """What the recipe matrices are built from: the setup's recipes and goods specs, as (name, record) pairs (the tile names are compared apart)."""
    return tuple(_held(getattr(setup, name, ())) for name in ("recipes", "specs"))


def same_source(first: tuple, second: tuple) -> bool:
    """Whether two `source_of` answers hold the very same records under the same names."""
    return len(first) == len(second) and all(
        len(old) == len(new) and all(a[0] == b[0] and a[1] is b[1] for a, b in zip(old, new)) for old, new in zip(first, second))


@dataclass
class YearArrays:
    matrices: RecipeMatrices
    tiles: Names
    area_index: AreaIndex
    producers: ProducerColumns
    cohorts: CohortColumns
    memory: MemoryArrays
    area_map: object
    source: tuple = ()               # `source_of(setup)` when the matrices were built (`carried` checks it)

    @classmethod
    def build(cls, setup, record, area_map, view) -> "YearArrays":
        service_lives = {good: spec.service_life_years for good, spec in setup.specs.items()}
        matrices = build_recipe_matrices(setup.recipes, service_lives, [good for good in setup.specs])
        tiles = tiles_of(record, setup)
        area_index = AreaIndex.build(area_map, matrices.goods, tiles)
        return cls(matrices, tiles, area_index, ProducerColumns.build(record.producers, matrices, tiles),
                   CohortColumns.build(record.cohorts, tiles), _memory_arrays(setup, matrices, tiles, area_index, record, view),
                   area_map, source_of(setup))

    @classmethod
    def carried(cls, previous, setup, record, area_map, view) -> "YearArrays":
        """The arrays of the year that closed, brought in step with the record now: what is built from the setup's recipes, goods and
        tiles and from the area map is kept while those are the same records, the producers and cohorts are read where they changed,
        the memory read again if anything was written to it (`MemoryArrays.is_current`). Anything else changed: `build`."""
        if (previous is None or previous.area_map is not area_map or not same_source(previous.source, source_of(setup))
                or tiles_of(record, setup).ids != previous.tiles.ids):
            return cls.build(setup, record, area_map, view)
        return previous.sync(setup, record, view)

    def sync(self, setup, record, view) -> "YearArrays":
        """The arrays in step with the record now: producers replaced, entered or left; cohorts and the memory read again.
        A tile no array knows (a producer founded on a new tile) rebuilds the lot."""
        try:
            producers = self.producers.refresh(record.producers)
            cohorts = CohortColumns.build(record.cohorts, self.tiles)
        except KeyError:
            return YearArrays.build(setup, record, self.area_map, view)
        memory = _memory_arrays(setup, self.matrices, self.tiles, self.area_index, record, view, self.memory)
        return YearArrays(self.matrices, self.tiles, self.area_index, producers, cohorts, memory, self.area_map, self.source)
