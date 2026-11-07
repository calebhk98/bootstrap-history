"""A market's settlement as one numba kernel over its pairs (settlement.py packs and unpacks).

A pair is a quantity one buyer bought from one seller at that seller's ask. The kernel scales each seller's pairs down to
the stock it holds, each payer's pairs down to the money it holds, walks the pairs in order taking what is still there,
and sums what each agent, each (agent, tile) key and each ledger line saw. Every sum runs left to right over the pairs.
"""
import numpy

from sim.jit import njit

KERNEL = {"error_model": "numpy"}


@njit(**KERNEL)
def settle_pairs(buyer_key, seller_key, quantity, ask, delivers, sale, key_agent, key_stock, agent_cash, agent_edge,
                 agent_mint, agent_external, agent_import, agent_export):
    """Settle `quantity[pair]` from `seller_key[pair]` to `buyer_key[pair]` (indices into the market's (agent, tile) keys;
    `key_agent` is each key's agent index) at the seller's signed `ask`: a negative ask reverses who pays.
    `key_stock` and `agent_cash` are what keys and agents hold; edge agents are never limited. `delivers`: goods move
    (a labour market moves only money). `sale`: the purpose names a goods sale, so the import and export accounts apply.

    Returns per pair: the goods moved, the money paid, the payer's agent; per agent: money paid, money received, goods
    received, goods given, buyer money (net paid as a buyer), whether it received goods, whether it paid as a buyer, the
    import and export figures of the ledger (`YearLedger._note_foreign`); per key: goods given, goods taken, goods
    delivered to the mint."""
    pairs = len(quantity)
    agents = len(agent_cash)
    keys = len(key_agent)
    amounts = quantity.copy()
    payer = numpy.zeros(pairs, dtype=numpy.int64)
    unit = numpy.zeros(pairs)
    for pair in range(pairs):
        if ask[pair] >= 0.0:
            payer[pair] = key_agent[buyer_key[pair]]
        else:
            payer[pair] = key_agent[seller_key[pair]]
        unit[pair] = abs(ask[pair])
    if delivers:
        asked = numpy.zeros(keys)
        for pair in range(pairs):
            asked[seller_key[pair]] += amounts[pair]
        scale = numpy.ones(keys)
        for key in range(keys):
            if asked[key] > key_stock[key] and not agent_edge[key_agent[key]]:
                scale[key] = max(key_stock[key], 0.0) / asked[key]
        for pair in range(pairs):
            amounts[pair] *= scale[seller_key[pair]]
    owed = numpy.zeros(agents)
    for pair in range(pairs):
        owed[payer[pair]] += amounts[pair] * unit[pair]
    purse_scale = numpy.ones(agents)
    for agent in range(agents):
        if owed[agent] > agent_cash[agent] and not agent_edge[agent]:
            purse_scale[agent] = max(agent_cash[agent], 0.0) / owed[agent]
    for pair in range(pairs):
        amounts[pair] *= purse_scale[payer[pair]]

    goods = numpy.zeros(pairs)
    money = numpy.zeros(pairs)
    stock_left = key_stock.copy()
    cash_left = agent_cash.copy()
    paid = numpy.zeros(agents)
    received = numpy.zeros(agents)
    goods_in = numpy.zeros(agents)
    goods_out = numpy.zeros(agents)
    buyer_money = numpy.zeros(agents)
    got_goods = numpy.zeros(agents, dtype=numpy.bool_)
    paid_as_buyer = numpy.zeros(agents, dtype=numpy.bool_)
    imports = numpy.zeros(agents)
    exports = numpy.zeros(agents)
    key_given = numpy.zeros(keys)
    key_taken = numpy.zeros(keys)
    key_to_mint = numpy.zeros(keys)
    for pair in range(pairs):
        amount = amounts[pair]
        if amount <= 0.0:
            continue
        buyer = key_agent[buyer_key[pair]]
        seller = key_agent[seller_key[pair]]
        if delivers:
            if not agent_edge[seller]:
                if stock_left[seller_key[pair]] < amount:
                    amount = stock_left[seller_key[pair]]
                stock_left[seller_key[pair]] -= amount
            goods[pair] = amount
            goods_in[buyer] += amount
            goods_out[seller] += amount
            got_goods[buyer] = True
            key_given[seller_key[pair]] += amount
            key_taken[buyer_key[pair]] += amount
            if agent_mint[buyer]:
                key_to_mint[seller_key[pair]] += amount
        paying = payer[pair]
        payee = buyer if ask[pair] < 0.0 else seller
        pay = amount * unit[pair]
        if not agent_edge[paying]:
            if cash_left[paying] < pay:
                pay = cash_left[paying]
            cash_left[paying] -= pay
        if pay > 0.0:
            money[pair] = pay
            paid[paying] += pay
            received[payee] += pay
            if paying == buyer:
                buyer_money[buyer] += pay
            else:
                buyer_money[buyer] -= pay
            paid_as_buyer[buyer] = True
            if agent_external[payee] and not agent_external[paying]:
                imports[paying] += pay
            elif agent_external[paying] and not agent_external[payee]:
                exports[payee] += pay
            elif sale and agent_import[payee]:
                imports[payee] += pay
            elif sale and agent_export[paying]:
                exports[paying] += pay
    return (goods, money, payer, paid, received, goods_in, goods_out, buyer_money, got_goods, paid_as_buyer, imports,
            exports, key_given, key_taken, key_to_mint)
