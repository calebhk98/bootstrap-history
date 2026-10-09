"""What holding a durable good for a year is expected to return, as a share of its price, and how a
household spreads a store across goods by that return. Pure functions; goods enter only as specs
and prices, never by id."""
import math
from typing import Dict, Mapping, Optional

from sim.constants import declare

from .types import GoodSpec

STORE_STORAGE_COST_PER_KG_YEAR = declare(
    "STORE_STORAGE_COST_PER_KG_YEAR", 0.01, kind="temporary_heuristic",
    unit="money per kg a year", source=None, confidence="D",
    why="Guarding and housing a hoard, and its exposure to theft, cost by the kilogram, so a dense good "
        "costs little per unit of value. The figure stands in for a strongroom and watchman, which are "
        "not modelled.")
STORE_PRICE_REVERSION_SPEED = declare(
    "STORE_PRICE_REVERSION_SPEED", 0.1, kind="temporary_heuristic",
    unit="share of the gap to the usual price expected to close in a year", source=None, confidence="D",
    why="Holders expect a price far above what it usually is to fall back and one far below to recover, "
        "so a dear good promises less to hold. The speed is an assumption; dated price runs of hoarded "
        "goods would bound it.")
STORE_RETURN_SENSITIVITY = declare(
    "STORE_RETURN_SENSITIVITY", 5.0, kind="temporary_heuristic",
    unit="e-folds of weight per unit of yearly return", source=None, confidence="D",
    why="How strongly households shift a store toward the good that promises the better yearly return. "
        "Stands in for a portfolio choice that is not modelled; the value is an assumption.")


def carry_cost_share(spec: GoodSpec, price: float) -> float:
    """Yearly cost of holding a unit as a share of its price: spoilage, wear, and storage by mass."""
    return (spec.spoilage_per_year + 1.0 / spec.service_life_years
            + STORE_STORAGE_COST_PER_KG_YEAR * spec.unit_mass_kg / price)


def expected_price_change(price: float, usual_price: Optional[float]) -> float:
    """Expected yearly change of a price (in logs, as a share of it): toward its usual price; none when
    no usual price is known. General inflation is left out because it lifts every good alike. In logs
    the demand a price draws depends on its ratio to the usual price, not on the money unit."""
    if usual_price is None or usual_price <= 0.0 or price <= 0.0:
        return 0.0
    return STORE_PRICE_REVERSION_SPEED * math.log(usual_price / price)


def carrying_return(spec: GoodSpec, price: float, usual_price: Optional[float]) -> float:
    """Expected yearly return on holding a unit, as a share of its price: the expected price change
    less the cost of carrying it. No service is counted, since a good's service is not in its spec."""
    return expected_price_change(price, usual_price) - carry_cost_share(spec, price)


def split_by_return(returns: Mapping[str, float]) -> Dict[str, float]:
    """Shares of a store (sum to one) by each good's carrying return, favouring the better return."""
    if not returns:
        return {}
    best = max(returns.values())
    weights = {good: math.exp(STORE_RETURN_SENSITIVITY * (value - best)) for good, value in sorted(returns.items())}
    total = math.fsum(weights.values())
    return {good: weight / total for good, weight in weights.items()}
