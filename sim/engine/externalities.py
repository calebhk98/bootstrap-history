"""Externalities: harm that activity on a tile does to people and land, fed in by whoever models the activity.

A provider is a function `(sim, year) -> {"deaths_by_band": {band: people}, "yield_factor_by_tile": {tile: factor}}`
(either key may be absent). The engine adds the deaths to the year's demographic step beside epidemic deaths, and
multiplies the yield of land-bound producers on a tile by its factor. Nothing names who the provider is or what it
models, so a mod, a scenario or a later engine mechanism (smoke, runoff, salted fields) can all use the one door.
With no provider registered every function here returns what it was given.
"""
from typing import Callable, Dict, List

PROVIDERS: List[Callable] = []
BANDS = ("children", "working_age", "elderly")


def register(provider: Callable) -> None:
    if provider not in PROVIDERS:
        PROVIDERS.append(provider)


def clear() -> None:
    PROVIDERS.clear()


def _answers(sim, year):
    return [provider(sim, year) or {} for provider in PROVIDERS]


def add_deaths(deaths_by_band: Dict[str, float], sim, year) -> Dict[str, float]:
    """`deaths_by_band` plus every provider's deaths, never negative; the same mapping when nothing is registered."""
    if not PROVIDERS:
        return deaths_by_band
    total = {band: float(count) for band, count in deaths_by_band.items()}
    for answer in _answers(sim, year):
        for band, count in (answer.get("deaths_by_band") or {}).items():
            total[band] = total.get(band, 0.0) + max(0.0, float(count))
    return total


def yield_factors(sim, year) -> Dict[str, float]:
    """{tile: factor} the providers agree on (factors multiply), each clamped to 0..1; empty when none is registered."""
    factors: Dict[str, float] = {}
    for answer in _answers(sim, year) if PROVIDERS else ():
        for tile, factor in (answer.get("yield_factor_by_tile") or {}).items():
            factors[tile] = factors.get(tile, 1.0) * min(1.0, max(0.0, float(factor)))
    return factors
