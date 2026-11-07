"""Many markets' settlements in one numba kernel call (settlement_batch.py packs and unpacks).

The markets are settled one after another in the order given, each as `settlement_kernel.settle_pairs` settles one, but the
stock of every (agent, tile) key and the money of every agent are carried from one market to the next, so a market sees what
the markets before it left. The markets' own sums come back by market (concatenated, cut at the offsets); the batch's sums
per agent and per key come back for one posting on the book.
"""
import numpy

from sim.jit import njit

from .settlement_kernel import KERNEL, settle_pairs


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
    for market in range(markets):
        first_pair, last_pair = pair_offset[market], pair_offset[market + 1]
        first_agent, last_agent = agent_offset[market], agent_offset[market + 1]
        first_key, last_key = key_offset[market], key_offset[market + 1]
        if last_pair == first_pair:
            continue
        agents_here = agent_global[first_agent:last_agent]
        keys_here = key_global[first_key:last_key]
        (market_goods, market_money, market_payer, market_paid, market_received, market_in, market_out, market_net,
         market_got, market_paid_as_buyer, market_imports, market_exports, market_given, market_taken,
         market_to_mint) = settle_pairs(
            buyer_key[first_pair:last_pair], seller_key[first_pair:last_pair], quantity[first_pair:last_pair],
            ask[first_pair:last_pair], delivers, sale, key_agent[first_key:last_key], stock_state[keys_here],
            cash_state[agents_here], agent_edge[agents_here], agent_mint[agents_here], agent_external[agents_here],
            agent_import[agents_here], agent_export[agents_here])
        goods[first_pair:last_pair] = market_goods
        money[first_pair:last_pair] = market_money
        payer[first_pair:last_pair] = market_payer
        paid[first_agent:last_agent] = market_paid
        received[first_agent:last_agent] = market_received
        goods_in[first_agent:last_agent] = market_in
        goods_out[first_agent:last_agent] = market_out
        buyer_net[first_agent:last_agent] = market_net
        got_goods[first_agent:last_agent] = market_got
        paid_as_buyer[first_agent:last_agent] = market_paid_as_buyer
        imports[first_agent:last_agent] = market_imports
        exports[first_agent:last_agent] = market_exports
        key_given[first_key:last_key] = market_given
        key_taken[first_key:last_key] = market_taken
        key_to_mint[first_key:last_key] = market_to_mint
        for local in range(last_agent - first_agent):
            agent = agents_here[local]
            cash_state[agent] = cash_state[agent] - market_paid[local] + market_received[local]
            batch_paid[agent] += market_paid[local]
            batch_received[agent] += market_received[local]
        if delivers:
            for local in range(last_key - first_key):
                key = keys_here[local]
                stock_state[key] = stock_state[key] - market_given[local] + market_taken[local]
                batch_given[key] += market_given[local]
                batch_taken[key] += market_taken[local]
    return (goods, money, payer, paid, received, goods_in, goods_out, buyer_net, got_goods, paid_as_buyer, imports, exports,
            key_given, key_taken, key_to_mint, batch_paid, batch_received, batch_given, batch_taken)
