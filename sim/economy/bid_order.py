"""The clearing order of a market's bids from the order tables' rows and the later rounds' added bids, without making `Bid` objects.

`goods_market.Buyers` sorts bids by (priority, buyer name, tile name), a stable sort over the bids in the order they reached the
book and then the added ones. `clearing_order` returns the same permutation as indexes into those bids' columns."""
import numpy

from .goods_respend import RESPEND_PRIORITY


def _ranks(names) -> numpy.ndarray:
    """Per entry: the place of its name among the distinct names sorted as text (equal names, equal ranks)."""
    place = {name: rank for rank, name in enumerate(sorted(set(names)))}
    return numpy.fromiter((place[name] for name in names), dtype=numpy.int64, count=len(names))


def clearing_order(rows, added) -> numpy.ndarray:
    """`rows` is the market's `goods_market_rows.MarketRows`, `added` its later rounds' `AddedBids` (or None)."""
    orders = rows.orders
    table = orders.tables()[0]
    agents, tiles = orders.book.agent_ids.name_list, orders.book.tile_ids.name_list
    selected = rows.bid_array
    buyers = [agents[each] for each in table.buyer[selected].tolist()]
    places = [tiles[each] for each in table.tile[selected].tolist()]
    priority = table.priority[selected].astype(numpy.float64)
    if added is not None and len(added):
        buyers += added.buyer
        places += added.tile
        priority = numpy.concatenate((priority, numpy.full(len(added), float(RESPEND_PRIORITY))))
    return numpy.lexsort((_ranks(places), _ranks(buyers), priority)).astype(numpy.int64)
