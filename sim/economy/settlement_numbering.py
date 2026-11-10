"""The numbering of a batch's (agent, tile) keys and agents market by market, shared by the settlements that pack names
(`settlement_batch.settle_packed`) and by the one that reads ids from the order tables (`settlement_ids.py`).

A batch numbers its keys and agents once, in order of first use. Each market's own keys and agents are those its pairs use,
listed in the batch's numbering; a batch of one market lists all of the batch's keys and agents (a key a pair does not use
settles nothing but is listed)."""
import numpy


def local_numbering(sizes: numpy.ndarray, receipt: numpy.ndarray, seller: numpy.ndarray, key_agent: numpy.ndarray,
                    agent_total: int) -> tuple:
    """(pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent_local) for markets with
    `sizes` pairs one after another, whose pairs are paid to the batch keys `receipt` (the buyer's) and sold from `seller`.
    `key_agent[key]` is the batch agent of a batch key. `buyer_key` and `seller_key` are numbers within the pair's market, and
    `key_global` and `agent_global` say which batch key or agent each of a market's keys or agents is; offsets cut the
    concatenations by market, `key_agent_local` gives each key's agent within its market."""
    markets, key_total = len(sizes), len(key_agent)
    pair_offset = numpy.concatenate(([0], numpy.cumsum(sizes))).astype(numpy.int64)
    pair_count = int(pair_offset[-1])
    market_ids = numpy.arange(markets + 1, dtype=numpy.int64)
    if markets == 1:         # the batch's keys and agents are the market's own
        key_global, agent_global = numpy.arange(key_total, dtype=numpy.int64), numpy.arange(agent_total, dtype=numpy.int64)
        key_offset, agent_offset = numpy.array([0, key_total], dtype=numpy.int64), numpy.array([0, agent_total], dtype=numpy.int64)
        return pair_offset, agent_offset, key_offset, receipt, seller, key_global, agent_global, key_agent.astype(numpy.int64)
    market_of_pair = numpy.repeat(market_ids[:-1], sizes)
    unique, inverse = numpy.unique(numpy.concatenate((market_of_pair * key_total + receipt, market_of_pair * key_total + seller)),
                                   return_inverse=True)
    key_market, key_global = unique // key_total, unique % key_total
    key_offset = numpy.searchsorted(key_market, market_ids).astype(numpy.int64)
    shift = key_offset[market_of_pair]
    inverse = inverse.reshape(-1)
    buyer_key, seller_key = inverse[:pair_count] - shift, inverse[pair_count:] - shift
    unique_agents, agent_inverse = numpy.unique(key_market * agent_total + key_agent[key_global], return_inverse=True)
    agent_market, agent_global = unique_agents // agent_total, unique_agents % agent_total
    agent_offset = numpy.searchsorted(agent_market, market_ids).astype(numpy.int64)
    key_agent_local = agent_inverse.reshape(-1) - agent_offset[key_market]
    return pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent_local
