"""What the labour package knows about a trade, read from the registry where it can be.

The registry reaches labour as the world's `trade_registry`: each trade's fields as a plain mapping.
A trade that does not state a field gets the generic answer (not literate, no tools, the default
teacher), so a mod's trade works without code. The role constants that remain are in
legacy_trade_defaults.py.
"""
from typing import Any, Callable, Dict, FrozenSet, Mapping, Optional, Tuple

from . import legacy_trade_defaults
from .market import trades as market_trades


def registry_view(training_years: Mapping[str, float], family_of: Callable[[str], str]) -> Dict[str, Dict[str, Any]]:
    """The registry fields labour can reach, as plain entries the market core reads."""
    return {trade: {"family": family_of(trade), "training_years": years}
            for trade, years in training_years.items()}


def fallback_trade(training_years: Mapping[str, float], family_of: Callable[[str], str]) -> str:
    """The work anyone can take up at once (the trade needing the fewest training years)."""
    return market_trades.fallback_trade(market_trades.trade_specs(registry_view(training_years, family_of)))


def registry_of(world) -> Mapping[str, Mapping[str, Any]]:
    """The world's trade registry; a world that states none has no trade facts."""
    return getattr(world, "trade_registry", None) or {}


def literate_trades(registry: Mapping[str, Mapping[str, Any]], trade_ids) -> FrozenSet[str]:
    return frozenset(trade for trade in trade_ids if registry.get(trade, {}).get("literate", False))


def taught_from(registry: Mapping[str, Mapping[str, Any]], trade: str) -> str:
    return registry.get(trade, {}).get("taught_from", legacy_trade_defaults.TAUGHT_FROM_DEFAULT)


def tool_basket(registry: Mapping[str, Mapping[str, Any]], trade: str) -> Tuple[str, ...]:
    return tuple(registry.get(trade, {}).get("tool_basket", ()))


def staff_resource_trade(registry: Mapping[str, Mapping[str, Any]], resource: str) -> str:
    """The trade that fills a generic staffing resource (the first by id that names it)."""
    filling = sorted(trade for trade, fields in registry.items() if fields.get("staff_resource") == resource)
    return filling[0] if filling else resource


def trade_of_family(trade_ids, family_of: Callable[[str], str], family: str) -> Optional[str]:
    """The first trade, by id, of a family; None if the family has none."""
    found = sorted(trade for trade in trade_ids if family_of(trade) == family)
    return found[0] if found else None


def scholar_trade() -> str:
    return legacy_trade_defaults.SCHOLAR_TRADE


def generic_craft_trade() -> str:
    return legacy_trade_defaults.GENERIC_CRAFT_TRADE


def is_generic_staff(trade: str) -> bool:
    return trade in legacy_trade_defaults.GENERIC_STAFF_TRADES


def drawn_from_unskilled_pool(trade: str) -> bool:
    return trade in legacy_trade_defaults.DRAWN_FROM_UNSKILLED_POOL
