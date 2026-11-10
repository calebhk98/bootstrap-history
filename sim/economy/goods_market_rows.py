"""A cleared market as rows of the order tables, for the rules that run after the clearing (the respend rounds, the market
memory's notes): its first-round bids, and the offers that were left, read as plain Python lists of the columns instead of
as `Bid` and `Offer` objects.

`OrderLists` holds every bid's (or offer's) columns as lists, made once; a market's rows index into them."""
import math
from typing import List, Sequence

import numpy

from .goods_market import _quantity, quantity_at
from .goods_table_views import LazyObjects
from .types import EDGE_EXTERNAL, QUOTE_BEST_UNFILLED_BID, QUOTE_COST_COVERING, Bid, Offer, Quote

class BidLists:
    """The columns of every bid row as lists (the table's `.tolist()` once), with the buyer and tile as names."""

    def __init__(self, orders):
        bids, _offers = orders.tables()
        count = int(bids.row_count[0])
        agents, tiles, goods = orders.book.agent_ids.name_list, orders.book.tile_ids.name_list, orders.book.good_ids.name_list
        areas = orders.memory_tables.areas.name_list
        self.buyer = [agents[each] for each in bids.buyer[:count].tolist()]
        self.good = [goods[each] for each in bids.good[:count].tolist()]
        self.area = [areas[each] for each in orders.memory_tables.goods_table.area[bids.market[:count]].tolist()]
        self.priority = bids.priority[:count].tolist()
        self.floor_quantity = bids.floor_quantity[:count].tolist()
        self.flexible_quantity = bids.flexible_quantity[:count].tolist()
        self.reference_price = bids.reference_price[:count].tolist()
        self.elasticity = bids.elasticity[:count].tolist()
        self.budget = bids.budget[:count].tolist()
        self.maximum_price = bids.maximum_price[:count].tolist()
        self.tile = [tiles[each] for each in bids.tile[:count].tolist()]


def wanted_at_rows(lists: BidLists, rows: Sequence[int], price: float, more_bids: Sequence[Bid] = (), added=None) -> float:
    """`market_memory_asks.wanted_at` over bid rows, some more `Bid` objects and the bids later rounds added (`AddedBids`, columns):
    what the market's own buyers would take at the price (the foreign partner's order left out), zero without a positive price."""
    if not price or price <= 0.0:
        return 0.0
    wanted = [_wanted(lists, row, price) for row in rows if lists.buyer[row] != EDGE_EXTERNAL]
    wanted.extend(quantity_at(bid, price) for bid in more_bids if bid.buyer != EDGE_EXTERNAL)
    if added is not None:
        wanted.extend(quantity for buyer, quantity in zip(added.buyer, added.quantities_at(price)) if buyer != EDGE_EXTERNAL)
    return math.fsum(wanted)


def _wanted(lists: BidLists, row: int, price: float) -> float:
    """`goods_market.quantity_at` of one bid row at a price."""
    budget = lists.budget[row]
    if budget <= 0.0 or price > lists.maximum_price[row]:
        return 0.0
    if price <= 0.0:
        return lists.floor_quantity[row] + lists.flexible_quantity[row]
    return _quantity(lists.floor_quantity[row], lists.flexible_quantity[row], lists.reference_price[row], lists.elasticity[row],
                     budget, price)


class MarketRows:
    """The rows of a cleared market: `bid_rows` and `offer_rows` (arrival order) and the rows of the offers left (in the order
    the old lists kept them)."""

    def __init__(self, orders, bid_rows: Sequence[int], left_rows: Sequence[int], offer_rows: Sequence[int] = ()):
        self.orders = orders
        self.bid_array = numpy.asarray(bid_rows, dtype=numpy.int64)      # the same rows as arrays, for the readers of whole columns
        self.left_array = numpy.asarray(left_rows, dtype=numpy.int64)
        self.offer_array = numpy.asarray(offer_rows, dtype=numpy.int64)
        self._lists = {}

    def _list_of(self, name: str, array: numpy.ndarray) -> list:
        """The rows as a list, made when first read (most markets are read as arrays only)."""
        found = self._lists.get(name)
        if found is None:
            found = self._lists[name] = array.tolist()
        return found

    @property
    def bid_rows(self) -> list:
        return self._list_of("bid", self.bid_array)

    @property
    def left_rows(self) -> list:
        return self._list_of("left", self.left_array)

    @property
    def offer_rows(self) -> list:
        return self._list_of("offer", self.offer_array)

    def bids_lazy(self) -> LazyObjects:
        """The market's bids as objects, built when first read."""
        return LazyObjects(lambda: self.orders.bids_of(self.bid_rows), len(self.bid_rows))

    def offers_lazy(self) -> LazyObjects:
        """All the market's offers (with the reservations the clearing chose) as objects, built when first read."""
        return LazyObjects(lambda: self.orders.offers_of(self.offer_rows), len(self.offer_rows))

    def left_lazy(self) -> LazyObjects:
        """The offers with units left, with those units, as objects, built when first read."""
        return LazyObjects(lambda: self.orders.offers_of(self.left_rows, self.orders.tables()[1].quantity_left[self.left_rows]),
                           len(self.left_rows))

    def offer_objects(self, quantities: Sequence[float]) -> List[Offer]:
        """`Offer` objects for the offers left with the given units (those with none dropped)."""
        keep = [place for place, units in enumerate(quantities) if units > 0.0]
        rows = numpy.array([self.left_rows[place] for place in keep], dtype=numpy.int64)
        return self.orders.offers_of(rows, [quantities[place] for place in keep])


def bids_only_quote(lists: BidLists, rows: Sequence[int], cost):
    """`market_quote.no_trade_quote(bids, [], cost)` over bid rows: a market where buyers bid and nobody offers quotes what a
    maker would have to ask to cover a unit's cost, else the best unfilled bid; None when it posts nothing to quote."""
    funded = False
    best = None
    for row in rows:
        if lists.budget[row] > 0.0:
            funded = True
            ceiling = lists.maximum_price[row]
            if math.isfinite(ceiling) and ceiling > 0.0 and (best is None or ceiling > best):
                best = ceiling
    if cost is not None and cost > 0.0 and funded:
        return Quote(QUOTE_COST_COVERING, cost)
    return Quote(QUOTE_BEST_UNFILLED_BID, best) if best is not None else None
