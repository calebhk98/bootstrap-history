"""Every merchant's carriers kept and worn in two passes over the book (`carriage_wear.settle` for all of them).

`settle_all` moves the carriers each merchant bought into its carrier account, then uses up the wear each merchant's shipments put on the
stock there. A merchant's moves are the ones `settle` made; the passes read the book's stock rows by kernel and build the moves
the book is handed (`GoodsMove`) only for the rows that move."""
from typing import Dict, List, Mapping, Sequence

import numpy

from . import carriage_wear, merchant_year_kernels
from .carriage_wear_kernel import wear_takes
from .types import EDGE_CONSUMPTION, GoodsMove


def _ordered_rows(book, agents: Sequence[str], good_names_wanted: Sequence[str]):
    """(position of the agent, good number, tile number, quantity, name rank of good, name rank of tile) of the positive stock of the
    wanted goods that the agents hold, ordered by agent position, good name, then tile name."""
    numbers = book.agent_ids.numbers
    agent_numbers = numpy.array([numbers.get(agent, -1) for agent in agents], numpy.int64)
    first = numpy.where(agent_numbers >= 0, book.agent_table.first_slot[numpy.where(agent_numbers >= 0, agent_numbers, 0)], -1)
    table = book.stock_rows.table
    owner, good, tile, quantity = merchant_year_kernels.merchant_stock(first, table.next_in_agent, table.good, table.tile, table.quantity)
    wanted = numpy.zeros(len(book.good_ids), numpy.bool_)
    for name in good_names_wanted:
        number = book.good_ids.numbers.get(name)
        if number is not None:
            wanted[number] = True
    keep = wanted[good]
    owner, good, tile, quantity = owner[keep], good[keep], tile[keep], quantity[keep]
    good_names, tile_names = book.good_ids.name_list, book.tile_ids.name_list
    good_rank = numpy.argsort(numpy.argsort(numpy.array(good_names))) if len(good_names) else numpy.zeros(0, numpy.int64)
    tile_rank = numpy.argsort(numpy.argsort(numpy.array(tile_names))) if len(tile_names) else numpy.zeros(0, numpy.int64)
    order = numpy.lexsort((tile_rank[tile], good_rank[good], owner)) if len(owner) else numpy.zeros(0, numpy.int64)
    return owner[order], good[order], tile[order], quantity[order]


def settle_all(book, merchant_ids: Sequence[str], goods: Sequence[str], units_worn: Mapping[str, Mapping[str, float]]) -> List[GoodsMove]:
    """`carriage_wear.settle` for each merchant of `merchant_ids` (in order; `units_worn[id]` is the units it wore, by carrier good).
    Returns the moves made, the keeping ones first."""
    if not merchant_ids or not goods:
        return []
    good_names, tile_names = book.good_ids.name_list, book.tile_ids.name_list
    owner, good, tile, quantity = _ordered_rows(book, merchant_ids, goods)
    kept = [GoodsMove(merchant_ids[agent], carriage_wear.account(merchant_ids[agent]), good_names[each_good], tile_names[each_tile], amount,
                      "carriers kept")
            for agent, each_good, each_tile, amount in zip(owner.tolist(), good.tolist(), tile.tolist(), quantity.tolist())]
    book.move_many(kept)
    if not any(units_worn.get(merchant) for merchant in merchant_ids):
        return kept
    accounts = [carriage_wear.account(merchant) for merchant in merchant_ids]
    owner, good, tile, quantity = _ordered_rows(book, accounts, sorted({name for each in units_worn.values() for name in each}))
    wanted = numpy.array([units_worn.get(merchant_ids[agent], {}).get(good_names[each_good], 0.0)
                          for agent, each_good in zip(owner.tolist(), good.tolist())])
    taken = wear_takes(owner * (int(good.max()) + 1 if len(good) else 1) + good, wanted, quantity)
    worn = [GoodsMove(accounts[agent], EDGE_CONSUMPTION, good_names[each_good], tile_names[each_tile], amount, "carriage wear")
            for agent, each_good, each_tile, amount in zip(owner[taken > 0.0].tolist(), good[taken > 0.0].tolist(), tile[taken > 0.0].tolist(),
                                                           taken[taken > 0.0].tolist())]
    book.move_many(worn)
    return kept + worn
