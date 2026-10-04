"""Trade specs from a trade registry given as plain data, with nothing named in code.

The registry is a mapping of trade id to a dict (the shape of data/world/trades.json and of any mod's
additions). Fields the core uses: `family`, `training_years` (a missing one takes the family's median),
`difficulty`, `fatality_risk_per_year` and `fallback`. The fallback trade is the work anyone can take up
at once: the trades the data flags `fallback`, else the trades needing the fewest training years.
"""
from typing import Any, Dict, List, Mapping

from . import aptitude
from .records import TradeSpec


def _median(values: List[float]) -> float:
    ordered = sorted(values)
    return ordered[len(ordered) // 2] if ordered else 0.0


def trade_specs(registry: Mapping[str, Mapping[str, Any]]) -> Dict[str, TradeSpec]:
    years_by_family: Dict[str, List[float]] = {}
    for entry in registry.values():
        if entry.get("training_years") is not None:
            years_by_family.setdefault(entry.get("family", ""), []).append(float(entry["training_years"]))
    years: Dict[str, float] = {}
    for trade_id, entry in registry.items():
        stated = entry.get("training_years")
        years[trade_id] = float(stated) if stated is not None else _median(
            years_by_family.get(entry.get("family", ""), []))
    flagged = {trade_id for trade_id, entry in registry.items() if entry.get("fallback")}
    if not flagged and years:
        fewest = min(years.values())
        flagged = {trade_id for trade_id, value in years.items() if value == fewest}
    return {
        trade_id: TradeSpec(
            trade_id=trade_id,
            family=str(entry.get("family", "")),
            training_years=years[trade_id],
            difficulty=aptitude.difficulty_from(years[trade_id], entry.get("difficulty")),
            fatality_risk_per_year=float(entry.get("fatality_risk_per_year", 0.0) or 0.0),
            fallback=trade_id in flagged)
        for trade_id, entry in sorted(registry.items())}


def fallback_trades(specs: Mapping[str, TradeSpec]) -> List[str]:
    return sorted(trade_id for trade_id, spec in specs.items() if spec.fallback)


def fallback_trade(specs: Mapping[str, TradeSpec]) -> str:
    """The one trade failed trainees and the displaced fall back to: the first fallback trade by id."""
    found = fallback_trades(specs)
    if not found:
        raise ValueError("the trade registry has no trades")
    return found[0]
