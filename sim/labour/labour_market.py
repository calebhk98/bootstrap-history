"""Society's hours by trade, moved toward what planned output needs (an hours-only allocator).

NEED is `labour_hours_required_by_trade`: hours a planned output calls for, read off
data/production/*.json. HAVE is `Workforce.hours_by_trade`: hours worked now. `Workforce.step` moves
hours each year out of trades with more than they are asked for and into those with less, at a speed
that grows with the gap, along paths weighted by skill family (the registry's `family`, passed in as
`skill_family_of`) and with a trade needing technology unable to start from nothing. No wage enters.
`have_versus_need` names the gap instead of assuming it shut.

This allocator is the engine's yearly society-hours split (labour_allocation.reallocate). The labour
core in sim/labour/market/ models the same market with wages, ability, training and migration, and
replaces it once the engine keeps the core's state (Complaints/401 and 403).
"""
import collections
import json
import os
from typing import (
    AbstractSet, Any, Callable, Dict, FrozenSet, Iterable, Optional, Tuple,
)

from sim.constants import declare
# sim.unit_conversions carries the same "imports nothing but sim.constants"
# property sim.constants itself already has, so importing it is not the
# cross-domain wiring this module's own STANDALONE section forbids.
from sim.unit_conversions import KILOGRAMS_PER_TONNE, KILOGRAMS_PER_GRAM
from sim.algorithm_parameters import MAXIMUM_REALLOCATION_PERIODS, CONVERGENCE_TOLERANCE_HOURS

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
# THE FRICTION: HOW FAST HOURS CAN ACTUALLY MOVE BETWEEN TRADES
# ============================================================================
# Four separate parameters control reallocation speed, replacing a single flat
# rate that could not account for crisis conditions or skill transfers:
#
#   OCCUPATIONAL_MOBILITY_RATE_PER_YEAR      steady-state rate - how fast
#                                             hours move between trades under
#                                             normal conditions.
#   OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN  accelerator applied when gaps
#                                             are large relative to trade size,
#                                             so crises pull faster than
#                                             routine reallocation.
#   OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR
#                                             hard upper bound on outflow or
#                                             inflow per year, even under
#                                             maximum urgency.
#   WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS
#                                             pool of available hours for
#                                             walkable trades (those needing
#                                             no prior master) to draw from
#                                             when starting from zero.
#
# A fifth parameter, CROSS_FAMILY_PROXIMITY, discounts reallocation rates
# between trades in different skill families, so hours favour skill-close
# destinations over distant ones.

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

CROSS_FAMILY_PROXIMITY = declare(
    "CROSS_FAMILY_PROXIMITY", 0.2,
    kind="temporary_heuristic",
    unit="fraction of same-family mobility ceiling applied to flows between "
        "different skill families.",
    source="No occupational-distance matrix for this period exists. One in "
        "five represents enough cross-family mobility to allow retraining "
        "over sustained shortages, without claiming distant skills are as "
        "transferable as closely related ones.",
    confidence="D",
    why="Allows hours to flow between skill families at reduced rate, "
        "reflecting that some skills transfer between trades while others "
        "require substantial retraining. Same-family flows use full ceiling; "
        "walkable trades use full ceiling from any origin.")


def _relative_gap_size(gap_hours: float, basis_hours: float) -> float:
    """abs(gap_hours) / basis_hours, as "how many multiples of the basis
    the gap represents" - `float("inf")` when `basis_hours` is exactly zero
    and there IS a gap (nothing to divide by, and no honest finite answer),
    `0.0` when there is no gap at all, however small the basis."""
    if basis_hours <= 0.0:
        return float("inf") if gap_hours != 0.0 else 0.0
    return abs(gap_hours) / basis_hours


def _gap_responsive_mobility_rate(
        base_rate: float, relative_gap: float,
        gain: float = OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN,
        rate_ceiling: float = OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR) -> float:
    """The rate `Workforce.step` actually uses for one trade's outflow or
    inflow ceiling this period: `base_rate` when `relative_gap` is zero,
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


# ----------------------------------------------------------------------------
# SKILL DISTANCE: WHICH TRADES ARE "CLOSE", AND WHICH TRADES NEED NO MASTER
# ----------------------------------------------------------------------------

_UNCLASSIFIED_TECHNOLOGY_GATE = object()
# Private sentinel to distinguish `requires_node: null` (technique needs no
# technology gate) from a missing field (entry not yet classified). `None`
# cannot be the missing marker because it is itself the meaningful value
# when a technique is available on day one.


def trades_reachable_given_technology(
        reached_node_ids: Iterable[str] = (),
        production: Optional[Dict[str, Any]] = None) -> FrozenSet[str]:
    """Return all trades reachable without an existing master, given reached
    tech-tree nodes. A trade is reachable if it appears in at least one
    recipe whose `requires_node` is `null` or a member of `reached_node_ids`.

    `requires_node: null` means the technique needs no prior knowledge;
    `requires_node: "node_id"` means that node must be reached first;
    missing field means unclassified (no walkability granted either way).

    One walkable recipe suffices: a partial master (hand-forge but not
    machine-work) is still a master a civilization can grow from zero.

    `reached_node_ids` is a parameter, not read from the tech tree itself,
    following this module's standalone design: no imports from sim/engine/.
    Empty default is day-one scenario state (no technology yet).

    Technology gates are enforced: a trade fully gated behind unreached nodes
    cannot start, however the function is called. The boundary is computed
    per-trade from actual recipes, not hand-picked and frozen, so it grows
    as technology is reached."""
    production = production if production is not None else production_data()
    reached = set(reached_node_ids)
    reachable_trades = set()
    for entry in production.values():
        gate = entry.get("requires_node", _UNCLASSIFIED_TECHNOLOGY_GATE)
        if gate is _UNCLASSIFIED_TECHNOLOGY_GATE:
            continue   # unclassified - "no data" claims no walkability either way
        if gate is not None and gate not in reached:
            continue   # a real gate, and it has not been reached
        for trade in (entry.get("labour_hours") or {}):
            reachable_trades.add(trade)
        for capital_item in entry.get("capital") or []:
            for trade in (capital_item.get("build_labour_hours") or {}):
                reachable_trades.add(trade)
    return frozenset(reachable_trades)


WALKABLE_TRADES = trades_reachable_given_technology()
# Trades reachable on day one (no technology reached yet), computed from
# data/production/'s `requires_node` field: whatever needs no technology is
# walkable. Default for `Workforce.step`'s `walkable_trades=` parameter.
#
# Trades not walkable require a master and can only start from zero via
# `minimum_absorption_hours_by_trade` (e.g., trained workforce from
# sim/labour/labour.py's institution mechanisms).
#
# Callers with access to the tech tree can grow this set as technology is
# reached, by calling `trades_reachable_given_technology(reached_node_ids)`
# and passing the result to `Workforce.step`. Callers can also add trades
# by hand (synthetic roles not in data/production/).

def trade_skill_family(trade: str) -> str:
    """Default skill family: each trade is its own family. Callers with a
    registry pass its `family` field as the `skill_family_of` parameter."""
    return trade


def _flow_proximity(
        origin_trade: str, destination_trade: str, destination_is_walkable: bool,
        skill_family_of: Callable[[str], str] = trade_skill_family,
        cross_family_proximity: float = CROSS_FAMILY_PROXIMITY) -> float:
    """Return the fraction of mobility ceiling (0-1) allowed for flow from
    origin to destination. Returns 1.0 (full ceiling) if destination is
    walkable (needs no prior skill) or if both trades share a skill family.
    Returns `cross_family_proximity` otherwise.

    Asymmetric: moving DOWN into unskilled work is unrestricted (no origin
    skill matters); moving UP into skilled work is discounted if skill
    families differ (some training needed). This reflects that destination
    requirements matter more than symmetric trade distance."""
    if origin_trade == destination_trade:
        return 1.0
    if destination_is_walkable:
        return 1.0
    return 1.0 if skill_family_of(origin_trade) == skill_family_of(destination_trade) \
        else cross_family_proximity


SKILL_DISTANCE_BALANCING_ITERATIONS = 25
# A purely ALGORITHMIC bound, exactly like MAXIMUM_REALLOCATION_PERIODS
# below - not a modelling claim, just how many rounds of iterative
# proportional fitting `_skill_distance_weighted_flow_matrix` runs to find a
# flow matrix that respects every trade's own mobility ceiling as closely as
# the proximity weights allow. With at most a few dozen trades this
# converges to floating-point stability in far fewer rounds than this; the
# margin costs nothing the test suite's time budget would notice.


# ============================================================================
# THE ALLOCATION: WORKFORCE STATE (HAVE), AND THE ONE STEP THAT MOVES IT
# ============================================================================

TradeFlow = collections.namedtuple(
    "TradeFlow",
    ["trade", "hours_required", "hours_before", "hours_moved_in",
     "hours_moved_out", "hours_after", "tightness_ratio"])
# tightness_ratio: hours_required / hours_before (before move) - scarcity
# in pure hours, no wage. 1.0 = met; >1.0 = short; <1.0 = slack.
# float("inf") when hours_before is zero and something required, signaling
# an unpopulated trade that needs institutional action, not reallocation.


class Workforce(object):
    """Mutable state of hours currently worked in each trade. Stepped forward
    one year at a time via `step()`, returning immutable TradeFlow records.

    `hours_by_trade` is in hours per year (same unit as production recipes),
    not headcount. Callers with headcount and per-worker hours multiply
    before constructing."""

    __slots__ = ("hours_by_trade",)

    def __init__(self, hours_by_trade: Dict[str, float]) -> None:
        # Sorted so sums do not depend on insertion or load order.
        self.hours_by_trade = {trade: float(hours)
                               for trade, hours in sorted(hours_by_trade.items())}

    def __repr__(self) -> str:
        return "Workforce(%r)" % (self.hours_by_trade,)

    def total_hours(self) -> float:
        return sum(self.hours_by_trade.values())

    def step(
            self, hours_required_by_trade: Dict[str, float],
            mobility_rate_per_year: float = OCCUPATIONAL_MOBILITY_RATE_PER_YEAR,
            minimum_absorption_hours_by_trade: Optional[Dict[str, float]] = None,
            mobility_gap_response_gain: float = OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN,
            mobility_rate_ceiling_per_year: float = OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR,
            walkable_trades: AbstractSet[str] = WALKABLE_TRADES,
            walkable_trade_seed_share_of_economy_hours: float = (
                WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS),
            skill_family_of: Callable[[str], str] = trade_skill_family,
            cross_family_proximity: float = CROSS_FAMILY_PROXIMITY,
            skill_distance_balancing_iterations: int = SKILL_DISTANCE_BALANCING_ITERATIONS,
            ) -> Dict[str, "TradeFlow"]:
        """Advance one year: reallocate hours from surplus trades into shortage
        trades, bounded by gap-responsive mobility ceilings and routed by
        skill family proximity. Mutates `self.hours_by_trade` and returns
        `{trade: TradeFlow}` - one entry per trade in either required or
        current allocation.

        The algorithm computes each trade's gap (required minus current),
        scales outflow/inflow rates by gap size (small gaps: slow movement;
        large gaps: faster), applies skill-distance discounts to cross-family
        flows, and uses iterative proportional fitting to balance supply and
        demand within constraints.

        For walkable trades (no prior master needed), the mobility basis
        includes a seed reference (percentage of total economy hours) so they
        can start from zero. Non-walkable trades stay zero unless minimum
        absorption hours are supplied (institutional training).

        Never refuses a result: if demand exceeds supply, returns the shortage
        allocation with unmet gaps shown in TradeFlow entries."""
        minimum_absorption_hours_by_trade = minimum_absorption_hours_by_trade or {}
        # Sorted so the float sums do not depend on string hash order.
        all_trades = sorted(set(self.hours_by_trade) | set(hours_required_by_trade))
        hours_before = {trade: self.hours_by_trade.get(trade, 0.0) for trade in all_trades}
        hours_required = {trade: hours_required_by_trade.get(trade, 0.0) for trade in all_trades}
        total_hours_before = sum(hours_before.values())
        seed_reference = walkable_trade_seed_share_of_economy_hours * total_hours_before

        capped_outflow = {}
        capped_inflow = {}
        for trade in all_trades:
            gap = hours_required[trade] - hours_before[trade]
            if gap < 0.0:
                relative_gap = _relative_gap_size(gap, hours_before[trade])
                rate = _gap_responsive_mobility_rate(
                    mobility_rate_per_year, relative_gap,
                    mobility_gap_response_gain, mobility_rate_ceiling_per_year)
                capped_outflow[trade] = min(rate * hours_before[trade], -gap)
            elif gap > 0.0:
                ceiling_basis = hours_before[trade]
                if trade in walkable_trades:
                    ceiling_basis = max(ceiling_basis, seed_reference)
                relative_gap = _relative_gap_size(gap, ceiling_basis)
                rate = _gap_responsive_mobility_rate(
                    mobility_rate_per_year, relative_gap,
                    mobility_gap_response_gain, mobility_rate_ceiling_per_year)
                floor = minimum_absorption_hours_by_trade.get(trade, 0.0)
                capped_inflow[trade] = min(max(rate * ceiling_basis, floor), gap)
            # gap == 0: this trade contributes nothing to either side.

        surplus_trades = [trade for trade, amount in capped_outflow.items() if amount > 0.0]
        shortage_trades = [trade for trade, amount in capped_inflow.items() if amount > 0.0]

        actual_outflow: collections.defaultdict[str, float] = collections.defaultdict(float)
        actual_inflow: collections.defaultdict[str, float] = collections.defaultdict(float)
        if surplus_trades and shortage_trades:
            flow_matrix = _skill_distance_weighted_flow_matrix(
                surplus_trades, shortage_trades, capped_outflow, capped_inflow,
                walkable_trades, skill_family_of, cross_family_proximity,
                skill_distance_balancing_iterations)
            for origin in surplus_trades:
                for destination in shortage_trades:
                    moved = flow_matrix[origin][destination]
                    if moved:
                        actual_outflow[origin] += moved
                        actual_inflow[destination] += moved

        flows = {}
        for trade in all_trades:
            hours_after = (hours_before[trade] - actual_outflow[trade]
                          + actual_inflow[trade])
            self.hours_by_trade[trade] = hours_after
            tightness_ratio = (hours_required[trade] / hours_before[trade]
                               if hours_before[trade] > 0.0
                               else (float("inf") if hours_required[trade] > 0.0 else 0.0))
            flows[trade] = TradeFlow(
                trade=trade, hours_required=hours_required[trade],
                hours_before=hours_before[trade],
                hours_moved_in=actual_inflow[trade],
                hours_moved_out=actual_outflow[trade],
                hours_after=hours_after, tightness_ratio=tightness_ratio)
        return flows


def _skill_distance_weighted_flow_matrix(
        surplus_trades: Iterable[str], shortage_trades: Iterable[str],
        capped_outflow: Dict[str, float], capped_inflow: Dict[str, float],
        walkable_trades: AbstractSet[str], skill_family_of: Callable[[str], str],
        cross_family_proximity: float, iterations: int) -> Dict[str, Dict[str, float]]:
    """{origin: {destination: hours}} - allocation of surplus to shortage
    trades, weighted by skill proximity. Uses gravity model (capacity on
    both sides times proximity discount) and iterative proportional fitting
    to respect per-trade caps.

    Initializes cells as `capped_outflow[origin] * capped_inflow[dest] *
    proximity(origin, dest)`, then iteratively rescales rows and columns
    to stay within caps. Each rescale shrinks, never grows, so result
    always respects caps exactly. Approximation tuned for annual recompute;
    when all proximities are 1.0 collapses to simple proportional split."""
    weight = {}
    for origin in surplus_trades:
        row = {}
        for destination in shortage_trades:
            proximity = _flow_proximity(
                origin, destination, destination in walkable_trades,
                skill_family_of, cross_family_proximity)
            row[destination] = capped_outflow[origin] * capped_inflow[destination] * proximity
        weight[origin] = row

    flow = {origin: dict(row) for origin, row in weight.items()}
    for _ in range(iterations):
        for origin in surplus_trades:
            row_total = sum(flow[origin].values())
            if row_total > capped_outflow[origin] and row_total > 0.0:
                scale = capped_outflow[origin] / row_total
                for destination in shortage_trades:
                    flow[origin][destination] *= scale
        for destination in shortage_trades:
            column_total = sum(flow[origin][destination] for origin in surplus_trades)
            if column_total > capped_inflow[destination] and column_total > 0.0:
                scale = capped_inflow[destination] / column_total
                for origin in surplus_trades:
                    flow[origin][destination] *= scale
    return flow


# ============================================================================
# WHAT WAS NOT MET: THE FIRST-CLASS OUTPUT THE OLD "converged=False" HID
# ============================================================================

def unmet_demand_by_trade(
        hours_by_trade: Dict[str, float],
        hours_required_by_trade: Dict[str, float]) -> Dict[str, float]:
    """{trade: shortage in hours}, positive entries only. Trades with enough
    or excess hours are omitted, so `bool(...)` answers "is anything short".

    Takes plain dicts, allowing checks at any point (initial state, mid-step
    loop, after convergence)."""
    all_trades = set(hours_by_trade) | set(hours_required_by_trade)
    shortfalls = {}
    for trade in all_trades:
        gap = hours_required_by_trade.get(trade, 0.0) - hours_by_trade.get(trade, 0.0)
        if gap > 0.0:
            shortfalls[trade] = gap
    return shortfalls


HaveVersusNeed = collections.namedtuple(
    "HaveVersusNeed", ["trade", "hours_have", "hours_need", "gap", "tightness_ratio"])


def have_versus_need(
        hours_by_trade: Dict[str, float],
        hours_required_by_trade: Dict[str, float]) -> Dict[str, "HaveVersusNeed"]:
    """{trade: HaveVersusNeed} - compare current hours against requirement.
    `hours_have` from workforce allocation; `hours_need` from target output.
    `gap` is hours_need minus hours_have (positive: short; negative: slack).

    Disagreement between HAVE and NEED is information, not noise: it is the
    pressure `Workforce.step` resolves over time."""
    all_trades = set(hours_by_trade) | set(hours_required_by_trade)
    result = {}
    for trade in all_trades:
        have = hours_by_trade.get(trade, 0.0)
        need = hours_required_by_trade.get(trade, 0.0)
        gap = need - have
        tightness_ratio = (need / have) if have > 0.0 else (float("inf") if need > 0.0 else 0.0)
        result[trade] = HaveVersusNeed(trade=trade, hours_have=have, hours_need=need,
                                       gap=gap, tightness_ratio=tightness_ratio)
    return result


# ============================================================================
# THE FIXED POINT: REPEAT THE STEP UNTIL THE ALLOCATION STOPS MOVING
# ============================================================================

# MAXIMUM_REALLOCATION_PERIODS and CONVERGENCE_TOLERANCE_HOURS moved to
# sim/algorithm_parameters.py (this task's own item 3: "algorithmic and
# computational parameters get their own file"), with their own comments
# carried verbatim - see that module's own section for both, and its own
# docstring for why solve_to_stable_allocation's default arguments below
# still resolve exactly as before. Imported above, at this file's own top,
# rather than re-declared here.

LabourMarketOutcome = collections.namedtuple(
    "LabourMarketOutcome",
    ["workforce", "periods_used", "stabilized", "unmet_demand_by_trade", "history"])


def solve_to_stable_allocation(
        hours_by_trade_initial: Dict[str, float],
        hours_required_by_trade: Dict[str, float],
        mobility_rate_per_year: float = OCCUPATIONAL_MOBILITY_RATE_PER_YEAR,
        minimum_absorption_hours_by_trade: Optional[Dict[str, float]] = None,
        maximum_periods: int = MAXIMUM_REALLOCATION_PERIODS,
        tolerance_hours: float = CONVERGENCE_TOLERANCE_HOURS,
        **step_kwargs: Any) -> "LabourMarketOutcome":
    """Repeatedly step workforce allocation until it stops moving (within
    tolerance) or maximum periods reached. Always returns an allocation with
    unmet demand, never raises.

    Returns LabourMarketOutcome:
      workforce             final Workforce state
      periods_used          years taken to stabilize
      stabilized            True if fixed point reached (see below)
      unmet_demand_by_trade shortage hours on final state
      history               list of TradeFlow dicts, one per period

    `stabilized` is True when allocation stops moving, whether because all
    gaps closed OR because no further reallocation is possible given caps
    (population growth, institution, or plan change needed instead).

    For dynamic demand (changing each year), call Workforce.step directly."""
    workforce = Workforce(hours_by_trade_initial)
    history = []
    for period in range(1, maximum_periods + 1):
        flows = workforce.step(hours_required_by_trade, mobility_rate_per_year,
                               minimum_absorption_hours_by_trade, **step_kwargs)
        history.append(flows)
        every_gap_closed = all(
            abs(flow.hours_required - flow.hours_after) <= tolerance_hours
            for flow in flows.values())
        total_moved_this_period = sum(flow.hours_moved_in for flow in flows.values())
        if every_gap_closed or total_moved_this_period <= tolerance_hours:
            return LabourMarketOutcome(
                workforce=workforce, periods_used=period, stabilized=True,
                unmet_demand_by_trade=unmet_demand_by_trade(
                    workforce.hours_by_trade, hours_required_by_trade),
                history=history)
    return LabourMarketOutcome(
        workforce=workforce, periods_used=maximum_periods, stabilized=False,
        unmet_demand_by_trade=unmet_demand_by_trade(
            workforce.hours_by_trade, hours_required_by_trade),
        history=history)
