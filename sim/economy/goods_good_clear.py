"""One good's markets cleared from the order tables, in area order: the batched markets by the table kernels, the others
(no units, a book edge selling, a good outside the year arrays, no arrays at all) by the rules still written over `Bid` and
`Offer` objects, made from the rows of their market.

`clear_good` returns one `Cleared` per market, in the order the markets clear and settle."""
from collections import namedtuple
from typing import List

import numpy

from . import goods_market, seller_offers, unsold_search
from .goods_respend import offers_left
from .goods_year_results import sold_by_result
from .goods_table_clear import clear_batch
from .goods_table_group import GoodRows, batch_flags, rows_of_good
from .goods_table_pack import pack_batch
from .goods_table_results import TableClearing
from .goods_table_views import LazyObjects, TableBatch

# One market after it cleared. `bids` and `offers` are the lists the respend and the memory still read (lazy where the market
# is on the tables); `offers_left` the offers with what sold taken off; `notes` the flags the market's memory is noted by.
Cleared = namedtuple("Cleared", ("area", "market", "result", "bids", "offers", "offers_left", "has_offers", "has_units", "has_funded_bid",
                                 "bid_rows", "offer_rows"))


def flags_by_market(bids, offers, rows: GoodRows) -> tuple:
    """Per market: (has any offer row, has an offer with units, has a bid with a budget), from the first round's orders."""
    count = len(rows.markets)
    offered = numpy.bincount(rows.offer_position, minlength=count) > 0
    units = numpy.bincount(rows.offer_position, weights=offers.quantity[rows.offer_rows] > 0.0, minlength=count) > 0
    funded = numpy.bincount(rows.bid_position, weights=bids.budget[rows.bid_rows] > 0.0, minlength=count) > 0
    return offered, units, funded


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


def clear_good(context, good: str, good_id: int) -> List[Cleared]:
    """Clear the markets of `good` that have orders, one after another in area order."""
    orders = context.orders
    bids, offers = orders.tables()
    rows = rows_of_good(orders, good_id)
    if not len(rows.markets):
        return []
    flags = batch_flags(offers, context.book.agent_table.is_edge, rows, context.good_is_batchable(good))
    batch = pack = slots = left_counts = None
    if flags.any():
        batch, pack, slots = _batched(context, good, rows, flags)
        left_counts = numpy.bincount(numpy.repeat(numpy.arange(int(flags.sum())), numpy.diff(pack.offer_ptr)),
                                     weights=batch.left > 0.0, minlength=int(flags.sum()))
    offered, units, funded = flags_by_market(bids, offers, rows)
    currency = context.setup.currency_id
    cleared = []
    for place, market in enumerate(rows.markets.tolist()):
        area = orders.area_name_of_market(market)
        bid_rows, offer_rows = rows.bids_of_market(place), rows.offers_of_market(place)
        lazy_bids = LazyObjects(lambda rows=bid_rows: orders.bids_of(rows), len(bid_rows))
        if flags[place]:
            slot = int(slots[place])
            if batch.traded_flag[slot]:
                result = TableClearing.of(batch, slot, good, area, currency)
                left = LazyObjects(result.offers_left, int(left_counts[slot]))
                cleared.append(Cleared(area, market, result, lazy_bids, LazyObjects(lambda rows=offer_rows: orders.offers_of(rows), len(offer_rows)),
                                       left, offered[place], units[place], funded[place], bid_rows, offer_rows))
                continue
            chosen = orders.offers_of(offer_rows)
            result = goods_market.clear(list(lazy_bids), chosen, good, area, currency, _last_price(context, market))
            cleared.append(Cleared(area, market, result, lazy_bids, chosen, _left_of(result, chosen), offered[place], units[place],
                                   funded[place], bid_rows, offer_rows))
            continue
        bid_objects, offer_objects = orders.bids_of(bid_rows), orders.offers_of(offer_rows)
        after, result = _plain(context, good, area, _last_price(context, market), bid_objects, offer_objects)
        cleared.append(Cleared(area, market, result, bid_objects, after, _left_of(result, after), offered[place], units[place],
                               funded[place], bid_rows, offer_rows))
    return cleared


def _left_of(result, offers):
    """The offers with what the result sold taken off."""
    return offers_left(offers, sold_by_result(result))


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
