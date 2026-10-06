"""What the recipe graph asks of each trade, and how fast the farm's hours can move.

`labour_hours_required_by_trade` reads the hours a planned output calls for off data/production/*.json.
Who works in which trade is the labour core's business (sim/labour/market/); the engine's hours by trade
come from its people (labour_allocation.py).
"""
import collections
import json
import os
from typing import Any, Dict, Optional, Tuple

from sim.constants import declare
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


def _dominant_output_key(entry: Dict[str, Any]) -> str:
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
    to how `sim.solve_prices.recipe_cost_and_allocation` prices the same
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
    basis_key = _dominant_output_key(entry)
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


# ============================================================================
# THE BRIDGE TO sim.world.agriculture'S MARGINAL PRODUCT, WITHOUT IMPORTING IT
# ============================================================================
# sim.world.agriculture.marginal_product_of_labour_kg_per_hour is computed
# fresh into YearFlows.marginal_product_last_hour_kg_per_hour EVERY year and
# read by nothing - see that module's own note, quoted in this module's
# docstring, calling it "exactly what the labour market needs to decide
# whether one more hour of a worker's time is worth more on the farm or
# somewhere else". This function is that decision, stated as plain algebra
# (a shortfall divided by a rate is a number of hours; there is no
# heuristic here to label) and taking the marginal product as a PARAMETER
# rather than importing agriculture.py, per this module's own STANDALONE
# section. A caller that HAS agriculture.py in scope (sim/engine/core.py,
# eventually, or this module's own worked example below) computes the real
# number and hands it in; this module never computes one on its own.

def additional_hours_to_close_a_shortfall(
        shortfall_quantity: float, marginal_product_per_hour: float) -> float:
    """Extra hours of a trade's labour needed to close a shortfall of
    `shortfall_quantity` units of that trade's output, given the marginal
    product of the NEXT hour of that trade's labour at its current
    allocation (quantity produced per additional hour - e.g. sim.world.
    agriculture.marginal_product_of_labour_kg_per_hour's own kg-per-hour
    figure). This is the inverse of a marginal product by definition, not
    an estimate: an extra hour producing `marginal_product_per_hour` units
    closes `shortfall_quantity` units of shortfall in exactly `shortfall_
    quantity / marginal_product_per_hour` hours.

    Raises ValueError if `marginal_product_per_hour` is not positive - a
    marginal product of zero or below means no number of extra hours closes
    the shortfall at the current allocation (the harvest window or some
    other hard ceiling is already binding), which is a different situation
    this function refuses to paper over with a division by zero.
    """
    if marginal_product_per_hour <= 0.0:
        raise ValueError(
            "marginal product %r is not positive - no number of additional "
            "hours closes a shortfall when the next hour adds nothing (or "
            "less than nothing); the binding constraint is elsewhere "
            "(land, a harvest window, a hard technical ceiling), not "
            "labour" % (marginal_product_per_hour,))
    return shortfall_quantity / marginal_product_per_hour


# ============================================================================
# THE FRICTION: HOW FAST THE FARM'S HOURS CAN MOVE
# ============================================================================
# Hours leave or join the farm no faster than OCCUPATIONAL_MOBILITY_RATE_PER_YEAR of its size under
# normal conditions, faster as the gap grows (OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN), never faster than
# OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR. WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS is the pool
# a trade with no workers draws from.

OCCUPATIONAL_MOBILITY_RATE_PER_YEAR = declare(
    "OCCUPATIONAL_MOBILITY_RATE_PER_YEAR", 0.05,
    kind="temporary_heuristic",
    unit="fraction of a trade's current hours that can move into or out of "
        "that trade in one year under normal conditions - when the gap is "
        "small relative to the trade's own size.",
    source="No occupational-mobility rate for the pre-industrial "
        "Mediterranean is measured. One in twenty per year is an order-of-"
        "magnitude estimate based on apprenticeship cycle lengths (several "
        "years to train) relative to career length (several decades), "
        "representing the maximum new entrants a trade's training system "
        "can absorb annually.",
    confidence="D",
    why="Bounds reallocation speed to prevent instant workforce shifts. "
        "Represents combined friction from apprenticeship terms, land "
        "tenure, calendars, and capital requirements. Higher gaps trigger "
        "faster movement via OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN; a "
        "ceiling via OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR prevents "
        "overnight clearing.")

OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN = declare(
    "OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN", 2.0,
    kind="temporary_heuristic",
    unit="dimensionless: extra multiples of the steady-state rate added per "
        "100% that a trade's gap represents of its own current size (or, "
        "for a walkable trade seeding from zero, of its seed reference).",
    source="No direct measurement of occupational mobility's response to "
        "shortage size exists. Uses linear growth with gap size, as the "
        "simplest functional form where larger shortages pull faster than "
        "small ones, and returns to base rate when gaps are near zero.",
    confidence="D",
    why="Accelerates reallocation for large gaps (war, strikes, booms) while "
        "maintaining slow steady-state movement for normal conditions. "
        "Tests verify monotonic response to gap size, not specific year "
        "counts, allowing adjustments without changing mechanism behavior.")

OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR = declare(
    "OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR", 0.6,
    kind="temporary_heuristic",
    unit="fraction of a trade's own current size (or seed reference) that "
        "can move into or out of it in one year even under the most "
        "extreme pressure.",
    source="Wartime industrial mobilization (e.g., US female manufacturing "
        "doubled within two years) and mining booms represent the fastest "
        "real occupational shifts, yet took months to low years rather than "
        "days due to transport, housing, tools, and training constraints. "
        "60% per year is a generous ceiling for maximum urgency.",
    confidence="D",
    why="Prevents unlimited growth of reallocation rate when gaps become "
        "very large, ensuring workforce cannot empty or fill a single trade "
        "instantly even under extreme shortage.")

WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS = declare(
    "WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS", 0.01,
    kind="temporary_heuristic",
    unit="fraction of the whole economy's current labour-hours that a "
        "walkable trade with zero current workers can draw from in its "
        "first years, replacing its zero base to allow initial growth.",
    source="Represents a pool of underemployed, seasonal, and transitional "
        "labour available for work requiring no master (new entrants, "
        "between-job transitions, young workers). One percent of total "
        "economy hours is an order-of-magnitude estimate of this margin.",
    confidence="D",
    why="Allows walkable trades (needing no prior master) to start growing "
        "from zero, while non-walkable ones cannot unless minimum absorption "
        "hours are supplied. Reflects pool of always-available, unskilled "
        "labour distinct from established trades' workforces.")

def relative_gap_size(gap_hours: float, basis_hours: float) -> float:
    """abs(gap_hours) / basis_hours, as "how many multiples of the basis
    the gap represents" - `float("inf")` when `basis_hours` is exactly zero
    and there IS a gap (nothing to divide by, and no honest finite answer),
    `0.0` when there is no gap at all, however small the basis."""
    if basis_hours <= 0.0:
        return float("inf") if gap_hours != 0.0 else 0.0
    return abs(gap_hours) / basis_hours


def gap_responsive_mobility_rate(
        base_rate: float, relative_gap: float,
        gain: float = OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN,
        rate_ceiling: float = OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR) -> float:
    """The rate one trade's outflow or inflow ceiling takes this period: `base_rate` when `relative_gap` is zero,
    rising LINEARLY with `relative_gap` (see OCCUPATIONAL_MOBILITY_GAP_
    RESPONSE_GAIN's own declaration for why linear), saturating at
    `max(rate_ceiling, base_rate)`.

    The ceiling is taken as `max(rate_ceiling, base_rate)`, never plain
    `rate_ceiling`, so that a CALLER who passes an explicit `base_rate`
    above the module's own default ceiling (sim.tests.test_labour_
    market.py does this deliberately, to make mobility itself a non-
    binding constraint in a hand-checked arithmetic test) is never
    silently capped BELOW the rate they asked for - this function only
    ever adds urgency on top of a caller's own base rate, never takes it
    away.
    """
    effective_ceiling = max(rate_ceiling, base_rate)
    if relative_gap == float("inf"):
        return effective_ceiling
    return min(effective_ceiling, base_rate * (1.0 + gain * relative_gap))
