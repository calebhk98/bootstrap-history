"""The year's plans for every producer: one kernel call over the year arrays (`plan_kernel.plan_rows`), read into a `PlanTable`.

`plans_of(setup, record, view, arrays, money)` is the `PlanTable` of every producer in sorted id order: columns for the runs, the runs
wanted, the wage line and the sums the outlay room and the land bids read, rows for the input bids and the labour bids (plan_table.py).
A producer whose recipe has tool fallbacks or tool wear, a zero quantity or hour entry, or whose crew's practice stretches the recipe's
hours is planned by `producers.plan` itself, and its `Plan` is read into the same columns. `write_bids` appends the input bids to the
book of orders as rows. The stocks the kernel reads are one block read of the book (stock_block.py)."""
from typing import Dict

import numpy as np

from . import producer_numbers, producers
from .inventory import DEFAULT_MONTHS_OF_COVER
from .plan_kernel import plan_rows
from .plan_table import PlanTable
from .plan_table_rows import LocalNames, merged, object_rows, kernel_rows
from .stock_block import stock_block

_simple: Dict[int, tuple] = {}      # id of the recipes mapping -> (mapping, recipe id -> whether the kernel plans it)


def simple_recipes(recipes) -> Dict[str, bool]:
    """Which recipes the kernel plans: no tool fallbacks or wear, every input, output and hour entry positive."""
    kept = _simple.get(id(recipes))
    if kept is None or kept[0] is not recipes or kept[2] != len(recipes):
        flags = {recipe_id: not recipe.tool_fallbacks and not recipe.tool_wear
                 and all(quantity > 0.0 for quantity in recipe.inputs.values())
                 and all(quantity > 0.0 for quantity in recipe.outputs.values())
                 and all(quantity > 0.0 for quantity in recipe.labour_hours.values())
                 for recipe_id, recipe in recipes.items()}
        kept = _simple[id(recipes)] = (recipes, flags, len(recipes))
    return kept[1]


def stocks_by_slot(record, columns, matrices, rows, slots: int) -> np.ndarray:
    """Stock held by row and good slot, for the slots that are an input or an output of the row's recipe: one block read of the book
    (`stock_block`) over the cells of every row."""
    stock = np.zeros((len(rows), slots))
    if not len(rows):
        return stock
    recipe_rows = columns.recipe_row[rows]
    held = (matrices.slot_goods >= 0) & (matrices.slot_is_input | matrices.slot_is_output)
    owner, slot = np.nonzero(held[recipe_rows])
    book = record.book
    agent_of_row, tile_of_row = producer_numbers.of_columns(columns, book)
    agents, tiles = agent_of_row[rows], tile_of_row[columns.tile_row[rows]]
    goods = producer_numbers.of_goods(matrices.goods, book)[matrices.slot_goods[recipe_rows[owner], slot]]
    stock[owner, slot] = stock_block(book, agents[owner], goods, tiles[owner])
    return stock


def plans_of(setup, record, view, arrays, money) -> PlanTable:
    """Every producer's plan, in sorted id order, as a `PlanTable`: the kernel's plans as columns, the plans of the producers it leaves
    to `producers.plan` (see the module docstring) as their `Plan` objects read into the same columns."""
    columns = arrays.producers.refresh(record.producers)
    matrices, memory = arrays.matrices, arrays.memory
    flags = simple_recipes(setup.recipes)
    recipes = setup.recipes
    simple_row = np.array([flags[recipe_id] for recipe_id in matrices.recipes.ids], dtype=bool)
    is_plain = simple_row[columns.recipe_row] & (columns.hours_scale == 1.0).all(axis=1)      # no practice stretches the recipe's hours
    rows = np.flatnonzero(is_plain)
    ids = columns.ids
    cash = record.book.balances_at(producer_numbers.of_columns(columns, record.book)[0][rows], money)
    stock = stocks_by_slot(record, columns, matrices, rows, matrices.good_slots)
    (runs, wanted, line, hours, ceilings, quantity, bid_price, budget, worth) = plan_rows(
        columns.recipe_row[rows], columns.tile_row[rows], columns.capacity_runs[rows], columns.yield_factor[rows],
        columns.land_rent_per_run[rows], columns.land_run_cap[rows], columns.expected_sales[rows], columns.last_runs[rows],
        columns.staffed_runs[rows], columns.idle_years[rows], columns.expected_prices[rows], cash, stock, matrices.slot_goods,
        matrices.slot_trades, matrices.inputs, matrices.outputs, matrices.labour_hours, memory.price, memory.offered,
        memory.cleared, memory.wage, arrays.area_index.of_good_tile, producers.COST_SPREAD_WITHIN_PRODUCER,
        producers.OUTPUT_CHANGE_SHARE_PER_YEAR, producers.STOCK_CLEARING_YEARS, DEFAULT_MONTHS_OF_COVER)
    count = len(ids)
    idle = runs <= 0.0              # an idle plan has no runs, no wage line and no orders
    runs_all, wanted_all, line_all = np.zeros(count), np.zeros(count), np.zeros(count)
    runs_all[rows], wanted_all[rows], line_all[rows] = np.where(idle, 0.0, runs), wanted, np.where(idle, 0.0, line)
    names = LocalNames(matrices.goods.ids, columns.tiles.ids, arrays.area_index.areas.ids, matrices.trades.ids)
    blocks = [kernel_rows(columns, matrices, arrays.area_index, view, names, rows, ~idle, hours, ceilings, quantity, bid_price, budget, worth)]
    objects: Dict[int, producers.Plan] = {}
    for position in np.flatnonzero(~is_plain).tolist():
        producer_id = ids[position]
        producer = record.producers[producer_id]
        objects[position] = plan = producers.plan(producer, recipes[producer.recipe_id], view, record.book.balance(producer_id, money))
        runs_all[position], wanted_all[position], line_all[position] = plan.runs, plan.wanted_runs, plan.wage_line
        blocks.append(object_rows(position, plan, names))
    bids, labour = merged(blocks)
    return PlanTable(ids, runs_all.tolist(), wanted_all.tolist(), line_all, bids, labour, names.goods, names.tiles, names.areas, objects,
                     names.trades)
