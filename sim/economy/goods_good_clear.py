"""One good's markets cleared from the order tables, in area order. Each market takes one of three ways:

  * traded in the batch: cleared by the table kernels (goods_table_clear.py) and read from the tables afterwards;
  * did not trade, and had no book edge or unsold stock to search: its quote read from the columns (goods_table_quotes.py);
  * anything else (a book edge selling, a good outside the year arrays, no arrays at all): the rules still written over `Bid`
    and `Offer` objects, made from the rows of the market.

`clear_good` returns one `Cleared` per market, in the order the markets clear and settle."""
from collections import namedtuple
import numpy

from . import seller_offers, unsold_search
from .goods_market import MINIMUM_PRICE_SHARE_OF_REFERENCE
from .goods_market_rows import MarketRows
from .goods_respend import offers_left
from .goods_table_clear import clear_batch
from .goods_table_group import GoodRows, batch_flags, note_stock_slots, rows_of_good
from .goods_table_pack import pack_batch, price_scales
from .goods_table_quotes import untraded_figures, untraded_result, wanted_by_market
from .goods_table_results import TableClearing
from .goods_table_views import TableBatch
from .goods_year_results import sold_by_result
from .types import QUOTE_BEST_UNFILLED_BID, QUOTE_COST_COVERING, QUOTE_LOWEST_UNFILLED_ASK, QUOTE_OPENING_ESTIMATE
from .entry import wanted_in_round

# One market after it cleared. A market on the tables has its `rows` and no objects (`bids`, `offers` and `offers_left` are None:
# `objects()` and the left market build them when something reads them); a market on the objects has the lists. `wanted` is what
# its buyers asked for; `has_*` the flags the market's memory is noted by.
class Cleared(namedtuple("Cleared", ("area", "market", "result", "bids", "offers", "offers_left", "wanted", "has_offers", "has_units",
                                     "has_funded_bid", "rows"))):
    __slots__ = ()

    def objects(self):
        """(the market's bids, all its offers) as objects: kept for a market on the objects, built from the rows for one on the tables."""
        return (self.bids, self.offers) if self.rows is None else (self.rows.bids_lazy(), self.rows.offers_lazy())


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


QUOTE_KINDS = (None, QUOTE_BEST_UNFILLED_BID, QUOTE_LOWEST_UNFILLED_ASK, QUOTE_COST_COVERING, QUOTE_OPENING_ESTIMATE)    # the code of a quote's kind in `GoodClearing.quote_kind`
TABLE_TRADED, TABLE_UNTRADED, ON_OBJECTS = 0, 1, 2                          # how a market was cleared (`GoodClearing.way`)


def untraded_quotes(lowest_ask: numpy.ndarray, best_bid: numpy.ndarray, funded: numpy.ndarray):
    """`goods_table_quotes.quote_of` for every market: (quote price, quote kind code), NaN and 0 for no quote."""
    no_ask, has_bid = numpy.isnan(lowest_ask), ~numpy.isnan(best_bid)
    bid_quote = has_bid & (no_ask | (best_bid < lowest_ask))
    ask_quote = ~bid_quote & ~no_ask & ~funded
    price = numpy.where(bid_quote, best_bid, numpy.where(ask_quote, lowest_ask, numpy.nan))
    return price, numpy.where(bid_quote, 1, numpy.where(ask_quote, 2, 0)).astype(numpy.int64)


def held_prices(last_price: numpy.ndarray, lowest_clamped: numpy.ndarray) -> numpy.ndarray:
    """`goods_table_quotes.held_price` for every market (NaN: none)."""
    keeps_last = numpy.isnan(lowest_clamped) | (~numpy.isnan(last_price) & (lowest_clamped <= last_price))
    return numpy.where(keeps_last, last_price, lowest_clamped)


class GoodClearing:
    """One good's cleared markets as columns, in the order they clear (every array has one entry per market): the id and area, the first
    round's result (`quantity`, `price` (NaN: none), `demand`, `offered`, the quote as `quote_price` and `quote_kind`), what the buyers
    `wanted`, the flags the market's memory is noted by, and `way` (`TABLE_TRADED`, `TABLE_UNTRADED`, `ON_OBJECTS`) with the batch `slot`.
    The row pointers cut a market's bids, offers and offers left out of `bid_rows`, `offer_rows` and `left_rows` (arrival order;
    a market on the objects has none: its `Bid` and `Offer` lists are in `objects`). `Cleared` objects are made on demand (`cleared`,
    iteration): the year's rules read the columns."""

    def __init__(self, context, good: str, rows: GoodRows, batch, pack, slots: numpy.ndarray, untraded, flags_of, last_price: numpy.ndarray):
        count = len(rows.markets)
        self.context, self.good, self.rows, self.batch, self.pack, self.slots, self.untraded = context, good, rows, batch, pack, slots, untraded
        self.market = rows.markets
        self.areas = [context.orders.area_name_of_market(each) for each in rows.markets.tolist()]
        self.has_offers, self.has_units, self.has_funded_bid = flags_of
        self.last_price = last_price
        traded = numpy.zeros(count, dtype=numpy.bool_)
        batched = slots >= 0
        if batch is not None:
            traded[batched] = batch.traded_flag[slots[batched]]
        self.way = numpy.where(traded, TABLE_TRADED, numpy.where(batched | ~self.has_units, TABLE_UNTRADED, ON_OBJECTS)).astype(numpy.int64)
        self.quantity = numpy.zeros(count)
        self.price = numpy.full(count, numpy.nan)
        self.demand = numpy.zeros(count)
        self.offered = numpy.zeros(count)
        self.wanted = numpy.zeros(count)
        self.quote_price = numpy.full(count, numpy.nan)
        self.quote_kind = numpy.zeros(count, dtype=numpy.int64)
        self.objects = {}                 # place -> (bid objects, offers after, offers left, result) of a market on the objects
        by_batch = self.way == TABLE_TRADED
        if by_batch.any():
            at = slots[by_batch]
            self.price[by_batch], self.quantity[by_batch] = batch.mean[at], batch.traded[at]
            self.demand[by_batch], self.offered[by_batch] = batch.requested[at], batch.supply[at]
            self.wanted[by_batch] = self.demand[by_batch]
        by_quote = self.way == TABLE_UNTRADED
        if by_quote.any():
            self.price[by_quote] = held_prices(last_price, untraded.lowest_clamped)[by_quote]
            self.offered[by_quote] = untraded.supply[by_quote]
            self.wanted[by_quote] = untraded.wanted[by_quote]
            self.quote_price[by_quote], self.quote_kind[by_quote] = [each[by_quote] for each in
                                                                    untraded_quotes(untraded.lowest_ask, untraded.best_bid, untraded.funded)]
        self.bid_count = numpy.diff(rows.bid_group_ptr)
        self.bought = None                # (place, buyer number, units, money) of the first round's settlement, set by `goods_settle.settle_good`
        self.left_grouped = numpy.zeros(0, dtype=numpy.int64)    # the rows of the offers that keep units after the first round, market by market
        self.left_ptr = numpy.zeros(count + 1, dtype=numpy.int64)
        self.left_count = numpy.zeros(count, dtype=numpy.int64)   # how many offers keep units after the first round
        if by_batch.any() or by_quote.any():
            self._count_left(by_batch, by_quote)
        for place in numpy.flatnonzero(self.way == ON_OBJECTS).tolist():
            self._clear_on_objects(place)

    def _count_left(self, by_batch: numpy.ndarray, by_quote: numpy.ndarray) -> None:
        """The offers that keep units after the first round, market by market (`left_grouped`, `left_ptr`, `left_count`): for a market that traded
        the batch's offers with units left, in the batch's order; for one that did not trade the offers with units, in arrival order."""
        count = len(self.market)
        places, found = [], []
        if by_batch.any():
            slot_of_place = numpy.full(len(self.pack.offer_ptr) - 1, -1, dtype=numpy.int64)
            slot_of_place[self.slots[by_batch]] = numpy.flatnonzero(by_batch)
            place_of_offer = slot_of_place[numpy.repeat(numpy.arange(len(self.pack.offer_ptr) - 1), numpy.diff(self.pack.offer_ptr))]
            kept = (self.batch.left > 0.0) & (place_of_offer >= 0)
            places.append(place_of_offer[kept])
            found.append(self.pack.offer_rows[kept])
        if by_quote.any():
            offers = self.context.orders.tables()[1]
            grouped = self.rows.offer_grouped
            place_of_row = numpy.repeat(numpy.arange(count), numpy.diff(self.rows.offer_group_ptr))
            kept = by_quote[place_of_row] & (offers.quantity[grouped] > 0.0)
            places.append(place_of_row[kept])
            found.append(grouped[kept])
        place, rows = numpy.concatenate(places), numpy.concatenate(found)
        order = numpy.argsort(place, kind="stable")
        self.left_grouped = rows[order]
        self.left_ptr = numpy.concatenate(([0], numpy.cumsum(numpy.bincount(place, minlength=count)))).astype(numpy.int64)
        self.left_count = numpy.diff(self.left_ptr)

    def _clear_on_objects(self, place: int) -> None:
        """The old rules on the market's `Bid` and `Offer` objects; the figures of the result are written into the columns."""
        context, orders = self.context, self.context.orders
        bid_objects, offer_objects = orders.bids_of(self.rows.bids_of_market(place)), orders.offers_of(self.rows.offers_of_market(place))
        price = self.last_price[place]
        after, result = _plain(context, self.good, self.areas[place], None if price != price else float(price), bid_objects, offer_objects)
        self.objects[place] = (bid_objects, after, offers_left(after, sold_by_result(result)), result)
        self.left_count[place] = len(self.objects[place][2])
        self.quantity[place], self.demand[place], self.offered[place] = result.quantity, result.demand_at_price, result.offered_at_price
        self.price[place] = numpy.nan if result.price is None else result.price
        wanted = wanted_in_round(bid_objects, after, result)
        self.wanted[place] = wanted
        if result.quote is not None:
            self.quote_price[place], self.quote_kind[place] = result.quote.price, QUOTE_KINDS.index(result.quote.kind)

    @classmethod
    def empty(cls) -> "GoodClearing":
        """No markets."""
        none = cls.__new__(cls)
        none.market = numpy.zeros(0, dtype=numpy.int64)
        none.quantity = none.price = none.demand = none.offered = none.wanted = none.quote_price = numpy.zeros(0)
        none.quote_kind = none.way = numpy.zeros(0, dtype=numpy.int64)
        none.has_offers = none.has_units = none.has_funded_bid = numpy.zeros(0, dtype=numpy.bool_)
        none.areas = []
        none.bid_count = none.left_count = numpy.zeros(0, dtype=numpy.int64)
        none.bought = None
        none.left_grouped, none.left_ptr = numpy.zeros(0, dtype=numpy.int64), numpy.zeros(1, dtype=numpy.int64)
        none.rows = None
        return none

    def __len__(self) -> int:
        return len(self.market)

    def result(self, place: int):
        """The first round's `ClearingResult` of market `place`, made now."""
        if self.way[place] == ON_OBJECTS:
            return self.objects[place][3]
        if self.way[place] == TABLE_TRADED:
            return TableClearing.of(self.batch, int(self.slots[place]), self.good, self.areas[place], self.context.setup.currency_id)
        figures = self.untraded
        price = self.last_price[place]
        return untraded_result(self.good, self.areas[place], self.context.setup.currency_id, None if price != price else float(price),
                               float(figures.supply[place]), figures.lowest_ask[place], figures.lowest_clamped[place], figures.best_bid[place],
                               bool(figures.funded[place]))

    def left_rows_of(self, place: int) -> numpy.ndarray:
        """The rows of the market's offers that kept units after the first round (offers with units, for a market that did not trade)."""
        return self.left_grouped[self.left_ptr[place]:self.left_ptr[place + 1]]

    def market_rows(self, place: int):
        """The market's `MarketRows` (None for a market on the objects)."""
        if self.way[place] == ON_OBJECTS:
            return None
        return MarketRows(self.context.orders, self.rows.bids_of_market(place), self.left_rows_of(place), self.rows.offers_of_market(place))

    def cleared(self, place: int) -> Cleared:
        """The market as a `Cleared`."""
        flags_of = (self.has_offers[place], self.has_units[place], self.has_funded_bid[place])
        if self.way[place] == ON_OBJECTS:
            bid_objects, after, left, result = self.objects[place]
            return Cleared(self.areas[place], int(self.market[place]), result, bid_objects, after, left, None, *flags_of, None)
        return Cleared(self.areas[place], int(self.market[place]), self.result(place), None, None, None, float(self.wanted[place]), *flags_of,
                       self.market_rows(place))

    def __iter__(self):
        return (self.cleared(place) for place in range(len(self)))

    def __getitem__(self, place: int) -> Cleared:
        return self.cleared(place)

    def __bool__(self) -> bool:
        return len(self) > 0


def clear_good(context, good: str, good_id: int) -> GoodClearing:
    """Clear the markets of `good` that have orders, one after another in area order."""
    orders = context.orders
    bids, offers = orders.tables()
    rows = rows_of_good(orders, good_id)
    if not len(rows.markets):
        return GoodClearing.empty()
    note_stock_slots(offers, context.book, good_id, rows.offer_rows)
    flags = batch_flags(offers, context.book.agent_table.is_edge, rows, context.good_is_batchable(good))
    batch = pack = untraded = None
    slots = numpy.full(len(rows.markets), -1, dtype=numpy.int64)
    if flags.any():
        batch, pack, slots = _batched(context, good, rows, flags)
    flags_of = flags_by_market(bids, offers, rows)
    last_price = orders.memory_tables.goods_table.price[rows.markets]
    traded = numpy.zeros(len(slots), dtype=numpy.bool_)
    if batch is not None:
        traded[slots >= 0] = batch.traded_flag[slots[slots >= 0]]
    if (((slots >= 0) & ~traded) | ~flags_of[1]).any():       # a market that did not trade has its quote read from the columns
        untraded = Untraded(bids, offers, rows, last_price)
    return GoodClearing(context, good, rows, batch, pack, slots, untraded, flags_of, last_price)


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
