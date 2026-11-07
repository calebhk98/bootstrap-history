"""A good's markets re-priced, searched and cleared together: `clear_markets` packs the offers and bids of the markets that
have both into the arrays of goods_year_kernel.decide_markets (the sellers' costs read from `OfferCosts`, not per offer from
dictionaries), runs the kernel once, and clears each market once with the reservations it returns. The rules are those of
seller_offers.strategic_offers and unsold_search.clear_with_search, which still serve the markets `batchable` leaves out.

A market is batched when it has units on offer, no book edge sells in it (the mint's wash of its own trades) and
its good is portable (ground has a rent to hold for, read off the land record)."""
import math
from operator import attrgetter
from typing import List, Sequence, Tuple

import numpy

from . import goods_market, goods_market_kernels, goods_year_kernel, goods_year_results, price_setting
from .goods_market_demand import _SCHEDULE_FIELDS
from .ask_adjust import ASK_BAND_CEILING
from .market_memory import market_key
from .types import Offer, is_edge

_SELLER_TILE = attrgetter("seller", "tile")


def batchable(setup, bids: Sequence, offers: Sequence[Offer], good: str, arrays) -> bool:
    if good not in arrays.matrices.goods.row:
        return False
    spec = setup.specs.get(good)
    if spec is not None and not spec.portable:
        return False
    units = False
    for offer in offers:
        if offer.quantity > 0.0:
            units = True
            if is_edge(offer.seller):
                return False
    return units


def _band_multiple(setup, tile: str, kept: dict) -> float:
    found = kept.get(tile)
    if found is None:
        elasticity = setup.basket_for(tile).substitution
        found = kept[tile] = min(elasticity / (elasticity - 1.0) if elasticity > 1.0 else ASK_BAND_CEILING, ASK_BAND_CEILING)
    return found


def clear_markets(setup, record, view, arrays, costs, markets: Sequence[tuple]) -> List[Tuple[List[Offer], object]]:
    """For each market (good, area, bids, offers, last price): (the offers after the sellers' re-pricing and the searches,
    the market's clearing with them)."""
    producers, matrices = arrays.producers, arrays.matrices
    row_of = producers.row
    memory = record.memory
    multiples: dict = {}
    buyers_of, order_of = [], []
    res0, qty, prow, grow, key_of, multiple = [], [], [], [], [], []
    offer_ptr, bid_ptr = [0], [0]
    size, rate, spoilage, minimum, has_minimum = [], [], [], [], []
    every_bid: list = []
    for good, area, bids, offers, last_price in markets:
        buyers = goods_market.Buyers(bids, last_price)
        buyers_of.append(buyers)
        order = sorted((index for index, offer in enumerate(offers) if offer.quantity > 0.0),
                       key=lambda index: _SELLER_TILE(offers[index]))
        order_of.append(order)
        good_row = matrices.goods.row[good]
        number, previous = -1, None
        for index in order:
            offer = offers[index]
            identity = _SELLER_TILE(offer)
            if identity != previous:
                number += 1
                previous = identity
            res0.append(offer.reservation_price)
            qty.append(offer.quantity)
            prow.append(row_of.get(offer.seller, -1))
            grow.append(good_row)
            key_of.append(number)
            multiple.append(_band_multiple(setup, offer.tile, multiples))
        offer_ptr.append(len(res0))
        key = market_key(good, area)
        usual = memory.volume_weights.get(key)
        size.append(math.nan if usual is None else usual + record.goods.unmet.get(key, 0.0))
        found = view.interest_rate(view.currency_of(area))
        rate.append(math.nan if found is None else found)
        spec = setup.specs.get(good)
        spoilage.append(spec.spoilage_per_year if spec is not None else 0.0)
        floor = buyers.minimum_price
        minimum.append(0.0 if floor is None else floor)
        has_minimum.append(floor is not None)
        every_bid.extend(buyers.bids)
        bid_ptr.append(len(every_bid))
    bid_pointers = numpy.array(bid_ptr, dtype=numpy.int64)
    table = numpy.array(list(map(_SCHEDULE_FIELDS, every_bid)), dtype=float).reshape(-1, 7)
    demand = goods_market_kernels.pack_demand_many(table, bid_pointers) + (table[:, 5].copy(),)
    final, packed = _decide(setup, arrays, costs, [bool(bids) for _g, _a, bids, _o, _p in markets], res0, qty, prow, grow, key_of, multiple, offer_ptr,
                            bid_pointers, size, rate, spoilage, minimum, has_minimum, demand)
    key_numbers = numpy.array(key_of, dtype=numpy.int64)
    offer_pointers = numpy.array(offer_ptr, dtype=numpy.int64)
    allocated = goods_year_results.final_allocations(
        offer_pointers, final, numpy.array(qty, dtype=float), key_numbers, numpy.array(minimum, dtype=float),
        numpy.array(has_minimum, dtype=bool), *packed)
    batch = goods_year_results.BatchAllocation(
        allocated, offer_pointers, packed[0], [buyers.bids for buyers in buyers_of],
        [[offers[index] for index in order] for (_g, _a, _b, offers, _p), order in zip(markets, order_of)], [])
    traded = allocated[0].tolist()
    final = final.tolist()
    results = []
    for market, (good, area, bids, offers, last_price) in enumerate(markets):
        chosen = list(offers)
        start = offer_ptr[market]
        for position, index in enumerate(order_of[market]):
            offer = offers[index]
            price = final[start + position]
            if price != offer.reservation_price:
                chosen[index] = Offer(offer.seller, offer.good, offer.area, offer.tile, offer.quantity, price)
                batch.offers[market][position] = chosen[index]
        if traded[market]:
            result = goods_year_results.ArrayClearing.of(batch, market, good, area, setup.currency_id)
        else:
            result = goods_market.clear(bids, chosen, good, area, setup.currency_id, last_price, buyers_of[market])
        results.append((chosen, result))
    return results


def _decide(setup, arrays, costs, has_bids, res0, qty, prow, grow, key_of, multiple, offer_ptr, bid_pointers, size, rate, spoilage,
            minimum, has_minimum, demand) -> tuple:
    producers, matrices = arrays.producers, arrays.matrices
    rows = numpy.array(prow, dtype=numpy.int64)
    goods = numpy.array(grow, dtype=numpy.int64)
    is_producer = rows >= 0
    safe = numpy.where(is_producer, rows, 0)
    recipe = producers.recipe_row[safe]
    slot = costs.slot_of[recipe, goods]
    known = is_producer & (slot >= 0)
    place = numpy.where(known, slot, 0)
    cost = numpy.where(known, costs.cost[safe, place], numpy.inf)
    share = numpy.where(known, costs.input_share[safe, place], 0.0)
    expected = numpy.where(known, costs.expected[safe, place], numpy.nan)
    workshops = numpy.where(is_producer, producers.workshops[safe], 1).astype(float)
    expected_sales = numpy.where(
        is_producer, producers.expected_sales[safe] * producers.yield_factor[safe] * matrices.outputs[recipe, goods], 0.0)
    steps = price_setting
    joined = [*demand[:5], demand[8]]
    capped_flags, tier_pointers, tier_values = demand[5], demand[6], demand[7]
    final = goods_year_kernel.decide_markets(
        numpy.array(has_bids, dtype=bool), numpy.array(offer_ptr, dtype=numpy.int64), numpy.array(res0, dtype=float), numpy.array(qty, dtype=float), is_producer,
        cost, share, expected, workshops, is_producer & (workshops > 1.0), expected_sales,
        numpy.array(multiple, dtype=float), numpy.array(key_of, dtype=numpy.int64), numpy.array(size, dtype=float),
        numpy.array(rate, dtype=float), numpy.array(spoilage, dtype=float), numpy.array(minimum, dtype=float),
        numpy.array(has_minimum, dtype=bool), bid_pointers, *joined, capped_flags, tier_pointers, tier_values,
        steps.LOGIT_INTENSITY, math.floor((steps.GRID_END - steps.GRID_START) / steps.GRID_STEP + 1e-9), steps.GRID_START,
        steps.GRID_STEP, steps.MONTHS, steps.MONTHLY_DISCOUNT_RATE)
    return final, (bid_pointers, *joined, capped_flags, tier_pointers, tier_values)
