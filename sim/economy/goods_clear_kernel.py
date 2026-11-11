"""A good's whole clearing chain in one kernel call: its rows cut out of the order tables, the batch packed, the sellers re-priced and
searched, the allocation worked out and written into the tables, then the quote figures of the markets that did not trade and the
columns of `goods_good_clear.GoodClearing`. It calls the kernels the chain used to call one after another (`good_rows`, `find_slots`,
`pack_arrays`, `decide_inputs`, `decide_markets`, `final_allocations`, `write_batch`, `untraded_columns`, `clearing_columns`), so the
sums and sorts are theirs.

Three things the chain asked Python for are asked by raising `NeedsInputs` before any row is written to the tables, and the call is made
again once Python has answered (the offers' stock slots are written first; they come out the same the second time): an area whose lending
rate is not known (`missing_areas`), a tile whose band multiple is not known (`missing_tiles`), and room in the appended tables (`room`:
rows to reserve in the bid order, offer order, pairs and results)."""
import numpy

from sim.book_read_kernels import find_slots
from sim.jit import njit

from .goods_batch_write_kernel import write_batch
from .goods_clearing_kernel import ON_OBJECTS, clearing_columns
from .goods_decide_inputs_kernel import decide_inputs
from .goods_pack_kernel import pack_arrays
from .goods_rows_kernel import good_rows
from .goods_untraded_kernel import untraded_columns
from .goods_year_kernel import decide_markets
from .goods_year_results import final_allocations


class NeedsInputs(Exception):
    """Python has to answer before the chain can run (see the module docstring); what is needed is in the arrays passed for it."""


@njit
def _reservations(offers, packed, held_value, producer_rows, producer_figures, cost_figures, good_column, outputs, band_multiples,
                  spoilage, missing_tiles, steps):
    """The final reservation of each offer of the pack (`goods_table_clear.decide_reservations` without its retry)."""
    (recipe_row, workshops_of_producer, expected_sales_of_producer, yield_factor) = producer_figures
    (slot_of, cost, input_share, expected) = cost_figures
    (reservation, quantity, is_producer, unit_cost, share, expected_price, workshops, multiple_workshops, expected_sales, band, spoilages,
     missing_count, tiles) = decide_inputs(packed[2], packed[3], offers, producer_rows, recipe_row, workshops_of_producer,
                                           expected_sales_of_producer, yield_factor, slot_of, good_column, cost, input_share, expected,
                                           outputs, band_multiples, spoilage)
    if missing_count > 0:
        missing_tiles[:] = tiles
        raise NeedsInputs("tile")
    return decide_markets(
        packed[20], packed[3], reservation, quantity, is_producer, unit_cost, share, expected_price, workshops, multiple_workshops,
        expected_sales, band, packed[4], packed[16], packed[17], spoilages, packed[18], packed[19], packed[6], packed[7], packed[8],
        packed[9], packed[10], packed[11], packed[15], packed[12], packed[13], packed[14], steps[0], steps[1], steps[2], steps[3],
        steps[4], steps[5], held_value), quantity


@njit
def clear_good_columns(tables, good_id, good_column, market_columns, ranks, is_edge, stock_slots, producer_rows, producer_figures,
                       cost_figures, outputs, band_multiples, spoilage, rates, rates_known, steps, minimum_share, missing_areas,
                       missing_tiles, room):
    """(rows, flags, flags_of, pack, allocated, untraded, clearing, on_objects, bid_count, last_price) of the good `good_id`.

    `tables` is (bids, offers, bid_order, offer_order, pairs, results); `market_columns` the goods markets' (area, price, usual
    volume, units unmet); `ranks` (area, agent, tile name ranks); `stock_slots` the book's (stock table, stock index);
    `producer_figures` (recipe row, workshops, expected sales, yield factor per producer), `cost_figures` (slot of a good in a recipe,
    unit cost, input share, expected price per producer and slot); `steps` the price-setting constants. `rows` and the rest are the
    tuples the kernels it calls return: `rows` is `good_rows`' first nine arrays, `flags_of` its offered, has-units and funded
    columns, `pack` `pack_arrays`' first twenty-one, `allocated` `final_allocations`' fifteen, `untraded` and `clearing` those of
    `untraded_columns` and `clearing_columns`. `on_objects` counts the markets the tables do not clear."""
    (bids, offers, bid_order, offer_order, pairs, results) = tables
    (market_area, market_price, market_volume, unmet) = market_columns
    (area_rank, agent_rank, tile_rank) = ranks
    found = good_rows(bids, offers, good_id, market_area, area_rank, is_edge, True)
    (markets, bid_rows, bid_position, offer_rows, offer_position, bid_grouped, bid_ptr, offer_grouped, offer_ptr, flags, offered,
     has_units, funded) = found
    slots = find_slots(stock_slots[0], stock_slots[1], offers.seller[offer_rows], good_id, offers.tile[offer_rows])
    for place in range(len(offer_rows)):
        offers.stock_slot[offer_rows[place]] = slots[place]
    packed = pack_arrays(bids, offers, offer_rows, offer_position, bid_rows, bid_position, flags, markets, agent_rank, agent_rank,
                         tile_rank, market_price, market_volume, market_area, unmet, rates, rates_known, minimum_share)
    if packed[21] > 0:
        missing_areas[:] = packed[22]
        raise NeedsInputs("area")
    held_value = numpy.full(len(packed[2]), numpy.nan)
    final, quantity = _reservations(offers, packed, held_value, producer_rows, producer_figures, cost_figures, good_column, outputs,
                                    band_multiples, spoilage, missing_tiles, steps)
    allocated = final_allocations(packed[3], final, quantity, packed[4], packed[18], packed[19], packed[6], packed[7], packed[8],
                                  packed[9], packed[10], packed[11], packed[15], packed[12], packed[13], packed[14])
    (traded_flag, requested, traded, mean, supply, ask, sold, left, rank, bid_quantity, bid_cost, pair_ptr, pair_offer, pair_bid,
     pair_quantity) = allocated
    pair_count = len(pair_quantity)
    if (bid_order.row_count[0] + len(packed[5]) > bid_order.capacity[0] or offer_order.row_count[0] + len(packed[2]) > offer_order.capacity[0]
            or pairs.row_count[0] + pair_count > pairs.capacity[0] or results.row_count[0] + len(packed[1]) > results.capacity[0]):
        room[0], room[1], room[2], room[3] = len(packed[5]), len(packed[2]), pair_count, len(packed[1])
        raise NeedsInputs("room")
    write_batch(bids, offers, bid_order, offer_order, pairs, results, packed[1], packed[5], packed[6], packed[2], packed[3], final,
                (ask, sold, left, rank), (bid_quantity, bid_cost), (traded_flag, requested, traded, mean, supply), pair_ptr, pair_bid,
                pair_offer, pair_quantity)
    last_price = market_price[markets]
    quotes = untraded_columns(bids, offers, bid_grouped, bid_ptr, offer_grouped, offer_ptr, last_price, minimum_share)
    (lowest_ask, lowest_clamped, quote_supply, quote_funded, best_bid, quote_wanted) = quotes
    clearing = clearing_columns(flags, has_units, last_price, traded_flag, mean, traded, requested, supply, left, packed[3], packed[2],
                                lowest_ask, lowest_clamped, quote_supply, quote_wanted, best_bid, quote_funded, offer_grouped,
                                offer_ptr, offers.quantity)
    on_objects = 0
    for way in clearing[1]:
        if way == ON_OBJECTS:
            on_objects += 1
    return ((markets, bid_rows, bid_position, offer_rows, offer_position, bid_grouped, bid_ptr, offer_grouped, offer_ptr), flags,
            (offered, has_units, funded), packed[:21], allocated, quotes, clearing, on_objects, bid_ptr[1:] - bid_ptr[:-1], last_price)
