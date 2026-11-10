"""The chain of kernel calls `goods_clear_kernel.clear_good_columns` replaced, written out in plain Python in the order
`goods_good_clear.clear_good` made them, and seeded random worlds (order tables, producers, costs) with many ties to run both on."""
import math

import numpy

from sim.compiled_tables.growth import reserve_rows
from sim.book_read_kernels import find_slots
from sim.economy import price_setting
from sim.economy.goods_batch_write_kernel import write_batch
from sim.economy.goods_clearing_kernel import ON_OBJECTS, clearing_columns
from sim.economy.goods_decide_inputs_kernel import decide_inputs
from sim.economy.goods_order_tables import (BID_ORDER, GOODS_MARKET_RESULTS, GOODS_PAIRS, OFFER_ORDER, BidOrder, GoodsMarketResults,
                                            GoodsPairs, OfferOrder)
from sim.economy.goods_pack_kernel import pack_arrays
from sim.economy.goods_rows_kernel import good_rows
from sim.economy.goods_untraded_kernel import untraded_columns
from sim.economy.goods_year_kernel import decide_markets
from sim.economy.goods_year_results import final_allocations
from sim.tests.book_table_fixtures import StockBook, agents_table
from sim.tests.goods_good_plain import random_tables

AGENTS, TILES, MARKETS, AREAS, GOODS = 6, 4, 6, 4, 3
STEPS = (price_setting.LOGIT_INTENSITY, math.floor((price_setting.GRID_END - price_setting.GRID_START) / price_setting.GRID_STEP + 1e-9),
         price_setting.GRID_START, price_setting.GRID_STEP, price_setting.MONTHS, price_setting.MONTHLY_DISCOUNT_RATE)


def order_tables(capacity):
    return [BID_ORDER.new_table(BidOrder, capacity), OFFER_ORDER.new_table(OfferOrder, capacity), GOODS_PAIRS.new_table(GoodsPairs, capacity),
            GOODS_MARKET_RESULTS.new_table(GoodsMarketResults, capacity)]


def random_world(seed, bid_count=None, offer_count=None):
    """(tables, arguments): the six order tables and the rest of `clear_good_columns`' arguments, after `good_id` and `good_column`.
    Rows of the first table pair are random; the appended tables are empty with room for a few rows."""
    generator = numpy.random.default_rng(seed)
    bids, offers = random_tables(generator, int(generator.integers(0, 30)) if bid_count is None else bid_count,
                                 int(generator.integers(0, 30)) if offer_count is None else offer_count, goods=GOODS, markets=MARKETS,
                                 agents=AGENTS, tiles=TILES)
    stocks = StockBook(agents_table(*[0] * AGENTS))
    for _ in range(int(generator.integers(0, 12))):
        stocks.hold(int(generator.integers(0, AGENTS)), int(generator.integers(0, GOODS)), int(generator.integers(0, TILES)), 1.0)
    producers = 4
    market_columns = (generator.integers(0, AREAS, MARKETS).astype(numpy.int64),
                      numpy.where(generator.integers(0, 3, MARKETS) == 0, numpy.nan, generator.integers(1, 9, MARKETS) * 0.25),
                      generator.integers(1, 9, MARKETS) * 0.5,
                      numpy.where(generator.integers(0, 3, MARKETS) == 0, numpy.nan, generator.integers(0, 5, MARKETS) * 0.5))
    ranks = (generator.permutation(AREAS).astype(numpy.int64), generator.permutation(AGENTS).astype(numpy.int64),
             generator.permutation(TILES).astype(numpy.int64))
    producer_figures = (generator.integers(0, 3, producers).astype(numpy.int64), generator.integers(1, 4, producers).astype(numpy.int64),
                        generator.random(producers) * 3.0, generator.random(producers) + 0.5)
    cost_figures = (generator.integers(-1, 2, (3, 5)).astype(numpy.int64), generator.random((producers, 2)) * 4.0 + 0.5,
                    generator.random((producers, 2)), generator.random((producers, 2)) * 4.0 + 0.5)
    arguments = (market_columns, ranks, (generator.integers(0, 5, AGENTS) == 0).astype(numpy.int64),
                 (stocks.stocks.table, stocks.stocks.index), generator.integers(-1, producers, AGENTS).astype(numpy.int64), producer_figures,
                 cost_figures, generator.random((3, 5)) + 0.5, generator.integers(10, 30, TILES) * 0.1, float(generator.integers(0, 3)) * 0.1,
                 generator.integers(1, 9, AREAS) * 0.01, numpy.ones(AREAS, dtype=numpy.bool_), STEPS, 0.25)
    return [bids, offers] + order_tables(4), arguments


def plain_clear_good(tables, good_id, good_column, arguments):
    """The chain as it was: it writes into the bid and offer tables and grows the appended ones as `goods_table_clear.write_batch` did.
    Returns the kernel's ten things and the four appended tables, grown."""
    (market_columns, ranks, is_edge, stock_slots, producer_rows, producer_figures, cost_figures, outputs, band_multiples, spoilage, rates,
     rates_known, steps, minimum_share) = arguments
    bids, offers, bid_order, offer_order, pairs, results = tables
    (market_area, market_price, market_volume, unmet), (area_rank, agent_rank, tile_rank) = market_columns, ranks
    found = good_rows(bids, offers, good_id, market_area, area_rank, is_edge, True)
    (markets, bid_rows, bid_position, offer_rows, offer_position, bid_grouped, bid_ptr, offer_grouped, offer_ptr, flags, offered,
     has_units, funded) = found
    offers.stock_slot[offer_rows] = find_slots(stock_slots[0], stock_slots[1], offers.seller[offer_rows], good_id, offers.tile[offer_rows])
    last_price = market_price[markets]
    batched = bool(flags.any())
    allocated = None
    if batched:
        packed = pack_arrays(bids, offers, offer_rows, offer_position, bid_rows, bid_position, flags, markets, agent_rank, agent_rank,
                             tile_rank, market_price, market_volume, market_area, unmet, rates, rates_known, minimum_share)
        packed = packed[:21]
        (positions, market_ids, sold_rows, pack_offer_ptr, key_of, batch_rows, pack_bid_ptr, floors, flexibles, budgets, references,
         exponents, capped, tier_ptr, tier_values, maximums, size, rate, minimum, has_minimum, has_bids) = packed
        (reservation, quantity, is_producer, unit_cost, share, expected_price, workshops, multiple, sales, band, spoilages, _count,
         _tiles) = decide_inputs(sold_rows, pack_offer_ptr, offers, producer_rows, *producer_figures, cost_figures[0], good_column,
                                 *cost_figures[1:], outputs, band_multiples, spoilage)
        final = decide_markets(has_bids, pack_offer_ptr, reservation, quantity, is_producer, unit_cost, share, expected_price, workshops,
                               multiple, sales, band, key_of, size, rate, spoilages, minimum, has_minimum, pack_bid_ptr, floors, flexibles,
                               budgets, references, exponents, maximums, capped, tier_ptr, tier_values, *steps, numpy.full(len(sold_rows), numpy.nan))
        allocated = final_allocations(pack_offer_ptr, final, offers.quantity[sold_rows], key_of, minimum, has_minimum, pack_bid_ptr, floors,
                                      flexibles, budgets, references, exponents, maximums, capped, tier_ptr, tier_values)
        (traded_flag, requested, traded, mean, supply, ask, sold, left, rank, bid_quantity, bid_cost, pair_ptr, pair_offer, pair_bid,
         pair_quantity) = allocated
        bid_order, offer_order = reserve_rows(bid_order, len(batch_rows)), reserve_rows(offer_order, len(sold_rows))
        pairs, results = reserve_rows(pairs, len(pair_quantity)), reserve_rows(results, len(market_ids))
        write_batch(bids, offers, bid_order, offer_order, pairs, results, market_ids, batch_rows, pack_bid_ptr, sold_rows, pack_offer_ptr,
                    final, (ask, sold, left, rank), (bid_quantity, bid_cost), (traded_flag, requested, traded, mean, supply), pair_ptr,
                    pair_bid, pair_offer, pair_quantity)
        batch_figures = (traded_flag, mean, traded, requested, supply, left, pack_offer_ptr, sold_rows)
    else:
        packed = None
        batch_figures = (numpy.zeros(0, dtype=numpy.bool_), *(numpy.zeros(0),) * 5, numpy.zeros(1, dtype=numpy.int64),
                         numpy.zeros(0, dtype=numpy.int64))
    quotes = untraded_columns(bids, offers, bid_grouped, bid_ptr, offer_grouped, offer_ptr, last_price, minimum_share)
    (lowest_ask, lowest_clamped, quote_supply, quote_funded, best_bid, quote_wanted) = quotes
    clearing = clearing_columns(flags, has_units, last_price, *batch_figures, lowest_ask, lowest_clamped, quote_supply, quote_wanted, best_bid,
                                quote_funded, offer_grouped, offer_ptr, offers.quantity)
    return ((markets, bid_rows, bid_position, offer_rows, offer_position, bid_grouped, bid_ptr, offer_grouped, offer_ptr), flags,
            (offered, has_units, funded), packed, allocated, quotes, clearing, int((clearing[1] == ON_OBJECTS).sum()),
            numpy.diff(bid_ptr), last_price, (bid_order, offer_order, pairs, results))
