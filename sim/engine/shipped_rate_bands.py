"""The opening's price solves, repeated at the other interest-rate bands a game is likely to meet.

A game solves its prices at the band holding the live market rate (prices.band_interest_rate), so the first
year that meets a new band pays for a cold solve. The solves the opening makes at the starting rate are
replayed here at the bands round it, so `openings` can ship them under the keys the game will compute.
"""
from typing import Any, Callable, Dict, List, Tuple

from sim.world import capital_market

from sim.prices.api import prices

# The market rate starts a game at the starting rate and swings in the early years from near nil (lenders'
# funds build; bounded_rate only caps it) to well above the start (a queue of borrowers). So the bands from nil
# up to twice the starting rate are shipped, nearest the starting rate first, never past the ceiling; the
# total is capped so the shipped solves stay bounded.
MAX_BANDS = 24

SolveCall = Tuple[tuple, Dict[str, Any]]


def banded_rates(starting_rate: float, max_bands: int = MAX_BANDS) -> List[float]:
    """The bands other than the starting rate's own, from nil to twice the start, nearest first."""
    ceiling = starting_rate * capital_market.RATE_CEILING_SHARE
    reach = round(starting_rate / prices.INTEREST_RATE_BAND)
    rates: List[float] = []
    for distance in range(1, reach + 1):
        for steps in (-distance, distance):
            rate = prices.band_interest_rate(starting_rate + steps * prices.INTEREST_RATE_BAND, starting_rate)
            if rate <= ceiling and rate != starting_rate and rate not in rates:
                rates.append(rate)
    return rates[:max_bands]


def _with_rate(call: SolveCall, rate: float) -> SolveCall:
    """The call with its interest rate (the seventh positional argument, or the keyword) set to `rate`."""
    arguments, keywords = call
    keywords = dict(keywords)
    if len(arguments) > 5:
        arguments = arguments[:5] + (rate,) + arguments[6:]
    else:
        keywords["interest_rate"] = rate
    return arguments, keywords


def _rate_of(call: SolveCall, starting_rate: float) -> float:
    arguments, keywords = call
    rate = arguments[5] if len(arguments) > 5 else keywords.get("interest_rate")
    return starting_rate if rate is None else rate


class SolveRecorder:
    """Wraps prices.solved_prices_at_wages for a block and keeps the calls made at the starting rate."""

    def __init__(self) -> None:
        self.calls: List[SolveCall] = []
        self._original: Callable = prices.solved_prices_at_wages

    def __enter__(self) -> "SolveRecorder":
        def recording(*arguments, **keywords):
            self.calls.append((arguments, keywords))
            return self._original(*arguments, **keywords)
        prices.solved_prices_at_wages = recording
        return self

    def __exit__(self, *_exc) -> None:
        prices.solved_prices_at_wages = self._original

    def at_starting_rate(self, starting_rate: float) -> List[SolveCall]:
        return [call for call in self.calls if _rate_of(call, starting_rate) == starting_rate
                and (call[0][2:3] or (None,))[0] is None and call[1].get("production_entries") is None]


def solve_other_bands(calls: List[SolveCall], starting_rate: float, max_bands: int = MAX_BANDS) -> None:
    """Solve every call at every other band; the disk cache keeps each (inside solve_cache.recording())."""
    for rate in banded_rates(starting_rate, max_bands):
        for call in calls:
            arguments, keywords = _with_rate(call, rate)
            prices.solved_prices_at_wages(*arguments, **keywords)
