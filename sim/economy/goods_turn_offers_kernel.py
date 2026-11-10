"""What each producer of a turn holds to offer: `year_goods._quick_outputs` for every producer of the turn at once.

For each output of a producer, in the order of the good's name, the stock it holds beyond the units its own runs use up
(`output_kept` per run times its capacity) is an offer when it is above zero, at the price the producer expects for the good
(`expected[producer, slot_of[recipe, good]]`). A producer with an offered output that has no expected price (NaN) is `slow`: its offers are
`producers.offers`' to make, and the pairs it has here are to be left out."""
import numpy

from sim.jit import njit

from .goods_turn_kernel import KERNEL, _stock


@njit(**KERNEL)
def offer_pairs(position, agent, tile, recipe, capacity, output_ptr, output_good, output_kept, spoilage, good_book, expected, slot_of,
                stock_key, stock_quantity, stock_index):
    """For the producers of the turn (`position[i]`: its row in the producer columns and in `expected`; the book's numbers of its
    `agent` and `tile`; its `recipe` row and `capacity`): the pairs as columns (the producer's place i, the good's row, the units,
    the expected price, the spoilage) with each producer's first pair in `pair_ptr`, and whether each is `slow`."""
    count = len(position)
    room = 0
    for place in range(count):
        room += output_ptr[recipe[place] + 1] - output_ptr[recipe[place]]
    pair_ptr = numpy.zeros(count + 1, dtype=numpy.int64)
    pair_good = numpy.zeros(room, dtype=numpy.int64)
    pair_units = numpy.zeros(room)
    pair_price = numpy.zeros(room)
    pair_spoilage = numpy.zeros(room)
    slow = numpy.zeros(count, dtype=numpy.bool_)
    pairs = 0
    for place in range(count):
        row = recipe[place]
        for entry in range(output_ptr[row], output_ptr[row + 1]):
            good = output_good[entry]
            units = _stock(stock_key, stock_quantity, stock_index, agent[place], good_book[good], tile[place]) - output_kept[entry] * capacity[place]
            if units <= 0.0:
                continue
            price = expected[position[place], slot_of[row, good]]
            if price != price:
                slow[place] = True
                continue
            pair_good[pairs], pair_units[pairs], pair_price[pairs], pair_spoilage[pairs] = good, units, price, spoilage[good]
            pairs += 1
        pair_ptr[place + 1] = pairs
    return pair_ptr, pair_good[:pairs], pair_units[:pairs], pair_price[:pairs], pair_spoilage[:pairs], slow
