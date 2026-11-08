"""A book of orders that also takes orders by name: the door the rare sources (`order_rows.OrderRows`, the plan table) write through.

`GoodsOrderBook` turns each waiting `Bid` or `Offer` into a row the next time the tables are read, numbering every name new to the
batch together (in sorted order, so the numbering does not follow the order the names arrived in). A source that writes names and
figures (`NamedBids`, `NamedOffers`) waits in the same list, in its place in the arrival order, and is flushed in the same pass: the
names of every waiting item are numbered as one batch, then the rows are written in arrival order. So a game numbers its agents,
goods, tiles and markets exactly as when each order waited as an object, and no object is made.

An item has `source` (a `goods_order_tables` code, or one per row), `names()` (the agents, goods, tiles and (good, area) pairs it
names) and `rows(book)` (its rows: buyer or seller ids, good ids, tile ids, market ids, then the priority and six figures of a bid or the
quantity and reservation of an offer), valid once its names are numbered. `ObjectBids` and `ObjectOffers` are the same for a run of
waiting objects."""
from typing import List

import numpy

from .goods_order_book import GoodsOrderBook

_BID_FIGURES = 6


class ObjectBids:
    """A run of waiting `Bid` objects, as an item."""

    def __init__(self, waiting: List[tuple]):
        self.bids = [bid for bid, _source in waiting]
        self.source = [source for _bid, source in waiting]

    def names(self) -> tuple:
        bids = self.bids
        return ([bid.buyer for bid in bids], [bid.good for bid in bids], [bid.tile for bid in bids], [(bid.good, bid.area) for bid in bids])

    def rows(self, book: GoodsOrderBook) -> tuple:
        bids = self.bids
        figures = numpy.array([(bid.floor_quantity, bid.flexible_quantity, bid.reference_price, bid.elasticity, bid.budget, bid.maximum_price)
                               for bid in bids], dtype=numpy.float64).reshape(-1, _BID_FIGURES)
        return (book.agent_ids_of([bid.buyer for bid in bids]), book.good_ids_of([bid.good for bid in bids]),
                book.tile_ids_of([bid.tile for bid in bids]), book.market_ids([bid.good for bid in bids], [bid.area for bid in bids]),
                [bid.priority for bid in bids], figures)


class ObjectOffers:
    """A run of waiting `Offer` objects, as an item."""

    def __init__(self, waiting: List[tuple]):
        self.offers = [offer for offer, _source in waiting]
        self.source = [source for _offer, source in waiting]

    def names(self) -> tuple:
        offers = self.offers
        return ([offer.seller for offer in offers], [offer.good for offer in offers], [offer.tile for offer in offers],
                [(offer.good, offer.area) for offer in offers])

    def rows(self, book: GoodsOrderBook) -> tuple:
        offers = self.offers
        return (book.agent_ids_of([offer.seller for offer in offers]), book.good_ids_of([offer.good for offer in offers]),
                book.tile_ids_of([offer.tile for offer in offers]), book.market_ids([offer.good for offer in offers], [offer.area for offer in offers]),
                [offer.quantity for offer in offers], [offer.reservation_price for offer in offers])


class NamedOrderBook(GoodsOrderBook):
    """A `GoodsOrderBook` whose waiting lists may also hold named items (see the module docstring)."""

    def add_named_bids(self, item) -> None:
        self._waiting_bids.append((item, item.source))

    def add_named_offers(self, item) -> None:
        self._waiting_offers.append((item, item.source))

    def _flush_bids(self) -> None:
        waiting = self._waiting_bids
        if not waiting:
            return
        self._waiting_bids = []
        items = _items(waiting, ObjectBids)
        self._number(items)
        for item in items:
            self._write_bids(*item.rows(self), item.source)

    def _flush_offers(self) -> None:
        waiting = self._waiting_offers
        if not waiting:
            return
        self._waiting_offers = []
        items = _items(waiting, ObjectOffers)
        self._number(items)
        for item in items:
            buyer, good, tile, market, quantity, reservation = item.rows(self)
            self._write_offers(buyer, good, tile, market, quantity, reservation, item.source)

    def _number(self, items: List) -> None:
        """Number the names new to this flush as one batch per kind (the numbering is by sorted name inside a batch)."""
        agents, goods, tiles, pairs = [], [], [], []
        for item in items:
            names = item.names()
            agents.extend(names[0])
            goods.extend(names[1])
            tiles.extend(names[2])
            pairs.extend(names[3])
        self.agent_ids_of(agents)
        self.good_ids_of(goods)
        self.tile_ids_of(tiles)
        if pairs:
            self.market_ids([good for good, _area in pairs], [area for _good, area in pairs])


def _items(waiting: List[tuple], run_type) -> List:
    """The waiting entries as items, consecutive plain objects gathered into one `run_type` item, named items kept where they were."""
    items, run = [], []
    for entry in waiting:
        if hasattr(entry[0], "rows"):
            if run:
                items.append(run_type(run))
                run = []
            items.append(entry[0])
        else:
            run.append(entry)
    if run:
        items.append(run_type(run))
    return items


def new_named_order_book(setup, record) -> NamedOrderBook:
    """An empty book of orders on the record's book and market memory that takes named items."""
    return NamedOrderBook(record.book, record.memory.tables)
