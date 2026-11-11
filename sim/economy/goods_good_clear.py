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
from .goods_clearing_kernel import ON_OBJECTS, TABLE_TRADED, TABLE_UNTRADED, clearing_columns
from .goods_table_group import GoodRows, note_stock_slots, rows_of_good
from .goods_table_pack import pack_batch
from .goods_table_quotes import untraded_result
from .goods_table_results import TableClearing
from .goods_table_views import TableBatch
from .goods_untraded_kernel import untraded_columns
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


class Untraded:
    """The quote figures of every market of a good that did not trade, worked out together (`goods_untraded_kernel`), or taken from
    the columns `goods_clear_kernel` worked out."""

    def __init__(self, bids, offers, rows: GoodRows, last_price: numpy.ndarray, columns=None):
        (self.lowest_ask, self.lowest_clamped, self.supply, self.funded, self.best_bid, self.wanted) = columns if columns is not None else (
            untraded_columns(bids, offers, rows.bid_grouped, rows.bid_group_ptr, rows.offer_grouped, rows.offer_group_ptr, last_price,
                             MINIMUM_PRICE_SHARE_OF_REFERENCE))


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
    """(the batch's allocation, the pack): the batched markets cleared."""
    pack = pack_batch(context, rows, flags)
    allocated = clear_batch(context, good, pack)
    return TableBatch(allocated, pack, context.orders), pack


QUOTE_KINDS = (None, QUOTE_BEST_UNFILLED_BID, QUOTE_LOWEST_UNFILLED_ASK, QUOTE_COST_COVERING, QUOTE_OPENING_ESTIMATE)    # the code of a quote's kind in `GoodClearing.quote_kind`


class GoodClearing:
    """One good's cleared markets as columns, in the order they clear (every array has one entry per market): the id and area, the first
    round's result (`quantity`, `price` (NaN: none), `demand`, `offered`, the quote as `quote_price` and `quote_kind`), what the buyers
    `wanted`, the flags the market's memory is noted by, and `way` (`TABLE_TRADED`, `TABLE_UNTRADED`, `ON_OBJECTS`) with the batch `slot`.
    The row pointers cut a market's bids, offers and offers left out of `bid_rows`, `offer_rows` and `left_rows` (arrival order;
    a market on the objects has none: its `Bid` and `Offer` lists are in `objects`). `Cleared` objects are made on demand (`cleared`,
    iteration): the year's rules read the columns."""

    def __init__(self, context, good: str, rows: GoodRows, batch, pack, untraded, flags_of, last_price: numpy.ndarray, flags: numpy.ndarray,
                 made=None):
        """`made` is (`clearing_columns`' twelve arrays, how many markets are on the objects, the bid counts) when `goods_clear_kernel` worked them out."""
        self.context, self.good, self.rows, self.batch, self.pack, self.untraded = context, good, rows, batch, pack, untraded
        self.market = rows.markets
        self.areas = context.orders.area_names_of_markets(rows.markets)
        self.has_offers, self.has_units, self.has_funded_bid = flags_of
        self.last_price = last_price
        if made is None:
            no_floats, no_ints = numpy.zeros(0), numpy.zeros(0, dtype=numpy.int64)
            batch_figures = (batch.traded_flag, batch.mean, batch.traded, batch.requested, batch.supply, batch.left, pack.offer_ptr,
                             pack.offer_rows) if batch is not None else (numpy.zeros(0, dtype=numpy.bool_), no_floats, no_floats, no_floats,
                                                                          no_floats, no_floats, numpy.zeros(1, dtype=numpy.int64), no_ints)
            quote_figures = (untraded.lowest_ask, untraded.lowest_clamped, untraded.supply, untraded.wanted, untraded.best_bid,
                             untraded.funded) if untraded is not None else (no_floats,) * 5 + (numpy.zeros(0, dtype=numpy.bool_),)
            columns = clearing_columns(
                flags, self.has_units, last_price, *batch_figures, *quote_figures, rows.offer_grouped, rows.offer_group_ptr,
                context.orders.tables()[1].quantity)
            on_objects, self.bid_count = True, numpy.diff(rows.bid_group_ptr)
        else:
            columns, on_objects, self.bid_count = made
        (self.slots, self.way, self.quantity, self.price, self.demand, self.offered, self.wanted, self.quote_price, self.quote_kind,
         self.left_grouped, self.left_ptr, self.left_count) = columns
        self.objects = {}                 # place -> (bid objects, offers after, offers left, result) of a market on the objects
        self.bought = None                # (place, buyer number, units, money) of the first round's settlement, set by `goods_settle.settle_good`
        if on_objects:
            for place in numpy.flatnonzero(self.way == ON_OBJECTS).tolist():
                self._clear_on_objects(place)

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
    from . import goods_clear_fused     # it makes `GoodClearing`s, so it imports this module
    if goods_clear_fused.can_fuse(context, good):
        return goods_clear_fused.fused_clear(context, good, good_id)
    orders = context.orders
    rows, flags, flags_of = rows_of_good(orders, good_id, context.book.agent_table.is_edge, context.good_is_batchable(good))
    if not len(rows.markets):
        return GoodClearing.empty()
    bids, offers = orders.tables()
    note_stock_slots(offers, context.book, good_id, rows.offer_rows)
    batch = pack = None
    if flags.any():
        batch, pack = _batched(context, good, rows, flags)
    last_price = orders.memory_tables.goods_table.price[rows.markets]
    untraded = Untraded(bids, offers, rows, last_price)     # read after the batch wrote the offers' final reservations
    return GoodClearing(context, good, rows, batch, pack, untraded, flags_of, last_price, flags)


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
