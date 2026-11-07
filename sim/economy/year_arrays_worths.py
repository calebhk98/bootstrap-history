"""The producers' net worths from the year arrays: the equity rule of `equity._built_worths` in one kernel.

`worths_from_arrays(setup, record, view, arrays)` gives what `equity._built_worths` gives. A producer's plant is its capacity times
the cost of a run's plant at its tile's prices and wages (read once per recipe and tile, in a grid, not per producer), its stock
is each good it holds at the price in its market (the book's quantities are packed in one pass, then priced in the kernel), and
the worth is cash plus plant plus stock less what it owes, not below nothing. A price or wage the memory lacks makes the plant
infinite (`unit_cost._bill`), as before."""
from typing import Dict

import math
import numpy as np

from sim.jit import njit

from . import credit_claims
from .year_arrays_costs import KERNEL, bill_goods, bill_hours, price_in
from .year_arrays_memory import price_grid
from .year_arrays_recipes import Names


@njit(**KERNEL)
def producer_worths(recipe_row, tile_row, capacity, cash, debt, eligible, stock_producer, stock_good, stock_quantity, extra_stock,
                    plant_goods, plant_labour_hours, plant_life, price, wage, area_of):
    """(worth by producer row, whether it has one). The stock lists are sorted by producer row, then good column; `extra_stock` is
    the value of goods the arrays have no column for, worked out by the caller."""
    count = len(recipe_row)
    stock = extra_stock.copy()
    for entry in range(len(stock_producer)):
        row = stock_producer[entry]
        found = price_in(price, area_of, stock_good[entry], tile_row[row])
        if found > 0.0:
            stock[row] += found * stock_quantity[entry]
    per_run = np.zeros((len(plant_life), wage.shape[1]))
    known = np.zeros((len(plant_life), wage.shape[1]), dtype=np.bool_)
    worth = np.zeros(count)
    has = np.zeros(count, dtype=np.bool_)
    for row in range(count):
        if not eligible[row] or not capacity[row] > 0.0:
            continue
        recipe, tile = recipe_row[row], tile_row[row]
        plant = 0.0
        if plant_life[recipe] > 0.0:
            if not known[recipe, tile]:
                per_run[recipe, tile] = bill_goods(plant_goods[recipe], price, area_of, tile) + bill_hours(plant_labour_hours[recipe], wage, tile)
                known[recipe, tile] = True
            plant = capacity[row] * per_run[recipe, tile]
        assets = cash[row] + plant + stock[row]
        net = assets - debt[row]
        worth[row] = net if net > 0.0 else 0.0
        has[row] = True
    return worth, has


def packed_stock(record, view, ids, records, matrices):
    """The stock the book holds, as lists sorted by producer row and good column: (producer rows, good columns, quantities), and
    by producer row the value of goods with no column, priced through the view."""
    book_goods = record.book.goods_of
    goods_row = matrices.goods.row
    rows, goods, quantities = [], [], []
    extra = np.zeros(len(ids))
    for row, producer_id in enumerate(ids):
        held = book_goods(producer_id)
        if not held:
            continue
        for good, by_tile in held.items():
            if len(by_tile) == 1:
                for total in by_tile.values():
                    break
                if not total > 0.0:
                    continue
            else:
                positive = [quantity for quantity in by_tile.values() if quantity > 0.0]
                if not positive:
                    continue
                total = positive[0] if len(positive) == 1 else math.fsum(positive)
            column = goods_row.get(good)
            if column is None:
                price = view.price(good, view.area_of(good, records[row].tile))
                if price is not None and price > 0.0:
                    extra[row] += price * total
                continue
            rows.append(row)
            goods.append(column)
            quantities.append(total)
    rows, goods = np.array(rows, dtype=np.int64), np.array(goods, dtype=np.int64)
    order = np.lexsort((goods, rows))
    return rows[order], goods[order], np.array(quantities, dtype=np.float64)[order], extra


def prices_and_wages(setup, record, view, arrays):
    """(price grid, wage grid) of the view's memory now: the arrays' own while nothing was written to it since they were read, else
    the remembered prices and the wages of the trades a plant takes hours of (a NaN row for any other trade)."""
    memory = arrays.memory
    if memory.is_current(record.memory):
        return memory.price, memory.wage
    from .year_arrays import wage_grid
    matrices = arrays.matrices
    needed = Names.of([matrices.trades.ids[column] for column in np.nonzero(matrices.plant_labour_hours.any(axis=0))[0]])
    wages = np.full((len(matrices.trades.ids), len(arrays.tiles.ids)), np.nan)
    if needed.ids:
        wages[[matrices.trades.row[trade] for trade in needed.ids]] = wage_grid(setup, view, needed, arrays.tiles)
    return price_grid(record.memory, matrices.goods, arrays.area_index), wages


def worths_from_arrays(setup, record, view, arrays) -> Dict[str, float]:
    """The net worth of each producer a household owns and that has plant (`equity._built_worths`), over the year `arrays`: the
    recipe and tile of each producer from the rows' names, its cash, capacity and stock from the records now, and the prices and
    wages as the memory holds them now."""
    ids = sorted(record.producers)
    if not ids:
        return {}
    records = [record.producers[each] for each in ids]
    matrices = arrays.matrices
    try:
        tile_row = np.fromiter((arrays.tiles.row[each.tile] for each in records), dtype=np.int64, count=len(ids))
    except KeyError:          # a producer on a tile the arrays do not know
        arrays = arrays.sync(setup, record, view)
        matrices = arrays.matrices
        tile_row = np.fromiter((arrays.tiles.row[each.tile] for each in records), dtype=np.int64, count=len(ids))
    recipe_row = np.fromiter((matrices.recipes.row[each.recipe_id] for each in records), dtype=np.int64, count=len(ids))
    capacity = np.fromiter((each.capacity_runs for each in records), dtype=np.float64, count=len(ids))
    price, wage = prices_and_wages(setup, record, view, arrays)
    money = setup.currency_id
    balance = record.book.balance
    cohorts = record.cohorts
    debts = credit_claims.debts_by_borrower(record.credit.loans, money)
    eligible = np.fromiter((each.owner in cohorts for each in records), dtype=np.bool_, count=len(ids))
    cash = np.fromiter((balance(each, money) for each in ids), dtype=np.float64, count=len(ids))
    debt = np.fromiter((debts.get(each, 0.0) for each in ids), dtype=np.float64, count=len(ids))
    rows, goods, quantities, extra = packed_stock(record, view, ids, records, matrices)
    worth, has = producer_worths(recipe_row, tile_row, capacity, cash, debt, eligible, rows, goods, quantities, extra,
                                 matrices.plant_goods, matrices.plant_labour_hours, matrices.plant_life_years, price, wage,
                                 arrays.area_index.of_good_tile)
    return {ids[row]: float(worth[row]) for row in np.nonzero(has)[0]}
