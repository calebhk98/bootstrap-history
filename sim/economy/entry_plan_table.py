"""The year's entry plans as a table: one row per newcomer to start, in the order the plans are applied.

Rows are written by the plan kernels (`entry_unmet_kernel.py`) and by `from_plans` for plans a rule still makes as `EntryPlan` objects;
`open_entrants` reads the columns. Recipe, tile and good are rows of the year arrays (`arrays.matrices.recipes`, `arrays.tiles`,
`arrays.matrices.goods`)."""
from typing import Sequence

import numpy

from sim.compiled_tables.spec import Column, TableSpec

from .entry import EntryPlan

ENTRY_PLANS = TableSpec("EntryPlans", (
    Column("recipe_row", numpy.int64, "the recipe the newcomer works", "recipe row of the year arrays"),
    Column("tile_row", numpy.int64, "the tile it is sited on", "tile row of the year arrays"),
    Column("good_col", numpy.int64, "the good whose market drew it", "good column of the year arrays"),
    Column("runs", numpy.float64, "yearly runs of capacity it is built for", "runs per year"),
    Column("yearly_return", numpy.float64, "its yearly return on capital the plant loan is priced from", "fraction per year"),
))
EntryPlans = ENTRY_PLANS.make_type(__name__)
NAMES = tuple(column.name for column in ENTRY_PLANS.columns)


def empty(capacity: int):
    """A table with room for `capacity` plans and none in it."""
    return ENTRY_PLANS.new_table(EntryPlans, max(1, capacity))


def count(plans) -> int:
    """How many plans the table holds."""
    return int(plans.row_count[0])


def joined(first, second):
    """The plans of `first` followed by those of `second`."""
    used_first, used_second = count(first), count(second)
    table = ENTRY_PLANS.new_table(EntryPlans, max(1, used_first + used_second), used_first + used_second)
    for name in NAMES:
        getattr(table, name)[:used_first] = getattr(first, name)[:used_first]
        getattr(table, name)[used_first:used_first + used_second] = getattr(second, name)[:used_second]
    return table


def from_plans(plans: Sequence, recipe_row, tile_row, good_col):
    """The table of `EntryPlan` objects (a rule not yet on tables makes them); `recipe_row`, `tile_row` and `good_col` map a name to its row."""
    return ENTRY_PLANS.table_of(
        EntryPlans, recipe_row=[recipe_row[each.recipe_id] for each in plans], tile_row=[tile_row[each.tile] for each in plans],
        good_col=[good_col[each.good] for each in plans], runs=[each.runs for each in plans],
        yearly_return=[each.yearly_return for each in plans])


def as_plans(plans, costs):
    """The plans as `EntryPlan` objects (for a test or a screen; the year's entry reads the columns)."""
    used = count(plans)
    recipe_ids, tile_ids, good_ids = costs.matrices.recipes.ids, costs.tiles.ids, costs.goods.ids
    return [EntryPlan(recipe_ids[recipe], tile_ids[tile], good_ids[good], runs, yearly_return) for recipe, tile, good, runs, yearly_return in zip(
        plans.recipe_row[:used].tolist(), plans.tile_row[:used].tolist(), plans.good_col[:used].tolist(), plans.runs[:used].tolist(),
        plans.yearly_return[:used].tolist())]


def markets_of(plans, costs) -> tuple:
    """(good, area id) of the market each plan was drawn by, the area being the good's area on the plan's tile."""
    used = count(plans)
    areas = costs.arrays.area_index.of_good_tile[plans.good_col[:used], plans.tile_row[:used]].tolist()
    area_ids, good_ids = costs.arrays.area_index.areas.ids, costs.goods.ids
    return tuple((good_ids[good], area_ids[area]) for good, area in zip(plans.good_col[:used].tolist(), areas))
