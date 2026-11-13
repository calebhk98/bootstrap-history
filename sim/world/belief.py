"""What an actor believes about something it cannot see directly: an estimate with a spread and the year it was learned.

A belief is a plain dict {"value", "variance", "year"}; `variance` is relative to the value (a spread of the estimate as a
share of what it estimates), so one rule serves army sizes, cash and technique counts. News arrives after the time it takes
to travel, an old belief loses reliability with the years, and a new signal is merged by weighing each by its precision.
Pure functions: the noise is drawn by the caller (`signal_noise_draw`)."""
import math
import zlib
from typing import Any, Dict, Mapping, Optional

from sim.constants import declare

OBSERVATION_VARIANCE = declare(
    "OBSERVATION_VARIANCE", 0.09, kind="temporary_heuristic", unit="relative variance", source=None, confidence="D",
    retire="Complaints/488-no-belief-or-intelligence-model.md",
    why="Relative variance of one casual observation of another actor (trade contact, a traveller's report), before spies "
        "improve it. Real reliability follows the channel; this is one figure for all.")
TRADE_OBSERVATION_VARIANCE = declare(
    "TRADE_OBSERVATION_VARIANCE", 0.01, kind="temporary_heuristic", unit="relative variance", source=None, confidence="D",
    retire="Complaints/488-no-belief-or-intelligence-model.md",
    why="Relative variance of what a merchant learns by trading at a place itself: firsthand, so far sharper than hearsay.")
VARIANCE_GROWTH_PER_YEAR = declare(
    "VARIANCE_GROWTH_PER_YEAR", 0.03, kind="temporary_heuristic", unit="relative variance per year", source=None,
    confidence="D", retire="Complaints/488-no-belief-or-intelligence-model.md",
    why="How fast an unrefreshed belief becomes unreliable as the thing believed about drifts. Drift really follows how "
        "fast that thing changes; this is one rate for all.")
UNRELIABLE_VARIANCE = declare(
    "UNRELIABLE_VARIANCE", 0.25, kind="temporary_heuristic", unit="relative variance", source=None, confidence="D",
    retire="Complaints/488-no-belief-or-intelligence-model.md",
    why="Relative variance (a spread of half the value) past which an actor no longer acts on a belief and drops it.")
NEWS_SPEED_KM_PER_YEAR = declare(
    "NEWS_SPEED_KM_PER_YEAR", 20000.0, kind="temporary_heuristic", unit="km per year", source=None, confidence="D",
    retire="Complaints/488-no-belief-or-intelligence-model.md",
    why="How fast news travels between two places; stands in for route speed (a courier, a ship) until news rides the "
        "freight routes.")


def news_age_years(distance_km: float, news_speed_km_per_year: float) -> float:
    """Years a report is old when it reaches a place `distance_km` from where it happened."""
    return distance_km / news_speed_km_per_year


def aged_variance(variance: float, years: float, growth_per_year: float) -> float:
    """The variance of a belief `years` after it was learned."""
    return variance + growth_per_year * max(0.0, years)


def years_until_unreliable(fresh_variance: float, growth_per_year: float, unreliable_variance: float) -> int:
    """Whole years a belief learned with `fresh_variance` stays reliable enough to act on (none if it never was)."""
    if fresh_variance >= unreliable_variance:
        return 0
    return int(math.floor((unreliable_variance - fresh_variance) / growth_per_year + 1e-9))


def merge(belief: Optional[Mapping[str, Any]], value: float, variance: float, year: int, growth_per_year: float) -> Dict[str, Any]:
    """The belief after a signal reading `value` with relative `variance` arrives in `year`: the old belief is aged to
    `year`, then the two are averaged weighted by their precision (one over variance). No old belief: the signal alone."""
    if belief is None:
        return {"value": float(value), "variance": float(variance), "year": int(year)}
    old_variance = aged_variance(belief["variance"], year - belief["year"], growth_per_year)
    old_precision, new_precision = 1.0 / old_variance, 1.0 / variance
    total = old_precision + new_precision
    return {"value": (belief["value"] * old_precision + value * new_precision) / total, "variance": 1.0 / total, "year": int(year)}


def is_reliable(belief: Optional[Mapping[str, Any]], year: int, growth_per_year: float, unreliable_variance: float) -> bool:
    """Whether the belief exists and, aged to `year`, is still below the variance an actor will act on."""
    if belief is None:
        return False
    return aged_variance(belief["variance"], year - belief["year"], growth_per_year) < unreliable_variance


def believed_value(belief: Optional[Mapping[str, Any]]) -> Optional[float]:
    """The estimate, or None when nothing is believed (never a stand-in zero)."""
    return None if belief is None else belief["value"]


def signal_noise_draw(*key_parts: Any) -> float:
    """A standard-normal draw fixed by the key (observer, target, kind, year), so a loaded game and a live one draw alike and
    the game's random stream is untouched."""
    key = "|".join(str(part) for part in key_parts).encode()
    first, second = zlib.crc32(key, 1), zlib.crc32(key, 2)
    uniform_a, uniform_b = (first + 0.5) / 2 ** 32, (second + 0.5) / 2 ** 32
    return math.sqrt(-2.0 * math.log(uniform_a)) * math.cos(2.0 * math.pi * uniform_b)


def reading(true_value: float, variance: float, draw: float) -> float:
    """What a signal of relative `variance` reports of `true_value`, given a standard-normal `draw` (never below zero)."""
    return max(0.0, true_value * (1.0 + math.sqrt(variance) * draw))
