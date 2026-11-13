"""A good's batched markets cleared from the order tables: the same decisions as `goods_year_batch.clear_markets` (the sellers'
re-pricing, the unsold search, the final allocation), read from columns and written back to them.

`clear_batch` runs `goods_year_kernel.decide_markets` once for the good's batched markets, then
`goods_year_results.final_allocations` at the reservations it chose, and writes what came out into the tables: the offers'
final reservation, ask, units sold and left, the bids' units and cost, the markets' results, and the pairs (`write_batch`)."""
import math

import numpy

from sim.compiled_tables.growth import reserve_rows

from . import goods_year_kernel, goods_year_results, price_setting, titles_value
from .goods_batch_write_kernel import write_batch as write_batch_kernel
from .goods_decide_inputs_kernel import decide_inputs
from .goods_table_pack import BatchPack


def decide_reservations(context, good: str, pack: BatchPack) -> numpy.ndarray:
    """The final reservation of each offer of the pack: the sellers re-priced and the unsold search done, over the arrays
    (`goods_decide_inputs_kernel.decide_inputs` gathers what each offer's seller needs, then `decide_markets` decides)."""
    arrays, costs = context.arrays, context.costs
    producers, matrices = arrays.producers, arrays.matrices
    offers = context.orders.offers
    spec = context.setup.specs.get(good)
    producer_rows = context.producer_row_table()
    while True:
        (reservation, quantity, is_producer, unit_cost, input_share, expected_price, workshops, multiple_workshops, expected_sales, band,
         spoilage, missing_count, missing_tiles) = decide_inputs(
            pack.offer_rows, pack.offer_ptr, offers, producer_rows, producers.recipe_row, producers.workshops, producers.expected_sales,
            producers.yield_factor, costs.slot_of, matrices.goods.row[good], costs.cost, costs.input_share, costs.expected, matrices.outputs,
            context.band_multiple_table(good), spec.spoilage_per_year if spec is not None else 0.0)
        if missing_count == 0:
            break
        for tile in numpy.flatnonzero(missing_tiles).tolist():
            context.note_band_multiple(tile, good)
    floors, flexibles, budgets, references, exponents, capped, tier_ptr, tier_values, maximums = pack.demand
    steps = price_setting
    return goods_year_kernel.decide_markets(
        pack.has_bids, pack.offer_ptr, reservation, quantity, is_producer, unit_cost, input_share, expected_price, workshops,
        multiple_workshops, expected_sales, band, pack.key_of, pack.size, pack.rate, spoilage, pack.minimum,
        pack.has_minimum, pack.bid_ptr, floors, flexibles, budgets, references, exponents, maximums, capped, tier_ptr, tier_values,
        steps.LOGIT_INTENSITY, math.floor((steps.GRID_END - steps.GRID_START) / steps.GRID_STEP + 1e-9), steps.GRID_START,
        steps.GRID_STEP, steps.MONTHS, steps.MONTHLY_DISCOUNT_RATE, _ground_values(context, good, pack, offers))


def _ground_values(context, good: str, pack: BatchPack, offers) -> numpy.ndarray:
    """Per offer of the pack, what its last unit is worth held for later where the good is ground (not portable): a hectare yields its rent
    while it is held (`unsold_search._held_value`); NaN for any other good, whose held value is the queued-stock rule's."""
    spec = context.setup.specs.get(good)
    value = numpy.full(len(pack.offer_rows), numpy.nan)
    if spec is None or spec.portable or not len(pack.offer_rows):
        return value
    book, setup = context.book, context.setup
    rent = context.record.land.land_rent
    tiles = book.tile_ids.name_list
    market_of_offer = numpy.repeat(numpy.arange(len(pack.offer_ptr) - 1), numpy.diff(pack.offer_ptr))
    for place, (row, market) in enumerate(zip(pack.offer_rows.tolist(), market_of_offer.tolist())):
        rate = pack.rate[market]
        if rate == rate:       # no rate remembered for the area: the offer is not searched at all
            value[place] = titles_value.hectare_value(rent.get(tiles[offers.tile[row]], 0.0), titles_value.capitalising_rate(rate, setup.opening_rate))
    return value


def allocate(pack: BatchPack, orders, final: numpy.ndarray) -> tuple:
    """`goods_year_results.final_allocations` for the pack at the reservations `final`."""
    floors, flexibles, budgets, references, exponents, capped, tier_ptr, tier_values, maximums = pack.demand
    return goods_year_results.final_allocations(
        pack.offer_ptr, final, orders.offers.quantity[pack.offer_rows], pack.key_of, pack.minimum, pack.has_minimum,
        pack.bid_ptr, floors, flexibles, budgets, references, exponents, maximums, capped, tier_ptr, tier_values)


def write_batch(orders, bids, offers, pack: BatchPack, final: numpy.ndarray, allocated: tuple) -> None:
    """Write the allocation into the tables in one kernel call: the offers' final reservation, ask, units sold and left, the bids' units
    and cost and place in clearing order, and the batch's rows appended to the bid order, offer order, pairs and results tables."""
    (traded_flag, requested, traded, mean, supply, ask, sold, left, rank, bid_quantity, bid_cost, pair_ptr, pair_offer, pair_bid,
     pair_quantity) = allocated
    for name, extra in (("bid_order", len(pack.bid_rows)), ("offer_order", len(pack.offer_rows)), ("pairs", len(pair_quantity)),
                        ("results", len(pack.market_ids))):
        setattr(orders, name, reserve_rows(getattr(orders, name), extra))
    write_batch_kernel(bids, offers, orders.bid_order, orders.offer_order, orders.pairs, orders.results, pack.market_ids, pack.bid_rows,
                       pack.bid_ptr, pack.offer_rows, pack.offer_ptr, final, (ask, sold, left, rank), (bid_quantity, bid_cost),
                       (traded_flag, requested, traded, mean, supply), pair_ptr, pair_bid, pair_offer, pair_quantity)


def clear_batch(context, good: str, pack: BatchPack) -> tuple:
    """Decide and allocate the pack's markets and write the answer into the tables. Returns the allocation arrays of
    `final_allocations` (per market the traded flag, units requested, traded, mean ask and supply; per offer and bid and pair
    the rest, indexed like the pack's rows)."""
    orders = context.orders
    final = decide_reservations(context, good, pack)
    allocated = allocate(pack, orders, final)
    bids, offers = orders.tables()
    write_batch(orders, bids, offers, pack, final, allocated)
    return allocated
