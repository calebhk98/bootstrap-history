"""One market's settlement written straight into a batch's output arrays (`settlement_batch_kernel.settle_markets` calls it for each
market; `settlement_kernel.settle_pairs` is the same rules on arrays of its own, for the callers that settle one market).

The sums are `settle_pairs`' to the last digit: each is added left to right over the pairs, from zero. A market's keys and agents are
numbered `0 ..` within it; its scratch (the `Scratch` columns below) is sized once for the widest market of the batch and reused, so a
market allocates nothing, and what a pair needs of its agents (buyer, seller, payer, price) is looked up once, before the pair loops."""
import numpy

from sim.jit import njit


@njit
def widest(offsets):
    """The largest difference between neighbouring offsets."""
    most = 0
    for place in range(len(offsets) - 1):
        most = max(most, offsets[place + 1] - offsets[place])
    return most


@njit
def resolve_pairs(first_pair, pairs, first_key, keys, delivers, buyer_key, seller_key, quantity, ask, key_agent, amounts, buyer_agent,
                  seller_agent, payer, payer_out, unit, asked):
    """Per pair of the market: the quantity asked, the agent that buys, the agent that sells, the agent that pays (the buyer, or the
    seller when the ask is negative) and the price paid per unit; and, when goods move, per key the quantity asked of it."""
    for key in range(keys):
        asked[key] = 0.0
    for pair in range(pairs):
        amounts[pair] = quantity[first_pair + pair]
        if delivers:
            asked[seller_key[first_pair + pair]] += amounts[pair]
        buyer_agent[pair] = key_agent[first_key + buyer_key[first_pair + pair]]
        seller_agent[pair] = key_agent[first_key + seller_key[first_pair + pair]]
        price = ask[first_pair + pair]
        payer[pair] = buyer_agent[pair] if price >= 0.0 else seller_agent[pair]
        payer_out[first_pair + pair] = payer[pair]
        unit[pair] = abs(price)


@njit
def stock_scales(first_key, keys, key_agent, stock_start, edge, asked, scale):
    """Per key the share of the quantity asked of it that its stock covers (one for an edge account, which is never limited).
    Returns whether any key is short."""
    short = False
    for key in range(keys):
        scale[key] = 1.0
        if asked[key] > stock_start[key] and not edge[key_agent[first_key + key]]:
            scale[key] = max(stock_start[key], 0.0) / asked[key]
            short = True
    return short


@njit
def sum_owed(first_pair, pairs, seller_key, short, scale, payer, unit, amounts, owed):
    """Each seller key's pairs scaled down by its key's `scale` (when some key is short; else they stay as they are), and what each
    payer owes for them."""
    for pair in range(pairs):
        if short:
            amounts[pair] *= scale[seller_key[first_pair + pair]]
        owed[payer[pair]] += amounts[pair] * unit[pair]


@njit
def purse_scales(agents, cash_start, edge, owed, purse_scale):
    """Per agent the share of what it owes that its purse covers (one for an edge account). `settle_market_into` multiplies each pair's
    amount by its payer's share as it walks the pairs."""
    for agent in range(agents):
        purse_scale[agent] = 1.0
        if owed[agent] > cash_start[agent] and not edge[agent]:
            purse_scale[agent] = max(cash_start[agent], 0.0) / owed[agent]


@njit
def settle_market_into(first_pair, pairs, first_key, keys, first_agent, agents, buyer_key, seller_key, quantity, ask, delivers, sale,
                       key_agent, stock_start, cash_start, edge, mint, external, imported, exported, amounts, buyer_agent, seller_agent,
                       payer, unit, asked, scale, stock_left, owed, purse_scale, cash_left, goods_moved, money_paid, payer_out, paid, received,
                       goods_in, goods_out, buyer_money, got_goods, paid_as_buyer, imports, exports, key_given, key_taken, key_to_mint):
    """Settle one market: `first_pair`, `first_key` and `first_agent` say where its pairs, keys and agents start in the batch's columns
    (`buyer_key`, `seller_key`, `quantity`, `ask`, `key_agent` and the outputs); `stock_start` and `cash_start` are what its keys and
    agents hold, the flags are per agent, and the arrays after `payer` are scratch sized for the batch's widest market. The sums are
    added into the outputs, which start at zero. Each rule is `settle_pairs`'."""
    resolve_pairs(first_pair, pairs, first_key, keys, delivers, buyer_key, seller_key, quantity, ask, key_agent, amounts, buyer_agent,
                  seller_agent, payer, payer_out, unit, asked)
    short = delivers and stock_scales(first_key, keys, key_agent, stock_start, edge, asked, scale)
    for agent in range(agents):
        owed[agent] = 0.0
    sum_owed(first_pair, pairs, seller_key, short, scale, payer, unit, amounts, owed)
    purse_scales(agents, cash_start, edge, owed, purse_scale)
    for key in range(keys):
        stock_left[key] = stock_start[key]
    for agent in range(agents):
        cash_left[agent] = cash_start[agent]
    for pair in range(pairs):
        amount = amounts[pair] * purse_scale[payer[pair]]
        if amount <= 0.0:
            continue
        buyer, seller = buyer_agent[pair], seller_agent[pair]
        seller_cell, buyer_cell = first_key + seller_key[first_pair + pair], first_key + buyer_key[first_pair + pair]
        if delivers:
            if not edge[seller]:
                if stock_left[seller_key[first_pair + pair]] < amount:
                    amount = stock_left[seller_key[first_pair + pair]]
                stock_left[seller_key[first_pair + pair]] -= amount
            goods_moved[first_pair + pair] = amount
            goods_in[first_agent + buyer] += amount
            goods_out[first_agent + seller] += amount
            got_goods[first_agent + buyer] = True
            key_given[seller_cell] += amount
            key_taken[buyer_cell] += amount
            if mint[buyer]:
                key_to_mint[seller_cell] += amount
        paying = payer[pair]
        payee = buyer if ask[first_pair + pair] < 0.0 else seller
        pay = amount * unit[pair]
        if not edge[paying]:
            if cash_left[paying] < pay:
                pay = cash_left[paying]
            cash_left[paying] -= pay
        if pay > 0.0:
            money_paid[first_pair + pair] = pay
            paid[first_agent + paying] += pay
            received[first_agent + payee] += pay
            if paying == buyer:
                buyer_money[first_agent + buyer] += pay
            else:
                buyer_money[first_agent + buyer] -= pay
            paid_as_buyer[first_agent + buyer] = True
            if external[payee] and not external[paying]:
                imports[first_agent + paying] += pay
            elif external[paying] and not external[payee]:
                exports[first_agent + payee] += pay
            elif sale and imported[payee]:
                imports[first_agent + payee] += pay
            elif sale and exported[paying]:
                exports[first_agent + paying] += pay
