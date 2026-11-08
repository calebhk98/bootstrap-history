"""A good's batched markets cleared from the order tables: the same decisions as `goods_year_batch.clear_markets` (the sellers'
re-pricing, the unsold search, the final allocation), read from columns and written back to them.

`clear_batch` runs `goods_year_kernel.decide_markets` once for the good's batched markets, then
`goods_year_results.final_allocations` at the reservations it chose, and writes what came out into the tables: the offers'
final reservation, ask, units sold and left, the bids' units and cost, the markets' results, and the pairs."""
import math

import numpy

from . import goods_year_kernel, goods_year_results, price_setting, titles_value
from .goods_table_pack import BatchPack


def decide_reservations(context, good: str, pack: BatchPack) -> numpy.ndarray:
    """The final reservation of each offer of the pack: the sellers re-priced and the unsold search done, over the arrays."""
    arrays, costs = context.arrays, context.costs
    producers, matrices = arrays.producers, arrays.matrices
    offers = context.orders.offers
    rows = context.producer_rows(offers.seller[pack.offer_rows])
    goods = numpy.full(len(rows), matrices.goods.row[good], dtype=numpy.int64)
    is_producer = rows >= 0
    safe = numpy.where(is_producer, rows, 0)
    recipe = producers.recipe_row[safe]
    slot = costs.slot_of[recipe, goods]
    known = is_producer & (slot >= 0)
    place = numpy.where(known, slot, 0)
    workshops = numpy.where(is_producer, producers.workshops[safe], 1).astype(float)
    expected_sales = numpy.where(
        is_producer, producers.expected_sales[safe] * producers.yield_factor[safe] * matrices.outputs[recipe, goods], 0.0)
    spec = context.setup.specs.get(good)
    spoilage = numpy.full(len(pack.market_ids), spec.spoilage_per_year if spec is not None else 0.0)
    floors, flexibles, budgets, references, exponents, capped, tier_ptr, tier_values, maximums = pack.demand
    steps = price_setting
    return goods_year_kernel.decide_markets(
        pack.has_bids, pack.offer_ptr, offers.reservation_price[pack.offer_rows], offers.quantity[pack.offer_rows], is_producer,
        numpy.where(known, costs.cost[safe, place], numpy.inf), numpy.where(known, costs.input_share[safe, place], 0.0),
        numpy.where(known, costs.expected[safe, place], numpy.nan), workshops, is_producer & (workshops > 1.0), expected_sales,
        context.band_multiples(offers.tile[pack.offer_rows]), pack.key_of, pack.size, pack.rate, spoilage, pack.minimum,
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


def write_offers(offers, pack: BatchPack, final, ask, sold, left, rank) -> None:
    """The offers' final reservations and what the allocation did to them, in place."""
    rows = pack.offer_rows
    offers.reservation_price[rows] = final
    offers.ask[rows], offers.quantity_sold[rows], offers.quantity_left[rows], offers.rank[rows] = ask, sold, left, rank


def write_bids(bids, pack: BatchPack, quantity, cost) -> None:
    """The bids' units and cost, and their place in their market's clearing order, in place."""
    rows = pack.bid_rows
    bids.quantity_bought[rows], bids.cost[rows] = quantity, cost
    bids.position[rows] = numpy.arange(len(rows)) - numpy.repeat(pack.bid_ptr[:-1], numpy.diff(pack.bid_ptr))


def record_batch(orders, pack: BatchPack, allocated: tuple) -> None:
    """Append the batch's markets to the results table, the clearing order tables and the pairs table."""
    (traded_flag, requested, traded, mean, supply, _ask, _sold, _left, _rank, _bid_quantity, _bid_cost, pair_ptr, pair_offer,
     pair_bid, pair_quantity) = allocated
    first_bid = orders.append_rows("bid_order", bid_row=pack.bid_rows)
    first_offer = orders.append_rows("offer_order", offer_row=pack.offer_rows)
    first_pair = orders.append_rows("pairs", bid_row=pack.bid_rows[pair_bid], offer_row=pack.offer_rows[pair_offer],
                                    quantity=pair_quantity)
    orders.append_rows("results", market=pack.market_ids, traded=traded_flag, quantity=traded, price=mean, demand_at_price=requested,
                       offered_at_price=supply, first_bid_slot=first_bid + pack.bid_ptr[:-1], bid_count=numpy.diff(pack.bid_ptr),
                       first_offer_slot=first_offer + pack.offer_ptr[:-1], offer_count=numpy.diff(pack.offer_ptr),
                       first_pair=first_pair + pair_ptr[:-1], pair_count=numpy.diff(pair_ptr))


def clear_batch(context, good: str, pack: BatchPack) -> tuple:
    """Decide and allocate the pack's markets and write the answer into the tables. Returns the allocation arrays of
    `final_allocations` (per market the traded flag, units requested, traded, mean ask and supply; per offer and bid and pair
    the rest, indexed like the pack's rows)."""
    orders = context.orders
    final = decide_reservations(context, good, pack)
    allocated = allocate(pack, orders, final)
    bids, offers = orders.tables()
    write_offers(offers, pack, final, *allocated[5:9])
    write_bids(bids, pack, *allocated[9:11])
    record_batch(orders, pack, allocated)
    return allocated
