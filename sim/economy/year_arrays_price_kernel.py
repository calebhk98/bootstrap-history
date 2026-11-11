"""The expected prices of the producer columns laid out by recipe slot, in one kernel call (`year_arrays_producers._expected_prices`)."""
import numpy as np

from sim.jit import njit


@njit
def expected_prices_by_slot(rows, recipe_row, price_count, price_good, price_value, column_of, slot_goods, no_slot):
    """producer by recipe slot: the price the producer (store row `rows[place]`) expects for the slot's good, NaN where it holds none.
    `column_of[number]` is the matrices' column of the store's good `number` (-1 for a good the year has no column for, which also covers
    a number past the array); a slot takes the producer's first held price of its good, and a good in two slots fills both."""
    slots = slot_goods.shape[1]
    prices = np.full((len(rows), slots), np.nan)
    filled = np.zeros(slots, dtype=np.bool_)
    for place in range(len(rows)):
        row = rows[place]
        recipe_slots = slot_goods[recipe_row[place]]
        for held in range(price_count[row]):
            number = price_good[row, held]
            column = column_of[number] if number < len(column_of) else -1
            if column < 0:
                continue
            for slot in range(slots):
                if recipe_slots[slot] == column and recipe_slots[slot] != no_slot and not filled[slot]:
                    prices[place, slot] = price_value[row, held]
                    filled[slot] = True
        for slot in range(slots):
            filled[slot] = False
    return prices
