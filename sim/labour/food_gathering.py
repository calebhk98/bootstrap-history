"""How much food the hours of a society's fishers and hunters can bring in.

A trade of the registry that gathers food names the food sources it works (`gathers_food_sources`) and its
return in kcal per hour (`food_kcal_per_hour`). The energy a source can yield in a year is bounded by the
hours worked in the trades that gather it times their return, whatever the land and sea could give. A food
source that no trade names is not bounded here. Geography states the ceiling; the caller takes the lower.
"""
from typing import Dict, Mapping

from .market.trades import field_of


def hours_cap_kcal(hours_by_trade: Mapping[str, float], registry: Mapping) -> Dict[str, float]:
    """{food source id: kcal} the working hours of each gathering trade can bring in, for every source a trade
    names (zero when no hours are worked in it)."""
    caps: Dict[str, float] = {}
    for trade_id, entry in registry.items():
        sources = field_of(entry, "gathers_food_sources") or ()
        rate = float(field_of(entry, "food_kcal_per_hour", 0.0) or 0.0)
        for source_id in sources:
            caps[source_id] = caps.get(source_id, 0.0) + rate * max(0.0, float(hours_by_trade.get(trade_id, 0.0)))
    return caps


def capped_kcal(kcal_by_source: Mapping[str, float], caps: Mapping[str, float]) -> Dict[str, float]:
    """Each source's energy held to its labour cap; sources with no cap pass unchanged."""
    return {source_id: min(kcal, caps[source_id]) if source_id in caps else kcal
            for source_id, kcal in kcal_by_source.items()}


def cap_share(kcal: float, cap: float) -> float:
    """The share of an uncapped yield the hours allow, between 0 and 1."""
    return 1.0 if kcal <= 0.0 else min(1.0, max(0.0, cap) / kcal)
