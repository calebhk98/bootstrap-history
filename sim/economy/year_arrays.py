"""The year's arrays: the producers', cohorts' and market memory's numeric fields as columns with id-to-row maps, built
once a year (`Economy._run_year`) and read by every ported phase, so a phase does not pack the records itself.

    arrays = YearArrays.build(setup, record, area_map, view)    # the year's start
    arrays.sync(record, view)                                   # before a phase reads: producers entered, left or were replaced

Rows are in sorted id order. `producers` follows the producer table through the records' identity (a producer is a
frozen record the table replaces, so a replaced row is re-read and a changed set of ids rebuilds the columns);
`cohorts` and `memory` are read again whole by `sync`. The saved record is not changed by any of this.
See year_arrays_recipes.py, year_arrays_producers.py, year_arrays_cohorts.py and year_arrays_memory.py."""
from dataclasses import dataclass

from .setup import labour_area
from .year_arrays_cohorts import CohortColumns
from .year_arrays_memory import AreaIndex, MemoryArrays
from .year_arrays_producers import ProducerColumns
from .year_arrays_recipes import Names, RecipeMatrices, build_recipe_matrices


def tiles_of(record) -> Names:
    return Names.of([each.tile for each in record.producers.values()] + [each.tile for each in record.cohorts.values()])


def _memory_arrays(setup, matrices: RecipeMatrices, tiles: Names, area_index: AreaIndex, record, view) -> MemoryArrays:
    from .trade_wages import wage_in_view
    return MemoryArrays.build(record.memory, matrices.goods, matrices.trades, tiles, area_index, setup.currency_id,
                              lambda trade, tile: wage_in_view(setup, view, trade, labour_area(tile)))


@dataclass
class YearArrays:
    matrices: RecipeMatrices
    tiles: Names
    area_index: AreaIndex
    producers: ProducerColumns
    cohorts: CohortColumns
    memory: MemoryArrays
    area_map: object

    @classmethod
    def build(cls, setup, record, area_map, view) -> "YearArrays":
        service_lives = {good: spec.service_life_years for good, spec in setup.specs.items()}
        matrices = build_recipe_matrices(setup.recipes, service_lives, [good for good in setup.specs])
        tiles = tiles_of(record)
        area_index = AreaIndex.build(area_map, matrices.goods, tiles)
        return cls(matrices, tiles, area_index, ProducerColumns.build(record.producers, matrices, tiles),
                   CohortColumns.build(record.cohorts, tiles), _memory_arrays(setup, matrices, tiles, area_index, record, view),
                   area_map)

    def sync(self, setup, record, view) -> "YearArrays":
        """The arrays in step with the record now: producers replaced, entered or left; cohorts and the memory read again.
        A tile no array knows (a producer founded on a new tile) rebuilds the lot."""
        try:
            producers = self.producers.refresh(record.producers)
            cohorts = CohortColumns.build(record.cohorts, self.tiles)
        except KeyError:
            return YearArrays.build(setup, record, self.area_map, view)
        memory = _memory_arrays(setup, self.matrices, self.tiles, self.area_index, record, view)
        return YearArrays(self.matrices, self.tiles, self.area_index, producers, cohorts, memory, self.area_map)
