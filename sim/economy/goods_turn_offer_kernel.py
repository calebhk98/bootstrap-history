"""A turn's offers in one kernel call: what each producer of the turn holds to offer (`offer_pairs`), the cash it presses to raise, and
the reservation of each pair of the quick producers (`offer_reservations`), from the whole producer columns and the producers' places
in them; the arrays `TurnWorld.offer` used to gather and filter between those calls are made here."""
import numpy

from sim.jit import njit

from .goods_turn_kernel import KERNEL
from .goods_turn_offers_kernel import offer_pairs
from .year_goods_offers import offer_reservations


@njit(**KERNEL)
def offer_turn(position, agent_of, tile_of_row, tile_row, recipe_row, capacity_runs, output_ptr, output_good, output_kept, spoilage,
               good_book, expected, slot_of, stock_key, stock_quantity, stock_index, cash, running, cash_target, last_runs,
               expected_sales, pays, rate, change_share, exponent):
    """For the producers at `position` (rows of the producer columns, in id order) with `cash` held and `running` costs so far each:
    (slow, shortfall, pair_place, pair_good, pair_units, reservation). `slow` marks a producer with an output held but no price expected,
    `shortfall` is the cash it still has to raise, and the pairs are the quick producers' only, as columns in producer order
    (`pair_place`: the producer's place in `position`)."""
    count = len(position)
    agent = numpy.empty(count, dtype=numpy.int64)
    tile = numpy.empty(count, dtype=numpy.int64)
    recipe = numpy.empty(count, dtype=numpy.int64)
    capacity = numpy.empty(count)
    shortfall = numpy.empty(count)
    for place in range(count):
        row = position[place]
        agent[place], tile[place] = agent_of[row], tile_of_row[tile_row[row]]
        recipe[place], capacity[place] = recipe_row[row], capacity_runs[row]
        lacking = cash_target[row] - cash[place] - running[place]
        shortfall[place] = 0.0 if 0.0 >= lacking else lacking
    pair_ptr, pair_good, pair_units, pair_price, pair_spoilage, slow = offer_pairs(
        position, agent, tile, recipe, capacity, output_ptr, output_good, output_kept, spoilage, good_book, expected, slot_of,
        stock_key, stock_quantity, stock_index)
    quick = 0
    kept = 0
    for place in range(count):
        if not slow[place]:
            quick += 1
            kept += pair_ptr[place + 1] - pair_ptr[place]
    quick_ptr = numpy.zeros(quick + 1, dtype=numpy.int64)
    quick_shortfall = numpy.empty(quick)
    quick_capacity = numpy.empty(quick)
    quick_cash_target = numpy.empty(quick)
    quick_last_runs = numpy.empty(quick)
    quick_sales = numpy.empty(quick)
    quick_pays = numpy.empty(quick)
    pair_place = numpy.empty(kept, dtype=numpy.int64)
    out_good = numpy.empty(kept, dtype=numpy.int64)
    out_units = numpy.empty(kept)
    out_price = numpy.empty(kept)
    out_spoilage = numpy.empty(kept)
    found = 0
    taken = 0
    for place in range(count):
        if slow[place]:
            continue
        row = position[place]
        quick_shortfall[found], quick_capacity[found], quick_cash_target[found] = shortfall[place], capacity[place], cash_target[row]
        quick_last_runs[found], quick_sales[found], quick_pays[found] = last_runs[row], expected_sales[row], pays[row]
        for pair in range(pair_ptr[place], pair_ptr[place + 1]):
            pair_place[taken], out_good[taken], out_units[taken] = place, pair_good[pair], pair_units[pair]
            out_price[taken], out_spoilage[taken] = pair_price[pair], pair_spoilage[pair]
            taken += 1
        found += 1
        quick_ptr[found] = taken
    reservation = offer_reservations(quick_ptr, out_price, out_spoilage, out_units, quick_shortfall, quick_capacity, quick_cash_target,
                                     quick_last_runs, quick_sales, quick_pays, rate, change_share, exponent)
    return slow, shortfall, pair_place, out_good, out_units, reservation
