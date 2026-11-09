"""What agents hold, read as columns and turned into names once: the engine behind `Book.goods_of`, `goods_held` and `goods_held_many`.

The stock slots of every asked agent are gathered by one kernel (sim/book_holdings_kernels.py), the rows are put in name order with
one sort (goods and tiles by their rank among the names, `IdTable.name_rank`), and the nested dictionaries are written in a single pass
over the sorted rows, so no row costs a dictionary lookup."""
from typing import Dict, List, Sequence

import numpy

from sim.book_holdings_kernels import many_holder_columns
from sim.book_types import AgentId, GoodId, TileId

Held = Dict[GoodId, Dict[TileId, float]]


def first_slots_of(book, agents: Sequence[AgentId]) -> numpy.ndarray:
    """Each agent's first stock slot, -1 for an agent the book has no number for or that has no slot."""
    numbers = book.agent_ids.numbers_of(agents)
    return numpy.where(numbers >= 0, book.agent_table.first_slot[numbers.clip(0)], -1)


def creation_order(owner: numpy.ndarray, goods: numpy.ndarray, good_count: int) -> numpy.ndarray:
    """The row order that groups each agent's rows by good, goods in the order the agent's first slot of each was made and rows of
    one good in the order they were made."""
    _pairs, first, inverse = numpy.unique(owner * good_count + goods, return_index=True, return_inverse=True)
    return numpy.lexsort((numpy.arange(len(owner)), first[inverse.reshape(-1)], owner))


def goods_of_many(book, agents: Sequence[AgentId], keep_zeros: bool, by_name: bool) -> List[Held]:
    """For each agent, what it holds as good to tile to quantity; a slot at zero is left out unless `keep_zeros`. With `by_name` goods and
    tiles are in name order, else in the order the slots were made (a good where the agent first got it). An agent the book never saw
    holds `{}`."""
    table = book.stock_rows.table
    starts, owner, goods, tiles, quantities = many_holder_columns(
        first_slots_of(book, agents), table.next_in_agent, table.good, table.tile, table.quantity)
    if not keep_zeros:
        kept = quantities != 0.0
        owner, goods, tiles, quantities = owner[kept], goods[kept], tiles[kept], quantities[kept]
    if by_name:
        order = numpy.lexsort((book.tile_ids.name_rank()[tiles], book.good_ids.name_rank()[goods], owner))
    else:
        order = creation_order(owner, goods, len(book.good_ids))
    cut = numpy.searchsorted(owner[order], numpy.arange(len(agents) + 1)).tolist()
    goods, tiles, quantities = goods[order].tolist(), tiles[order].tolist(), quantities[order].tolist()
    good_names, tile_names = book.good_ids.name_list, book.tile_ids.name_list
    return [nested(goods[first:last], tiles[first:last], quantities[first:last], good_names, tile_names)
            for first, last in zip(cut[:-1], cut[1:])]


def nested(goods: List[int], tiles: List[int], quantities: List[float], good_names: List[GoodId], tile_names: List[TileId]) -> Held:
    """Rows already sorted by good then tile as good name to tile name to quantity."""
    held: Held = {}
    previous = -1
    by_tile: Dict[TileId, float] = {}
    for good, tile, quantity in zip(goods, tiles, quantities):
        if good != previous:
            by_tile = held[good_names[good]] = {}
            previous = good
        by_tile[tile_names[tile]] = quantity
    return held
