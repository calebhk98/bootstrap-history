"""The price where a falling demand meets a step supply, as kernels: `goods_market_solve.solve_price` and `goods_market.at_a_ceiling`
bit for bit, over `crossing_columns.DemandColumns`.

Supply is `level_price` (ascending reservations, positive) and `level_supply` (the cumulative quantity at or below each). Every
step is the Python's, in the same order: the binary search over levels, the secant in log price inside the gap, the cheap pass over
`uncapped_at` that brackets the root. The Python remembers answers between books against one schedule (`solve_price`'s `memo`);
the kernels do not, since a search is cheaper than the call that would look it up. A power or exponential the Python raises on
(`math.exp` of more than about 709, a logarithm of zero) sets `flags[0]` (`crossing_demand.FALLBACK`): the caller reruns the
search on objects.
"""
import math

import numpy

from sim.book import ROUNDING_SHARE
from sim.jit import njit

from .crossing_demand import FALLBACK, KERNEL, total_at, uncapped_at

EXPANSION_STEPS = 2000
CHEAP_EXPANSION_STEPS = 200
CHEAP_BISECTION_STEPS = 45
ROOT_STEPS = 200
LOG_PRICE_TOLERANCE = 1e-11
RELATIVE_RESIDUAL_TOLERANCE = 1e-14
LARGEST_EXPONENT = 709.782712893384      # `math.exp` raises OverflowError above this


@njit(**KERNEL)
def exponential(x, flags):
    """`math.exp(x)`, flagging the fallback where the Python raises."""
    if x > LARGEST_EXPONENT:
        flags[0] = FALLBACK
    return math.exp(x)


@njit(**KERNEL)
def logarithm(x, flags):
    """`math.log(x)`, flagging the fallback where the Python raises (x of zero or below)."""
    if not x > 0.0:
        flags[0] = FALLBACK
        return 0.0
    return math.log(x)


@njit(**KERNEL)
def first_level_met(level_price, level_supply, demand, flags):
    """First level after the first at which uncapped demand is at or below its cumulative supply (the count if none)."""
    failing, passing = 0, len(level_price)
    while passing - failing > 1:
        middle = (failing + passing) // 2
        if uncapped_at(level_price[middle], demand, flags) <= level_supply[middle]:
            passing = middle
        else:
            failing = middle
    return passing


@njit(**KERNEL)
def uncapped_root(low, supply, has_ceiling, ceiling, demand, flags):
    """(found, price) above `low` where uncapped demand falls to `supply`; not found when it does not within reach. A ceiling
    reached on the way is the price."""
    high = low * 2.0
    reached = False
    for _ in range(CHEAP_EXPANSION_STEPS):
        if has_ceiling and high >= ceiling:
            return True, ceiling
        if uncapped_at(high, demand, flags) <= supply:
            reached = True
            break
        low, high = high, high * 2.0
    if not reached:
        return False, 0.0
    log_low, log_high = logarithm(low, flags), logarithm(high, flags)
    for _ in range(CHEAP_BISECTION_STEPS):
        middle = 0.5 * (log_low + log_high)
        if uncapped_at(exponential(middle, flags), demand, flags) > supply:
            log_low = middle
        else:
            log_high = middle
    return True, exponential(log_high, flags)


@njit(**KERNEL)
def root_between(low, excess_low, high, excess_high, supply, demand, flags):
    """Root of demand minus supply between low (positive excess) and high (negative excess): a safeguarded secant in log price."""
    log_low, log_high = logarithm(low, flags), logarithm(high, flags)
    tolerance = RELATIVE_RESIDUAL_TOLERANCE * (abs(supply) if abs(supply) > 1e-300 else 1e-300)
    side = 0
    have_previous = False
    previous = 0.0
    for _ in range(ROOT_STEPS):
        if log_high - log_low < LOG_PRICE_TOLERANCE:
            break
        if excess_high == excess_low:        # both ends at the same excess: the secant has no slope
            point = 0.5 * (log_low + log_high)
        else:
            point = (log_low * excess_high - log_high * excess_low) / (excess_high - excess_low)
        if not log_low < point < log_high:
            point = 0.5 * (log_low + log_high)
        excess = total_at(exponential(point, flags), demand, flags) - supply
        if excess > 0.0:
            log_low, excess_low = point, excess
            if side > 0:
                excess_high *= 0.5
            side = 1
        else:
            log_high, excess_high = point, excess
            if side < 0:
                excess_low *= 0.5
            side = -1
        if abs(excess) <= tolerance:
            return exponential(point, flags)
        if have_previous and abs(point - previous) < LOG_PRICE_TOLERANCE:
            return exponential(point, flags)
        previous = point
        have_previous = True
    return exponential(log_high, flags)


@njit(**KERNEL)
def root_above(low, excess_low, has_guess, guess, supply, demand, flags):
    """Root above `low` when no upper price is known: step upwards in log price, doubling the step."""
    step = logarithm(guess / low, flags) if has_guess else math.log(2.0)
    for _ in range(EXPANSION_STEPS):
        high = low * exponential(step, flags)
        excess = total_at(high, demand, flags) - supply
        if excess < 0.0:
            return root_between(low, excess_low, high, excess, supply, demand, flags)
        low, excess_low = high, excess
        step *= 2.0
    return low * exponential(step, flags)


@njit(**KERNEL)
def refine(low, demand_low, has_ceiling, ceiling, has_ceiling_demand, demand_at_ceiling, supply, use_uncapped, demand, flags):
    """The price in the gap above the level at `low` (where demand is `demand_low`) and below `ceiling`."""
    excess_low = demand_low - supply
    if has_ceiling_demand:
        if demand_at_ceiling >= supply:
            return ceiling
        return root_between(low, excess_low, ceiling, demand_at_ceiling - supply, supply, demand, flags)
    has_guess, guess = False, 0.0
    if use_uncapped:
        has_guess, guess = uncapped_root(low, supply, has_ceiling, ceiling, demand, flags)
    if has_ceiling and ((not has_guess) or guess >= ceiling):
        excess = total_at(ceiling, demand, flags) - supply
        if excess >= 0.0:
            return ceiling
        return root_between(low, excess_low, ceiling, excess, supply, demand, flags)
    return root_above(low, excess_low, has_guess, guess, supply, demand, flags)


@njit(**KERNEL)
def solve_levels(level_price, level_supply, demand_at_first, use_uncapped, demand, flags):
    """Price where demand meets the step supply (`goods_market_solve.solve_price`); `demand_at_first` is demand at the first
    reservation, already known to the caller."""
    if demand_at_first <= level_supply[0]:
        return level_price[0]
    count = len(level_price)
    known = numpy.zeros(count)
    is_known = numpy.zeros(count, dtype=numpy.bool_)
    known[0], is_known[0] = demand_at_first, True
    failing, passing = 0, count
    if use_uncapped:
        passing = first_level_met(level_price, level_supply, demand, flags)
        if passing - failing > 1:
            known[passing - 1], is_known[passing - 1] = total_at(level_price[passing - 1], demand, flags), True
            if known[passing - 1] <= level_supply[passing - 1]:
                passing -= 1
            else:
                failing = passing - 1
    while passing - failing > 1:
        middle = (failing + passing) // 2
        known[middle], is_known[middle] = total_at(level_price[middle], demand, flags), True
        if known[middle] <= level_supply[middle]:
            passing = middle
        else:
            failing = middle
    has_ceiling = passing < count
    ceiling = level_price[passing] if has_ceiling else 0.0
    has_ceiling_demand = has_ceiling and is_known[passing]
    demand_at_ceiling = known[passing] if has_ceiling_demand else 0.0
    return refine(level_price[failing], known[failing], has_ceiling, ceiling, has_ceiling_demand, demand_at_ceiling,
                  level_supply[failing], use_uncapped, demand, flags)


@njit(**KERNEL)
def supply_at(level_price, level_supply, price):
    """Cumulative supply of the last level at or below `price` (zero below the first)."""
    count = 0
    while count < len(level_price) and level_price[count] <= price:
        count += 1
    return level_supply[count - 1] if count else 0.0


@njit(**KERNEL)
def at_a_ceiling(price, level_price, level_supply, lowest, demand, flags):
    """Where demand falls off a buyer's ceiling, the crossing can sit just above it with nothing wanted: then the market clears at
    that ceiling (`goods_market.at_a_ceiling`)."""
    if total_at(price, demand, flags) >= supply_at(level_price, level_supply, price):
        return price
    for place in range(len(demand.ceilings)):
        ceiling = demand.ceilings[place]
        if not lowest <= ceiling <= price:
            if ceiling < lowest:
                break
            continue
        supply = supply_at(level_price, level_supply, ceiling)
        if (total_at(ceiling, demand, flags) >= supply
                and total_at(ceiling * (1.0 + ROUNDING_SHARE), demand, flags) <= supply * (1.0 + ROUNDING_SHARE)):
            return ceiling
    return price
