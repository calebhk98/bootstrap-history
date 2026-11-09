"""A good's traded markets numbered for settlement in one kernel call: which pairs they hold, the (agent, tile) keys and agents of
the batch in order of first use, and each market's own keys and agents.

This is `settlement_ids`' bookkeeping before the settling kernel runs (the pairs of the chosen markets, the keys and agents numbered
as `settlement_batch.KeyTable` numbered them, then `settlement_numbering.local_numbering`), read straight from the order tables'
columns. The plain numpy version is kept in `sim/tests/settlement_ids_plain.py`, and `test_settlement_number_kernel.py` runs both."""
import numpy

from sim.jit import njit

HASH_MULTIPLIER = 2654435761       # spreads whole-number keys over the hash table's slots


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
def number_of(values, distinct):
    """The first-use number of each of `values`, all of which are among `distinct` (listed in first-use order)."""
    return first_use(numpy.concatenate((distinct, values)))[0][len(distinct):]


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
def batch_keys(positions, pair_bid, pair_offer, bid_rows, offer_rows, bid_buyer, bid_tile, offer_seller, offer_tile, tile_stride,
               empty_tile):
    """(receipt key of each pair, selling key of each pair, holder and tile of each key, agent of each key within the batch's agents, the
    batch's agents as book numbers). A key is `holder * tile_stride + tile`; keys are numbered by the used bids' keys in bid order, the used
    offers' keys in offer order, then the keys of buyers with no tile, who take delivery where the seller holds the goods."""
    count = len(positions)
    bid_used = numpy.zeros(len(bid_rows), dtype=numpy.bool_)
    offer_used = numpy.zeros(len(offer_rows), dtype=numpy.bool_)
    for pair in range(count):
        bid_used[pair_bid[positions[pair]]] = True
        offer_used[pair_offer[positions[pair]]] = True
    candidates = numpy.zeros(bid_used.sum() + offer_used.sum() + count, dtype=numpy.int64)
    found = 0
    for place in range(len(bid_rows)):
        if bid_used[place]:
            candidates[found] = bid_buyer[bid_rows[place]] * tile_stride + bid_tile[bid_rows[place]]
            found += 1
    for place in range(len(offer_rows)):
        if offer_used[place]:
            candidates[found] = offer_seller[offer_rows[place]] * tile_stride + offer_tile[offer_rows[place]]
            found += 1
    receipt_key = numpy.zeros(count, dtype=numpy.int64)
    sold_key = numpy.zeros(count, dtype=numpy.int64)
    for pair in range(count):
        row, offer_row = bid_rows[pair_bid[positions[pair]]], offer_rows[pair_offer[positions[pair]]]
        sold_key[pair] = offer_seller[offer_row] * tile_stride + offer_tile[offer_row]
        if bid_tile[row] == empty_tile:
            receipt_key[pair] = bid_buyer[row] * tile_stride + offer_tile[offer_row]
            candidates[found] = receipt_key[pair]
            found += 1
        else:
            receipt_key[pair] = bid_buyer[row] * tile_stride + bid_tile[row]
    keys = first_use(candidates[:found].copy())[1]
    holder, tile = keys // tile_stride, keys % tile_stride
    key_agent, agents = first_use(holder)
    return number_of(receipt_key, keys), number_of(sold_key, keys), holder, tile, key_agent, agents


@njit
def market_keys(sizes, receipt, seller, key_agent, agent_total):
    """(pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent_local): the batch's keys and
    agents cut by market, each market's in ascending batch number (offsets cut the concatenations; `buyer_key` and `seller_key` number a
    pair's keys within its market; a batch of one market lists every key and agent of the batch)."""
    markets, key_total = len(sizes), len(key_agent)
    pair_offset = numpy.zeros(markets + 1, dtype=numpy.int64)
    for market in range(markets):
        pair_offset[market + 1] = pair_offset[market] + sizes[market]
    if markets == 1:
        return (pair_offset, numpy.array([0, agent_total], dtype=numpy.int64), numpy.array([0, key_total], dtype=numpy.int64),
                receipt.copy(), seller.copy(), numpy.arange(key_total, dtype=numpy.int64), numpy.arange(agent_total, dtype=numpy.int64),
                key_agent.astype(numpy.int64))
    key_used = numpy.zeros(markets * key_total, dtype=numpy.bool_)
    for market in range(markets):
        for pair in range(pair_offset[market], pair_offset[market + 1]):
            key_used[market * key_total + receipt[pair]] = True
            key_used[market * key_total + seller[pair]] = True
    key_offset = numpy.zeros(markets + 1, dtype=numpy.int64)
    for market in range(markets):
        key_offset[market + 1] = key_offset[market] + key_used[market * key_total:(market + 1) * key_total].sum()
    key_global = numpy.zeros(key_offset[markets], dtype=numpy.int64)
    key_local = numpy.zeros(markets * key_total, dtype=numpy.int64)
    agent_used = numpy.zeros(markets * agent_total, dtype=numpy.bool_)
    for market in range(markets):
        at = key_offset[market]
        for key in range(key_total):
            if key_used[market * key_total + key]:
                key_global[at] = key
                key_local[market * key_total + key] = at - key_offset[market]
                agent_used[market * agent_total + key_agent[key]] = True
                at += 1
    agent_offset = numpy.zeros(markets + 1, dtype=numpy.int64)
    for market in range(markets):
        agent_offset[market + 1] = agent_offset[market] + agent_used[market * agent_total:(market + 1) * agent_total].sum()
    agent_global = numpy.zeros(agent_offset[markets], dtype=numpy.int64)
    agent_local = numpy.zeros(markets * agent_total, dtype=numpy.int64)
    for market in range(markets):
        at = agent_offset[market]
        for agent in range(agent_total):
            if agent_used[market * agent_total + agent]:
                agent_global[at] = agent
                agent_local[market * agent_total + agent] = at - agent_offset[market]
                at += 1
    buyer_key = numpy.zeros(pair_offset[markets], dtype=numpy.int64)
    seller_key = numpy.zeros(pair_offset[markets], dtype=numpy.int64)
    key_agent_local = numpy.zeros(key_offset[markets], dtype=numpy.int64)
    for market in range(markets):
        for pair in range(pair_offset[market], pair_offset[market + 1]):
            buyer_key[pair] = key_local[market * key_total + receipt[pair]]
            seller_key[pair] = key_local[market * key_total + seller[pair]]
        for place in range(key_offset[market], key_offset[market + 1]):
            key_agent_local[place] = agent_local[market * agent_total + key_agent[key_global[place]]]
    return pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent_local


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
