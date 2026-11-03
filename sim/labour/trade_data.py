"""What the labour package knows about a trade, read from the registry where it can be.

The registry reaches labour as the world's `trade_registry`: each trade's fields as a plain mapping.
A trade that does not state a field gets the generic answer (not literate, no tools, the default
teacher), so a mod's trade works without code. The role constants that remain are in
legacy_trade_defaults.py.
"""
import functools
from typing import Any, Callable, Dict, FrozenSet, Mapping, Tuple

from . import legacy_trade_defaults
from .market import trades as market_trades


@functools.lru_cache(maxsize=64)
def _fallback_of(entries: Tuple[Tuple[str, float, str], ...]) -> str:
    registry = {trade: {"family": family, "training_years": years} for trade, years, family in entries}
    return market_trades.fallback_trade(market_trades.trade_specs(registry))


def fallback_trade(training_years: Mapping[str, float], family_of: Callable[[str], str]) -> str:
    """The work anyone can take up at once (the trade needing the fewest training years). Memoised on
    the registry's content, which the callers ask about many times a year."""
    return _fallback_of(tuple((trade, years, family_of(trade)) for trade, years in training_years.items()))


def fallback_trade_of(world, training_years: Mapping[str, float]) -> str:
    """The world's unskilled fallback trade: the registry's flagged trade, else the fewest-years rule."""
    registry = registry_of(world)
    if registry:
        return market_trades.fallback_trade_of_registry(registry)
    return fallback_trade(training_years, world.trades.trade_family)


def registry_of(world) -> Mapping[str, Mapping[str, Any]]:
    """The world's trade registry: each trade's fields as plain mappings."""
    return world.trades.trade_registry


def literate_trades(registry: Mapping[str, Mapping[str, Any]], trade_ids) -> FrozenSet[str]:
    return frozenset(trade for trade in trade_ids if registry.get(trade, {}).get("literate", False))


def taught_from(registry: Mapping[str, Mapping[str, Any]], trade: str) -> str:
    return registry.get(trade, {}).get("taught_from", legacy_trade_defaults.TAUGHT_FROM_DEFAULT)


def tool_basket(registry: Mapping[str, Mapping[str, Any]], trade: str) -> Tuple[str, ...]:
    return tuple(registry.get(trade, {}).get("tool_basket", ()))


def tool_stock_per_worker(registry: Mapping[str, Mapping[str, Any]], trade: str) -> Dict[str, float]:
    """Units of each basket good one worker of the trade keeps in use; a basket good with no stated stock is
    only a price factor on the wage (it draws and wears nothing)."""
    basket = tool_basket(registry, trade)
    stock = registry.get(trade, {}).get("tool_stock_per_worker", {}) or {}
    return {good: float(units) for good, units in stock.items() if good in basket and units > 0.0}


def tool_order(registry: Mapping[str, Mapping[str, Any]], trade: str) -> Tuple[str, ...]:
    """The trade's tool goods that carry a stock, in basket order: the first is the tool its workers keep, each
    later one is drawn when the one before it is short."""
    stock = tool_stock_per_worker(registry, trade)
    return tuple(good for good in tool_basket(registry, trade) if good in stock)


def tool_hours_factors(registry: Mapping[str, Mapping[str, Any]], trade: str) -> Tuple[Dict[str, float], float]:
    """(hours per run factor by tool good, factor working by hand) for a trade: how much longer a run takes
    with that tool in place of the first, and with none. A good or case the data does not state is 1.0."""
    fields = registry.get(trade, {})
    by_good = {good: max(1.0, float(factor)) for good, factor in (fields.get("tool_hours_factor") or {}).items()}
    return by_good, max(1.0, float(fields.get("tool_hours_factor_by_hand", 1.0)))


def tool_draw(registry: Mapping[str, Mapping[str, Any]], trade: str, workers: float,
              service_life_years: Mapping[str, float]) -> Dict[str, Dict[str, float]]:
    """What `workers` of the trade hold and wear: {good: {"stock": units in use, "wear_per_year": units worn out a year}}.
    A tool wears out at its stock over its service life; a good with no life is not worn (it is not a durable)."""
    draw = {}
    for good, units in tool_stock_per_worker(registry, trade).items():
        life = float(service_life_years.get(good, 0.0))
        draw[good] = {"stock": units * workers, "wear_per_year": units * workers / life if life > 0.0 else 0.0}
    return draw


def staff_resource_trade(registry: Mapping[str, Mapping[str, Any]], resource: str) -> str:
    """The trade that fills a generic staffing resource (the first by id that names it)."""
    filling = sorted(trade for trade, fields in registry.items() if fields.get("staff_resource") == resource)
    return filling[0] if filling else resource


def scholar_trade() -> str:
    return legacy_trade_defaults.SCHOLAR_TRADE


def generic_craft_trade() -> str:
    return legacy_trade_defaults.GENERIC_CRAFT_TRADE


def bonded_pseudo_trade() -> str:
    return legacy_trade_defaults.BONDED_PSEUDO_TRADE


def farm_trade() -> str:
    return legacy_trade_defaults.FARM_TRADE


def craft_family() -> str:
    return legacy_trade_defaults.CRAFT_FAMILY


def generic_staff_trades(unskilled_trade: str) -> FrozenSet[str]:
    """Trades whose people are interchangeable hands rather than specialists: scholars, generic craftsmen, farm
    hands, the bonded and the unskilled fallback trade (the caller reads it from the registry). A foreman is never
    drawn from them and they are not topped up trade by trade."""
    return frozenset((scholar_trade(), generic_craft_trade(), farm_trade(), bonded_pseudo_trade(), unskilled_trade))


def is_generic_staff(trade: str, unskilled_trade: str) -> bool:
    return trade in generic_staff_trades(unskilled_trade)


def drawn_from_unskilled_pool(trade: str) -> bool:
    return trade in legacy_trade_defaults.DRAWN_FROM_UNSKILLED_POOL


def trade_of_role(registry: Mapping[str, Mapping[str, Any]], role: str) -> str:
    """The trade that plays a role in a state's books (soldier, builder, clerk; unskilled is the fallback trade), the
    first by id that names it. A registry with none refuses."""
    if role == "unskilled":
        return market_trades.fallback_trade_of_registry(registry)
    found = sorted(trade for trade, fields in registry.items() if fields.get("role") == role)
    if not found:
        raise ValueError("no trade in the registry has the role %r" % role)
    return found[0]


def role_field(registry: Mapping[str, Mapping[str, Any]], role: str, field: str) -> Any:
    """A field of the trade that plays `role`; None when it states none."""
    return registry[trade_of_role(registry, role)].get(field)
