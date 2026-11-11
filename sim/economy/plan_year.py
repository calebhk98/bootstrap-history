"""The year's plans for every producer: one kernel call over the year arrays (`plan_kernel.plan_rows`), read into a `PlanTable`.

`plans_of(setup, record, view, arrays, money)` is the `PlanTable` of every producer in sorted id order: columns for the runs, the runs
wanted, the wage line and the sums the outlay room and the land bids read, rows for the input bids and the labour bids (plan_table.py).
Every producer is planned by the kernel, whatever its recipe (tool wear and fallbacks, zero entries) and whatever its crew's practice
does to the recipe's hours. `write_bids` appends the input bids to the book of orders as rows. The stocks the kernel reads are one block
read of the book (stock_block.py)."""
import numpy as np

from . import producer_numbers, producers
from .inventory import DEFAULT_MONTHS_OF_COVER
from .plan_kernel import plan_rows
from .plan_table import PlanTable
from .plan_table_rows import LocalNames, merged, kernel_rows
from .stock_block import stock_block


def stocks_by_slot(record, columns, matrices, tools, rows) -> np.ndarray:
    """Stock held by row and bid place: the recipe's good slots that are an input or an output of the row's recipe, then the fallback goods
    that are not inputs (`ToolTables.bid_goods`); one block read of the book (`stock_block`) over the cells of every row."""
    stock = np.zeros((len(rows), tools.bid_goods.shape[1]))
    if not len(rows):
        return stock
    recipe_rows = columns.recipe_row[rows]
    slots = matrices.good_slots
    held = np.zeros(tools.bid_goods.shape, dtype=bool)
    held[:, :slots] = (matrices.slot_goods >= 0) & (matrices.slot_is_input | matrices.slot_is_output)
    held[:, slots:] = tools.bid_goods[:, slots:] >= 0
    owner, place = np.nonzero(held[recipe_rows])
    book = record.book
    agent_of_row, tile_of_row = producer_numbers.of_columns(columns, book)
    agents, tiles = agent_of_row[rows], tile_of_row[columns.tile_row[rows]]
    goods = producer_numbers.of_goods(matrices.goods, book)[tools.bid_goods[recipe_rows[owner], place]]
    stock[owner, place] = stock_block(book, agents[owner], goods, tiles[owner])
    return stock


def plans_of(setup, record, view, arrays, money) -> PlanTable:
    """Every producer's plan, in sorted id order, as a `PlanTable` (see the module docstring)."""
    columns = arrays.producers.refresh(record.producers)
    matrices, memory, tools = arrays.matrices, arrays.memory, arrays.tools
    rows = np.arange(len(columns.ids))
    ids = columns.ids
    cash = record.book.balances_at(producer_numbers.of_columns(columns, record.book)[0][rows], money)
    stock = stocks_by_slot(record, columns, matrices, tools, rows)
    (runs, wanted, line, hours, ceilings, bid_good, quantity, bid_price, budget, worth) = plan_rows(
        columns.recipe_row, columns.tile_row, columns.capacity_runs, columns.yield_factor, columns.land_rent_per_run, columns.land_run_cap,
        columns.expected_sales, columns.last_runs, columns.staffed_runs, columns.idle_years, columns.expected_prices, cash, stock,
        columns.hours_scale, tools, matrices.slot_goods, matrices.slot_trades, matrices.inputs, matrices.outputs, arrays.revenue_outputs, matrices.labour_hours,
        memory.price, memory.offered, memory.cleared, memory.wage, arrays.area_index.of_good_tile, producers.COST_SPREAD_WITHIN_PRODUCER,
        producers.OUTPUT_CHANGE_SHARE_PER_YEAR, producers.STOCK_CLEARING_YEARS, DEFAULT_MONTHS_OF_COVER)
    idle = runs <= 0.0              # an idle plan has no runs, no wage line and no orders
    names = LocalNames(matrices.goods.ids, columns.tiles.ids, arrays.area_index.areas.ids, matrices.trades.ids)
    block = kernel_rows(columns, matrices, arrays.area_index, view, names, rows, ~idle, hours, ceilings, bid_good, quantity, bid_price, budget,
                        worth)
    bids, labour = merged([block])
    return PlanTable(ids, np.where(idle, 0.0, runs).tolist(), wanted.tolist(), np.where(idle, 0.0, line), bids, labour, names.goods, names.tiles,
                     names.areas, {}, names.trades)
