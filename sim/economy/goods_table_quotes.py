"""Markets that did not trade, read off the order tables: what `goods_market.clear` and `market_quote.no_trade_quote` give such a
market from its `Bid` and `Offer` lists, from the columns of its rows.

A market that did not trade has a quote instead of a price (market_quote.py): the best unfilled bid when buyers bid but every ask
was above it, the lowest unfilled ask when nobody bid. `untraded_figures` finds, for each market of a good, the figures the
quote and the result are made of; `untraded_result` builds the `ClearingResult`; `wanted_by_market` is what the buyers asked
for at the price the quote names (`entry.wanted_in_round`)."""
import numpy

from sim.jit import njit

from .types import (QUOTE_BEST_UNFILLED_BID, QUOTE_LOWEST_UNFILLED_ASK, ClearingResult, Quote)


@njit
def untraded_figures(bid_ptr, offer_ptr, budget, maximum_price, reservation, quantity, minimum, has_minimum):
    """Per market (its bids `bid_ptr[m]:bid_ptr[m + 1]` and offers `offer_ptr[m]:offer_ptr[m + 1]` of the given columns): the
    lowest positive reservation of an offer with units (NaN: none), the lowest ask once raised to the token minimum, the units on
    offer (added left to right), whether some bid has a budget, and the highest finite ceiling of a bid with a budget (NaN: none)."""
    markets = len(bid_ptr) - 1
    lowest_ask = numpy.full(markets, numpy.nan)
    lowest_clamped = numpy.full(markets, numpy.nan)
    supply = numpy.zeros(markets)
    funded = numpy.zeros(markets, dtype=numpy.bool_)
    best_bid = numpy.full(markets, numpy.nan)
    for market in range(markets):
        for offer in range(offer_ptr[market], offer_ptr[market + 1]):
            if quantity[offer] > 0.0:
                supply[market] += quantity[offer]
                asked = max(reservation[offer], minimum[market]) if has_minimum[market] else reservation[offer]
                if not asked >= lowest_clamped[market]:
                    lowest_clamped[market] = asked
                if reservation[offer] > 0.0 and not reservation[offer] >= lowest_ask[market]:
                    lowest_ask[market] = reservation[offer]
        for bid in range(bid_ptr[market], bid_ptr[market + 1]):
            if budget[bid] > 0.0:
                funded[market] = True
                if numpy.isfinite(maximum_price[bid]) and maximum_price[bid] > 0.0 and not maximum_price[bid] <= best_bid[market]:
                    best_bid[market] = maximum_price[bid]
    return lowest_ask, lowest_clamped, supply, funded, best_bid


@njit
def wanted_by_market(bid_ptr, price, floor_quantity, flexible_quantity, reference_price, elasticity, budget, maximum_price):
    """Per market, the units its bids ask for at the market's price (`goods_market.quantity_at` of each, added left to right);
    zero where the price is NaN."""
    markets = len(bid_ptr) - 1
    wanted = numpy.zeros(markets)
    for market in range(markets):
        if numpy.isnan(price[market]):
            continue
        for bid in range(bid_ptr[market], bid_ptr[market + 1]):
            if budget[bid] <= 0.0 or price[market] > maximum_price[bid]:
                continue
            units = floor_quantity[bid]
            if flexible_quantity[bid] > 0.0 and reference_price[bid] > 0.0:
                units += flexible_quantity[bid] * (price[market] / reference_price[bid]) ** -elasticity[bid]
            wanted[market] += min(units, budget[bid] / price[market])
    return wanted


def quote_of(lowest_ask: float, best_bid: float, funded: bool):
    """`market_quote.no_trade_quote` from the three figures (no cost to quote): None when the market posts nothing to quote."""
    if lowest_ask != lowest_ask:
        return Quote(QUOTE_BEST_UNFILLED_BID, best_bid) if best_bid == best_bid else None
    if best_bid == best_bid and best_bid < lowest_ask:
        return Quote(QUOTE_BEST_UNFILLED_BID, best_bid)
    if funded:
        return None
    return Quote(QUOTE_LOWEST_UNFILLED_ASK, lowest_ask)


def held_price(last_price, lowest_clamped: float):
    """The figure a market that did not trade carries as its price: the last price held, or the lowest ask when that is above it."""
    if lowest_clamped != lowest_clamped or (last_price is not None and lowest_clamped <= last_price):
        return last_price
    return lowest_clamped


def untraded_result(good: str, area: str, currency: str, last_price, supply: float, lowest_ask: float, lowest_clamped: float,
                    best_bid: float, funded: bool) -> ClearingResult:
    """The clearing of a market that did not trade, as `goods_market.clear` returns it."""
    return ClearingResult(good, area, currency, held_price(last_price, lowest_clamped), 0.0, 0.0, supply, (),
                          quote_of(lowest_ask, best_bid, funded))
