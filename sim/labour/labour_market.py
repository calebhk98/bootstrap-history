"""What the recipe graph asks of each trade.

`labour_hours_required_by_trade` reads the hours a planned output calls for off data/production/*.json.
Who works in which trade is the labour core's business (sim/labour/market/); the engine's hours by trade
come from its people (labour_allocation.py).
"""
import collections
import os
from typing import Any, Dict, Optional, Tuple

# sim.unit_conversions carries the same "imports nothing but sim.constants"
# property sim.constants itself already has, so importing it is not the
# cross-domain wiring this module's own STANDALONE section forbids.
from sim.unit_conversions import KILOGRAMS_PER_TONNE, KILOGRAMS_PER_GRAM

# ============================================================================
# DATA FILE LOCATIONS - SAME ROOT-RELATIVE PATTERN AS THE SIBLING MODULES
# ============================================================================
# Repeated rather than imported, for the reason every sim/world/ module gives
# for not importing another one: see this module's own STANDALONE section.

_THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(_THIS_DIRECTORY))
PRODUCTION_DIRECTORY = os.path.join(_REPOSITORY_ROOT, "data", "production")


def _load_production_data() -> Dict[str, Any]:
    """Return the canonical base-and-enabled-mod production graph."""
    from sim.world.demand import production_data as canonical_production_data
    return canonical_production_data()


def production_data() -> Dict[str, Any]:
    """The shared canonical production graph used by every subsystem."""
    return _load_production_data()


# ============================================================================
# DEMAND SIDE: HOW MANY HOURS OF EACH TRADE A PLANNED OUTPUT REQUIRES (NEED)
# ============================================================================
# This is pure aggregation, not an equilibrium - exactly like
# sim.world.demand.derived_intermediate_demand, which this section mirrors
# field for field but sums `labour_hours` instead of `inputs`. Handing this
# function "society wants this many units of these materials produced this
# year" is what CLAUDE.md's own "given a set of things society wants
# produced" instruction means in code: the quantities are a parameter this
# module takes, never one it invents (see the module docstring's STANDALONE
# section for why, and sim.world.deposits's own DEMAND IS A PARAMETER
# section for the identical discipline applied to a metal quantity).
#
# THIS IS THE "NEED" HALF OF THE MODULE DOCSTRING'S HAVE-VERSUS-NEED
# DISTINCTION. Everything in this section computes how many hours a target
# output calls for; nothing in it reads how many hours are actually worked -
# that is `Workforce.hours_by_trade`, several sections down, computed by an
# entirely different route.

_KILOGRAM_EQUIVALENT_PER_UNIT_SUFFIX = {"_kg": 1.0, "_g": KILOGRAMS_PER_GRAM,
                                        "_t": KILOGRAMS_PER_TONNE}


def _kilogram_equivalent(material_key: str, quantity: float) -> float:
    for suffix, multiplier in _KILOGRAM_EQUIVALENT_PER_UNIT_SUFFIX.items():
        if material_key.endswith(suffix):
            return quantity * multiplier
    return quantity


def dominant_output_key(entry: Dict[str, Any]) -> str:
    """Which of `entry`'s outputs its `labour_hours` are quoted "per unit
    of" - the identical bookkeeping choice sim.world.demand._dominant_
    output_key makes for `inputs`, restated here rather than imported (see
    the module docstring's STANDALONE section)."""
    outputs = entry.get("outputs") or {}
    if not outputs:
        raise ValueError("recipe entry has no outputs at all: %r" % (entry,))
    return max(outputs, key=lambda key: _kilogram_equivalent(key, outputs[key]))


def labour_hours_coefficients_per_unit_output(
        recipe_key: str, production: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """{trade: hours of that trade needed per unit of `recipe_key`'s own
    DOMINANT output produced}, from that recipe's `labour_hours` (spent
    making one batch) and `capital.build_labour_hours` (spent building the
    plant the recipe runs in, amortised over `service_life_years` *
    `annual_output_at_basis` - identical to how `sim.world.demand.input_
    coefficients_per_unit_output` amortises `capital.build_materials`, and
    to how `sim.prices.solve_prices_core.recipe_cost_and_allocation` prices the same
    two `labour_hours` fields).

    Building a furnace that is never fired still needs its trades' worth of
    labour amortised across whatever the furnace eventually makes, exactly
    as a furnace's iron fittings need their materials amortised the same
    way - the two channels are the same physical fact (a capital good costs
    something to build) counted on two different ledgers.
    """
    production = production if production is not None else production_data()
    if recipe_key not in production:
        raise KeyError("no data/production/ entry for %r" % (recipe_key,))
    entry = production[recipe_key]
    basis_key = dominant_output_key(entry)
    basis_quantity = entry["outputs"][basis_key]
    if not basis_quantity:
        raise ValueError("%r's dominant output %r has a zero or missing "
                         "quantity" % (recipe_key, basis_key))

    coefficients: collections.defaultdict[str, float] = collections.defaultdict(float)
    for trade, hours_per_batch in (entry.get("labour_hours") or {}).items():
        coefficients[trade] += hours_per_batch / basis_quantity
    for capital_item in entry.get("capital") or []:
        service_life = capital_item.get("service_life_years")
        annual_output = capital_item.get("annual_output_at_basis")
        if not service_life or not annual_output:
            continue
        for trade, hours_per_build in (capital_item.get("build_labour_hours") or {}).items():
            coefficients[trade] += hours_per_build / (service_life * annual_output)
    return dict(coefficients)


def labour_hours_required_by_trade(
        planned_output_levels: Dict[str, float],
        production: Optional[Dict[str, Any]] = None,
        ) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
    """Total hours of each trade society's planned output requires this
    year (NEED - see the module docstring's HAVE-versus-NEED section),
    given `planned_output_levels` (a dict of recipe_key -> how much of
    that recipe's own dominant output is being produced per year - the
    "society has decided to make this much of this" fact this module takes
    as a parameter rather than inventing, exactly as `sim.world.demand.
    derived_intermediate_demand` takes it for materials).

    Returns (hours_by_trade, contributing_recipes_by_trade):
      hours_by_trade               {trade: total hours required}
      contributing_recipes_by_trade {trade: {recipe_key: hours contributed}}

    The breakdown is what lets a caller (or a test) show WHICH planned
    output is creating the pull on a trade - the labour-market equivalent
    of `derived_intermediate_demand`'s own `by_recipe` return value, and
    for the identical reason: "an industrial base is its own customer" is
    a claim worth being able to point at the recipe that makes it true.
    """
    production = production if production is not None else production_data()
    hours_by_trade: collections.defaultdict[str, float] = collections.defaultdict(float)
    contributing_recipes_by_trade: collections.defaultdict[str, Dict[str, float]] = (
        collections.defaultdict(dict))
    for recipe_key, output_level in planned_output_levels.items():
        if recipe_key not in production or not output_level:
            continue
        coefficients = labour_hours_coefficients_per_unit_output(recipe_key, production)
        for trade, hours_per_unit in coefficients.items():
            if not hours_per_unit:
                continue
            hours = hours_per_unit * output_level
            hours_by_trade[trade] += hours
            contributing_recipes_by_trade[trade][recipe_key] = hours
    return dict(hours_by_trade), dict(contributing_recipes_by_trade)
