"""The items a `GoodsOrderBook` holds while orders wait to become rows: the door the rare sources (`order_rows.OrderRows`, the plan table) write through.

The book turns each waiting `Bid` or `Offer` into a row the next time the tables are read, numbering every name new to the
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

_BID_FIGURES = 6


class ObjectBids:
    """A run of waiting `Bid` objects, as an item."""

    def __init__(self, waiting: List[tuple]):
        self.bids = [bid for bid, _source in waiting]
        self.source = [source for _bid, source in waiting]

    def names(self) -> tuple:
        bids = self.bids
        return ([bid.buyer for bid in bids], [bid.good for bid in bids], [bid.tile for bid in bids], [(bid.good, bid.area) for bid in bids])

    def rows(self, book) -> tuple:
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

    def rows(self, book) -> tuple:
        offers = self.offers
        return (book.agent_ids_of([offer.seller for offer in offers]), book.good_ids_of([offer.good for offer in offers]),
                book.tile_ids_of([offer.tile for offer in offers]), book.market_ids([offer.good for offer in offers], [offer.area for offer in offers]),
                [offer.quantity for offer in offers], [offer.reservation_price for offer in offers])


def items_of(waiting: List[tuple], run_type) -> List:
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


def joined_runs(items: List) -> List:
    """The items with those that wait one after another and share a `run_key` written as one item each (the rows stay in arrival order;
    an item with no `run_key`, like a run of plain objects, stays alone). A source that writes one order at a time leaves hundreds of
    items of a row or two, each a numbering call and a table write."""
    joined, run, run_key = [], [], None
    for item in items:
        key = item.run_key() if hasattr(item, "run_key") else None
        if run and key is not None and key == run_key:
            run.append(item)
            continue
        if run:
            joined.append(run[0] if len(run) == 1 else type(run[0]).joined(run))
        run, run_key = [item], key
    if run:
        joined.append(run[0] if len(run) == 1 else type(run[0]).joined(run))
    return joined


def number_names(book, items: List) -> None:
    """Number the names new to this flush as one batch per kind (the numbering is by sorted name inside a batch)."""
    agents, goods, tiles, pairs = [], [], [], []
    for item in items:
        names = item.names()
        agents.extend(names[0])
        goods.extend(names[1])
        tiles.extend(names[2])
        pairs.extend(names[3])
    book.agent_ids_of(agents)
    book.good_ids_of(goods)
    book.tile_ids_of(tiles)
    if pairs:
        book.market_ids([good for good, _area in pairs], [area for _good, area in pairs])
