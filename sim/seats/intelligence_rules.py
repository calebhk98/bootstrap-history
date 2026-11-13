"""What a seat learns of another each year from what it can observe, and what its spies cost (the rules are sim/world/belief.py
and sim/world/espionage.py)."""
from typing import Any, Dict, Mapping, Optional

from sim.world import belief, espionage


def fielded_spies(placed: Mapping[str, int], balance: float, cost_per_spy: float) -> Dict[str, int]:
    """The spies a purse of `balance` pays for in a year: targets are served in id order and the rest lapse."""
    affordable = espionage.affordable_spies(sum(placed.values()), balance, cost_per_spy)
    fielded = {}
    for target_id in sorted(placed):
        count = min(placed[target_id], affordable)
        affordable -= count
        if count > 0:
            fielded[target_id] = count
    return fielded


def beliefs_after_year(held: Optional[Mapping[str, Mapping[str, Any]]], truths: Mapping[str, float], observer_id: str,
                       target_id: str, year: int, distance_km: float, spies: int) -> Dict[str, Dict[str, Any]]:
    """The observer's beliefs about one target after the year's signals: for each kind in `truths` a reading with noise (less with
    spies) that is as old as the news takes to travel `distance_km`, merged into what was believed."""
    result = {kind: dict(entry) for kind, entry in (held or {}).items()}
    lag = belief.news_age_years(distance_km, belief.NEWS_SPEED_KM_PER_YEAR)
    base = espionage.observation_variance(belief.OBSERVATION_VARIANCE, spies, espionage.SPY_PRECISION)
    for kind in sorted(truths):
        variance = belief.aged_variance(base, lag, belief.VARIANCE_GROWTH_PER_YEAR)
        value = belief.reading(truths[kind], variance, belief.signal_noise_draw(observer_id, target_id, kind, year))
        result[kind] = belief.merge(result.get(kind), value, variance, year, belief.VARIANCE_GROWTH_PER_YEAR)
    return result
