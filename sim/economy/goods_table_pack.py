"""A good's batched markets read out of the order tables into the arrays of `goods_year_kernel.decide_markets`.

What `goods_year_batch.clear_markets` built from lists of `Bid` and `Offer`, built from columns: the offers with units of each
market in seller-and-tile order, its bids in clearing order (priority, buyer, tile; ties by arrival), the demand schedules
packed per market (`goods_market_kernels.pack_demand_many`), and the per-market figures the kernel reads (market size,
lending rate, spoilage, token minimum price). The rows are cut by market with `offer_ptr` and `bid_ptr`."""
from dataclasses import dataclass

import numpy

from sim.jit import njit

from . import goods_market_kernels
from .goods_market import MINIMUM_PRICE_SHARE_OF_REFERENCE


@dataclass
class BatchPack:
    """The batched markets of one good as the kernels read them: markets `positions` (places in the good's market list)."""
    positions: numpy.ndarray        # the batched markets' places in GoodRows.markets
    market_ids: numpy.ndarray       # their goods market ids
    offer_rows: numpy.ndarray       # offer rows with units, market after market, in seller-and-tile order
    offer_ptr: numpy.ndarray        # per market: where its offers start in offer_rows (length markets + 1)
    key_of: numpy.ndarray           # per offer: its (seller, tile) number within its market
    bid_rows: numpy.ndarray         # bid rows, market after market, in clearing order
    bid_ptr: numpy.ndarray
    demand: tuple                   # goods_market_kernels.pack_demand_many's arrays, then each bid's ceiling
    size: numpy.ndarray             # per market: its usual volume plus the unmet demand (NaN: no history)
    rate: numpy.ndarray             # per market: the lending rate of its area (NaN: none)
    minimum: numpy.ndarray          # per market: the token minimum price (0 where has_minimum is false)
    has_minimum: numpy.ndarray
    has_bids: numpy.ndarray


@njit
def price_scales(bid_ptr, reference_price, last_price):
    """Per market, the mean positive reference price of its bids, else its last price when positive, else NaN
    (`goods_market._price_scale`). The reference prices are added left to right."""
    markets = len(bid_ptr) - 1
    scale = numpy.full(markets, numpy.nan)
    for market in range(markets):
        total = 0.0
        count = 0
        for bid in range(bid_ptr[market], bid_ptr[market + 1]):
            if reference_price[bid] > 0.0:
                total += reference_price[bid]
                count += 1
        if count > 0:
            scale[market] = total / count
        elif last_price[market] > 0.0:
            scale[market] = last_price[market]
    return scale


def _slot_of_position(flags: numpy.ndarray) -> numpy.ndarray:
    """Per market place: its place among the batched markets, -1 for a market that is not batched."""
    return numpy.where(flags, numpy.cumsum(flags) - 1, -1)


def _pointers(slots: numpy.ndarray, markets: int) -> numpy.ndarray:
    return numpy.concatenate(([0], numpy.cumsum(numpy.bincount(slots, minlength=markets)))).astype(numpy.int64)


def sorted_offers(offers, rows, flags, seller_rank, tile_rank):
    """(offer rows, market slots) of the batched markets' offers with units, by (market, seller name, tile name), arrival order
    breaking ties."""
    slot_of = _slot_of_position(flags)
    chosen = flags[rows.offer_position] & (offers.quantity[rows.offer_rows] > 0.0)
    candidates, slots = rows.offer_rows[chosen], slot_of[rows.offer_position[chosen]]
    order = numpy.lexsort((tile_rank[offers.tile[candidates]], seller_rank[offers.seller[candidates]], slots))
    return candidates[order], slots[order]


def sorted_bids(bids, rows, flags, buyer_rank, tile_rank):
    """(bid rows, market slots) of the batched markets' bids, by (market, priority, buyer name, tile name), arrival order
    breaking ties (`goods_market.Buyers`)."""
    slot_of = _slot_of_position(flags)
    chosen = flags[rows.bid_position]
    candidates, slots = rows.bid_rows[chosen], slot_of[rows.bid_position[chosen]]
    order = numpy.lexsort((tile_rank[bids.tile[candidates]], buyer_rank[bids.buyer[candidates]], bids.priority[candidates], slots))
    return candidates[order], slots[order]


def seller_tile_numbers(offers, offer_rows, offer_slots, offer_ptr) -> numpy.ndarray:
    """Per offer (already in seller-and-tile order): the number of its (seller, tile) within its market, from 0."""
    if not len(offer_rows):
        return numpy.zeros(0, dtype=numpy.int64)
    seller, tile = offers.seller[offer_rows], offers.tile[offer_rows]
    new = numpy.ones(len(offer_rows), dtype=bool)
    new[1:] = (seller[1:] != seller[:-1]) | (tile[1:] != tile[:-1]) | (offer_slots[1:] != offer_slots[:-1])
    running = numpy.cumsum(new) - 1
    return running - running[offer_ptr[offer_slots]]


def demand_table(bids, bid_rows) -> numpy.ndarray:
    """The bids' schedule fields as `goods_market_demand._SCHEDULE_FIELDS` gives them, one row per bid."""
    return numpy.column_stack((bids.floor_quantity[bid_rows], bids.flexible_quantity[bid_rows], bids.reference_price[bid_rows],
                               bids.elasticity[bid_rows], bids.budget[bid_rows], bids.maximum_price[bid_rows],
                               bids.priority[bid_rows].astype(numpy.float64)))


def market_figures(context, market_ids, good: str):
    """(size, rate, last price) per market: the usual volume plus the unmet demand, the area's lending rate, and the remembered
    price, each NaN where there is none."""
    tables = context.orders.memory_tables
    goods_table = tables.goods_table
    unmet = context.record.goods.unmet.take(market_ids)
    last_price = goods_table.price[market_ids]
    usual = goods_table.volume_weight[market_ids]
    size = usual + numpy.where(numpy.isnan(unmet), 0.0, unmet)      # NaN where the market has no usual volume
    rate = numpy.array([context.rate_in(area) for area in context.orders.area_names_of_markets(market_ids)], dtype=numpy.float64)
    return size, rate, last_price


def pack_batch(context, good: str, rows, flags: numpy.ndarray) -> BatchPack:
    """Everything the decision kernel reads for the good's batched markets."""
    orders = context.orders
    bids, offers = orders.tables()
    seller_rank, buyer_rank, tile_rank = context.agent_rank(), context.agent_rank(), context.tile_rank()
    count = int(flags.sum())
    offer_rows, offer_slots = sorted_offers(offers, rows, flags, seller_rank, tile_rank)
    bid_rows, bid_slots = sorted_bids(bids, rows, flags, buyer_rank, tile_rank)
    offer_ptr, bid_ptr = _pointers(offer_slots, count), _pointers(bid_slots, count)
    positions = numpy.flatnonzero(flags)
    market_ids = rows.markets[positions]
    table = demand_table(bids, bid_rows)
    demand = goods_market_kernels.pack_demand_many(table, bid_ptr) + (table[:, 5].copy(),)
    size, rate, last_price = market_figures(context, market_ids, good)
    scale = price_scales(bid_ptr, bids.reference_price[bid_rows], last_price)
    has_minimum = ~numpy.isnan(scale)
    minimum = numpy.where(has_minimum, MINIMUM_PRICE_SHARE_OF_REFERENCE * numpy.where(has_minimum, scale, 0.0), 0.0)
    return BatchPack(positions, market_ids, offer_rows, offer_ptr, seller_tile_numbers(offers, offer_rows, offer_slots, offer_ptr),
                     bid_rows, bid_ptr, demand, size, rate, minimum, has_minimum, numpy.diff(bid_ptr) > 0)
