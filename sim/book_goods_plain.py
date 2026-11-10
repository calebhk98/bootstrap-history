"""The book's goods stock as nested plain data, {holder: {good: {tile: quantity}}}, holders, goods and tiles in name order."""
import numpy


def goods_nested(agents, goods, tiles, quantities, agent_ids, good_ids, tile_ids) -> dict:
    """The stock rows (parallel arrays of agent, good and tile numbers and quantities) as nested dicts; a (holder, good, tile) that
    occurs twice keeps its last row in name order, ties going by quantity."""
    agent_rank, good_rank, tile_rank = agent_ids.name_rank(), good_ids.name_rank(), tile_ids.name_rank()
    order = numpy.lexsort((tile_rank[tiles], good_rank[goods], agent_rank[agents]))
    agents, goods, tiles, quantities = agents[order], goods[order], tiles[order], quantities[order]
    if len(order) > 1 and (numpy.diff(agents) == 0)[(numpy.diff(goods) == 0) & (numpy.diff(tiles) == 0)].any():
        return _by_sorting_rows(agents, goods, tiles, quantities, agent_ids, good_ids, tile_ids)
    agent_names, good_names, tile_names = agent_ids.name_list, good_ids.name_list, tile_ids.name_list
    nested: dict = {}
    last_agent = last_good = None
    for agent, good, tile, quantity in zip(agents.tolist(), goods.tolist(), tiles.tolist(), quantities.tolist()):
        if agent != last_agent:
            by_good = nested[agent_names[agent]] = {}
            last_agent, last_good = agent, None
        if good != last_good:
            by_tile = by_good[good_names[good]] = {}
            last_good = good
        by_tile[tile_names[tile]] = quantity
    return nested


def _by_sorting_rows(agents, goods, tiles, quantities, agent_ids, good_ids, tile_ids) -> dict:
    """The same by sorting the rows as tuples of names and quantity."""
    entries = sorted(zip([agent_ids.name(number) for number in agents.tolist()], [good_ids.name(number) for number in goods.tolist()],
                         [tile_ids.name(number) for number in tiles.tolist()], quantities.tolist()))
    nested: dict = {}
    for holder, kind, place, quantity in entries:
        nested.setdefault(holder, {}).setdefault(kind, {})[place] = quantity
    return nested


def money_nested(agents, currencies, amounts, agent_ids, currency_ids) -> dict:
    """{holder: {currency: amount}} from parallel arrays of agent and currency numbers (each pair once) and amounts, both levels in name order."""
    order = numpy.lexsort((currency_ids.name_rank()[currencies], agent_ids.name_rank()[agents]))
    agent_names, currency_names = agent_ids.name_list, currency_ids.name_list
    nested: dict = {}
    last_agent = None
    for agent, currency, amount in zip(agents[order].tolist(), currencies[order].tolist(), amounts[order].tolist()):
        if agent != last_agent:
            by_currency = nested[agent_names[agent]] = {}
            last_agent = agent
        by_currency[currency_names[currency]] = amount
    return nested
