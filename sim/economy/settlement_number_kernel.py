"""A good's traded markets numbered for settlement in one kernel call: which pairs they hold, the (agent, tile) keys and agents of
the batch in order of first use, and each market's own keys and agents.

This is `settlement_ids`' bookkeeping before the settling kernel runs (the pairs of the chosen markets, the keys and agents numbered
as `settlement_batch.KeyTable` numbered them, then `settlement_numbering.local_numbering`), read straight from the order tables'
columns. The plain numpy version is kept in `sim/tests/settlement_ids_plain.py`, and `test_settlement_number_kernel.py` runs both."""
import numpy

from sim.jit import njit

HASH_MULTIPLIER = 2654435761       # spreads whole-number keys over the hash table's slots
SMALL_SORT = 24                    # a market with no more keys or agents than this is sorted by insertion


@njit
def first_use(values):
    """(the number of each value by order of first appearance, the distinct values in that order), found with a hash table so the
    work grows with the values, not with a sort."""
    count = len(values)
    capacity = 16
    while capacity < 2 * count:
        capacity *= 2
    held = numpy.full(capacity, -1, dtype=numpy.int64)
    number_at = numpy.zeros(capacity, dtype=numpy.int64)
    numbers = numpy.zeros(count, dtype=numpy.int64)
    distinct = numpy.zeros(count, dtype=numpy.int64)
    found = 0
    for place in range(count):
        value = values[place]
        slot = (value * HASH_MULTIPLIER) & (capacity - 1)
        while held[slot] != -1 and held[slot] != value:
            slot = (slot + 1) & (capacity - 1)
        if held[slot] == -1:
            held[slot] = value
            number_at[slot] = found
            distinct[found] = value
            found += 1
        numbers[place] = number_at[slot]
    return numbers, distinct[:found].copy()


@njit
def pair_positions(pair_ptr, slots):
    """(pairs per market, the positions of all those markets' pairs one market after another) for the markets `slots`."""
    sizes = pair_ptr[slots + 1] - pair_ptr[slots]
    positions = numpy.zeros(int(sizes.sum()), dtype=numpy.int64)
    at = 0
    for place in range(len(slots)):
        for pair in range(pair_ptr[slots[place]], pair_ptr[slots[place] + 1]):
            positions[at] = pair
            at += 1
    return sizes, positions


@njit
def intern(value, held, number_at, found):
    """(the number of `value` by order of first sight, whether it is new) in the hash table `held` / `number_at` (a power of two
    long, never full), which already holds `found` values; a new value takes number `found`."""
    mask = len(held) - 1
    slot = (value * HASH_MULTIPLIER) & mask
    while held[slot] != -1 and held[slot] != value:
        slot = (slot + 1) & mask
    if held[slot] == -1:
        held[slot] = value
        number_at[slot] = found
        return found, True
    return number_at[slot], False


@njit
def table_size(count):
    """The length of a hash table for up to `count` values: a power of two, at least twice as long."""
    capacity = 16
    while capacity < 2 * count:
        capacity *= 2
    return capacity


@njit
def batch_keys(positions, pair_bid, pair_offer, bid_rows, offer_rows, bid_buyer, bid_tile, offer_seller, offer_tile, tile_stride,
               empty_tile):
    """(receipt key of each pair, selling key of each pair, holder and tile of each key, agent of each key within the batch's agents, the
    batch's agents as book numbers). A key is `holder * tile_stride + tile`; keys are numbered by the used bids' keys in bid order, the used
    offers' keys in offer order, then the keys of buyers with no tile, who take delivery where the seller holds the goods. Each used
    bid and offer is numbered once and its pairs read the number; the agents are numbered by their first key."""
    count = len(positions)
    bid_used = numpy.zeros(len(bid_rows), dtype=numpy.bool_)
    offer_used = numpy.zeros(len(offer_rows), dtype=numpy.bool_)
    untiled = 0
    for pair in range(count):
        bid_used[pair_bid[positions[pair]]] = True
        offer_used[pair_offer[positions[pair]]] = True
        if bid_tile[bid_rows[pair_bid[positions[pair]]]] == empty_tile:
            untiled += 1
    most = int(bid_used.sum()) + int(offer_used.sum()) + untiled
    held = numpy.full(table_size(most), -1, dtype=numpy.int64)
    number_at = numpy.zeros(len(held), dtype=numpy.int64)
    keys = numpy.zeros(most, dtype=numpy.int64)
    bid_number = numpy.zeros(len(bid_rows), dtype=numpy.int64)
    offer_number = numpy.zeros(len(offer_rows), dtype=numpy.int64)
    found = 0
    for place in range(len(bid_rows)):
        if bid_used[place]:
            key = bid_buyer[bid_rows[place]] * tile_stride + bid_tile[bid_rows[place]]
            bid_number[place], is_new = intern(key, held, number_at, found)
            if is_new:
                keys[found] = key
                found += 1
    for place in range(len(offer_rows)):
        if offer_used[place]:
            key = offer_seller[offer_rows[place]] * tile_stride + offer_tile[offer_rows[place]]
            offer_number[place], is_new = intern(key, held, number_at, found)
            if is_new:
                keys[found] = key
                found += 1
    receipt_key = numpy.zeros(count, dtype=numpy.int64)
    sold_key = numpy.zeros(count, dtype=numpy.int64)
    for pair in range(count):
        row = bid_rows[pair_bid[positions[pair]]]
        sold_key[pair] = offer_number[pair_offer[positions[pair]]]
        if bid_tile[row] == empty_tile:
            key = bid_buyer[row] * tile_stride + offer_tile[offer_rows[pair_offer[positions[pair]]]]
            receipt_key[pair], is_new = intern(key, held, number_at, found)
            if is_new:
                keys[found] = key
                found += 1
        else:
            receipt_key[pair] = bid_number[pair_bid[positions[pair]]]
    keys = keys[:found]
    holder, tile = keys // tile_stride, keys % tile_stride
    key_agent, agents = first_use(holder)
    return receipt_key, sold_key, holder, tile, key_agent, agents


@njit
def list_new(values, stamp, market, listed, at):
    """Write each of `values` that `stamp` has not yet marked for this `market` into `listed` from `at` and mark it (`stamp[value]` is
    then `market + 1`). Returns the place after the last one written."""
    for place in range(len(values)):
        value = values[place]
        if stamp[value] != market + 1:
            stamp[value] = market + 1
            listed[at] = value
            at += 1
    return at


@njit
def sort_listed(listed, first, last):
    """`listed[first:last]` in ascending order (insertion for the few, numpy's sort for the many)."""
    if last - first > SMALL_SORT:
        listed[first:last] = numpy.sort(listed[first:last])
        return
    for place in range(first + 1, last):
        value = listed[place]
        before = place - 1
        while before >= first and listed[before] > value:
            listed[before + 1] = listed[before]
            before -= 1
        listed[before + 1] = value


@njit
def market_keys(sizes, receipt, seller, key_agent, agent_total):
    """(pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent_local): the batch's keys and
    agents cut by market, each market's in ascending batch number (offsets cut the concatenations; `buyer_key` and `seller_key` number a
    pair's keys within its market; a batch of one market lists every key and agent of the batch). A market's keys are the ones its pairs
    name, found by marking them, so the work grows with the pairs, not with the batch's keys times its markets."""
    markets, key_total = len(sizes), len(key_agent)
    pair_offset = numpy.zeros(markets + 1, dtype=numpy.int64)
    for market in range(markets):
        pair_offset[market + 1] = pair_offset[market] + sizes[market]
    if markets == 1:
        return (pair_offset, numpy.array([0, agent_total], dtype=numpy.int64), numpy.array([0, key_total], dtype=numpy.int64),
                receipt.copy(), seller.copy(), numpy.arange(key_total, dtype=numpy.int64), numpy.arange(agent_total, dtype=numpy.int64),
                key_agent.astype(numpy.int64))
    pairs_total = pair_offset[markets]
    most_keys = 0
    for market in range(markets):
        most_keys += min(key_total, 2 * sizes[market])
    key_stamp = numpy.zeros(key_total, dtype=numpy.int64)
    agent_stamp = numpy.zeros(agent_total, dtype=numpy.int64)
    key_local = numpy.zeros(key_total, dtype=numpy.int64)
    agent_local = numpy.zeros(agent_total, dtype=numpy.int64)
    listed_keys = numpy.zeros(most_keys, dtype=numpy.int64)
    listed_agents = numpy.zeros(most_keys, dtype=numpy.int64)
    key_offset = numpy.zeros(markets + 1, dtype=numpy.int64)
    agent_offset = numpy.zeros(markets + 1, dtype=numpy.int64)
    buyer_key = numpy.zeros(pairs_total, dtype=numpy.int64)
    seller_key = numpy.zeros(pairs_total, dtype=numpy.int64)
    key_agent_local = numpy.zeros(most_keys, dtype=numpy.int64)
    for market in range(markets):
        first, last = pair_offset[market], pair_offset[market + 1]
        first_key, first_agent = key_offset[market], agent_offset[market]
        last_key = list_new(receipt[first:last], key_stamp, market, listed_keys, first_key)
        last_key = list_new(seller[first:last], key_stamp, market, listed_keys, last_key)
        sort_listed(listed_keys, first_key, last_key)
        found = last_key - first_key
        key_offset[market + 1] = last_key
        for place in range(found):
            key_local[listed_keys[first_key + place]] = place
        last_agent = list_new(key_agent[listed_keys[first_key:last_key]], agent_stamp, market, listed_agents, first_agent)
        sort_listed(listed_agents, first_agent, last_agent)
        agents_found = last_agent - first_agent
        agent_offset[market + 1] = last_agent
        for place in range(agents_found):
            agent_local[listed_agents[first_agent + place]] = place
        for pair in range(first, last):
            buyer_key[pair] = key_local[receipt[pair]]
            seller_key[pair] = key_local[seller[pair]]
        for place in range(found):
            key_agent_local[first_key + place] = agent_local[key_agent[listed_keys[first_key + place]]]
    return (pair_offset, agent_offset, key_offset, buyer_key, seller_key, listed_keys[:key_offset[markets]].copy(),
            listed_agents[:agent_offset[markets]].copy(), key_agent_local[:key_offset[markets]].copy())


@njit
def number_good(pair_ptr, slots, pair_bid, pair_offer, bid_rows, offer_rows, bid_buyer, bid_tile, offer_seller, offer_tile, tile_stride,
                empty_tile):
    """Everything the settling kernel needs numbered, for the traded markets `slots` of a batch (`pair_ptr` cuts its pairs; `pair_bid`
    and `pair_offer` are places in the pack, `bid_rows` and `offer_rows` take them to the order tables' rows): (positions of the pairs,
    pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent_local, holder, tile, agents,
    the batch key each pair sells from)."""
    sizes, positions = pair_positions(pair_ptr, slots)
    receipt, sold_from, holder, tile, key_agent, agents = batch_keys(
        positions, pair_bid, pair_offer, bid_rows, offer_rows, bid_buyer, bid_tile, offer_seller, offer_tile, tile_stride, empty_tile)
    (pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent_local) = market_keys(
        sizes, receipt, sold_from, key_agent, len(agents))
    return (positions, pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent_local, holder,
            tile, agents, sold_from)


@njit
def numpy_sum(values, first, last):
    """`values[first:last].sum()` as numpy adds it: pairwise (under eight elements left to right, up to 128 with eight running sums, wider
    halved at a multiple of eight)."""
    return _pairwise(values, first, last - first)


@njit
def _pairwise(values, start, count):
    if count < 8:
        total = 0.0
        for place in range(start, start + count):
            total += values[place]
        return total
    if count <= 128:
        eight = values[start:start + 8].copy()
        place = 8
        while place < count - (count % 8):
            for lane in range(8):
                eight[lane] += values[start + place + lane]
            place += 8
        total = ((eight[0] + eight[1]) + (eight[2] + eight[3])) + ((eight[4] + eight[5]) + (eight[6] + eight[7]))
        while place < count:
            total += values[start + place]
            place += 1
        return total
    half = count // 2
    half -= half % 8
    return _pairwise(values, start, half) + _pairwise(values, start + half, count - half)


@njit
def delivered_by_market(goods, pair_offset):
    """The goods moved by each market: `goods[first:last].sum()` per market as numpy sums."""
    delivered = numpy.zeros(len(pair_offset) - 1)
    for market in range(len(delivered)):
        delivered[market] = numpy_sum(goods, pair_offset[market], pair_offset[market + 1])
    return delivered
