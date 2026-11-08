"""The pairing of a year's labour markets, as kernels over fill columns (`labour_fills.py` builds the columns).

A market's fills are its employers' hours (buys) and its workers' hours sold (sells), each side listed in name order. The pairs
are the greedy walk of `settlement_limits.pair_fills`: buyers and sellers matched in order until one side runs out.
Every kernel visits the markets in the order given and takes a side's rows of market `m` as `start[m]:start[m + 1]`.
"""
import numpy

from sim.jit import njit
from sim.labour.api import python_sum


@njit
def walk_pairs(buy_start, buy_quantity, sell_start, sell_quantity):
    """The greedy pairs of every market: per market the pairs in order, each as the position of the buy and of the sell in
    their arrays and the quantity matched, exactly as `settlement_limits.pair_fills` walks one market (all quantities above
    zero). Returns (pair_start, pair_buy, pair_sell, pair_quantity): market `m`'s pairs are `pair_start[m]:pair_start[m + 1]`."""
    markets = len(buy_start) - 1
    capacity = len(buy_quantity) + len(sell_quantity)
    pair_start = numpy.zeros(markets + 1, dtype=numpy.int64)
    pair_buy = numpy.zeros(capacity, dtype=numpy.int64)
    pair_sell = numpy.zeros(capacity, dtype=numpy.int64)
    pair_quantity = numpy.zeros(capacity)
    count = 0
    for market in range(markets):
        pair_start[market] = count
        buy_index, buy_stop = buy_start[market], buy_start[market + 1]
        sell_index, sell_stop = sell_start[market], sell_start[market + 1]
        if buy_index == buy_stop or sell_index == sell_stop:
            continue
        buy_left, sell_left = buy_quantity[buy_index], sell_quantity[sell_index]
        while True:
            take = buy_left if buy_left < sell_left else sell_left
            pair_buy[count] = buy_index
            pair_sell[count] = sell_index
            pair_quantity[count] = take
            count += 1
            buy_left -= take
            sell_left -= take
            if buy_left <= 0.0:
                buy_index += 1
                if buy_index == buy_stop:
                    break
                buy_left = buy_quantity[buy_index]
            if sell_left <= 0.0:
                sell_index += 1
                if sell_index == sell_stop:
                    break
                sell_left = sell_quantity[sell_index]
    pair_start[markets] = count
    return pair_start, pair_buy[:count], pair_sell[:count], pair_quantity[:count]


@njit
def grouped_python_sums(group_start, values):
    """`sum(values[group_start[g]:group_start[g + 1]])` for every group, as CPython's `sum` of a list of floats adds them."""
    groups = len(group_start) - 1
    totals = numpy.zeros(groups)
    for group in range(groups):
        first, last = group_start[group], group_start[group + 1]
        totals[group] = python_sum(values[first:last], last - first)
    return totals


@njit
def market_agents(pair_start, pair_buy, pair_sell, buy_start, buy_ref, sell_start, sell_ref, ref_count):
    """The agents each market's settlement lists, in the order a settlement of its pairs lists them: the buyers its pairs
    used (in order), then the sellers they used that are not buyers there already. A pair's buyer and seller come back as
    positions in that list. Returns (agent_start, agent_ref, pair_buyer_agent, pair_seller_agent): market `m`'s agents are
    `agent_ref[agent_start[m]:agent_start[m + 1]]` (each a ref into the year's names) and a pair's agent numbers count from
    the market's first agent."""
    markets = len(pair_start) - 1
    agent_start = numpy.zeros(markets + 1, dtype=numpy.int64)
    agent_ref = numpy.zeros(len(buy_ref) + len(sell_ref), dtype=numpy.int64)
    pair_buyer_agent = numpy.zeros(len(pair_buy), dtype=numpy.int64)
    pair_seller_agent = numpy.zeros(len(pair_buy), dtype=numpy.int64)
    seen_in = numpy.full(ref_count, -1, dtype=numpy.int64)
    place = numpy.zeros(ref_count, dtype=numpy.int64)
    count = 0
    for market in range(markets):
        agent_start[market] = count
        first_pair, last_pair = pair_start[market], pair_start[market + 1]
        if first_pair == last_pair:
            continue
        for buy in range(buy_start[market], pair_buy[last_pair - 1] + 1):
            ref = buy_ref[buy]
            seen_in[ref] = market
            place[ref] = count - agent_start[market]
            agent_ref[count] = ref
            count += 1
        for sell in range(sell_start[market], pair_sell[last_pair - 1] + 1):
            ref = sell_ref[sell]
            if seen_in[ref] != market:
                seen_in[ref] = market
                place[ref] = count - agent_start[market]
                agent_ref[count] = ref
                count += 1
        for pair in range(first_pair, last_pair):
            pair_buyer_agent[pair] = place[buy_ref[pair_buy[pair]]]
            pair_seller_agent[pair] = place[sell_ref[pair_sell[pair]]]
    agent_start[markets] = count
    return agent_start, agent_ref[:count], pair_buyer_agent, pair_seller_agent


@njit
def fill_slots(buy_start, buy_ref, sell_start, sell_ref, ref_count):
    """A slot for each distinct agent among a market's fills (buys, then sells), counted on over all markets. Returns
    (buy_slot, sell_slot, slot_market, slot_ref): the slot of each fill, and the market and ref of each slot."""
    markets = len(buy_start) - 1
    total = len(buy_ref) + len(sell_ref)
    buy_slot = numpy.zeros(len(buy_ref), dtype=numpy.int64)
    sell_slot = numpy.zeros(len(sell_ref), dtype=numpy.int64)
    slot_market = numpy.zeros(total, dtype=numpy.int64)
    slot_ref = numpy.zeros(total, dtype=numpy.int64)
    seen_in = numpy.full(ref_count, -1, dtype=numpy.int64)
    place = numpy.zeros(ref_count, dtype=numpy.int64)
    count = 0
    for market in range(markets):
        for buy in range(buy_start[market], buy_start[market + 1]):
            ref = buy_ref[buy]
            if seen_in[ref] != market:
                seen_in[ref] = market
                place[ref] = count
                slot_market[count] = market
                slot_ref[count] = ref
                count += 1
            buy_slot[buy] = place[ref]
        for sell in range(sell_start[market], sell_start[market + 1]):
            ref = sell_ref[sell]
            if seen_in[ref] != market:
                seen_in[ref] = market
                place[ref] = count
                slot_market[count] = market
                slot_ref[count] = ref
                count += 1
            sell_slot[sell] = place[ref]
    return buy_slot, sell_slot, slot_market[:count], slot_ref[:count]
