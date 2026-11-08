"""The book of orders: the year's goods bids and offers as the tables of goods_order_tables.py.

`GoodsOrderBook` is what `year_goods.clear_goods` clears. Writers reach it two ways:

  * a kernel's rows are appended whole (`append_bids`, `append_offers`: arrays of ids and figures, no object made);
  * everything else keeps handing over `Bid` and `Offer` objects, through `add_orders` or the dict-shaped door legacy
    writers use (`book.setdefault((good, area), ([], []))[0].append(bid)`): the object waits in a list and is turned into
    a row, in arrival order, the next time anyone reads the tables (`flush`).

Rows keep the order they arrived in, so a market's bids and offers are in the same order the lists of the old dict held.
Names become ids at the boundary (`book.agent_number`, `book.good_number`, `book.tile_number`, the memory's goods market
for `good|area`); objects are rebuilt from rows only at the edge (`bids_of`, `offers_of`)."""
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy

from sim.compiled_tables.growth import reserve_rows

from .goods_order_tables import (BID_ORDER, GOODS_BIDS, GOODS_MARKET_RESULTS, GOODS_OFFERS, GOODS_PAIRS, OFFER_ORDER, OTHER, BidOrder,
                                 GoodsBids, GoodsMarketResults, GoodsOffers, GoodsPairs, OfferOrder)
from .goods_order_objects import make_bid, make_offer
from .market_memory import market_key
from .protocols import AgentOrders
from .types import Bid, Offer

_FIRST_CAPACITY = 1024
_BID_FIGURES = 6
UNCLEARED = -1


def blank_bid_results(table, first: int, last: int) -> None:
    """Rows `first .. last - 1` of the bids table have not been cleared: no place in clearing order."""
    table.position[first:last] = UNCLEARED


def blank_offer_results(table, first: int, last: int) -> None:
    """Rows `first .. last - 1` of the offers table have not been cleared: no rank, and no stock slot found yet."""
    table.rank[first:last] = UNCLEARED
    table.stock_slot[first:last] = UNCLEARED


class _Sink:
    """What a legacy writer appends to: `append` hands the order to the book, which keeps it in arrival order."""

    def __init__(self, add, source: int):
        self._add, self._source = add, source

    def append(self, order) -> None:
        self._add(order, self._source)

    def extend(self, orders: Iterable) -> None:
        for order in orders:
            self._add(order, self._source)


class GoodsOrderBook:
    """The goods bids and offers of one year, with the ids they are numbered by."""

    def __init__(self, book, memory_tables):
        self.book = book
        self.memory_tables = memory_tables
        self.bids = GOODS_BIDS.new_table(GoodsBids, _FIRST_CAPACITY)
        self.offers = GOODS_OFFERS.new_table(GoodsOffers, _FIRST_CAPACITY)
        self.results = GOODS_MARKET_RESULTS.new_table(GoodsMarketResults, _FIRST_CAPACITY)
        self.pairs = GOODS_PAIRS.new_table(GoodsPairs, _FIRST_CAPACITY)
        self.bid_order = BID_ORDER.new_table(BidOrder, _FIRST_CAPACITY)
        self.offer_order = OFFER_ORDER.new_table(OfferOrder, _FIRST_CAPACITY)
        self._waiting_bids: List[Tuple[Bid, int]] = []
        self._waiting_offers: List[Tuple[Offer, int]] = []
        self._markets: Dict[Tuple[str, str], int] = {}
        self._bid_lists = None
        self._sinks = (_Sink(self.add_bid, OTHER), _Sink(self.add_offer, OTHER))
        self._numbers = ({}, {}, {})          # name -> id for agents, goods and tiles, kept for the year (ids are never reused)
        self._area_of_market: Dict[int, str] = {}

    # ---- ids -------------------------------------------------------------------------------------

    def market_id(self, good: str, area: str) -> int:
        """The memory's goods market row of (good, area), numbering the market when it is new."""
        key = (good, area)
        found = self._markets.get(key)
        if found is None:
            found = self._markets[key] = self.memory_tables.goods_row_for_write(market_key(good, area))
        return found

    def agent_id(self, name: str) -> int:
        found = self._numbers[0].get(name)
        if found is None:
            found = self._numbers[0][name] = self.book.agent_number(name)
        return found

    def good_id(self, name: str) -> int:
        found = self._numbers[1].get(name)
        if found is None:
            found = self._numbers[1][name] = self.book.good_number(name)
        return found

    def tile_id(self, name: str) -> int:
        found = self._numbers[2].get(name)
        if found is None:
            found = self._numbers[2][name] = self.book.tile_number(name)
        return found

    def market_ids(self, goods: Sequence[str], areas: Sequence[str]) -> List[int]:
        """`market_id` of each (good, area) pair, a market new to the year numbered in the order it first appears."""
        pairs = list(zip(goods, areas))
        known = self._markets
        for pair in dict.fromkeys(pairs):
            if pair not in known:
                self.market_id(*pair)
        return list(map(known.__getitem__, pairs))

    def _numbers_of(self, kind: int, names: Sequence[str], admit) -> List[int]:
        """The ids of the names: those new to the year are looked up (admitted by `admit`, in name order) once, not once per order."""
        cache = self._numbers[kind]
        for name in sorted(name for name in dict.fromkeys(names) if name not in cache):
            cache[name] = admit(name)
        return list(map(cache.__getitem__, names))

    def agent_ids_of(self, names: Sequence[str]) -> List[int]:
        return self._numbers_of(0, names, self.book.agent_number)

    def good_ids_of(self, names: Sequence[str]) -> List[int]:
        return self._numbers_of(1, names, self.book.good_number)

    def tile_ids_of(self, names: Sequence[str]) -> List[int]:
        return self._numbers_of(2, names, self.book.tile_number)

    # ---- legacy doors (objects) ------------------------------------------------------------------

    def add_bid(self, bid: Bid, source: int = OTHER) -> None:
        self._waiting_bids.append((bid, source))

    def add_offer(self, offer: Offer, source: int = OTHER) -> None:
        self._waiting_offers.append((offer, source))

    def add_orders(self, orders: AgentOrders, source: int = OTHER) -> None:
        """The goods bids and offers of one agent's orders."""
        for bid in orders.bids:
            self._waiting_bids.append((bid, source))
        for offer in orders.offers:
            self._waiting_offers.append((offer, source))

    def setdefault(self, key: Tuple[str, str], default=None) -> Tuple[_Sink, _Sink]:
        """The dict door: `(bids, offers)` to append to for the market `key`; the market's name is read from the order itself."""
        return self._sinks

    # ---- flushing waiting objects into rows -------------------------------------------------------

    def flush(self) -> None:
        """Turn the waiting `Bid` and `Offer` objects into rows, in the order they came."""
        self._flush_bids()
        self._flush_offers()

    def _flush_bids(self) -> None:
        waiting = self._waiting_bids
        if not waiting:
            return
        self._waiting_bids = []
        buyer = self.agent_ids_of([bid.buyer for bid, _source in waiting])
        good = self.good_ids_of([bid.good for bid, _source in waiting])
        tile = self.tile_ids_of([bid.tile for bid, _source in waiting])
        market = self.market_ids([bid.good for bid, _source in waiting], [bid.area for bid, _source in waiting])
        figures = numpy.array([(bid.floor_quantity, bid.flexible_quantity, bid.reference_price, bid.elasticity, bid.budget, bid.maximum_price)
                               for bid, _source in waiting], dtype=numpy.float64).reshape(-1, _BID_FIGURES)
        self._write_bids(buyer, good, tile, market, [bid.priority for bid, _source in waiting], figures, [source for _bid, source in waiting])

    def _flush_offers(self) -> None:
        waiting = self._waiting_offers
        if not waiting:
            return
        self._waiting_offers = []
        seller = self.agent_ids_of([offer.seller for offer, _source in waiting])
        good = self.good_ids_of([offer.good for offer, _source in waiting])
        tile = self.tile_ids_of([offer.tile for offer, _source in waiting])
        market = self.market_ids([offer.good for offer, _source in waiting], [offer.area for offer, _source in waiting])
        figures = numpy.array([(offer.quantity, offer.reservation_price) for offer, _source in waiting], dtype=numpy.float64).reshape(-1, 2)
        self._write_offers(seller, good, tile, market, figures[:, 0], figures[:, 1], [source for _offer, source in waiting])

    # ---- rows from kernels ------------------------------------------------------------------------

    def append_bids(self, buyer, good, tile, market, priority, figures, source: int) -> None:
        """Rows for bids already numbered: `figures` is (rows, 6) of floor, flexible, reference price, elasticity, budget, ceiling."""
        self.flush()
        self._write_bids(buyer, good, tile, market, priority, figures, source)

    def append_offers(self, seller, good, tile, market, quantity, reservation_price, source: int) -> None:
        """Rows for offers already numbered."""
        self.flush()
        self._write_offers(seller, good, tile, market, quantity, reservation_price, source)

    def _write_bids(self, buyer, good, tile, market, priority, figures, source) -> None:
        count = len(buyer)
        if not count:
            return
        table = self.bids = reserve_rows(self.bids, count)
        first = int(table.row_count[0])
        last = first + count
        table.buyer[first:last], table.good[first:last], table.tile[first:last], table.market[first:last] = buyer, good, tile, market
        table.sequence[first:last] = numpy.arange(first, last)
        table.priority[first:last] = priority
        figures = numpy.asarray(figures, dtype=numpy.float64)
        table.floor_quantity[first:last], table.flexible_quantity[first:last] = figures[:, 0], figures[:, 1]
        table.reference_price[first:last], table.elasticity[first:last] = figures[:, 2], figures[:, 3]
        table.budget[first:last], table.maximum_price[first:last] = figures[:, 4], figures[:, 5]
        table.source[first:last] = source
        table.quantity_bought[first:last] = 0.0
        table.cost[first:last] = 0.0
        blank_bid_results(table, first, last)
        table.row_count[0] = last

    def _write_offers(self, seller, good, tile, market, quantity, reservation_price, source) -> None:
        count = len(seller)
        if not count:
            return
        table = self.offers = reserve_rows(self.offers, count)
        first = int(table.row_count[0])
        last = first + count
        table.seller[first:last], table.good[first:last], table.tile[first:last], table.market[first:last] = seller, good, tile, market
        table.sequence[first:last] = numpy.arange(first, last)
        table.quantity[first:last] = quantity
        table.reservation_price[first:last] = reservation_price
        table.source[first:last] = source
        table.ask[first:last] = 0.0
        table.quantity_sold[first:last] = 0.0
        table.quantity_left[first:last] = table.quantity[first:last]
        blank_offer_results(table, first, last)
        table.row_count[0] = last

    def append_rows(self, name: str, **columns) -> int:
        """Rows at the end of the clearing table `name` (results, pairs, bid_order or offer_order): one array per column. Returns
        the number of the first new row."""
        count = len(next(iter(columns.values())))
        table = reserve_rows(getattr(self, name), count)
        first = int(table.row_count[0])
        for column, values in columns.items():
            getattr(table, column)[first:first + count] = values
        table.row_count[0] = first + count
        setattr(self, name, table)
        return first

    # ---- reads ------------------------------------------------------------------------------------

    def tables(self):
        """(bids, offers) with every waiting object written in."""
        if self._waiting_bids or self._waiting_offers:
            self.flush()
        return self.bids, self.offers

    def goods_with_orders(self) -> set:
        """The names of the goods that have a bid or an offer now."""
        bids, offers = self.tables()
        names = self.book.good_ids.name_list
        found = set(bids.good[:int(bids.row_count[0])].tolist()) | set(offers.good[:int(offers.row_count[0])].tolist())
        return {names[good] for good in found}

    def bid_lists(self):
        """Every bid row's columns as lists (`goods_market_rows.BidLists`), made again only when rows have been added."""
        from .goods_market_rows import BidLists
        self.flush()
        count = int(self.bids.row_count[0])
        if self._bid_lists is None or self._bid_lists[0] != count:
            self._bid_lists = (count, BidLists(self))
        return self._bid_lists[1]

    def offer_lists(self):
        """Every offer row's columns as lists, read now (units left change as markets clear and the respend runs)."""
        from .goods_market_rows import OfferLists
        return OfferLists(self)

    def bid_count(self) -> int:
        self.flush()
        return int(self.bids.row_count[0])

    def offer_count(self) -> int:
        self.flush()
        return int(self.offers.row_count[0])

    # ---- objects at the edge ----------------------------------------------------------------------

    def _area_names(self) -> List[str]:
        tables = self.memory_tables
        return tables.areas.name_list

    def area_name_of_market(self, market: int) -> str:
        """The area of a goods market id."""
        found = self._area_of_market.get(market)
        if found is None:
            found = self._area_of_market[market] = self._area_names()[self.memory_tables.goods_table.area[market]]
        return found

    def bids_of(self, rows: Sequence[int]) -> List[Bid]:
        """`Bid` objects for the rows, in the order given (the edge for a rule still written over objects)."""
        lists = self.bid_lists()
        return [make_bid(lists.buyer[row], lists.good[row], lists.area[row], lists.tile[row], lists.floor_quantity[row],
                         lists.flexible_quantity[row], lists.reference_price[row], lists.elasticity[row], lists.budget[row],
                         lists.priority[row], lists.maximum_price[row]) for row in numpy.asarray(rows, dtype=numpy.int64).tolist()]

    def offers_of(self, rows: Sequence[int], quantities=None) -> List[Offer]:
        """`Offer` objects for the rows (with `quantities` in place of the rows' own when given)."""
        self.flush()
        table, book = self.offers, self.book
        rows = numpy.asarray(rows, dtype=numpy.int64)
        agents, goods, tiles = book.agent_ids.name_list, book.good_ids.name_list, book.tile_ids.name_list
        areas = self._area_names()
        market_area = self.memory_tables.goods_table.area[table.market[rows]].tolist()
        units = (table.quantity[rows] if quantities is None else numpy.asarray(quantities)).tolist()
        return [make_offer(agents[seller], goods[good], areas[area], tiles[tile], quantity, price)
                for seller, good, tile, area, quantity, price in zip(
                    table.seller[rows].tolist(), table.good[rows].tolist(), table.tile[rows].tolist(), market_area, units,
                    table.reservation_price[rows].tolist())]


def new_order_book(setup, record) -> GoodsOrderBook:
    """An empty book of orders on the record's book and market memory."""
    return GoodsOrderBook(record.book, record.memory.tables)


def from_dict(order_book: dict, record) -> GoodsOrderBook:
    """A book of orders holding the bids and offers of a `{(good, area): (bids, offers)}` dict (a caller that still builds one)."""
    made = new_order_book(None, record)
    for _key, (bids, offers) in sorted(order_book.items()):
        for bid in bids:
            made.add_bid(bid)
        for offer in offers:
            made.add_offer(offer)
    return made


def as_book(order_book, record) -> GoodsOrderBook:
    """`order_book` itself when it is a book of orders, else the book a dict makes."""
    return order_book if isinstance(order_book, GoodsOrderBook) else from_dict(order_book, record)
