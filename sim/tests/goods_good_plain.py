"""The numpy chains the per-good kernels (`goods_rows_kernel`, `goods_pack_kernel`, `goods_decide_inputs_kernel`,
`goods_batch_write_kernel`, `goods_clearing_kernel`) replaced, written over the same columns, so the kernels are tested against them;
and seeded random order tables with many ties."""
import numpy

from sim.compiled_tables.growth import reserve_rows
from sim.economy.goods_market_kernels import pack_demand_many
from sim.economy.goods_order_tables import (BID_ORDER, GOODS_BIDS, GOODS_MARKET_RESULTS, GOODS_OFFERS, GOODS_PAIRS, OFFER_ORDER, BidOrder,
                                            GoodsBids, GoodsMarketResults, GoodsOffers, GoodsPairs, OfferOrder)
from sim.economy.goods_table_scales import price_scales


def random_tables(generator, bid_count, offer_count, goods=3, markets=6, agents=5, tiles=4):
    """(bids, offers) tables of random rows: ids from small ranges so keys tie, a quarter of the offers without units."""
    bids = GOODS_BIDS.new_table(GoodsBids, bid_count + 3)
    offers = GOODS_OFFERS.new_table(GoodsOffers, offer_count + 3)
    for table, count in ((bids, bid_count), (offers, offer_count)):
        table.good[:count] = generator.integers(0, goods, count)
        table.market[:count] = generator.integers(0, markets, count)
        table.tile[:count] = generator.integers(0, tiles, count)
        table.row_count[0] = count
    bids.buyer[:bid_count] = generator.integers(0, agents, bid_count)
    bids.priority[:bid_count] = generator.integers(0, 3, bid_count)
    for name in ("floor_quantity", "flexible_quantity", "reference_price", "elasticity"):
        getattr(bids, name)[:bid_count] = generator.integers(0, 4, bid_count) * 0.5
    bids.budget[:bid_count] = generator.integers(0, 3, bid_count) * 7.0
    bids.maximum_price[:bid_count] = numpy.where(generator.integers(0, 3, bid_count) == 0, 9.0, numpy.inf)
    offers.seller[:offer_count] = generator.integers(0, agents, offer_count)
    offers.quantity[:offer_count] = generator.integers(0, 4, offer_count) * 1.5
    offers.reservation_price[:offer_count] = generator.integers(1, 5, offer_count) * 0.75
    return bids, offers


def plain_good_rows(bids, offers, good_id, market_area, area_rank, is_edge, batchable):
    """`goods_table_group.rows_of_good`, `batch_flags` and `goods_good_clear.flags_by_market` as they were."""
    bid_rows = numpy.flatnonzero(bids.good[:int(bids.row_count[0])] == good_id)
    offer_rows = numpy.flatnonzero(offers.good[:int(offers.row_count[0])] == good_id)
    bid_markets, offer_markets = bids.market[bid_rows], offers.market[offer_rows]
    distinct = numpy.unique(numpy.concatenate((bid_markets, offer_markets)))
    by_area = numpy.argsort(area_rank[market_area[distinct]], kind="stable")
    place_of = numpy.empty(len(distinct), dtype=numpy.int64)
    place_of[by_area] = numpy.arange(len(distinct), dtype=numpy.int64)
    bid_position = place_of[numpy.searchsorted(distinct, bid_markets)]
    offer_position = place_of[numpy.searchsorted(distinct, offer_markets)]
    bid_grouped, bid_ptr = grouped(bid_rows, bid_position, len(distinct))
    offer_grouped, offer_ptr = grouped(offer_rows, offer_position, len(distinct))
    count = len(distinct)
    has_units = offers.quantity[offer_rows] > 0.0
    edge = has_units & (is_edge[offers.seller[offer_rows]] != 0)
    units = numpy.bincount(offer_position, weights=has_units, minlength=count)
    edge_units = numpy.bincount(offer_position, weights=edge, minlength=count)
    flags = (units > 0) & (edge_units == 0) if batchable else numpy.zeros(count, dtype=bool)
    offered = numpy.bincount(offer_position, minlength=count) > 0
    funded = numpy.bincount(bid_position, weights=bids.budget[bid_rows] > 0.0, minlength=count) > 0
    return (distinct[by_area], bid_rows, bid_position, offer_rows, offer_position, bid_grouped, bid_ptr, offer_grouped, offer_ptr,
            flags, offered, units > 0, funded)


def grouped(rows, position, groups):
    order = numpy.argsort(position, kind="stable")
    pointers = numpy.concatenate(([0], numpy.cumsum(numpy.bincount(position, minlength=groups)))).astype(numpy.int64)
    return rows[order], pointers


def _slot_of_position(flags):
    return numpy.where(flags, numpy.cumsum(flags) - 1, -1)


def _pointers(slots, markets):
    return numpy.concatenate(([0], numpy.cumsum(numpy.bincount(slots, minlength=markets)))).astype(numpy.int64)


def plain_pack(bids, offers, offer_rows, offer_position, bid_rows, bid_position, flags, markets, seller_rank, buyer_rank, tile_rank,
               market_price, market_volume, market_area, unmet, rate_of_area, minimum_share):
    """`goods_table_pack.pack_batch` as it was (rates read from a complete table), without the BatchPack wrapper."""
    count = int(flags.sum())
    slot_of = _slot_of_position(flags)
    chosen = flags[offer_position] & (offers.quantity[offer_rows] > 0.0)
    candidates, slots = offer_rows[chosen], slot_of[offer_position[chosen]]
    order = numpy.lexsort((tile_rank[offers.tile[candidates]], seller_rank[offers.seller[candidates]], slots))
    sold_rows, offer_slots = candidates[order], slots[order]
    chosen = flags[bid_position]
    candidates, slots = bid_rows[chosen], slot_of[bid_position[chosen]]
    order = numpy.lexsort((tile_rank[bids.tile[candidates]], buyer_rank[bids.buyer[candidates]], bids.priority[candidates], slots))
    batch_rows, bid_slots = candidates[order], slots[order]
    offer_ptr, bid_ptr = _pointers(offer_slots, count), _pointers(bid_slots, count)
    positions = numpy.flatnonzero(flags)
    market_ids = markets[positions]
    table = numpy.column_stack((bids.floor_quantity[batch_rows], bids.flexible_quantity[batch_rows], bids.reference_price[batch_rows],
                                bids.elasticity[batch_rows], bids.budget[batch_rows], bids.maximum_price[batch_rows],
                                bids.priority[batch_rows].astype(numpy.float64)))
    demand = pack_demand_many(table, bid_ptr) + (table[:, 5].copy(),)
    last_price = market_price[market_ids]
    size = market_volume[market_ids] + numpy.where(numpy.isnan(unmet[market_ids]), 0.0, unmet[market_ids])
    rate = rate_of_area[market_area[market_ids]]
    scale = price_scales(bid_ptr, bids.reference_price[batch_rows], last_price)
    has_minimum = ~numpy.isnan(scale)
    minimum = numpy.where(has_minimum, minimum_share * numpy.where(has_minimum, scale, 0.0), 0.0)
    key_of = numpy.zeros(0, dtype=numpy.int64)
    if len(sold_rows):
        seller, tile = offers.seller[sold_rows], offers.tile[sold_rows]
        new = numpy.ones(len(sold_rows), dtype=bool)
        new[1:] = (seller[1:] != seller[:-1]) | (tile[1:] != tile[:-1]) | (offer_slots[1:] != offer_slots[:-1])
        running = numpy.cumsum(new) - 1
        key_of = running - running[offer_ptr[offer_slots]]
    return (positions, market_ids, sold_rows, offer_ptr, key_of, batch_rows, bid_ptr) + demand + (
        size, rate, minimum, has_minimum, numpy.diff(bid_ptr) > 0)


def plain_decide_inputs(offers, offer_rows, producer_row_of_agent, recipe_row, workshops_of_producer, expected_sales_of_producer,
                        yield_factor, slot_of, good_column, cost, input_share, expected, outputs, band_multiple_of_tile, markets,
                        spoilage):
    """`goods_table_clear.decide_reservations`' argument building as it was."""
    rows = producer_row_of_agent[offers.seller[offer_rows]]
    goods = numpy.full(len(rows), good_column, dtype=numpy.int64)
    is_producer = rows >= 0
    safe = numpy.where(is_producer, rows, 0)
    recipe = recipe_row[safe]
    slot = slot_of[recipe, goods]
    known = is_producer & (slot >= 0)
    place = numpy.where(known, slot, 0)
    workshops = numpy.where(is_producer, workshops_of_producer[safe], 1).astype(float)
    expected_sales = numpy.where(is_producer, expected_sales_of_producer[safe] * yield_factor[safe] * outputs[recipe, goods], 0.0)
    return (offers.reservation_price[offer_rows], offers.quantity[offer_rows], is_producer,
            numpy.where(known, cost[safe, place], numpy.inf), numpy.where(known, input_share[safe, place], 0.0),
            numpy.where(known, expected[safe, place], numpy.nan), workshops, is_producer & (workshops > 1.0), expected_sales,
            band_multiple_of_tile[offers.tile[offer_rows]], numpy.full(len(markets), spoilage))


def plain_clearing_columns(flags, has_units, last_price, batch, pack_offer_ptr, pack_offer_rows, untraded, offer_grouped, offer_ptr,
                           offer_quantity):
    """`GoodClearing.__init__` and `_count_left`'s columns as they were. `batch` and `untraded` are dicts of arrays or None."""
    count = len(flags)
    slots = numpy.where(flags, numpy.cumsum(flags) - 1, -1)
    traded = numpy.zeros(count, dtype=numpy.bool_)
    batched = slots >= 0
    if batch is not None:
        traded[batched] = batch["traded_flag"][slots[batched]]
    way = numpy.where(traded, 0, numpy.where(batched | ~has_units, 1, 2)).astype(numpy.int64)
    quantity, price, demand = numpy.zeros(count), numpy.full(count, numpy.nan), numpy.zeros(count)
    offered, wanted = numpy.zeros(count), numpy.zeros(count)
    quote_price, quote_kind = numpy.full(count, numpy.nan), numpy.zeros(count, dtype=numpy.int64)
    by_batch, by_quote = way == 0, way == 1
    if by_batch.any():
        at = slots[by_batch]
        price[by_batch], quantity[by_batch] = batch["mean"][at], batch["traded"][at]
        demand[by_batch], offered[by_batch] = batch["requested"][at], batch["supply"][at]
        wanted[by_batch] = demand[by_batch]
    if by_quote.any():
        keeps_last = numpy.isnan(untraded["lowest_clamped"]) | (~numpy.isnan(last_price) & (untraded["lowest_clamped"] <= last_price))
        price[by_quote] = numpy.where(keeps_last, last_price, untraded["lowest_clamped"])[by_quote]
        offered[by_quote], wanted[by_quote] = untraded["supply"][by_quote], untraded["wanted"][by_quote]
        no_ask, has_bid = numpy.isnan(untraded["lowest_ask"]), ~numpy.isnan(untraded["best_bid"])
        bid_quote = has_bid & (no_ask | (untraded["best_bid"] < untraded["lowest_ask"]))
        ask_quote = ~bid_quote & ~no_ask & ~untraded["funded"]
        quote_price[by_quote] = numpy.where(bid_quote, untraded["best_bid"], numpy.where(ask_quote, untraded["lowest_ask"], numpy.nan))[by_quote]
        quote_kind[by_quote] = numpy.where(bid_quote, 1, numpy.where(ask_quote, 2, 0))[by_quote]
    left_grouped, left_ptr = numpy.zeros(0, dtype=numpy.int64), numpy.zeros(count + 1, dtype=numpy.int64)
    if by_batch.any() or by_quote.any():
        places, found = [], []
        if by_batch.any():
            slot_of_place = numpy.full(len(pack_offer_ptr) - 1, -1, dtype=numpy.int64)
            slot_of_place[slots[by_batch]] = numpy.flatnonzero(by_batch)
            place_of_offer = slot_of_place[numpy.repeat(numpy.arange(len(pack_offer_ptr) - 1), numpy.diff(pack_offer_ptr))]
            kept = (batch["left"] > 0.0) & (place_of_offer >= 0)
            places.append(place_of_offer[kept])
            found.append(pack_offer_rows[kept])
        if by_quote.any():
            place_of_row = numpy.repeat(numpy.arange(count), numpy.diff(offer_ptr))
            kept = by_quote[place_of_row] & (offer_quantity[offer_grouped] > 0.0)
            places.append(place_of_row[kept])
            found.append(offer_grouped[kept])
        place, rows = numpy.concatenate(places), numpy.concatenate(found)
        order = numpy.argsort(place, kind="stable")
        left_grouped = rows[order]
        left_ptr = numpy.concatenate(([0], numpy.cumsum(numpy.bincount(place, minlength=count)))).astype(numpy.int64)
    return (slots, way, quantity, price, demand, offered, wanted, quote_price, quote_kind, left_grouped, left_ptr, numpy.diff(left_ptr))


def plain_write_batch(bids, offers, bid_order, offer_order, pairs, results, market_ids, bid_rows, bid_ptr, offer_rows, offer_ptr, final,
                      allocated_offers, allocated_bids, allocated_markets, pair_ptr, pair_bid, pair_offer, pair_quantity):
    """`goods_table_clear.write_offers`, `write_bids` and `record_batch` as they were: the tables appended to, returned."""
    ask, sold, left, rank = allocated_offers
    offers.reservation_price[offer_rows] = final
    offers.ask[offer_rows], offers.quantity_sold[offer_rows], offers.quantity_left[offer_rows], offers.rank[offer_rows] = ask, sold, left, rank
    bids.quantity_bought[bid_rows], bids.cost[bid_rows] = allocated_bids
    bids.position[bid_rows] = numpy.arange(len(bid_rows)) - numpy.repeat(bid_ptr[:-1], numpy.diff(bid_ptr))
    traded_flag, requested, traded, mean, supply = allocated_markets
    tables = []
    for table, columns in ((bid_order, {"bid_row": bid_rows}), (offer_order, {"offer_row": offer_rows}),
                           (pairs, {"bid_row": bid_rows[pair_bid], "offer_row": offer_rows[pair_offer], "quantity": pair_quantity})):
        count = len(next(iter(columns.values())))
        table = reserve_rows(table, count)
        first = int(table.row_count[0])
        for column, values in columns.items():
            getattr(table, column)[first:first + count] = values
        table.row_count[0] = first + count
        tables.append((table, first))
    (bid_order, first_bid), (offer_order, first_offer), (pairs, first_pair) = tables
    columns = dict(market=market_ids, traded=traded_flag, quantity=traded, price=mean, demand_at_price=requested, offered_at_price=supply,
                   first_bid_slot=first_bid + bid_ptr[:-1], bid_count=numpy.diff(bid_ptr), first_offer_slot=first_offer + offer_ptr[:-1],
                   offer_count=numpy.diff(offer_ptr), first_pair=first_pair + pair_ptr[:-1], pair_count=numpy.diff(pair_ptr))
    results = reserve_rows(results, len(market_ids))
    first = int(results.row_count[0])
    for column, values in columns.items():
        getattr(results, column)[first:first + len(market_ids)] = values
    results.row_count[0] = first + len(market_ids)
    return bid_order, offer_order, pairs, results
