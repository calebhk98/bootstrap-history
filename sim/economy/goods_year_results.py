"""The final allocation of a good's batched markets as arrays, and the clearing results built on them.

`final_allocations` clears every market of the batch once at the reservations `goods_year_kernel.decide_markets` chose, with the
rules of `goods_market.clear` (asks cheapest first with the token minimum, the logit rounds of `goods_market_kernels.allocate_arrays`),
and returns what each reader needs as arrays cut by market: per market the units traded, the first round's requests, the supply
and the mean price; per offer its ask and units sold (and units left, by `goods_respend.offers_left`'s rule); per bid its quantity
and cost; per pair (bid, offer, quantity), in the order the old `Pairing` listed them. A market whose book does not trade is
flagged and cleared by `goods_market.clear` (it has a quote to build).

`ArrayClearing` is a `ClearingResult` whose `fills` and `pairing` are built when first read.
"""
from itertools import chain
from typing import List

import numpy

from sim.book import ROUNDING_SHARE
from sim.jit import njit

from . import goods_market_kernels as kernels
from .goods_market_fills import make_fill, sold_by_seller_tile
from .types import ClearingResult, Offer, Pairing, is_edge

KERNEL = {"error_model": "numpy"}


@njit(**KERNEL)
def final_allocations(offer_ptr, reservation, quantity, keys, minimum, has_minimum, bid_ptr, floors, flexibles, budgets,
                      references, exponents, maximums, capped, tier_ptr, tier_values):
    """Per market (offers `offer_ptr[m]:offer_ptr[m + 1]` in seller-and-tile order, bids cut by `bid_ptr`, tier starts by
    `tier_ptr`): returns
      market:  traded flag, units requested in round one, units traded, mean price, supply;
      offer:   ask, units sold, units left unsold under `offers_left`'s rule, position in clearing order;
      bid:     quantity bought, cost;
      pairs:   pair_ptr by market, then per pair the offer (index in the arrays), the bid (index in the arrays), the quantity."""
    markets = len(offer_ptr) - 1
    offers_total, bids_total = offer_ptr[markets], bid_ptr[markets]
    traded_flag = numpy.zeros(markets, dtype=numpy.bool_)
    requested = numpy.zeros(markets)
    traded = numpy.zeros(markets)
    mean = numpy.zeros(markets)
    supply = numpy.zeros(markets)
    ask_of = numpy.zeros(offers_total)
    sold_of = numpy.zeros(offers_total)
    left_of = numpy.zeros(offers_total)
    rank_of = numpy.zeros(offers_total, dtype=numpy.int64)
    bid_quantity = numpy.zeros(bids_total)
    bid_cost = numpy.zeros(bids_total)
    pair_ptr = numpy.zeros(markets + 1, dtype=numpy.int64)
    capacity = 4 * (offers_total + bids_total) + 16
    pair_offer = numpy.zeros(capacity, dtype=numpy.int64)
    pair_bid = numpy.zeros(capacity, dtype=numpy.int64)
    pair_quantity = numpy.zeros(capacity)
    pairs = 0
    for market in range(markets):
        o0, o1 = offer_ptr[market], offer_ptr[market + 1]
        b0, b1 = bid_ptr[market], bid_ptr[market + 1]
        count = o1 - o0
        pair_ptr[market] = pairs
        for index in range(count):
            left_of[o0 + index] = quantity[o0 + index]
        if count == 0:
            continue
        order = numpy.argsort(reservation[o0:o1], kind="mergesort")
        asks = numpy.zeros(count)
        quantities = numpy.zeros(count)
        total = 0.0
        for position in range(count):
            ask = reservation[o0 + order[position]]
            if has_minimum[market] and ask < minimum[market]:
                ask = minimum[market]
            asks[position] = ask
            quantities[position] = quantity[o0 + order[position]]
            total += quantities[position]
        supply[market] = total
        market_floors, market_flexibles, market_budgets = floors[b0:b1], flexibles[b0:b1], budgets[b0:b1]
        market_references, market_exponents, market_maximums = references[b0:b1], exponents[b0:b1], maximums[b0:b1]
        wanted = kernels.total_wanted(asks[0], market_floors, market_flexibles, market_budgets, market_references,
                                      market_exponents, market_maximums, capped[market])
        if not (wanted > 0.0 and total > ROUNDING_SHARE * wanted):
            continue
        taken, cost, sold_ordered, round_one, flow = kernels.allocate_arrays(
            asks, quantities, market_floors, market_flexibles, market_budgets, market_references, market_exponents,
            market_maximums, capped[market], tier_values[tier_ptr[market]:tier_ptr[market + 1]])
        moved = 0.0
        value = 0.0
        for position in range(count):
            if sold_ordered[position] > 0.0:
                moved += sold_ordered[position]
                value += sold_ordered[position] * asks[position]
        if not moved > 0.0:
            continue
        traded_flag[market] = True
        requested[market] = round_one
        traded[market] = moved
        mean[market] = value / moved
        for position in range(count):
            offer = o0 + order[position]
            ask_of[offer] = asks[position]
            sold_of[offer] = sold_ordered[position]
            rank_of[offer] = position
        for bid in range(b1 - b0):
            bid_quantity[b0 + bid] = taken[bid]
            bid_cost[b0 + bid] = cost[bid]
        for position in range(count):
            for bid in range(b1 - b0):
                if flow[position, bid] > 0.0:
                    if pairs == len(pair_quantity):
                        pair_offer = numpy.concatenate((pair_offer, numpy.zeros(len(pair_offer), dtype=numpy.int64)))
                        pair_bid = numpy.concatenate((pair_bid, numpy.zeros(len(pair_bid), dtype=numpy.int64)))
                        pair_quantity = numpy.concatenate((pair_quantity, numpy.zeros(len(pair_quantity))))
                    pair_offer[pairs] = o0 + order[position]
                    pair_bid[pairs] = b0 + bid
                    pair_quantity[pairs] = flow[position, bid]
                    pairs += 1
        # what offers_left leaves: each (seller, tile) key's units sold are taken off its offers in turn
        key_count = keys[o1 - 1] + 1
        key_sold = numpy.zeros(key_count)
        for index in range(count):
            key_sold[keys[o0 + index]] += sold_of[o0 + index]
        for index in range(count):
            key = keys[o0 + index]
            taken_here = min(quantity[o0 + index], key_sold[key])
            key_sold[key] -= taken_here
            left_of[o0 + index] = quantity[o0 + index] - taken_here
    pair_ptr[markets] = pairs
    return (traded_flag, requested, traded, mean, supply, ask_of, sold_of, left_of, rank_of, bid_quantity, bid_cost, pair_ptr,
            pair_offer[:pairs].copy(), pair_bid[:pairs].copy(), pair_quantity[:pairs].copy())


class BatchAllocation:
    """The arrays `final_allocations` returned for a good's batch, with the bids and offers they index: `bids[m]` the market's
    bids in clearing order (`Buyers.bids`), `offers[m]` its offers with units, in seller-and-tile order (the order of the arrays)."""

    FIELDS = ("traded_flag", "requested", "traded", "mean", "supply", "ask", "sold", "left", "rank", "bid_quantity",
              "bid_cost", "pair_ptr", "pair_offer", "pair_bid", "pair_quantity")

    def __init__(self, arrays, offer_ptr, bid_ptr, bids: List[list], offers: List[list], good_of: List[str]):
        for name, values in zip(self.FIELDS, arrays):
            setattr(self, name, values)
        self.offer_ptr, self.bid_ptr = offer_ptr, bid_ptr
        self.bids, self.offers = bids, offers
        self.good_of = good_of
        self._flat_bids = self._flat_offers = None

    @property
    def flat_bids(self) -> list:
        """The bids of all markets, one after another (the order of the bid arrays)."""
        if self._flat_bids is None:
            self._flat_bids = list(chain.from_iterable(self.bids))
        return self._flat_bids

    @property
    def flat_offers(self) -> list:
        """The offers of all markets, one after another (the order of the offer arrays)."""
        if self._flat_offers is None:
            self._flat_offers = list(chain.from_iterable(self.offers))
        return self._flat_offers


class ArrayClearing(ClearingResult):
    """A clearing result that traded, held as slices of a `BatchAllocation`: `fills` and `pairing` are built on first read."""

    @classmethod
    def of(cls, batch: BatchAllocation, market: int, good: str, area: str, currency: str) -> "ArrayClearing":
        result = object.__new__(cls)
        values = result.__dict__
        values["good"], values["area"], values["currency"] = good, area, currency
        values["price"] = float(batch.mean[market])
        values["quantity"] = float(batch.traded[market])
        values["demand_at_price"] = float(batch.requested[market])
        values["offered_at_price"] = float(batch.supply[market])
        values["quote"] = None
        values["batch"], values["market"] = batch, market
        return result

    def _clearing_order(self):
        batch, market = self.batch, self.market
        first, last = batch.offer_ptr[market], batch.offer_ptr[market + 1]
        return first, sorted(range(last - first), key=lambda index: batch.rank[first + index])

    @property
    def fills(self):
        cached = self.__dict__.get("_fills")
        if cached is None:
            batch, market = self.batch, self.market
            first_bid = batch.bid_ptr[market]
            fills = []
            for index, bid in enumerate(batch.bids[market]):
                quantity = batch.bid_quantity[first_bid + index]
                if quantity > 0.0:
                    fills.append(make_fill(bid.buyer, self.good, self.area, bid.tile, float(quantity),
                                           float(batch.bid_cost[first_bid + index] / quantity), "buy"))
            first, order = self._clearing_order()
            for index in order:
                sold = batch.sold[first + index]
                if sold > 0.0:
                    offer = batch.offers[market][index]
                    fills.append(make_fill(offer.seller, self.good, self.area, offer.tile, float(sold),
                                           float(batch.ask[first + index]), "sell"))
            cached = self.__dict__["_fills"] = tuple(fills)
        return cached

    @property
    def pairing(self) -> Pairing:
        cached = self.__dict__.get("_pairing")
        if cached is None:
            batch, market = self.batch, self.market
            first, order = self._clearing_order()
            position = {index: place for place, index in enumerate(order)}
            offers = batch.offers[market]
            pairs = slice(batch.pair_ptr[market], batch.pair_ptr[market + 1])
            first_bid = batch.bid_ptr[market]
            cached = self.__dict__["_pairing"] = Pairing(
                tuple((bid.buyer, bid.tile) for bid in batch.bids[market]),
                tuple((offers[index].seller, offers[index].tile) for index in order),
                tuple(float(batch.ask[first + index]) for index in order),
                tuple((batch.pair_bid[pairs] - first_bid).tolist()),
                tuple(position[index] for index in (batch.pair_offer[pairs] - first).tolist()),
                tuple(batch.pair_quantity[pairs].tolist()))
        return cached

    def sold_by_key(self) -> dict:
        """(seller, tile) -> units sold, as the sell fills add up."""
        batch, market = self.batch, self.market
        first = batch.offer_ptr[market]
        sold: dict = {}
        for index, offer in enumerate(batch.offers[market]):
            quantity = batch.sold[first + index]
            if quantity > 0.0:
                key = (offer.seller, offer.tile)
                sold[key] = sold.get(key, 0.0) + float(quantity)
        return sold

    def offers_left(self) -> List[Offer]:
        """The offers (units to sell, in seller-and-tile order) with what sold taken off; none left, none listed."""
        batch, market = self.batch, self.market
        first = batch.offer_ptr[market]
        left = []
        for offer, remaining in zip(batch.offers[market], batch.left[first:first + len(batch.offers[market])].tolist()):
            if remaining > 0.0:
                left.append(offer if remaining == offer.quantity else
                            Offer(offer.seller, offer.good, offer.area, offer.tile, remaining, offer.reservation_price))
        return left

    def bought_by(self, watchers) -> dict:
        """The buy fills of the bids whose buyer is in `watchers`, by buyer, in bid order."""
        batch, market = self.batch, self.market
        first_bid = batch.bid_ptr[market]
        found: dict = {}
        for index, bid in enumerate(batch.bids[market]):
            if bid.buyer in watchers:
                quantity = batch.bid_quantity[first_bid + index]
                if quantity > 0.0:
                    found.setdefault(bid.buyer, []).append(
                        make_fill(bid.buyer, self.good, self.area, bid.tile, float(quantity),
                                  float(batch.bid_cost[first_bid + index] / quantity), "buy"))
        return found

    def taken_by(self, buyer: str) -> List[tuple]:
        """(seller, tile, quantity, ask) of each pair `buyer` bought, in pair order."""
        batch, market = self.batch, self.market
        first, first_bid = batch.offer_ptr[market], batch.bid_ptr[market]
        pairs = slice(batch.pair_ptr[market], batch.pair_ptr[market + 1])
        bids, offers = batch.bids[market], batch.offers[market]
        found = []
        for bid_at, offer_at, quantity in zip((batch.pair_bid[pairs] - first_bid).tolist(),
                                              (batch.pair_offer[pairs] - first).tolist(), batch.pair_quantity[pairs].tolist()):
            if bids[bid_at].buyer == buyer:
                offer = offers[offer_at]
                found.append((offer.seller, offer.tile, quantity, float(batch.ask[first + offer_at])))
        return found

    def sold_by_producers(self) -> float:
        """Units the non-edge sellers sold."""
        batch, market = self.batch, self.market
        first = batch.offer_ptr[market]
        return float(sum(batch.sold[first + index] for index, offer in enumerate(batch.offers[market])
                         if batch.sold[first + index] > 0.0 and not is_edge(offer.seller)))


def sold_by_result(result) -> dict:
    """(seller, tile) -> units the result's sellers sold, read from the arrays where the result holds them."""
    return result.sold_by_key() if isinstance(result, ArrayClearing) else sold_by_seller_tile(result.fills)
