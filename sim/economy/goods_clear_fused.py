"""A good's clearing in one kernel call (`goods_clear_kernel.clear_good_columns`) and the `GoodClearing` made from what it returns.

`fused_clear` answers None for a good the kernel does not hold, and `clear_good` then takes the chain of separate steps: a good outside the
year arrays, and a good that is ground (not portable: the hectare it holds is worth its land rent, `goods_table_clear._ground_values`)."""
import math

import numpy

from sim.compiled_tables.growth import reserve_rows

from . import price_setting
from .goods_clear_kernel import NeedsInputs, clear_good_columns
from .goods_good_clear import GoodClearing, Untraded
from .goods_market import MINIMUM_PRICE_SHARE_OF_REFERENCE
from .goods_table_group import GoodRows
from .goods_table_pack import BatchPack
from .goods_table_views import TableBatch

STEPS = (price_setting.LOGIT_INTENSITY, math.floor((price_setting.GRID_END - price_setting.GRID_START) / price_setting.GRID_STEP + 1e-9),
         price_setting.GRID_START, price_setting.GRID_STEP, price_setting.MONTHS, price_setting.MONTHLY_DISCOUNT_RATE)


GROWTH = 7        # a table that has no room for a good's rows is given room for this many times its size more


def can_fuse(context, good: str) -> bool:
    """The good is in the year arrays and portable (or has no spec)."""
    if not context.good_is_batchable(good):
        return False
    spec = context.setup.specs.get(good)
    return spec is None or spec.portable


def _answer(context, good: str, flags_to_ask: tuple, room: numpy.ndarray) -> None:
    """Ask Python's questions the kernel raised for: lending rates, band multiples, room in the appended tables."""
    missing_areas, missing_tiles = flags_to_ask
    for area in numpy.flatnonzero(missing_areas).tolist():
        context.note_area_rate(area)
    for tile in numpy.flatnonzero(missing_tiles).tolist():
        context.note_band_multiple(tile, good)
    orders = context.orders
    for name, extra in zip(("bid_order", "offer_order", "pairs", "results"), room.tolist()):
        table = getattr(orders, name)
        if table.row_count[0] + extra > table.capacity[0]:         # grows by a factor, so that few goods ask again
            setattr(orders, name, reserve_rows(table, extra + GROWTH * int(table.capacity[0])))
    missing_areas[:] = False
    missing_tiles[:] = False
    room[:] = 0


def fused_clear(context, good: str, good_id: int):
    """The good's `GoodClearing`, made by one kernel call (answering what it asks for and calling again)."""
    orders, arrays = context.orders, context.arrays
    producers, matrices, costs = arrays.producers, arrays.matrices, context.costs
    spec = context.setup.specs.get(good)
    book = context.book
    context.reserve_cleared_rows()
    while True:
        bids, offers = orders.tables()           # first: it numbers the names of the orders waiting, which the ranks and tables read below follow
        goods_table = orders.memory_tables.goods_table
        rates, known = context.area_rates()
        band_multiples = context.band_multiple_table(good)
        scratch = context.scratch(len(known), len(band_multiples))
        try:
            found = clear_good_columns(
                (bids, offers, orders.bid_order, orders.offer_order, orders.pairs, orders.results), good_id, matrices.goods.row[good],
                (goods_table.area, goods_table.price, goods_table.volume_weight, context.record.goods.unmet.values),
                (orders.area_ranks(), context.agent_rank(), context.tile_rank()), book.agent_table.is_edge, (book.stock_rows.table, book.stock_rows.index),
                context.producer_row_table(), (producers.recipe_row, producers.workshops, producers.expected_sales, producers.yield_factor),
                (costs.slot_of, costs.cost, costs.input_share, costs.expected), matrices.outputs, band_multiples,
                spec.spoilage_per_year if spec is not None else 0.0, rates, known, STEPS, MINIMUM_PRICE_SHARE_OF_REFERENCE, *scratch)
        except NeedsInputs:
            _answer(context, good, scratch[:2], scratch[2])
            continue
        break
    rows, flags, flags_of, pack, allocated, quotes, clearing, on_objects, bid_count, last_price = found
    if not len(rows[0]):
        return GoodClearing.empty()
    pack = BatchPack(*pack[:7], pack[7:16], *pack[16:21])
    batch = TableBatch(allocated, pack, orders) if len(pack.market_ids) else None
    if batch is None:
        pack = None
    rows = GoodRows(*rows)
    return GoodClearing(context, good, rows, batch, pack, Untraded(bids, offers, rows, last_price, quotes), flags_of, last_price, flags,
                        (clearing, on_objects, bid_count))
