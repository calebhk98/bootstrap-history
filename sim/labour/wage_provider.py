"""The inputs to a wage schedule that need no engine: the reference civilisation, its coin standard,
the population's age structure and each trade's training years.

The schedule itself lives in sim.labour.wages and is actor-agnostic; the engine builds it from
these and the price solver (sim/engine/wage_schedule.py).
"""
import functools
import json
import os
from typing import Any, Dict, Mapping

from sim.default_civilisation import CIVILISATION_DIRECTORY, default_civilisation_id
from sim.world import demography
from sim.labour import wages

# The staple the subsistence basket is priced in.
FOOD_PRICE_MATERIAL = "wheat_kg"

REFERENCE_POPULATION = 10000.0



@functools.lru_cache(maxsize=None)
def reference_civilisation() -> Dict[str, Any]:
    """The default civilisation's own file, for the context-free wage table
    tools and the price solver use when no civilisation is in play."""
    path = os.path.join(CIVILISATION_DIRECTORY, default_civilisation_id() + ".json")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def reference_discount_rate() -> float:
    return float(reference_civilisation()["starting_interest_rate"])


def validate_coin_standard(civ: Mapping[str, Any]) -> None:
    """Raise ValueError unless the civilisation states what its unit of money
    is worth in a physical material, with a source."""
    name = civ.get("id", "?")
    standard = civ.get("coin_standard")
    if not isinstance(standard, dict):
        raise ValueError("civilization %r must declare a coin_standard (the material "
                         "and mass one unit of its money stands for)" % name)
    material = standard.get("material")
    if not isinstance(material, str) or not material:
        raise ValueError("civilization %r coin_standard needs a material" % name)
    mass = standard.get("kg_per_unit")
    if isinstance(mass, bool) or not isinstance(mass, (int, float)) or mass <= 0:
        raise ValueError("civilization %r coin_standard needs a positive kg_per_unit" % name)
    if not isinstance(standard.get("source"), str) or not standard["source"].strip():
        raise ValueError("civilization %r coin_standard needs a source" % name)


def coin_standard(civ: Mapping[str, Any]) -> Dict[str, Any]:
    validate_coin_standard(civ)
    return civ["coin_standard"]


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
