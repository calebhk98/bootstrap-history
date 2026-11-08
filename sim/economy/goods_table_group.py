"""A good's markets cut out of the order tables: which rows belong to which market, and which markets the batch can clear.

`rows_of_good` finds the good's bid and offer rows and the markets they are in, the markets in the order they clear (area
name, as the dict loop sorted them). `name_ranks` turns an id table into "who sorts first by name", because the clearing sorts
bids by (priority, buyer, tile) and offers by (seller, tile) as text while ids are numbered by arrival.
`batch_flags` is `goods_year_batch.batchable` for every market of the good at once."""
from dataclasses import dataclass

import numpy

from sim.book_read_kernels import find_slots


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


def rows_of_good(orders, good_id: int) -> GoodRows:
    """The rows of the good's bids and offers and the markets they make up, in the order the markets clear."""
    bids, offers = orders.tables()
    bid_rows = numpy.flatnonzero(bids.good[:int(bids.row_count[0])] == good_id)
    offer_rows = numpy.flatnonzero(offers.good[:int(offers.row_count[0])] == good_id)
    bid_markets, offer_markets = bids.market[bid_rows], offers.market[offer_rows]
    distinct = numpy.unique(numpy.concatenate((bid_markets, offer_markets)))
    areas = orders.area_name_of_market
    by_area = sorted(range(len(distinct)), key=lambda place: areas(int(distinct[place])))
    place_of = numpy.empty(len(distinct), dtype=numpy.int64)
    place_of[by_area] = numpy.arange(len(distinct), dtype=numpy.int64)
    bid_position = place_of[numpy.searchsorted(distinct, bid_markets)]
    offer_position = place_of[numpy.searchsorted(distinct, offer_markets)]
    bid_grouped, bid_group_ptr = grouped(bid_rows, bid_position, len(distinct))
    offer_grouped, offer_group_ptr = grouped(offer_rows, offer_position, len(distinct))
    return GoodRows(distinct[by_area], bid_rows, bid_position, offer_rows, offer_position, bid_grouped, bid_group_ptr,
                    offer_grouped, offer_group_ptr)


def grouped(rows: numpy.ndarray, position: numpy.ndarray, groups: int):
    """The rows grouped by their group's place (arrival order kept inside a group), and where each group starts."""
    order = numpy.argsort(position, kind="stable")
    pointers = numpy.concatenate(([0], numpy.cumsum(numpy.bincount(position, minlength=groups)))).astype(numpy.int64)
    return rows[order], pointers


def batch_flags(offers, is_edge, rows: GoodRows, good_is_batchable: bool) -> numpy.ndarray:
    """Per market: whether the batch clears it. It must have units on offer and no book edge (the mint's wash of its own
    trades) selling units in it, and its good must be batchable (portable, and in the year arrays)."""
    count = len(rows.markets)
    if not good_is_batchable:
        return numpy.zeros(count, dtype=bool)
    has_units = offers.quantity[rows.offer_rows] > 0.0
    edge = has_units & (is_edge[offers.seller[rows.offer_rows]] != 0)
    units = numpy.bincount(rows.offer_position, weights=has_units, minlength=count)
    edge_units = numpy.bincount(rows.offer_position, weights=edge, minlength=count)
    return (units > 0) & (edge_units == 0)


def note_stock_slots(offers, book, good_id: int, offer_rows: numpy.ndarray) -> None:
    """Write into the offers' `stock_slot` the book slot each seller holds the good in at its tile (-1: none yet)."""
    offers.stock_slot[offer_rows] = find_slots(book.stock_rows.table, book.stock_rows.index, offers.seller[offer_rows], good_id,
                                               offers.tile[offer_rows])
