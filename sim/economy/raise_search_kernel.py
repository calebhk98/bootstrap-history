"""The sold-out sellers' raise (`goods_market_kernels.raise_search`) over one market, evaluated without rebuilding the book at every
bisection step: the offers' asks are the reservations with the raisable ones lifted to the level (held to their limits), put in
ascending order by insertion (ties keep their given order, as the stable sort does), and a buyer's quantity at an ask is worked
out once for each offer and ask it sits at, since only the lifted asks move between steps. Sums run in the order
`goods_market_kernels.requested_round_one` runs them, so the answers are that function's."""
import numpy

from sim.book import ROUNDING_SHARE
from sim.jit import njit

from . import goods_market_kernels as kernels
from .stock_residue import STOCK_RESIDUE_UNITS

KERNEL = {"error_model": "numpy"}


@njit(**KERNEL)
def covers_lifted(reservations, quantities, supply, raisable, limits, level, minimum, has_minimum, floors, flexibles, budgets,
                  references, exponents, maximums, capped, scratch):
    """`covers_at` with every raisable ask lifted to min(level, its limit) where that is above its reservation (a negative
    `level` lifts nothing). `scratch` is `make_scratch`'s: `asked[offer]` is the ask the offer's row of `wants` was worked
    out at (NaN: none)."""
    scratch_asks, scratch_order, scratch_weights, scratch_running, asked, wants = scratch
    count = len(reservations)
    if count == 0:
        return supply >= supply * (1.0 - ROUNDING_SHARE)
    for offer in range(count):
        ask = reservations[offer]
        if raisable[offer] and level >= 0.0:
            lifted = min(level, limits[offer])
            if lifted >= 0.0 and lifted > ask:
                ask = lifted
        scratch_asks[offer] = ask
        place = offer
        while place > 0 and scratch_asks[scratch_order[place - 1]] > ask:      # equal asks keep their offer order
            scratch_order[place] = scratch_order[place - 1]
            place -= 1
        scratch_order[place] = offer
    bids = len(floors)
    cheapest = 0.0
    found = False
    scratch_running[0] = 0.0
    for position in range(count):
        offer = scratch_order[position]
        ask = scratch_asks[offer]
        if has_minimum and ask < minimum:
            ask = minimum
        scratch_asks[offer] = ask
        stocked = quantities[offer] >= STOCK_RESIDUE_UNITS
        weight = 0.0
        if stocked:
            if not found:
                cheapest = ask
                found = True
            previous = scratch_order[position - 1] if position > 0 else 0
            if position > 0 and quantities[previous] >= STOCK_RESIDUE_UNITS and ask == scratch_asks[previous]:
                weight = scratch_weights[position - 1]
            elif cheapest > 0.0:
                weight = numpy.exp(-kernels.LOGIT_INTENSITY * numpy.log(ask / cheapest))
            elif ask <= cheapest:
                weight = 1.0
        scratch_weights[position] = weight
        scratch_running[position + 1] = scratch_running[position] + weight
        if asked[offer] != ask:
            asked[offer] = ask
            for bid in range(bids):
                wants[offer, bid] = kernels.want_at(ask, floors[bid], flexibles[bid], budgets[bid], references[bid], exponents[bid],
                                                    maximums[bid], capped)
    first = scratch_order[0]
    wanted = 0.0
    for bid in range(bids):
        wanted += wants[first, bid]
    requested = 0.0
    if wanted > 0.0 and supply > ROUNDING_SHARE * wanted:
        for bid in range(bids):
            reach = 0
            while reach < count and scratch_asks[scratch_order[reach]] <= maximums[bid]:
                reach += 1
            total = scratch_running[reach]
            if not total > 0.0:
                total = 1.0
            for position in range(count):
                requested += wants[scratch_order[position], bid] * scratch_weights[position] / total
    return requested >= supply * (1.0 - ROUNDING_SHARE)


@njit(**KERNEL)
def make_scratch(count, bids):
    """The arrays `covers_lifted` works in, for a market of `count` offers and `bids` buyers."""
    return (numpy.zeros(count), numpy.zeros(count, dtype=numpy.int64), numpy.zeros(count), numpy.zeros(count + 1),
            numpy.full(count, numpy.nan), numpy.zeros((count, bids)))


@njit(**KERNEL)
def search_covers(reservations, quantities, supply, raisable, limits, lowest, ceiling, minimum, has_minimum, floors, flexibles,
                  budgets, references, exponents, maximums, capped, scratch):
    """`goods_market_kernels.raise_search` with `covers_lifted`."""
    if not covers_lifted(reservations, quantities, supply, raisable, limits, lowest * (1.0 + kernels.SEARCH_PRECISION), minimum,
                         has_minimum, floors, flexibles, budgets, references, exponents, maximums, capped, scratch):
        return -1.0
    low, high = lowest, ceiling
    while high / low - 1.0 > kernels.SEARCH_PRECISION:
        middle = numpy.sqrt(low) * numpy.sqrt(high)
        if covers_lifted(reservations, quantities, supply, raisable, limits, middle, minimum, has_minimum, floors, flexibles,
                         budgets, references, exponents, maximums, capped, scratch):
            low = middle
        else:
            high = middle
    return low
