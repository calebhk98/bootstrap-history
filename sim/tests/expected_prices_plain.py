"""`year_arrays_producers._expected_prices` as it was before one kernel laid the prices out: whole-table numpy selection."""
import numpy as np

from sim.economy.year_arrays_recipes import NO_SLOT


def plain_expected_prices(store, rows, recipe_row, matrices):
    table = store.table
    prices = np.full((len(rows), matrices.good_slots), np.nan)
    held = table.price_count[rows]
    if not len(rows) or not held.max():
        return prices
    width = int(held.max())
    names = store.names["goods"].name_list
    producer, place = np.nonzero(np.arange(width)[None, :] < held[:, None])
    numbers = table.price_good[rows, :width][producer, place]
    column_of = np.full(len(names) + 1, -1, dtype=np.int64)
    for number in np.nonzero(np.bincount(numbers))[0].tolist():
        if number < len(names):
            column_of[number] = matrices.goods.row.get(names[number], -1)
    slots = matrices.slot_goods[recipe_row][producer]
    pair, slot = np.nonzero((column_of[numbers][:, None] == slots) & (slots != NO_SLOT))
    _keys, first = np.unique(producer[pair] * matrices.good_slots + slot, return_index=True)
    pair, slot = pair[first], slot[first]
    prices[producer[pair], slot] = table.price_value[rows, :width][producer[pair], place[pair]]
    return prices
