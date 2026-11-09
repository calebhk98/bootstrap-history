"""Objects at the edge of the order tables, made only when a rule still written over `Bid`, `Offer` or their (agent, tile) keys
reads them: lazy sequences of the rows of a market, and cheap (agent, tile) views of the rows of a good's batch."""
from collections import namedtuple
from typing import Callable, Sequence

import numpy

from .few_ids import in_ids
from .goods_year_results import BatchAllocation

Held = namedtuple("Held", ("agent", "tile"))


class LazyObjects(Sequence):
    """A list that is built from `build()` the first time anything but its length is read."""

    def __init__(self, build: Callable[[], list], count: int):
        self._build, self._count, self._items = build, count, None

    def _list(self) -> list:
        if self._items is None:
            self._items = self._build()
        return self._items

    def __len__(self) -> int:
        return self._count

    def __bool__(self) -> bool:
        return self._count > 0

    def __getitem__(self, index):
        return self._list()[index]

    def __iter__(self):
        return iter(self._list())


class RowLists(Sequence):
    """Per market, a `LazyObjects` of the objects of the market's rows (`pointers` cut `rows` by market)."""

    def __init__(self, make: Callable[[numpy.ndarray], list], rows: numpy.ndarray, pointers: numpy.ndarray):
        self._make, self._rows, self._pointers = make, rows, pointers
        self._kept = {}

    def __len__(self) -> int:
        return len(self._pointers) - 1

    def __getitem__(self, market: int) -> LazyObjects:
        found = self._kept.get(market)
        if found is None:
            first, last = int(self._pointers[market]), int(self._pointers[market + 1])
            found = self._kept[market] = LazyObjects(lambda: self._make(self._rows[first:last]), last - first)
        return found


class HeldViews(Sequence):
    """The (agent, tile) of each row of a batch, built when a row is read: what settlement keys its pairs by."""

    def __init__(self, names: list, agents: numpy.ndarray, tiles: numpy.ndarray, rows: numpy.ndarray, tile_names: list):
        self._names, self._tile_names = names, tile_names
        self._agents, self._tiles = agents[rows].tolist(), tiles[rows].tolist()

    def __len__(self) -> int:
        return len(self._agents)

    def __getitem__(self, index: int) -> Held:
        return Held(self._names[self._agents[index]], self._tile_names[self._tiles[index]])


class BidViews(HeldViews):
    """`.buyer` and `.tile` of each bid row."""

    def __getitem__(self, index: int):
        return BidView(self._names[self._agents[index]], self._tile_names[self._tiles[index]])


class OfferViews(HeldViews):
    """`.seller` and `.tile` of each offer row."""

    def __getitem__(self, index: int):
        return OfferView(self._names[self._agents[index]], self._tile_names[self._tiles[index]])


BidView = namedtuple("BidView", ("buyer", "tile"))
OfferView = namedtuple("OfferView", ("seller", "tile"))


class TableBatch(BatchAllocation):
    """The allocation arrays of a good's batch, with its bids and offers read from the order tables: whole objects of a
    market's rows when its `bids[m]` or `offers[m]` is read, (agent, tile) views for `flat_bids` and `flat_offers`."""

    def __init__(self, arrays, pack, orders):
        self.pack, self.orders = pack, orders
        self._watched = None
        super().__init__(arrays, pack.offer_ptr, pack.bid_ptr, RowLists(orders.bids_of, pack.bid_rows, pack.bid_ptr),
                         RowLists(orders.offers_of, pack.offer_rows, pack.offer_ptr), [])
        bids, offers = orders.tables()
        book = orders.book
        self._views = (BidViews(book.agent_ids.name_list, bids.buyer, bids.tile, pack.bid_rows, book.tile_ids.name_list),
                       OfferViews(book.agent_ids.name_list, offers.seller, offers.tile, pack.offer_rows, book.tile_ids.name_list))

    def watched_buys(self, watchers):
        """Per bid of the batch: whether a watcher's bid took units. None when no watcher has an id (it bought nothing). Worked
        out once for the batch, whatever markets ask."""
        if self._watched is None or (self._watched[0] is not watchers and self._watched[0] != watchers):
            numbers = self.orders.book.agent_ids.numbers
            ids = [numbers[name] for name in watchers if name in numbers]
            mask = None
            if ids:
                bids, _offers = self.orders.tables()
                mask = in_ids(bids.buyer[self.pack.bid_rows], ids, len(self.orders.book.agent_ids)) & (self.bid_quantity > 0.0)
            self._watched = (watchers, mask)
        return self._watched[1]

    @property
    def flat_bids(self):
        return self._views[0]

    @property
    def flat_offers(self):
        return self._views[1]
