"""A good's batched markets read out of the order tables into the arrays of `goods_year_kernel.decide_markets`.

What `goods_year_batch.clear_markets` built from lists of `Bid` and `Offer`, built from columns: the offers with units of each
market in seller-and-tile order, its bids in clearing order (priority, buyer, tile; ties by arrival), the demand schedules
packed per market (`goods_market_kernels.pack_demand_many`), and the per-market figures the kernel reads (market size,
lending rate, spoilage, token minimum price). The rows are cut by market with `offer_ptr` and `bid_ptr`."""
from dataclasses import dataclass

import numpy

from .goods_market import MINIMUM_PRICE_SHARE_OF_REFERENCE
from .goods_pack_kernel import pack_arrays


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


def pack_batch(context, rows, flags: numpy.ndarray) -> BatchPack:
    """Everything the decision kernel reads for the good's batched markets: `goods_pack_kernel.pack_arrays` over the order tables.
    The lending rate of an area it has not been asked for is asked now (all such areas together) and the kernel runs again."""
    orders = context.orders
    bids, offers = orders.tables()
    agent_rank, tile_rank = context.agent_rank(), context.tile_rank()
    goods_table = orders.memory_tables.goods_table
    unmet = context.record.goods.unmet.values      # a market id is always numbered, so the column holds it
    while True:
        rates, known = context.area_rates()
        found = pack_arrays(bids, offers, rows.offer_rows, rows.offer_position, rows.bid_rows, rows.bid_position, flags, rows.markets,
                            agent_rank, agent_rank, tile_rank, goods_table.price, goods_table.volume_weight, goods_table.area, unmet,
                            rates, known, MINIMUM_PRICE_SHARE_OF_REFERENCE)
        if found[-2] == 0:
            break
        for area in numpy.flatnonzero(found[-1]).tolist():
            context.note_area_rate(area)
    return BatchPack(*found[:7], found[7:16], *found[16:21])
