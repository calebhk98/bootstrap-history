"""One kernel for the book's holdings reads: the stock slots of many agents gathered into columns (see sim/book_holdings.py)."""
import numpy

from sim.book_tables import FREE
from sim.jit import njit


@njit
def many_holder_columns(first_slots, next_in_agent, good, tile, quantity):
    """(starts, owner, good numbers, tile numbers, quantities) of the stock slots of the agents whose first slots are given (-1 for an
    agent with none): rows grouped by agent in the order given, each agent's rows in the order the slots were made. Agent i's rows are
    `starts[i]:starts[i + 1]`, and `owner` repeats i for each of them."""
    count = len(first_slots)
    starts = numpy.zeros(count + 1, dtype=numpy.int64)
    for position in range(count):
        slot = first_slots[position]
        rows = 0
        while slot != FREE:
            rows += 1
            slot = next_in_agent[slot]
        starts[position + 1] = starts[position] + rows
    total = starts[count]
    owner = numpy.empty(total, dtype=numpy.int64)
    goods = numpy.empty(total, dtype=numpy.int64)
    tiles = numpy.empty(total, dtype=numpy.int64)
    quantities = numpy.empty(total)
    row = 0
    for position in range(count):
        slot = first_slots[position]
        while slot != FREE:
            owner[row] = position
            goods[row] = good[slot]
            tiles[row] = tile[slot]
            quantities[row] = quantity[slot]
            row += 1
            slot = next_in_agent[slot]
    return starts, owner, goods, tiles, quantities
