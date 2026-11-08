"""The households' year end over arrays: the need units each cohort went short of its floors (`households_close.unmet_floor_by_need` for every
cohort at once).

A basket is packed once (`households_close_pack.BasketRows`): its needs in order, each with its floor per person and its goods' book numbers,
effects and service lives. A cohort names its basket, its people, and the slice of the year's receipts (`year_close_household_kernels.
receipts_with_grown`) it got; the durables it holds are read as a block beforehand. The plain sums are made in the order the Python made
them (a need's goods in order, each added to a running total), so the figures equal the Python's to the last bit."""
import numpy as np

from sim.jit import njit


@njit
def unmet_floors(people, basket_of, receipt_start, receipt_goods, receipt_amounts, need_start, need_floor, row_start, row_good, row_effect,
                 row_life, row_held_place, held_start, held, good_count, unmet):
    """For each cohort `c` and each need `n` of its basket (position within the basket), `unmet[c, n]`: the need units short of the floor
    (`need_floor[n] * people[c]`), NaN where there is no shortage or the floor is nothing. A good with a service life above zero serves at
    its held stock over its life (`held[held_start[c] + row_held_place[row]]`); any other good, at the quantity the cohort received of it
    (the last entry for a good listed twice, as the dictionary of receipts kept). `row_good` is the book's good number, -1 for a good the book
    never numbered (nothing received). Baskets: needs `need_start[b] .. need_start[b + 1] - 1`, goods of need `n` rows `row_start[n] ..
    row_start[n + 1] - 1`."""
    received = np.zeros(good_count)
    for cohort in range(len(people)):
        for entry in range(receipt_start[cohort], receipt_start[cohort + 1]):
            received[receipt_goods[entry]] = receipt_amounts[entry]
        basket = basket_of[cohort]
        for need in range(need_start[basket], need_start[basket + 1]):
            place = need - need_start[basket]
            unmet[cohort, place] = np.nan
            floor_units = need_floor[need] * people[cohort]
            if floor_units <= 0.0:
                continue
            delivered = 0.0
            for row in range(row_start[need], row_start[need + 1]):
                if row_life[row] > 0.0:
                    delivered += held[held_start[cohort] + row_held_place[row]] * row_effect[row] / row_life[row]
                elif row_good[row] >= 0:
                    delivered += received[row_good[row]] * row_effect[row]
            if delivered < floor_units:
                unmet[cohort, place] = floor_units - delivered
        for entry in range(receipt_start[cohort], receipt_start[cohort + 1]):
            received[receipt_goods[entry]] = 0.0
