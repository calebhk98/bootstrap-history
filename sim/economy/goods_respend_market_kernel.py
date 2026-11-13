"""The small rules the respend rounds' kernel applies to a market: what a bid wants at a price, the lowest ask and the highest
ceiling in a book, and the quantity a round adds to a market's wanted (year_goods's `_wanted_adding`). Numba kernels over
numpy arrays and numbers only.
"""
import numpy

from sim.jit import njit

from .goods_market_kernels import KERNEL, want_at
from .stock_residue import STOCK_RESIDUE_UNITS


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
        if quantity[offer] >= STOCK_RESIDUE_UNITS and reservation[offer] > 0.0 and not lowest <= reservation[offer]:
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
def bid_units(floor, flexible, budget, reference):
    """The units a bid counts as asking for, at its own reference price: its floor and, with a budget and a reference price, its
    flexible part (goods_respend.bid_units)."""
    if budget > 0.0 and flexible > 0.0 and reference > 0.0:
        return floor + flexible
    return floor


@njit(**KERNEL)
def added_fraction(units, counted):
    """The share of a bid of `units` that is new demand: what exceeds the `counted` units the buyer already has in the market."""
    if units <= 0.0:
        return 0.0
    return max(0.0, units - counted) / units


@njit(**KERNEL)
def all_adding(adding):
    """Whether every bid adds in full (the fractions are all one)."""
    for bid in range(len(adding)):
        if adding[bid] < 1.0:
            return False
    return True


@njit(**KERNEL)
def added_units(units, fraction, price, floor, flexible, budget, reference, exponent, maximum):
    """What the added share of a bid asks for at a price: all of `units` (its quantity at the price) when it adds in full, nothing
    when it adds none, else the quantity of the bid cut to that share (flexible part and budget scaled together)."""
    if fraction >= 1.0:
        return units
    if fraction <= 0.0:
        return 0.0
    return quantity_of(price, floor, flexible * fraction, budget * fraction, reference, exponent, maximum)


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
    if all_adding(adding):
        return wanted
    if quote != quote:
        return 0.0
    total = 0.0
    added = 0.0
    for bid in range(count):
        units = quantity_of(quote, floors[bid], flexibles[bid], budgets[bid], references[bid], exponents[bid], maximums[bid])
        total += units
        added += added_units(units, adding[bid], quote, floors[bid], flexibles[bid], budgets[bid], references[bid], exponents[bid],
                             maximums[bid])
    if total <= 0.0:
        return 0.0
    return share * wanted * added / total


@njit(**KERNEL)
def wants_at(price, floors, flexibles, budgets, references, exponents, maximums, capped, wants):
    """`total_wanted` that keeps each bid's quantity: fills `wants` and returns the sum, added in the same order."""
    total = 0.0
    for bid in range(len(floors)):
        wants[bid] = want_at(price, floors[bid], flexibles[bid], budgets[bid], references[bid], exponents[bid],
                             maximums[bid], capped)
        total += wants[bid]
    return total


@njit(**KERNEL)
def quote_of(price, maximums, budgets):
    """The price a round's demand is read at when nothing traded: the lowest ask before it, else the highest ceiling (NaN: none)."""
    ceiling = best_bid_ceiling(maximums, budgets)
    return price if price == price else ceiling


@njit(**KERNEL)
def units_at_quote(quote, first_price, first_wants, floors, flexibles, budgets, references, exponents, maximums, units):
    """Fills `units` with `quantity_of` each bid at `quote`. `first_wants` are the bids' `want_at` the market's cheapest ask
    `first_price` (NaN: none), the same figure where the two prices are equal and a bid has a budget."""
    same = quote == first_price
    for bid in range(len(floors)):
        if same:
            units[bid] = first_wants[bid] if budgets[bid] > 0.0 else 0.0
        else:
            units[bid] = quantity_of(quote, floors[bid], flexibles[bid], budgets[bid], references[bid], exponents[bid],
                                     maximums[bid])


@njit(**KERNEL)
def added_at_quote(quote, units, adding, floors, flexibles, budgets, references, exponents, maximums, added):
    """Fills `added` with `added_units` of each bid at `quote`, given the bids' `units` there."""
    for bid in range(len(floors)):
        added[bid] = added_units(units[bid], adding[bid], quote, floors[bid], flexibles[bid], budgets[bid], references[bid],
                                 exponents[bid], maximums[bid])


@njit(**KERNEL)
def wanted_adding_untraded(quote, units, added, adding, share):
    """`wanted_adding` of a round that traded nothing, from the bids' `units` at `quote` and the `added` part of them: what the
    buyers asked for, less what buyers already counted in the market asked again."""
    if quote != quote:
        return 0.0
    total = 0.0
    added_total = 0.0
    for bid in range(len(units)):
        total += units[bid]
        added_total += added[bid]
    if all_adding(adding):
        return total
    if total <= 0.0:
        return 0.0
    return share * total * added_total / total
