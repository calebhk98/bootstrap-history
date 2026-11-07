"""The small rules the respend rounds' kernel applies to a market: what a bid wants at a price, the lowest ask and the highest
ceiling in a book, and the quantity a round adds to a market's wanted (year_goods's `_wanted_adding`). Numba kernels over
numpy arrays and numbers only.
"""
import numpy

from sim.jit import njit

from .goods_market_kernels import KERNEL, want_at


@njit(**KERNEL)
def quantity_of(price, floor, flexible, budget, reference, exponent, maximum):
    """goods_market.quantity_at: what a bid wants at a price (nothing without a budget or above its ceiling)."""
    if budget <= 0.0:
        return 0.0
    return want_at(price, floor, flexible, budget, reference, exponent, maximum, True)


@njit(**KERNEL)
def lowest_ask(first, last, reservation, quantity):
    """market_quote.lowest_unfilled_ask over offers `first` to `last`: NaN when none has stock and a positive reservation."""
    lowest = numpy.nan
    for offer in range(first, last):
        if quantity[offer] > 0.0 and reservation[offer] > 0.0 and not lowest <= reservation[offer]:
            lowest = reservation[offer]
    return lowest


@njit(**KERNEL)
def best_bid_ceiling(maximums, budgets):
    """market_quote.best_unfilled_bid: the highest finite positive ceiling among bids with a budget; NaN when none."""
    best = numpy.nan
    for bid in range(len(maximums)):
        if budgets[bid] > 0.0 and maximums[bid] < numpy.inf and maximums[bid] > 0.0 and not best >= maximums[bid]:
            best = maximums[bid]
    return best


@njit(**KERNEL)
def wanted_adding(price, adding, share, requested, traded, floors, flexibles, budgets, references, exponents, maximums):
    """year_goods's `_wanted_adding`: what a round's buyers asked for, less what buyers already counted in the market asked
    again. `price` is the lowest ask on offer before the round (NaN: none). `requested` is the clearing's demand when it
    traded; otherwise buyers' demand at the price."""
    count = len(floors)
    ceiling = best_bid_ceiling(maximums, budgets)
    quote = price if price == price else ceiling
    if traded:
        wanted = requested
    elif quote == quote:
        wanted = 0.0
        for bid in range(count):
            wanted += quantity_of(quote, floors[bid], flexibles[bid], budgets[bid], references[bid], exponents[bid],
                                  maximums[bid])
    else:
        wanted = 0.0
    adds = 0
    for bid in range(count):
        if adding[bid]:
            adds += 1
    if adds == count:
        return wanted
    if quote != quote:
        return 0.0
    total = 0.0
    added = 0.0
    for bid in range(count):
        units = quantity_of(quote, floors[bid], flexibles[bid], budgets[bid], references[bid], exponents[bid], maximums[bid])
        total += units
        if adding[bid]:
            added += units
    if total <= 0.0:
        return 0.0
    return share * wanted * added / total
