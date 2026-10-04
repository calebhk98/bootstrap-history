"""What the labour package knows about a trade, read from the registry where it can be.

The registry reaches labour as the wage schedule's training years and the world's trade families
(the engine's trade record keeps no other field yet, Complaints/413). A field the registry does not
state comes from legacy_trade_defaults.py, and a trade absent there too gets the generic answer, so a
mod's trade works without code.
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


def literate_trades(trade_ids) -> FrozenSet[str]:
    return frozenset(trade for trade in trade_ids if trade in legacy_trade_defaults.LITERATE)


def taught_from(trade: str) -> str:
    return legacy_trade_defaults.TAUGHT_FROM.get(trade, legacy_trade_defaults.TAUGHT_FROM_DEFAULT)


def tool_basket(trade: str) -> Tuple[str, ...]:
    return legacy_trade_defaults.TOOL_BASKETS.get(trade, ())


def staff_resource_trade(resource: str) -> str:
    return legacy_trade_defaults.STAFF_RESOURCE_TRADES.get(resource, resource)


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
