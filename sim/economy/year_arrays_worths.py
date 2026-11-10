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
from .close_pack_kernels import held_goods
from .year_arrays_costs import KERNEL, bill_goods, bill_hours, price_in
from .year_arrays_memory import price_grid
from .year_arrays_owners import debts_by_row, eligible_owners
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


def packed_stock(record, view, ids, tiles, matrices, agent_numbers=None):
    """The stock the book holds, as lists sorted by producer row and good column: (producer rows, good columns, quantities), and
    by producer row the value of goods with no column, priced through the view. The book is read in one kernel call
    (`close_pack_kernels.held_goods`); a good with no column is given a column past the matrices' own, so it comes back in the
    same call and is priced here."""
    book = record.book
    column_of_book_good, others = _columns_of_book_goods(book, matrices)
    if agent_numbers is None:
        agent_numbers = book.rows_of(ids)
    start, columns, quantities = held_goods(book.agent_table.first_slot, book.stock_rows.table, agent_numbers, column_of_book_good)
    rows = np.repeat(np.arange(len(ids), dtype=np.int64), np.diff(start))
    positive = quantities > 0.0
    own_column = columns < len(matrices.goods.ids)
    extra = np.zeros(len(ids))
    outside = np.nonzero(positive & ~own_column)[0]
    if len(outside):
        _price_unlisted(record, view, ids, tiles, rows[outside], columns[outside] - len(matrices.goods.ids), quantities[outside],
                        others, extra)
    keep = positive & own_column
    return rows[keep], columns[keep], quantities[keep], extra


def _columns_of_book_goods(book, matrices):
    """(for each good the book numbers: its column in the matrices, or a column past them for a good the matrices lack; the names
    of the goods past them, in that order)."""
    goods_row = matrices.goods.row
    column_of = np.full(len(book.good_ids.name_list), -1, dtype=np.int64)
    others = []
    for number, name in enumerate(book.good_ids.name_list):
        column = goods_row.get(name)
        if column is None:
            column = len(matrices.goods.ids) + len(others)
            others.append(name)
        column_of[number] = column
    return column_of, others


def _price_unlisted(record, view, ids, tiles, rows, other_index, quantities, others, extra) -> None:
    """Add to `extra[row]` the value of each good without a column that the producer holds. A producer holding two such goods is
    summed in the order the book lists its goods (the per-producer read), so it is read that way."""
    crowded = set(np.nonzero(np.bincount(rows, minlength=len(ids)) > 1)[0].tolist())
    for row, index, quantity in zip(rows.tolist(), other_index.tolist(), quantities.tolist()):
        if row in crowded:
            continue
        good = others[index]
        price = view.price(good, view.area_of(good, tiles[row]))
        if price is not None and price > 0.0:
            extra[row] += price * quantity
    for row in sorted(crowded):
        listed = set(others)
        for good, by_tile in record.book.goods_of(ids[row]).items():
            positives = [quantity for quantity in by_tile.values() if quantity > 0.0]
            if good not in listed or not positives:
                continue
            price = view.price(good, view.area_of(good, tiles[row]))
            if price is not None and price > 0.0:
                extra[row] += price * (positives[0] if len(positives) == 1 else math.fsum(positives))


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
    if not record.producers:
        return {}
    try:
        columns = arrays.producers.refresh(record.producers)
    except KeyError:          # a producer on a tile the arrays do not know
        arrays = arrays.sync(setup, record, view)
        columns = arrays.producers
    matrices = arrays.matrices
    ids = list(columns.ids)
    tile_row, recipe_row, capacity = columns.tile_row, columns.recipe_row, columns.capacity_runs
    price, wage = prices_and_wages(setup, record, view, arrays)
    money = setup.currency_id
    cohorts = record.cohorts
    debts = credit_claims.debts_by_borrower(record.credit.loans, money)
    eligible = eligible_owners(columns, cohorts)
    agent_numbers = record.book.rows_of(ids)
    cash = record.book.balances_at(agent_numbers, money)
    debt = debts_by_row(columns, debts)
    rows, goods, quantities, extra = packed_stock(record, view, ids, columns.tile_names(), matrices, agent_numbers)
    worth, has = producer_worths(recipe_row, tile_row, capacity, cash, debt, eligible, rows, goods, quantities, extra,
                                 matrices.plant_goods, matrices.plant_labour_hours, matrices.plant_life_years, price, wage,
                                 arrays.area_index.of_good_tile)
    held = np.nonzero(has)[0]
    return dict(zip(map(ids.__getitem__, held.tolist()), worth[held].tolist()))
