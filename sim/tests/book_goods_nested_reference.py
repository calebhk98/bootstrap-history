"""`Book._goods_record` as it was: the rows as tuples of names, sorted."""


def nested_by_tuples(agents, goods, tiles, quantities, agent_ids, good_ids, tile_ids):
    entries = sorted(zip([agent_ids.name(number) for number in agents.tolist()], [good_ids.name(number) for number in goods.tolist()],
                         [tile_ids.name(number) for number in tiles.tolist()], quantities.tolist()))
    goods_by_holder = {}
    for holder, kind, place, quantity in entries:
        goods_by_holder.setdefault(holder, {}).setdefault(kind, {})[place] = quantity
    return goods_by_holder


def money_by_loop(agents, currencies, amounts, agent_ids, currency_ids):
    """`Book._money_record` as it was: the pairs set into dicts, then both levels sorted."""
    money = {}
    for number, currency_number, amount in zip(agents.tolist(), currencies.tolist(), amounts.tolist()):
        money.setdefault(agent_ids.name(number), {})[currency_ids.name(currency_number)] = amount
    return {agent: dict(sorted(by_currency.items())) for agent, by_currency in sorted(money.items())}
