"""Builds the wage schedule from what the engine already knows: the trade
registry, the food price and the population's age structure.

The schedule itself lives in sim.world.wages and is actor-agnostic; this is
the glue that supplies its inputs.
"""
import functools
import json
import os
from typing import Any, Dict, Mapping, Optional

from sim.world import demand, demography, wages

# Same source the food price for the household's own cost of living uses.
FOOD_PRICE_MATERIAL = "wheat_kg"

REFERENCE_POPULATION = 10000.0

_CIVILISATION_DIRECTORY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "civilizations")


@functools.lru_cache(maxsize=None)
def reference_discount_rate() -> float:
    """The default civilisation's starting interest rate, for the context-free
    wage table tools and the price solver use when no civilisation is in play."""
    from .settings import CONFIG_DEFAULTS
    path = os.path.join(_CIVILISATION_DIRECTORY, CONFIG_DEFAULTS["default_civ"] + ".json")
    with open(path, encoding="utf-8") as handle:
        return float(json.load(handle)["starting_interest_rate"])


@functools.lru_cache(maxsize=None)
def people_fed_per_worker() -> float:
    """Total people per working-age adult in the model's own stable age
    structure (children and elderly are fed from the worker's wage)."""
    population = demography.Population.stationary(REFERENCE_POPULATION)
    return population.total / population.working_age


def training_years_by_trade(registry: Mapping[str, Any]) -> Dict[str, float]:
    return wages.training_years_with_family_default(
        {trade_id: trade.training_years for trade_id, trade in registry.items()},
        {trade_id: trade.family for trade_id, trade in registry.items()})


def build_schedule(registry: Mapping[str, Any], food_price_per_kg: float,
                   discount_rate: float,
                   tightness_factors: Optional[Dict[str, float]] = None) -> wages.WageSchedule:
    floor = wages.subsistence_wage_per_hour(
        demand.FOOD_SUBSISTENCE_QUANTITY_KG_PER_CAPITA_PER_YEAR,
        food_price_per_kg, people_fed_per_worker())
    return wages.WageSchedule(
        training_years_by_trade(registry), floor, discount_rate=discount_rate,
        tightness_factors=tightness_factors)
