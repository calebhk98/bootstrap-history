"""Kernels that fill the close pack from the book's and the year ledger's tables, one call for every producer.

`close_pack.pack` hands these the producers' book numbers (one per row of the producer columns, -1 for an agent the book never
saw, which holds nothing) and the numbers of the goods and trades each recipe slot stands for. Nothing here changes a table.

    slot_stocks         stock[row, slot]: what the producer holds on its own tile of the good in each of its recipe's slots
    held_goods          what the producer holds of every good in the matrices, summed over tiles, in the matrices' column order
    pair_values_by_slot figure[row, slot] from a ledger pair table (sold, output, hours hired), looked up by agent and subkey
"""
import numpy

from sim.book_index import EMPTY, index_find, pack_key
from sim.book_tables import FREE
from sim.jit import njit
from sim.labour.market.exact_sums import exact_sum


@njit
def slot_stocks(stocks, stock_index, agent_numbers, tile_numbers, recipe_rows, slot_book_goods):
    """The quantity each producer holds of the good in each slot of its recipe, on `tile_numbers[row]` (its own tile); zero where
    nothing was ever held or a number is -1. `slot_book_goods[recipe, slot]` is the book's good number, -1 for no slot or a
    good the book never saw."""
    width = slot_book_goods.shape[1]
    found = numpy.zeros((len(agent_numbers), width))
    for row in range(len(agent_numbers)):
        agent = agent_numbers[row]
        tile = tile_numbers[row]
        if agent < 0 or tile < 0:
            continue
        recipe = recipe_rows[row]
        for slot in range(width):
            good = slot_book_goods[recipe, slot]
            if good >= 0:
                position = index_find(stocks.key, stock_index, pack_key(agent, good, tile))
                if position != EMPTY:
                    found[row, slot] = stocks.quantity[position]
    return found


@njit
def _chain_length(first_slot, next_in_agent):
    count = 0
    slot = first_slot
    while slot != FREE:
        count += 1
        slot = next_in_agent[slot]
    return count


@njit
def held_goods(agent_first_slot, stocks, agent_numbers, column_of_book_good):
    """For each producer, the goods it holds that have a column in the matrices: (start, column, quantity). Producer `row`'s goods
    are entries `start[row]` .. `start[row + 1] - 1`, in column order. A good is listed when any of its tiles is not zero; its
    quantity is the exact sum (as `math.fsum`) of the tiles holding more than zero."""
    count = len(agent_numbers)
    start = numpy.zeros(count + 1, dtype=numpy.int64)
    longest = 0
    total = 0
    for row in range(count):
        agent = agent_numbers[row]
        if agent >= 0:
            length = _chain_length(agent_first_slot[agent], stocks.next_in_agent)
            total += length
            if length > longest:
                longest = length
    columns = numpy.empty(total, dtype=numpy.int64)
    quantities = numpy.empty(total)
    chain_columns = numpy.empty(longest, dtype=numpy.int64)
    chain_values = numpy.empty(longest)
    positives = numpy.empty(longest)
    used = 0
    for row in range(count):
        start[row] = used
        agent = agent_numbers[row]
        if agent < 0:
            continue
        entries = 0
        slot = agent_first_slot[agent]
        while slot != FREE:
            column = column_of_book_good[stocks.good[slot]]
            if column >= 0:
                chain_columns[entries] = column
                chain_values[entries] = stocks.quantity[slot]
                entries += 1
            slot = stocks.next_in_agent[slot]
        if entries == 0:
            continue
        order = numpy.argsort(chain_columns[:entries], kind="mergesort")
        position = 0
        while position < entries:
            column = chain_columns[order[position]]
            nonzero = False
            gathered = 0
            while position < entries and chain_columns[order[position]] == column:
                value = chain_values[order[position]]
                if value != 0.0:
                    nonzero = True
                if value > 0.0:
                    positives[gathered] = value
                    gathered += 1
                position += 1
            if nonzero:
                columns[used] = column
                quantities[used] = exact_sum(positives, gathered)
                used += 1
    start[count] = used
    return start, columns[:used].copy(), quantities[:used].copy()


@njit
def pair_values_by_slot(pair_rows, pair_index, agent_numbers, recipe_rows, slot_subkeys):
    """`figure[row, slot]`: the amount of the pair table's row for (the producer, the subkey of the slot's good or trade),
    zero where there is none. `slot_subkeys[recipe, slot]` is -1 for no slot or a subkey the ledger never numbered."""
    width = slot_subkeys.shape[1]
    found = numpy.zeros((len(agent_numbers), width))
    for row in range(len(agent_numbers)):
        agent = agent_numbers[row]
        if agent < 0:
            continue
        recipe = recipe_rows[row]
        for slot in range(width):
            subkey = slot_subkeys[recipe, slot]
            if subkey >= 0:
                position = index_find(pair_rows.key, pair_index, pack_key(agent, subkey, 0))
                if position != EMPTY:
                    found[row, slot] = 0.0 + pair_rows.amount[position]
    return found
