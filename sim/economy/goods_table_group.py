"""A good's markets cut out of the order tables: which rows belong to which market, and which markets the batch can clear.

`rows_of_good` finds the good's bid and offer rows and the markets they are in, the markets in the order they clear (area
name, as the dict loop sorted them), and the markets the batch can clear (`goods_year_batch.batchable` for every market of the
good at once); the work is `goods_rows_kernel.good_rows`. `name_ranks` turns an id table into "who sorts first by name", because
the clearing sorts bids by (priority, buyer, tile) and offers by (seller, tile) as text while ids are numbered by arrival."""
from dataclasses import dataclass

import numpy

from sim.book_read_kernels import find_slots

from .goods_rows_kernel import good_rows


@dataclass
class GoodRows:
    """One good's orders: `markets[p]` is the id of the pth market to clear; each row's `*_position` says which p it is in."""
    markets: numpy.ndarray          # goods market ids, in clearing order (area name)
    bid_rows: numpy.ndarray         # the good's bid rows, in table order
    bid_position: numpy.ndarray     # per bid row: its market's place in `markets`
    offer_rows: numpy.ndarray
    offer_position: numpy.ndarray
    bid_grouped: numpy.ndarray      # the bid rows market by market, each market's in arrival order
    bid_group_ptr: numpy.ndarray    # where market p's bids start in bid_grouped (length markets + 1)
    offer_grouped: numpy.ndarray
    offer_group_ptr: numpy.ndarray

    def bids_of_market(self, place: int) -> numpy.ndarray:
        """The rows of market `place`'s bids, in arrival order."""
        return self.bid_grouped[self.bid_group_ptr[place]:self.bid_group_ptr[place + 1]]

    def offers_of_market(self, place: int) -> numpy.ndarray:
        return self.offer_grouped[self.offer_group_ptr[place]:self.offer_group_ptr[place + 1]]


def name_ranks(names) -> numpy.ndarray:
    """Per id: its place when all names are sorted as text (names are distinct, so there are no ties)."""
    order = sorted(range(len(names)), key=names.__getitem__)
    ranks = numpy.empty(len(names), dtype=numpy.int64)
    ranks[order] = numpy.arange(len(names), dtype=numpy.int64)
    return ranks


def rows_of_good(orders, good_id: int, is_edge: numpy.ndarray, good_is_batchable: bool):
    """(the good's `GoodRows`, which markets the batch clears, the flags (has an offer row, has an offer with units, has a bid with a
    budget) per market): one kernel call over the order tables.

    A market is batched when it has units on offer and no book edge (the mint's wash of its own trades) selling units in it, and
    the good is batchable (portable, and in the year arrays)."""
    bids, offers = orders.tables()
    found = good_rows(bids, offers, good_id, orders.memory_tables.goods_table.area, orders.area_ranks(), is_edge, good_is_batchable)
    return GoodRows(*found[:9]), found[9], found[10:]


def note_stock_slots(offers, book, good_id: int, offer_rows: numpy.ndarray) -> None:
    """Write into the offers' `stock_slot` the book slot each seller holds the good in at its tile (-1: none yet)."""
    offers.stock_slot[offer_rows] = find_slots(book.stock_rows.table, book.stock_rows.index, offers.seller[offer_rows], good_id,
                                               offers.tile[offer_rows])
