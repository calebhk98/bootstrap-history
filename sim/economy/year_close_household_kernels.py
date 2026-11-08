"""The households' year-end goods as tables: what each cohort received (and grew), and the consumption that follows.

    receipts_with_grown   per cohort: its goods received and its goods grown, merged as the close's dictionary merged them
    consumption_postings  per cohort: the goods it uses up, as goods-move rows from the cohort to the consumption account,
                          each cut to what the cohort holds, one all-or-none batch per cohort
"""
import numpy

from sim.book_index import EMPTY, index_find, pack_key
from sim.jit import njit


@njit
def _chain_length(first_links, next_links, agent):
    count = 0
    if agent < 0 or agent >= len(first_links):
        return count
    link = first_links[agent]
    while link != 0:
        count += 1
        link = next_links[link - 1]
    return count


@njit
def receipts_with_grown(received_first, received_rows, grown_first, grown_rows, agent_numbers):
    """(start, good, amount): for each cohort (by its agent number; -1 holds nothing), entries `start[c]` .. `start[c + 1] - 1`,
    its received goods in the order the ledger made the rows, then its grown goods: a grown good already listed adds to it
    (`received + grown`), a new one is added with `0.0 + grown`. `good` is the book's good number. The first links are the ledger's
    `first_received` and `first_grown` (row + 1, 0 for none), the rows its pair tables."""
    count = len(agent_numbers)
    start = numpy.zeros(count + 1, dtype=numpy.int64)
    bound = 0
    for position in range(count):
        bound += (_chain_length(received_first, received_rows.next_in_agent, agent_numbers[position])
                  + _chain_length(grown_first, grown_rows.next_in_agent, agent_numbers[position]))
    goods = numpy.empty(bound, dtype=numpy.int64)
    amounts = numpy.empty(bound)
    used = 0
    for position in range(count):
        start[position] = used
        agent = agent_numbers[position]
        if agent < 0:
            continue
        if agent < len(received_first):
            link = received_first[agent]
            while link != 0:
                goods[used] = received_rows.subkey[link - 1]
                amounts[used] = received_rows.amount[link - 1]
                used += 1
                link = received_rows.next_in_agent[link - 1]
        if agent < len(grown_first):
            link = grown_first[agent]
            while link != 0:
                good = grown_rows.subkey[link - 1]
                found = -1
                for entry in range(start[position], used):
                    if goods[entry] == good:
                        found = entry
                        break
                if found >= 0:
                    amounts[found] = amounts[found] + grown_rows.amount[link - 1]
                else:
                    goods[used] = good
                    amounts[used] = 0.0 + grown_rows.amount[link - 1]
                    used += 1
                link = grown_rows.next_in_agent[link - 1]
    start[count] = used
    return start, goods[:used].copy(), amounts[:used].copy()


@njit
def consumption_postings(start, goods, amounts, agent_numbers, tile_numbers, consumed, good_rank, stocks, stock_index):
    """Goods-move rows (giver, good, tile, quantity, batch, cohort) from `receipts_with_grown`'s entries (`cohort` is the position of
    the row's cohort among those given; a giver or tile the book never numbered is -1 in the row and the caller numbers it). A cohort uses up each good that
    `consumed` marks (1) and that it received above zero, in good-name order (`good_rank`), cut to what it holds on its tile (nothing
    when it holds none). Cohorts with no row make no batch; batch numbers rise by one for each cohort that has rows."""
    count = len(agent_numbers)
    longest = 0
    for position in range(count):
        longest = max(longest, start[position + 1] - start[position])
    givers = numpy.empty(len(goods), dtype=numpy.int64)
    good_rows = numpy.empty(len(goods), dtype=numpy.int64)
    tiles = numpy.empty(len(goods), dtype=numpy.int64)
    quantities = numpy.empty(len(goods))
    batches = numpy.empty(len(goods), dtype=numpy.int64)
    owners = numpy.empty(len(goods), dtype=numpy.int64)
    keys = numpy.empty(longest, dtype=numpy.int64)
    places = numpy.empty(longest, dtype=numpy.int64)
    used = 0
    batch = -1
    for position in range(count):
        entries = 0
        for entry in range(start[position], start[position + 1]):
            if amounts[entry] > 0.0 and consumed[goods[entry]] != 0:
                keys[entries] = good_rank[goods[entry]]
                places[entries] = entry
                entries += 1
        if entries == 0:
            continue
        batch += 1
        agent, tile = agent_numbers[position], tile_numbers[position]
        order = numpy.argsort(keys[:entries])
        for place in range(entries):
            entry = places[order[place]]
            held = 0.0
            slot = index_find(stocks.key, stock_index, pack_key(agent, goods[entry], tile)) if agent >= 0 and tile >= 0 else EMPTY
            if slot != EMPTY:
                held = stocks.quantity[slot]
            givers[used] = agent
            good_rows[used] = goods[entry]
            tiles[used] = tile
            quantities[used] = min(amounts[entry], max(0.0, held))
            batches[used] = batch
            owners[used] = position
            used += 1
    return givers[:used].copy(), good_rows[:used].copy(), tiles[:used].copy(), quantities[:used].copy(), batches[:used].copy(), owners[:used].copy()
