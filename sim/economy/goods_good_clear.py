"""One good's markets cleared from the order tables, in area order. Each market takes one of three ways:

  * traded in the batch: cleared by the table kernels (goods_table_clear.py) and read from the tables afterwards;
  * did not trade, and had no book edge or unsold stock to search: its quote read from the columns (goods_table_quotes.py);
  * anything else (a book edge selling, a good outside the year arrays, no arrays at all): the rules still written over `Bid`
    and `Offer` objects, made from the rows of the market.

`clear_good` returns one `Cleared` per market, in the order the markets clear and settle."""
from collections import namedtuple
from typing import List

import numpy

from . import seller_offers, unsold_search
from .goods_market import MINIMUM_PRICE_SHARE_OF_REFERENCE
from .goods_market_rows import MarketRows
from .goods_respend import offers_left
from .goods_table_clear import clear_batch
from .goods_table_group import GoodRows, batch_flags, rows_of_good
from .goods_table_pack import BatchPack, pack_batch, price_scales
from .goods_table_quotes import untraded_figures, untraded_result, wanted_by_market
from .goods_table_results import TableClearing
from .goods_table_views import LazyObjects, TableBatch
from .goods_year_results import sold_by_result

# One market after it cleared. `bids`, `offers` and `offers_left` are the lists the memory's notes and the curves still read
# (lazy where the market is on the tables); `wanted` what its buyers asked for when it did not trade (None: read the result);
# `has_*` the flags the market's memory is noted by; `rows` the market's rows when it is on the tables (None for objects).
Cleared = namedtuple("Cleared", ("area", "market", "result", "bids", "offers", "offers_left", "wanted", "has_offers", "has_units",
                                 "has_funded_bid", "rows"))


def flags_by_market(bids, offers, rows: GoodRows) -> tuple:
    """Per market: (has any offer row, has an offer with units, has a bid with a budget), from the first round's orders."""
    count = len(rows.markets)
    offered = numpy.bincount(rows.offer_position, minlength=count) > 0
    units = numpy.bincount(rows.offer_position, weights=offers.quantity[rows.offer_rows] > 0.0, minlength=count) > 0
    funded = numpy.bincount(rows.bid_position, weights=bids.budget[rows.bid_rows] > 0.0, minlength=count) > 0
    return offered, units, funded


class Untraded:
    """The quote figures of every market of a good that did not trade, worked out together."""

    def __init__(self, bids, offers, rows: GoodRows, last_price: numpy.ndarray):
        bid_ptr, offer_ptr = rows.bid_group_ptr, rows.offer_group_ptr
        bid_rows, offer_rows = rows.bid_grouped, rows.offer_grouped
        scale = price_scales(bid_ptr, bids.reference_price[bid_rows], last_price)
        has_minimum = ~numpy.isnan(scale)
        minimum = numpy.where(has_minimum, MINIMUM_PRICE_SHARE_OF_REFERENCE * numpy.where(has_minimum, scale, 0.0), 0.0)
        (self.lowest_ask, self.lowest_clamped, self.supply, self.funded, self.best_bid) = untraded_figures(
            bid_ptr, offer_ptr, bids.budget[bid_rows], bids.maximum_price[bid_rows], offers.reservation_price[offer_rows],
            offers.quantity[offer_rows], minimum, has_minimum)
        asked = numpy.where(numpy.isnan(self.lowest_ask), self.best_bid, self.lowest_ask)
        self.wanted = wanted_by_market(bid_ptr, asked, bids.floor_quantity[bid_rows], bids.flexible_quantity[bid_rows],
                                       bids.reference_price[bid_rows], bids.elasticity[bid_rows], bids.budget[bid_rows],
                                       bids.maximum_price[bid_rows])


def _plain(context, good: str, area: str, last_price, bids: list, offers: list):
    """The old rules on objects: the sellers' re-pricing, the unsold search, the clearing. Returns (offers after, result)."""
    costs = seller_offers.UnitCosts()
    chosen = seller_offers.strategic_offers(context.setup, context.record, context.view, bids, offers, last_price, costs)
    return unsold_search.clear_with_search(context.setup, context.record, context.view, bids, offers, chosen, good, area,
                                           context.setup.currency_id, last_price, costs)


def _last_price(context, market: int):
    price = context.orders.memory_tables.goods_table.price[market]
    return None if price != price else float(price)


def _batched(context, good: str, rows: GoodRows, flags: numpy.ndarray):
    """(the batch's allocation, the pack, each market's slot in it or -1): the batched markets cleared."""
    pack = pack_batch(context, good, rows, flags)
    allocated = clear_batch(context, good, pack)
    return TableBatch(allocated, pack, context.orders), pack, numpy.where(flags, numpy.cumsum(flags) - 1, -1)


def _left_counts(batch: TableBatch, pack: BatchPack) -> numpy.ndarray:
    """Per batched market: how many of its offers have units left."""
    count = len(pack.offer_ptr) - 1
    return numpy.bincount(numpy.repeat(numpy.arange(count), numpy.diff(pack.offer_ptr)), weights=batch.left > 0.0, minlength=count)


def clear_good(context, good: str, good_id: int) -> List[Cleared]:
    """Clear the markets of `good` that have orders, one after another in area order."""
    orders = context.orders
    bids, offers = orders.tables()
    rows = rows_of_good(orders, good_id)
    if not len(rows.markets):
        return []
    flags = batch_flags(offers, context.book.agent_table.is_edge, rows, context.good_is_batchable(good))
    batch = pack = slots = left_counts = untraded = None
    if flags.any():
        batch, pack, slots = _batched(context, good, rows, flags)
        left_counts = _left_counts(batch, pack)
    offered, units, funded = flags_by_market(bids, offers, rows)
    last_price = orders.memory_tables.goods_table.price[rows.markets]
    currency = context.setup.currency_id
    cleared = []
    for place, market in enumerate(rows.markets.tolist()):
        area = orders.area_name_of_market(market)
        bid_rows, offer_rows = rows.bids_of_market(place), rows.offers_of_market(place)
        lazy_bids = LazyObjects(lambda rows=bid_rows: orders.bids_of(rows), len(bid_rows))
        lazy_offers = LazyObjects(lambda rows=offer_rows: orders.offers_of(rows), len(offer_rows))
        flags_of = (offered[place], units[place], funded[place])
        slot = int(slots[place]) if flags[place] else -1
        if slot >= 0 and batch.traded_flag[slot]:
            result = TableClearing.of(batch, slot, good, area, currency)
            first, last = pack.offer_ptr[slot], pack.offer_ptr[slot + 1]
            left_rows = pack.offer_rows[first:last][batch.left[first:last] > 0.0]
            cleared.append(Cleared(area, market, result, lazy_bids, lazy_offers, LazyObjects(result.offers_left, int(left_counts[slot])),
                                   None, *flags_of, MarketRows(orders, bid_rows, left_rows)))
        elif slot >= 0 or not units[place]:
            if untraded is None:
                untraded = Untraded(bids, offers, rows, last_price)
            left_rows = offer_rows[offers.quantity[offer_rows] > 0.0]
            price = last_price[place]
            result = untraded_result(good, area, currency, None if price != price else float(price), float(untraded.supply[place]),
                                     untraded.lowest_ask[place], untraded.lowest_clamped[place], untraded.best_bid[place],
                                     bool(untraded.funded[place]))
            cleared.append(Cleared(area, market, result, lazy_bids, lazy_offers,
                                   LazyObjects(lambda rows=left_rows: orders.offers_of(rows), len(left_rows)),
                                   float(untraded.wanted[place]), *flags_of, MarketRows(orders, bid_rows, left_rows)))
        else:
            bid_objects, offer_objects = orders.bids_of(bid_rows), orders.offers_of(offer_rows)
            after, result = _plain(context, good, area, _last_price(context, market), bid_objects, offer_objects)
            cleared.append(Cleared(area, market, result, bid_objects, after, offers_left(after, sold_by_result(result)), None,
                                   *flags_of, None))
    return cleared


def note_idle_years(memory, key: str, cleared: Cleared) -> int:
    """Count the years the market has had offers and nobody bidding, and bids and no seller, as `market_memory_asks.note_bids` and
    `note_offers` do from the lists; returns the two counts before this year, added."""
    if cleared.has_offers and not cleared.has_funded_bid:
        before_bids = memory.count_year_without_bids(key)
    else:
        before_bids = memory.end_years_without_bids(key)
    if not cleared.has_units and cleared.has_funded_bid:
        before_offers = memory.count_year_without_offers(key)
    else:
        before_offers = memory.end_years_without_offers(key)
    return before_bids + before_offers
