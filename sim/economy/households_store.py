"""Households keep part of their savings in durable, non-spoiling goods of high value per kilogram.
Pure functions: which goods qualify and how the holding is split among them, and how much of savings
goes into the holding. Goods are chosen by their physical properties and price, never by id."""
import math
from typing import Dict, Mapping

from sim.constants import declare

from .households_orders import HOUSEHOLD_TIME_PREFERENCE
from .types import GoodId, GoodSpec

STORE_MAX_SPOILAGE = declare(
    "STORE_MAX_SPOILAGE", 0.01, kind="temporary_heuristic", unit="share of a stock lost a year",
    source=None, confidence="D",
    why="A good is worth keeping as a store of wealth only if it barely spoils. The cut-off is a "
        "round figure, not measured for any society here.")
STORE_MIN_DENSITY_MULTIPLE = declare(
    "STORE_MIN_DENSITY_MULTIPLE", 20.0, kind="temporary_heuristic",
    unit="multiple of the staple's price per kg", source=None, confidence="D",
    why="Wealth kept as goods has to be small enough to hide, carry and guard, so only goods worth many "
        "times a staple's price per kg qualify. The multiple is an assumption, not measured.")
STORE_STORAGE_COST_PER_KG_YEAR = declare(
    "STORE_STORAGE_COST_PER_KG_YEAR", 0.01, kind="temporary_heuristic",
    unit="money per kg a year", source=None, confidence="D",
    why="Guarding and housing a hoard costs by the kilogram, so a dense good costs little per unit of "
        "value. The figure stands in for a strongroom and watchman, which are not modelled.")
STORE_CHOICE_ELASTICITY = declare(
    "STORE_CHOICE_ELASTICITY", 0.5, kind="temporary_heuristic",
    unit="exponent on the inverse of carrying cost", source=None, confidence="D",
    why="Households spread a store across the goods that qualify, favouring the cheaper to carry. Below "
        "one, a dearer good never draws more demand because of its price; the value itself is assumed.")
STORE_SAVINGS_SHARE = declare(
    "STORE_SAVINGS_SHARE", 0.1, kind="temporary_heuristic", unit="share of savings", source=None,
    confidence="D",
    why="The share of savings a household keeps in goods when it expects no inflation and lending pays "
        "its time preference. It is an assumption; hoard finds and probate inventories would bound it.")
STORE_SHARE_LIMIT = declare(
    "STORE_SHARE_LIMIT", 0.5, kind="temporary_heuristic", unit="share of savings", source=None,
    confidence="D",
    why="Even when inflation is expected a household keeps some savings as claims or cash; the bound is "
        "an assumption standing in for a portfolio choice that is not modelled.")

assert STORE_CHOICE_ELASTICITY < 1.0, "an elasticity of 1 or more makes a price rise raise its own demand"


def _carry_cost_share(spec: GoodSpec, price: float) -> float:
    """Yearly cost of holding a unit as a share of its price: spoilage, wear, and storage by mass."""
    return (spec.spoilage_per_year + 1.0 / spec.service_life_years
            + STORE_STORAGE_COST_PER_KG_YEAR * spec.unit_mass_kg / price)


def store_candidates(specs: Mapping[GoodId, GoodSpec], prices: Mapping[GoodId, float],
                     staple_price_per_kg: float) -> Dict[GoodId, float]:
    """Goods fit to hold as wealth, each with its share of the holding (sums to one; empty if none)."""
    weights = {}
    for good, spec in specs.items():
        price = prices.get(good, 0.0)
        if (spec.service_life_years <= 0.0 or spec.spoilage_per_year > STORE_MAX_SPOILAGE
                or not math.isfinite(spec.unit_mass_kg) or spec.unit_mass_kg <= 0.0 or price <= 0.0):
            continue
        if price / spec.unit_mass_kg < STORE_MIN_DENSITY_MULTIPLE * staple_price_per_kg:
            continue
        weights[good] = (1.0 / _carry_cost_share(spec, price)) ** STORE_CHOICE_ELASTICITY
    total = math.fsum(weights.values())
    return {good: weight / total for good, weight in sorted(weights.items())} if total > 0.0 else {}


def store_value_target(savings: float, expected_inflation: float, real_rate: float) -> float:
    """Value of savings to hold as goods: more when inflation is expected, less when lending pays
    more than the time preference, never above the limit."""
    inflation_pull = 1.0 + max(0.0, expected_inflation) / HOUSEHOLD_TIME_PREFERENCE
    lending_pull = 1.0 + max(0.0, real_rate - HOUSEHOLD_TIME_PREFERENCE) / HOUSEHOLD_TIME_PREFERENCE
    share = min(STORE_SHARE_LIMIT, STORE_SAVINGS_SHARE * inflation_pull / lending_pull)
    return share * max(0.0, savings)
