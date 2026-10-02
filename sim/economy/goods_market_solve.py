"""Find the price where a falling demand meets a step supply.

Supply is given as levels (reservation, cumulative quantity at or below it). Demand is monotone, so
the first level whose demand is at or below its supply is found by binary search; inside the gap
below it supply is flat and the crossing is a root of demand minus that supply, found by a safeguarded
secant in log price (the bracket always holds the root).

Exact demand costs a pass over every buyer. The same demand ignoring budget caps (`uncapped`) costs one
step per distinct schedule and is never lower, so the true price is never above the price it gives:
that locates the level and a first bracket without exact passes.
"""
import math
from typing import Callable, Dict, List, Optional, Tuple

EXPANSION_STEPS = 2000
CHEAP_EXPANSION_STEPS = 200
CHEAP_BISECTION_STEPS = 45
ROOT_STEPS = 200
LOG_PRICE_TOLERANCE = 1e-11
RELATIVE_RESIDUAL_TOLERANCE = 1e-14

Levels = List[Tuple[float, float]]


def solve_price(levels: Levels, demand: Callable[[float], float], demand_at_first: float,
                uncapped: Optional[Callable[[float], float]] = None) -> float:
    """Price where demand meets the step supply. levels are ascending and positive; demand_at_first is
    demand at the first reservation, already known to the caller."""
    if demand_at_first <= levels[0][1]:
        return levels[0][0]
    known: Dict[int, float] = {0: demand_at_first}
    count = len(levels)
    failing, passing = 0, count
    if uncapped is not None:
        passing = _first_level_met(levels, uncapped)
        if passing - failing > 1:
            _probe(demand, levels, known, passing - 1)
            if known[passing - 1] <= levels[passing - 1][1]:
                passing -= 1
            else:
                failing = passing - 1
    while passing - failing > 1:
        middle = (failing + passing) // 2
        _probe(demand, levels, known, middle)
        if known[middle] <= levels[middle][1]:
            passing = middle
        else:
            failing = middle
    supply = levels[failing][1]
    low, excess_low = levels[failing][0], known[failing] - supply
    ceiling = levels[passing][0] if passing < count else None
    if passing in known:
        if known[passing] >= supply:
            return ceiling
        return _root(demand, low, excess_low, ceiling, known[passing] - supply, supply)
    guess = _uncapped_root(uncapped, low, supply, ceiling) if uncapped is not None else None
    if ceiling is not None and (guess is None or guess >= ceiling):
        excess = demand(ceiling) - supply
        if excess >= 0.0:
            return ceiling
        return _root(demand, low, excess_low, ceiling, excess, supply)
    return _root_above(demand, low, excess_low, guess, supply)


def _probe(demand, levels: Levels, known: Dict[int, float], index: int) -> None:
    known[index] = demand(levels[index][0])


def _first_level_met(levels: Levels, uncapped) -> int:
    """First level after the first at which uncapped demand is at or below its cumulative supply (the count if none)."""
    failing, passing = 0, len(levels)
    while passing - failing > 1:
        middle = (failing + passing) // 2
        if uncapped(levels[middle][0]) <= levels[middle][1]:
            passing = middle
        else:
            failing = middle
    return passing


def _uncapped_root(uncapped, low: float, supply: float, ceiling: Optional[float]) -> Optional[float]:
    """Price above `low` where uncapped demand falls to `supply`, or None when it does not within reach."""
    high = low * 2.0
    for _ in range(CHEAP_EXPANSION_STEPS):
        if ceiling is not None and high >= ceiling:
            return ceiling
        if uncapped(high) <= supply:
            break
        low, high = high, high * 2.0
    else:
        return None
    log_low, log_high = math.log(low), math.log(high)
    for _ in range(CHEAP_BISECTION_STEPS):
        middle = 0.5 * (log_low + log_high)
        if uncapped(math.exp(middle)) > supply:
            log_low = middle
        else:
            log_high = middle
    return math.exp(log_high)


def _root_above(demand, low: float, excess_low: float, guess: Optional[float], supply: float) -> float:
    """Root above `low` when no upper price is known: step upwards in log price, doubling the step."""
    step = math.log(guess / low) if guess is not None else math.log(2.0)
    for _ in range(EXPANSION_STEPS):
        high = low * math.exp(step)
        excess = demand(high) - supply
        if excess < 0.0:
            return _root(demand, low, excess_low, high, excess, supply)
        low, excess_low = high, excess
        step *= 2.0
    return low * math.exp(step)


def _root(demand, low: float, excess_low: float, high: float, excess_high: float, supply: float) -> float:
    """Root of demand minus supply between low (positive excess) and high (negative excess)."""
    log_low, log_high = math.log(low), math.log(high)
    scale = max(abs(supply), 1e-300)
    side = 0
    previous = None
    for _ in range(ROOT_STEPS):
        if log_high - log_low < LOG_PRICE_TOLERANCE:
            break
        point = (log_low * excess_high - log_high * excess_low) / (excess_high - excess_low)
        if not log_low < point < log_high:
            point = 0.5 * (log_low + log_high)
        excess = demand(math.exp(point)) - supply
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
        if abs(excess) <= RELATIVE_RESIDUAL_TOLERANCE * scale:
            return math.exp(point)
        if previous is not None and abs(point - previous) < LOG_PRICE_TOLERANCE:
            return math.exp(point)
        previous = point
    return math.exp(log_high)
