"""A good's batched markets read out of the order tables into the arrays of `goods_year_kernel.decide_markets`, in one kernel call
(`goods_table_pack.pack_batch` is the thin Python around it).

The sorts are stable argsorts by the last key first, which orders exactly as `numpy.lexsort` over the same keys does (ties keep
their arrival order). The rate of an area is read from a table filled as areas are first asked (`rate_known`); an area not in it is
reported (`missing_areas`, with its count) so the caller can ask for them and call again."""
import numpy

from sim.jit import njit

from .goods_market_kernels import pack_demand_many
from .goods_table_scales import price_scales
from .stable_order_kernel import stable_order


@njit
def _pointers(slots, markets):
    pointers = numpy.zeros(markets + 1, dtype=numpy.int64)
    for slot in slots:
        pointers[slot + 1] += 1
    for market in range(markets):
        pointers[market + 1] += pointers[market]
    return pointers


@njit
def _sorted_offers(offers, offer_rows, offer_position, slot_of, seller_rank, tile_rank):
    """(offer rows, market slots) of the batched markets' offers with units by (slot, seller name, tile name)."""
    count = 0
    for place in range(len(offer_rows)):
        if slot_of[offer_position[place]] >= 0 and offers.quantity[offer_rows[place]] > 0.0:
            count += 1
    candidates = numpy.empty(count, dtype=numpy.int64)
    slots = numpy.empty(count, dtype=numpy.int64)
    found = 0
    for place in range(len(offer_rows)):
        if slot_of[offer_position[place]] >= 0 and offers.quantity[offer_rows[place]] > 0.0:
            candidates[found] = offer_rows[place]
            slots[found] = slot_of[offer_position[place]]
            found += 1
    order = stable_order((tile_rank[offers.tile[candidates]], seller_rank[offers.seller[candidates]], slots))
    return candidates[order], slots[order]


@njit
def _sorted_bids(bids, bid_rows, bid_position, slot_of, buyer_rank, tile_rank):
    """(bid rows, market slots) of the batched markets' bids by (slot, priority, buyer name, tile name)."""
    count = 0
    for place in range(len(bid_rows)):
        if slot_of[bid_position[place]] >= 0:
            count += 1
    candidates = numpy.empty(count, dtype=numpy.int64)
    slots = numpy.empty(count, dtype=numpy.int64)
    found = 0
    for place in range(len(bid_rows)):
        if slot_of[bid_position[place]] >= 0:
            candidates[found] = bid_rows[place]
            slots[found] = slot_of[bid_position[place]]
            found += 1
    order = stable_order((tile_rank[bids.tile[candidates]], buyer_rank[bids.buyer[candidates]], bids.priority[candidates], slots))
    return candidates[order], slots[order]


@njit
def _key_numbers(offers, offer_rows, offer_slots, offer_ptr):
    """Per offer (in seller-and-tile order): the number of its (seller, tile) within its market, from 0."""
    key_of = numpy.zeros(len(offer_rows), dtype=numpy.int64)
    for place in range(1, len(offer_rows)):
        row, before = offer_rows[place], offer_rows[place - 1]
        if (offer_slots[place] == offer_slots[place - 1] and offers.seller[row] == offers.seller[before]
                and offers.tile[row] == offers.tile[before]):
            key_of[place] = key_of[place - 1]
        elif offer_slots[place] == offer_slots[place - 1]:
            key_of[place] = key_of[place - 1] + 1
    return key_of


@njit
def pack_arrays(bids, offers, offer_rows, offer_position, bid_rows, bid_position, flags, markets, seller_rank, buyer_rank,
                tile_rank, market_price, market_volume, market_area, unmet, rate_of_area, rate_known, minimum_share):
    """(positions, market_ids, offer_rows, offer_ptr, key_of, bid_rows, bid_ptr, floors, flexibles, budgets, references, exponents,
    capped, tier_ptr, tier_values, maximums, size, rate, minimum, has_minimum, has_bids, missing_count, missing_areas) of the batched markets.

    `offer_rows`, `offer_position`, `bid_rows`, `bid_position` and `markets` are a good's rows (`good_rows`), `flags` the markets
    to batch; `market_price`, `market_volume`, `market_area` the goods markets' remembered price, usual volume and area, `unmet` the
    units each market left unmet last year. `missing_areas` flags the areas whose lending rate is not in `rate_of_area` (`rate_known`
    false) that a batched market is in, `missing_count` how many."""
    count = 0
    slot_of = numpy.full(len(flags), -1, dtype=numpy.int64)
    for place in range(len(flags)):
        if flags[place]:
            slot_of[place] = count
            count += 1
    positions = numpy.empty(count, dtype=numpy.int64)
    for place in range(len(flags)):
        if flags[place]:
            positions[slot_of[place]] = place
    market_ids = markets[positions]
    sold_rows, offer_slots = _sorted_offers(offers, offer_rows, offer_position, slot_of, seller_rank, tile_rank)
    batch_rows, bid_slots = _sorted_bids(bids, bid_rows, bid_position, slot_of, buyer_rank, tile_rank)
    offer_ptr, bid_ptr = _pointers(offer_slots, count), _pointers(bid_slots, count)
    key_of = _key_numbers(offers, sold_rows, offer_slots, offer_ptr)
    table = numpy.empty((len(batch_rows), 7))
    for place in range(len(batch_rows)):
        row = batch_rows[place]
        table[place, 0] = bids.floor_quantity[row]
        table[place, 1] = bids.flexible_quantity[row]
        table[place, 2] = bids.reference_price[row]
        table[place, 3] = bids.elasticity[row]
        table[place, 4] = bids.budget[row]
        table[place, 5] = bids.maximum_price[row]
        table[place, 6] = float(bids.priority[row])
    floors, flexibles, budgets, references, exponents, capped, tier_ptr, tier_values = pack_demand_many(table, bid_ptr)
    maximums = table[:, 5].copy()
    size = numpy.empty(count)
    rate = numpy.empty(count)
    last_price = numpy.empty(count)
    missing_areas = numpy.zeros(len(rate_known), dtype=numpy.bool_)
    missing_count = 0
    for slot in range(count):
        market = market_ids[slot]
        last_price[slot] = market_price[market]
        size[slot] = market_volume[market] + (0.0 if numpy.isnan(unmet[market]) else unmet[market])
        area = market_area[market]
        if rate_known[area]:
            rate[slot] = rate_of_area[area]
        else:
            rate[slot] = numpy.nan
            if not missing_areas[area]:
                missing_areas[area] = True
                missing_count += 1
    scale = price_scales(bid_ptr, table[:, 2].copy(), last_price)
    has_minimum = ~numpy.isnan(scale)
    minimum = numpy.where(has_minimum, minimum_share * numpy.where(has_minimum, scale, 0.0), 0.0)
    has_bids = (bid_ptr[1:] - bid_ptr[:-1]) > 0
    return (positions, market_ids, sold_rows, offer_ptr, key_of, batch_rows, bid_ptr, floors, flexibles, budgets, references,
            exponents, capped, tier_ptr, tier_values, maximums, size, rate, minimum, has_minimum, has_bids, missing_count, missing_areas)
