"""Many markets' settlements in one numba kernel call (settlement_batch.py packs and unpacks).

The markets are settled one after another in the order given, each as `settlement_kernel.settle_pairs` settles one, but the
stock of every (agent, tile) key and the money of every agent are carried from one market to the next, so a market sees what
the markets before it left. The markets' own sums come back by market (concatenated, cut at the offsets); the batch's sums
per agent and per key come back for one posting on the book.
"""
import numpy

from sim.jit import njit

from .settlement_kernel import KERNEL
from .settlement_market_kernel import settle_market_into, widest


@njit(**KERNEL)
def settle_markets(pair_offset, agent_offset, key_offset, buyer_key, seller_key, quantity, ask, key_agent, key_global,
                   agent_global, stock_state, cash_state, agent_edge, agent_mint, agent_external, agent_import,
                   agent_export, delivers, sale):
    """Settle each market: its pairs are `pair_offset[market]:pair_offset[market + 1]`, its agents and keys cut the same way
    by `agent_offset` and `key_offset`. `buyer_key`, `seller_key` and `key_agent` number a market's keys and agents from
    zero; `key_global` and `agent_global` say which batch-wide key or agent each is, and `stock_state`, `cash_state` and the
    agent flags are indexed by those. `stock_state` and `cash_state` are updated in place.

    Returns, concatenated by market: per pair the goods moved, the money paid and the payer; per agent the sums
    `settle_pairs` returns; per key goods given, taken and delivered to the mint; then per batch agent the money paid and
    received, and per batch key the goods given and taken."""
    markets = len(pair_offset) - 1
    pairs_total, agents_total, keys_total = pair_offset[markets], agent_offset[markets], key_offset[markets]
    goods = numpy.zeros(pairs_total)
    money = numpy.zeros(pairs_total)
    payer = numpy.zeros(pairs_total, dtype=numpy.int64)
    paid = numpy.zeros(agents_total)
    received = numpy.zeros(agents_total)
    goods_in = numpy.zeros(agents_total)
    goods_out = numpy.zeros(agents_total)
    buyer_net = numpy.zeros(agents_total)
    got_goods = numpy.zeros(agents_total, dtype=numpy.bool_)
    paid_as_buyer = numpy.zeros(agents_total, dtype=numpy.bool_)
    imports = numpy.zeros(agents_total)
    exports = numpy.zeros(agents_total)
    key_given = numpy.zeros(keys_total)
    key_taken = numpy.zeros(keys_total)
    key_to_mint = numpy.zeros(keys_total)
    batch_paid = numpy.zeros(len(cash_state))
    batch_received = numpy.zeros(len(cash_state))
    batch_given = numpy.zeros(len(stock_state))
    batch_taken = numpy.zeros(len(stock_state))
    most_pairs, most_agents, most_keys = widest(pair_offset), widest(agent_offset), widest(key_offset)
    amounts, unit = numpy.zeros(most_pairs), numpy.zeros(most_pairs)
    buyer_agent, seller_agent, payer_here = (numpy.zeros(most_pairs, dtype=numpy.int64), numpy.zeros(most_pairs, dtype=numpy.int64),
                                             numpy.zeros(most_pairs, dtype=numpy.int64))
    asked, scale, stock_start, stock_left = numpy.zeros(most_keys), numpy.zeros(most_keys), numpy.zeros(most_keys), numpy.zeros(most_keys)
    owed, purse_scale, cash_start, cash_left = (numpy.zeros(most_agents), numpy.zeros(most_agents), numpy.zeros(most_agents),
                                                numpy.zeros(most_agents))
    edge, mint, external, imported, exported = (numpy.zeros(most_agents, dtype=numpy.bool_), numpy.zeros(most_agents, dtype=numpy.bool_),
                                                numpy.zeros(most_agents, dtype=numpy.bool_), numpy.zeros(most_agents, dtype=numpy.bool_),
                                                numpy.zeros(most_agents, dtype=numpy.bool_))
    for market in range(markets):
        first_pair, first_agent, first_key = pair_offset[market], agent_offset[market], key_offset[market]
        pairs, agents, keys = pair_offset[market + 1] - first_pair, agent_offset[market + 1] - first_agent, key_offset[market + 1] - first_key
        if pairs == 0:
            continue
        for local in range(agents):
            agent = agent_global[first_agent + local]
            cash_start[local] = cash_state[agent]
            edge[local], mint[local], external[local] = agent_edge[agent], agent_mint[agent], agent_external[agent]
            imported[local], exported[local] = agent_import[agent], agent_export[agent]
        for local in range(keys):
            stock_start[local] = stock_state[key_global[first_key + local]]
        settle_market_into(first_pair, pairs, first_key, keys, first_agent, agents, buyer_key, seller_key, quantity, ask, delivers, sale,
                           key_agent, stock_start, cash_start, edge, mint, external, imported, exported, amounts, buyer_agent,
                           seller_agent, payer_here, unit, asked, scale, stock_left, owed, purse_scale, cash_left, goods, money, payer,
                           paid, received, goods_in, goods_out, buyer_net, got_goods, paid_as_buyer, imports, exports, key_given,
                           key_taken, key_to_mint)
        for local in range(agents):
            agent = agent_global[first_agent + local]
            cash_state[agent] = cash_state[agent] - paid[first_agent + local] + received[first_agent + local]
            batch_paid[agent] += paid[first_agent + local]
            batch_received[agent] += received[first_agent + local]
        if delivers:
            for local in range(keys):
                key = key_global[first_key + local]
                stock_state[key] = stock_state[key] - key_given[first_key + local] + key_taken[first_key + local]
                batch_given[key] += key_given[first_key + local]
                batch_taken[key] += key_taken[first_key + local]
    return (goods, money, payer, paid, received, goods_in, goods_out, buyer_net, got_goods, paid_as_buyer, imports, exports,
            key_given, key_taken, key_to_mint, batch_paid, batch_received, batch_given, batch_taken)
