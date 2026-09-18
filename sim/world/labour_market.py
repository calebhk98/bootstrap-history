"""A labour market: what `sim/solve_prices.py` does for MATERIALS, done for
TRADES.

THE QUESTION THIS ANSWERS, IN THE STAKEHOLDER'S OWN WORDS. "We have a
calculator for the hours each product has to settle/optimize towards, do we
have an equivalence for the labour market?" The answer was no, and this
module is that equivalence. "If fewer farmers, food should be more scarce,
which should mean food becomes more expensive, so jobs shift. Same for other
professions: a country goes to war, which raises demand for swords, so
blacksmiths can go up. But as more people go into a profession, they create
more supply." That is the mechanism this file builds: hours of a trade bid
toward whatever work needs them most, and a trade that gains workers stops
being as scarce, exactly the two-sided adjustment the quotation describes.

THE MEASURED GAP THIS CLOSES. `sim/world/agriculture.py`'s
`farm_workers_fte_for_population` multiplies population by a farm-worker
share computed purely from crop, soil, rotation and toolkit constants - it
never reads nutrition, a wage, or any scarcity signal, and it returns the
IDENTICAL share whether or not an 85% land-loss famine is under way that
year (`sim/tests/test_agriculture_wiring.py`'s
`FamineHasAPhysicalCauseTests` shocks `farm_land.hectares` by exactly that
amount and the farm-workforce SIZE this project's engine derives from it
never notices). A famine can kill people in this model; it cannot yet turn a
blacksmith into a farmer. Every profession in `sim/engine/labour.py` is
priced off a static classification (`TRADE_DENSITY`: "abundant", "common",
"scarce", "uncommon") that never moves with any other trade's fortunes
either - a war raising demand for `smith` hours does not shrink `mason`'s
share, because nothing connects the two. This module is the mechanism that
would.

THE STAKEHOLDER'S OWN KEY INSIGHT, WHICH IS WHY THIS IS TRACTABLE NOW.
"Even without wages, we should know the labour hours for demand to get a
good estimate right." That is exactly the trick `sim/solve_prices.py`
already plays for materials: it solves in LABOUR-HOURS, not money, because
the numeraire only needs to be A unit, not a currency (see that file's own
NUMERAIRE section). This module solves in the same unit for the same
reason: every quantity below is hours of a trade's labour, comparable
directly to hours of another trade's labour, with no wage, no price and no
denarii anywhere in the mechanism. A caller that DOES have relative wages
(`sim.solve_prices.wage_ratios_by_trade`, already expressed in this same
labour-hour numeraire) can hand them in as an optional priority weight - see
`reallocate_one_period`'s `priority_weight_by_trade` parameter - but nothing
here requires it, which is the whole point of building this before a wage
system for labour exists.

THE MECHANISM, IN ONE SENTENCE. Given how many hours of each trade society's
planned output requires (`labour_hours_required_by_trade`, read straight off
`data/production/*.json`'s own `labour_hours` coefficients - the same data
`sim/solve_prices.py` already uses for the cost side of the identical
number) and how many hours of each trade are currently worked
(`Workforce.hours_by_trade`), `Workforce.step` moves hours out of trades
with more supply than is asked of them and into trades with less, one
bounded step at a time, and `solve_to_stable_allocation` repeats that step
until the two agree - the same "found where every equation agrees with
every other" idea `sim/solve_prices.py`'s docstring states for prices,
applied to an allocation instead of a price vector.

WHY THIS IS A STEP PROCESS AND NOT AN INSTANT FIXED POINT, UNLIKE
`sim/solve_prices.py`'s PRICES. A price can update the instant a recipe's
inputs change; nothing physical stops it. A WORKER cannot: a farmer does not
become a blacksmith in a day, and a blacksmith becomes a farmer only a
little faster (farm labour needs less specific training, so the ceiling on
how fast people can be ABSORBED into an already-large trade like
`labourer` is looser than the ceiling on how fast a small skilled trade can
grow). `OCCUPATIONAL_MOBILITY_RATE_PER_YEAR` below is this project's
explicit, labelled answer (CLAUDE.md SS3.4) to "how fast" - a single number
standing in for guild apprenticeship terms, harvest-season timing, land
tenure, and every other real friction this project does not yet model
individually (see that constant's own declaration for what it is trying to
approximate and how weak the evidence behind the specific figure is). A
trade with ZERO current workers cannot grow AT ALL under this mechanism,
however profitable filling it would be - see `Workforce.step`'s own
docstring for why that is a correct property of this mechanism, not a bug:
you cannot train the first optician by bidding hours at him, someone has to
found the trade, which is exactly what `sim/engine/labour.py`'s own
`TRADES_ABSENT` and `trade_schools` machinery is for (see WHAT THIS DOES NOT
MODEL below and this module's WIRING section for how the two would meet).

STANDALONE ON PURPOSE, LIKE ITS SIBLINGS. Nothing here imports
`sim.engine`, `sim.solve_prices`, or any other `sim.world` module - see
`sim/world/__init__.py`, and `sim/world/deposits.py` and
`sim/world/demand.py`'s own docstrings, for why a module built this way
survives other agents editing those paths concurrently with this one's
construction. Every quantity this module cannot itself compute (planned
output levels, a trade's current workforce, a marginal product, a mobility
rate override) is taken as an explicit parameter, exactly as
`sim/world/deposits.py` takes quantity demanded and `sim/world/land.py`
takes population, rather than imported or invented. `production_data()`
below re-reads `data/production/*.json` directly, as plain JSON, the same
data and the same loading pattern `sim/world/demand.py`'s own
`production_data()` already uses (duplicated here rather than imported, for
the same reason) - reading a data file that already exists is not an
import of the module that will eventually read the same file.

WHAT THIS DOES NOT MODEL, STATED PLAINLY (CLAUDE.md's "be honest about what
is missing").

  1. WHICH SPECIFIC RECIPE LOSES HOURS. This module aggregates a trade's
     hours required across every recipe that names it and compares that ONE
     total against the trade's total supply - it does not decide which of
     the many recipes competing for, say, `labourer` hours gets rationed
     first when the trade as a whole is short. That is a within-trade
     allocation question a real price (or `sim.world.demand`'s marginal
     budget shares) would answer; this module only answers the across-trade
     question the stakeholder actually asked.

  2. WHERE A BRAND NEW TRADE'S FIRST WORKER COMES FROM. As stated above, a
     trade at zero hours stays at zero forever under `Workforce.step` alone.
     `sim/engine/labour.py` already has the concept this module lacks
     (`TRADES_ABSENT`, `trade_schools`, `SCHOOL_FOUNDED_HIRING_COEFFICIENT`)
     - a founder-built institution that seeds a trade society could not
     otherwise reach. `Workforce.step`'s `minimum_absorption_hours_by_trade`
     parameter is the seam where that seeding would enter this mechanism;
     this module invents no number for it.

  3. SKILL DISTANCE. A farmer and a mason are both, in this model, exactly
     as far from becoming a smith - `OCCUPATIONAL_MOBILITY_RATE_PER_YEAR`
     is one number for every trade pair. A real economy has this be a
     matrix (a smith's son becomes a farmer far more easily than a farmer
     becomes a smith), and this project has no data to populate one.

  4. WAGES, DELIBERATELY, PER THE STAKEHOLDER'S OWN INSTRUCTION. This
     module answers "how many hours does each trade need" and "where would
     hours move to close that gap", not "what does an hour of each trade
     cost" - `sim.solve_prices.wage_ratios_by_trade` already answers the
     second question in the same numeraire and can be handed to
     `reallocate_one_period` as an optional priority weight (see that
     function's docstring) the day a caller wants demand to be VALUE-
     weighted rather than gap-weighted; nothing here requires it.

  5. A TRADE'S OWN SIZE DOES NOT BOUND ITS SHARE OF FRESH POPULATION. This
     module reallocates hours ALREADY on someone's books between trades; it
     does not model a newly working-age adult choosing a first trade at
     all (`sim.world.demography.Population`'s `working_age` inflow has no
     representation here). A caller wiring this in has to decide where a
     new adult's hours start - the honest default is "wherever their
     household already works", which this module does not compute.

WORKED EXAMPLE, AND HOW TO REPRODUCE IT. Run this file directly:

    python3 sim/world/labour_market.py

for the stakeholder's own two scenarios end to end: a food shortfall that
pulls hours into farming, and a war that pulls hours into smithing, in both
cases FROM the trades least needed elsewhere, over several years, never
instantly.
"""
import collections
import json
import os

from sim.constants import declare

# ============================================================================
# DATA FILE LOCATIONS - SAME ROOT-RELATIVE PATTERN AS THE SIBLING MODULES
# ============================================================================
# Repeated rather than imported, for the reason every sim/world/ module gives
# for not importing another one: see this module's own STANDALONE section.

_THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(_THIS_DIRECTORY))
PRODUCTION_DIRECTORY = os.path.join(_REPOSITORY_ROOT, "data", "production")


def _load_production_data():
    """Every material entry across data/production/*.json, merged by
    material key - the identical merge `sim.world.demand._load_production_
    data` performs, kept as a second copy rather than an import (see the
    module docstring's STANDALONE section)."""
    materials = {}
    for filename in sorted(os.listdir(PRODUCTION_DIRECTORY)):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(PRODUCTION_DIRECTORY, filename)) as handle:
            data = json.load(handle)
        materials.update(data.get("materials", {}))
    return materials


_PRODUCTION_CACHE = None


def production_data():
    """Cached, read-only view of data/production/*.json's materials. A
    caller that already has this in hand can pass it straight to any
    function below via its `production` argument instead of paying the
    parse cost again - see `sim.world.demand.production_data` for the same
    convention."""
    global _PRODUCTION_CACHE
    if _PRODUCTION_CACHE is None:
        _PRODUCTION_CACHE = _load_production_data()
    return _PRODUCTION_CACHE


# ============================================================================
# DEMAND SIDE: HOW MANY HOURS OF EACH TRADE A PLANNED OUTPUT REQUIRES
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

_KILOGRAM_EQUIVALENT_PER_UNIT_SUFFIX = {"_kg": 1.0, "_g": 0.001, "_t": 1000.0}


def _kilogram_equivalent(material_key, quantity):
    for suffix, multiplier in _KILOGRAM_EQUIVALENT_PER_UNIT_SUFFIX.items():
        if material_key.endswith(suffix):
            return quantity * multiplier
    return quantity


def _dominant_output_key(entry):
    """Which of `entry`'s outputs its `labour_hours` are quoted "per unit
    of" - the identical bookkeeping choice sim.world.demand._dominant_
    output_key makes for `inputs`, restated here rather than imported (see
    the module docstring's STANDALONE section)."""
    outputs = entry.get("outputs") or {}
    if not outputs:
        raise ValueError("recipe entry has no outputs at all: %r" % (entry,))
    return max(outputs, key=lambda key: _kilogram_equivalent(key, outputs[key]))


def labour_hours_coefficients_per_unit_output(recipe_key, production=None):
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

    coefficients = collections.defaultdict(float)
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


def labour_hours_required_by_trade(planned_output_levels, production=None):
    """Total hours of each trade society's planned output requires this
    year, given `planned_output_levels` (a dict of recipe_key -> how much of
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
    hours_by_trade = collections.defaultdict(float)
    contributing_recipes_by_trade = collections.defaultdict(dict)
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

def additional_hours_to_close_a_shortfall(shortfall_quantity, marginal_product_per_hour):
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

OCCUPATIONAL_MOBILITY_RATE_PER_YEAR = declare(
    "OCCUPATIONAL_MOBILITY_RATE_PER_YEAR", 0.05,
    kind="temporary_heuristic",
    unit="fraction of a trade's current hours that can move into or out of "
        "that trade in one year",
    source="No occupational-mobility rate for the pre-industrial "
        "Mediterranean is measured anywhere this project has read. The "
        "figure is an order-of-magnitude stand-in built from two facts "
        "this project DOES have some grip on: a Roman-era craft "
        "apprenticeship typically ran several years before someone was "
        "producing at a trained rate, and a working career runs several "
        "decades, so even a trade under maximum pressure to grow or "
        "shrink is bounded by how many NEW entrants a apprenticeship "
        "system can process in a year, not by how many people would "
        "switch instantly if switching were free. One in twenty (5%) a "
        "year is the rough scale of 'one apprenticeship cohort's worth' "
        "relative to an established trade's total size - a plausible "
        "order of magnitude, not a measurement.",
    confidence="D",
    why="This is the single number standing in for every real friction "
        "this project does not yet model individually: guild "
        "apprenticeship terms, land tenure locking a farmer to a holding, "
        "the harvest calendar, literacy, capital needed to set up a "
        "workshop. Without SOME bound, `Workforce.step` would let the "
        "entire labour force retrain into whatever trade the current "
        "shortage points at in a single year, which is the 'instant "
        "clearing' sim.solve_prices.py can get away with for a price and "
        "a labour market plainly cannot - see CLAUDE.md SS3.4's own "
        "instruction to label a heuristic rather than hide it. Changing "
        "this number changes ONLY how many YEARS a given reallocation "
        "takes to complete, never which allocation `solve_to_stable_"
        "allocation` eventually reaches, which is the property sim.tests."
        "test_labour_market.py checks so this constant can be revised "
        "later without silently changing what the mechanism proves.")


# ============================================================================
# THE ALLOCATION: WORKFORCE STATE, AND THE ONE STEP THAT MOVES IT
# ============================================================================

TradeFlow = collections.namedtuple(
    "TradeFlow",
    ["trade", "hours_required", "hours_before", "hours_moved_in",
     "hours_moved_out", "hours_after", "tightness_ratio"])
# tightness_ratio: hours_required / hours_before (before this step's move) -
# the scarcity signal, expressed purely in hours, no wage or price anywhere
# in it. 1.0 means this trade's current workforce exactly meets what is
# asked of it; above 1.0 it is short; below 1.0 it has slack to give up.
# float("inf") when hours_before is 0.0 and something is still required of
# it - a trade that does not exist at all yet but is being asked for hours,
# which `Workforce.step` cannot resolve (see its own docstring) and which a
# caller should treat as a flag that an institution, not a reallocation, is
# what is actually missing.


class Workforce(object):
    """Hours of labour currently worked in each trade - mutable state, in
    the same shape as `sim.world.agriculture.Storage` and `sim.world.
    demography.Population`: one small state dict, stepped forward one year
    at a time, returning an immutable record of exactly what moved.

    `hours_by_trade` is HOURS PER YEAR, not a headcount - the same unit
    `sim.solve_prices.py` prices everything in and the same unit `data/
    production/*.json`'s own `labour_hours` field is stated in, so a
    caller with a headcount and an hours-per-worker-year figure (this
    module does not compute one - see the module docstring's item 5 under
    WHAT THIS DOES NOT MODEL) multiplies the two before constructing this.
    """

    __slots__ = ("hours_by_trade",)

    def __init__(self, hours_by_trade):
        self.hours_by_trade = {trade: float(hours)
                               for trade, hours in hours_by_trade.items()}

    def __repr__(self):
        return "Workforce(%r)" % (self.hours_by_trade,)

    def total_hours(self):
        return sum(self.hours_by_trade.values())

    def step(self, hours_required_by_trade,
             mobility_rate_per_year=OCCUPATIONAL_MOBILITY_RATE_PER_YEAR,
             minimum_absorption_hours_by_trade=None):
        """Advance one year: move hours out of trades with more supply than
        is required of them and into trades with less, bounded on BOTH
        ends by `mobility_rate_per_year` times that trade's OWN current
        size. Mutates `self.hours_by_trade` and returns
        `{trade: TradeFlow}` - one row per trade named in EITHER
        `hours_required_by_trade` or `self.hours_by_trade`, exactly like
        `sim.solve_prices.solve`'s per-material result.

        THE ALGORITHM, IN FOUR STEPS - a bounded, hours-conserving
        analogue of `sim.solve_prices.py`'s damped Jacobi iteration, with
        the bound being a real friction rather than a numerical damping
        choice:

          1. Every trade's GAP is `hours_required - hours_before`: positive
             is a shortage (it needs more hours than it has), negative is
             a surplus (it has more than is asked of it).

          2. A trade in surplus can give up at most `mobility_rate_per_
             year * hours_before` of its OWN size, capped at its actual
             surplus (a trade cannot give up more than its slack, however
             generous the mobility rate). A trade in shortage can absorb
             at most the SAME rate applied to ITS OWN current size, capped
             at its actual shortage - this is the apprenticeship-capacity
             reading of the constant (see OCCUPATIONAL_MOBILITY_RATE_PER_
             YEAR's own declaration): a trade can only grow by a bounded
             PROPORTION of itself in one year, not by an absolute amount,
             which is why a trade at exactly zero hours can absorb exactly
             zero hours here, however large its shortage - a real
             constraint (nobody can apprentice under a master who does not
             exist yet), not an oversight. `minimum_absorption_hours_by_
             trade` is the seam for a caller that KNOWS a trade has just
             been founded (sim.engine.labour.py's own `trade_schools`,
             `TRADES_ABSENT` machinery already tracks exactly this) to
             hand this mechanism a floor above zero for that one trade;
             left at None (the default), every trade is bound by its own
             current size alone, and this module invents no number for
             how a brand-new trade gets its first workers.

          3. The economy-wide total that CAN leave surplus trades this
             year and the total that CAN be absorbed by shortage trades
             this year are, in general, different numbers (a small
             shortage next to a huge, deeply-staffed surplus trade cannot
             absorb everything that trade could shed in one year, and
             vice versa) - `actual_total_moved` is the smaller of the two,
             so hours are never invented or destroyed and never moved
             past what either side can actually supply or take up this
             year.

          4. That total is split across surplus trades in proportion to
             each one's OWN capped outflow, and across shortage trades in
             proportion to each one's OWN capped inflow - the largest
             capped gaps on each side draw the largest share of the move,
             which is the direct mechanism behind "a country goes to war,
             blacksmiths go up, other trades that have the least urgent
             claim on their own hours are what gives them up". This
             proportional split is a modelling choice, not a physical
             fact (see the module docstring's WHAT THIS DOES NOT MODEL
             item 3 on skill distance): it assumes movers are otherwise
             indifferent among origins and destinations, which is
             obviously false in detail (a farmer displaced by a bumper
             harvest is not equally likely to become a scribe or a
             miner) and is the reason this module does not claim to route
             any INDIVIDUAL worker, only the aggregate hours.

        `self.hours_by_trade`'s TOTAL is unchanged by this method to
        floating-point precision - see sim.tests.test_labour_market.py's
        own conservation check, the same discipline sim.world.agriculture.
        Storage.step's docstring states for grain.
        """
        minimum_absorption_hours_by_trade = minimum_absorption_hours_by_trade or {}
        all_trades = set(self.hours_by_trade) | set(hours_required_by_trade)
        hours_before = {trade: self.hours_by_trade.get(trade, 0.0) for trade in all_trades}
        hours_required = {trade: hours_required_by_trade.get(trade, 0.0) for trade in all_trades}

        capped_outflow = {}
        capped_inflow = {}
        for trade in all_trades:
            gap = hours_required[trade] - hours_before[trade]
            trade_mobility_ceiling = mobility_rate_per_year * hours_before[trade]
            if gap < 0.0:
                capped_outflow[trade] = min(trade_mobility_ceiling, -gap)
            else:
                floor = minimum_absorption_hours_by_trade.get(trade, 0.0)
                capped_inflow[trade] = min(max(trade_mobility_ceiling, floor), gap)

        total_capped_outflow = sum(capped_outflow.values())
        total_capped_inflow = sum(capped_inflow.values())
        actual_total_moved = min(total_capped_outflow, total_capped_inflow)

        actual_outflow = collections.defaultdict(float)
        actual_inflow = collections.defaultdict(float)
        if actual_total_moved > 0.0:
            outflow_scale = actual_total_moved / total_capped_outflow
            for trade, capped in capped_outflow.items():
                actual_outflow[trade] = capped * outflow_scale
            inflow_scale = actual_total_moved / total_capped_inflow
            for trade, capped in capped_inflow.items():
                actual_inflow[trade] = capped * inflow_scale

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


# ============================================================================
# THE FIXED POINT: REPEAT THE STEP UNTIL SUPPLY AND DEMAND AGREE
# ============================================================================

MAXIMUM_REALLOCATION_PERIODS = 500
# An algorithmic ceiling on the search, exactly like sim.solve_prices.py's
# own MAXIMUM_ITERATIONS - not a claim about how long a real reallocation
# takes (that claim is OCCUPATIONAL_MOBILITY_RATE_PER_YEAR's job), only a
# guard against a demand vector this mechanism genuinely cannot satisfy
# (more total hours required across all trades than total hours exist)
# looping forever.

CONVERGENCE_TOLERANCE_HOURS = 1e-6
# Absolute hours, not a ratio - a trade required at 0.0 hours must be able
# to reach exactly 0.0 tightness, which a ratio-based tolerance cannot
# express cleanly at that boundary.


def solve_to_stable_allocation(hours_by_trade_initial, hours_required_by_trade,
                               mobility_rate_per_year=OCCUPATIONAL_MOBILITY_RATE_PER_YEAR,
                               minimum_absorption_hours_by_trade=None,
                               maximum_periods=MAXIMUM_REALLOCATION_PERIODS,
                               tolerance_hours=CONVERGENCE_TOLERANCE_HOURS):
    """Call `Workforce.step` repeatedly against a FIXED `hours_required_by_
    trade` until every trade's gap is within `tolerance_hours`, or
    `maximum_periods` is reached - "the allocation where the two agree",
    in the task's own words, found the honest way: as a limit of bounded
    yearly moves, not as an instantaneous solve.

    Returns (final_workforce, periods_used, converged, history) where
    `history` is the list of `{trade: TradeFlow}` dicts `Workforce.step`
    returned each period, in order - the same shape a caller would get
    calling `step` in a loop themselves, so a caller who wants to feed in
    a NEW `hours_required_by_trade` every period (a realistic use: this
    year's demand is not next year's) calls `Workforce.step` directly
    instead of this function, which exists for the case demand is held
    fixed and the question is purely "how long does this take to settle,
    and does it settle at all before `maximum_periods`".

    A demand vector whose total across every trade exceeds `hours_by_
    trade_initial`'s total can never converge (there are not enough hours
    in the economy to satisfy it, however long reallocation runs) -
    `converged` comes back False and `history` shows the shortfall
    stabilising rather than closing, which is itself the honest answer
    ("no reallocation of the EXISTING workforce solves this - population
    has to grow, or the plan has to shrink"), not a bug in the search.
    """
    workforce = Workforce(hours_by_trade_initial)
    history = []
    for period in range(1, maximum_periods + 1):
        flows = workforce.step(hours_required_by_trade, mobility_rate_per_year,
                               minimum_absorption_hours_by_trade)
        history.append(flows)
        if all(abs(flow.hours_required - flow.hours_after) <= tolerance_hours
              for flow in flows.values()):
            return workforce, period, True, history
    return workforce, maximum_periods, False, history


if __name__ == "__main__":
    # ========================================================================
    # THE STAKEHOLDER'S OWN TWO SCENARIOS, WORKED END TO END.
    # ========================================================================
    # Deliberately NOT part of the module's importable surface - a
    # demonstration, not a function another module should call. It imports
    # sim.world.agriculture ONLY here, in the demo, to get a REAL marginal-
    # product number for the food-shortfall scenario's `additional_hours_
    # to_close_a_shortfall` call; the module above never does this itself
    # (see the module docstring's STANDALONE section) - a caller with no
    # agriculture.py in scope can run every function above with a bare
    # float instead.
    import sys
    sys.path.insert(0, _REPOSITORY_ROOT)
    from sim.world import agriculture

    production = production_data()

    def hours_line(flow):
        return ("  %-12s required %9.0f h  before %9.0f h  after %9.0f h  "
               "tightness %6.3f" % (flow.trade, flow.hours_required, flow.hours_before,
                                    flow.hours_after, flow.tightness_ratio))

    # A small toy economy: mostly wheat (booked, in data/production/
    # 40_organics.json, to the generic `labourer` trade - see the module
    # docstring's item 1 under WHAT THIS DOES NOT MODEL for why farm
    # labour and every other unskilled task share one trade in this
    # project's own data), a little iron, a little ceramic.
    baseline_output_levels = {"wheat_kg": 2_000_000.0, "iron_bar_kg": 20_000.0,
                              "ceramic_kg": 30_000.0}
    baseline_hours_required, baseline_contributors = labour_hours_required_by_trade(
        baseline_output_levels, production)
    print("Hours required at baseline output:")
    for trade in sorted(baseline_hours_required):
        print("  %-12s %9.0f h" % (trade, baseline_hours_required[trade]))

    # THE STARTING ALLOCATION - an INITIAL CONDITION (CLAUDE.md SS3.1),
    # exactly like sim.world.land.py's per-civilisation territory: this
    # demo's own choice of how a society happens to be staffed on day one,
    # not something this module derives. `labourer` starts with NO slack
    # (realistic for a subsistence economy: virtually everyone not in a
    # craft is already doing SOME unskilled task, farm or otherwise);
    # every craft trade starts with a modest 20% margin above what this
    # narrow three-recipe plan strictly needs, standing in for the many
    # OTHER things a real craft sector spends part of its time on that
    # this toy economy does not model (illustrative, not measured - see
    # OCCUPATIONAL_MOBILITY_RATE_PER_YEAR's own declaration for the same
    # honesty about a different number in this same demo).
    settled_workforce = {trade: (hours if trade == "labourer" else hours * 1.2)
                         for trade, hours in baseline_hours_required.items()}

    print("=" * 78)
    print("SCENARIO 1: A BAD HARVEST PULLS HOURS TOWARD FARM LABOUR - "
         "AND SHOWS THE CRAFT SECTOR IS FAR TOO SMALL TO ANSWER IT")
    print("=" * 78)
    # THE SHOCK: an ordinary bad-weather year (weather_multiplier < 1.0,
    # the same mechanism sim.world.agriculture.Storage.step draws its own
    # weather from every year), not the catastrophic 85% land loss sim.
    # tests.test_agriculture_wiring.py's own FamineHasAPhysicalCauseTests
    # uses - THAT shock is cited here only as the measured proof the gap
    # is real (see this module's own docstring), because an 85% land loss
    # asks for MORE extra labour-hours than the entire economy has ever
    # had, which this demo shows below is already true of a comparatively
    # mild 10% bad year.
    reference_land = agriculture.Land(10_000.0)
    reference_hours = 150.0 * 10_000.0    # wheat_kg's own 150 h/ha, at the reference area
    harvest_normal = agriculture.gross_harvest_kg(reference_land, reference_hours)
    weather_multiplier = 0.9
    harvest_bad_year = agriculture.gross_harvest_kg(
        reference_land, reference_hours, weather_multiplier=weather_multiplier)
    shortfall_kg = harvest_normal - harvest_bad_year
    marginal_product_now = agriculture.marginal_product_of_labour_kg_per_hour(
        reference_land, reference_hours, weather_multiplier=weather_multiplier)
    print("A 10%% bad-weather year drops the wheat harvest from %.0f kg to "
         "%.0f kg - a shortfall of %.0f kg." % (
             harvest_normal, harvest_bad_year, shortfall_kg))
    print("marginal_product_of_labour_kg_per_hour on the SAME land, at the "
         "SAME labour already applied, is %.4f kg/hour (diminishing "
         "returns have already pushed it below the %.4f kg/hour the land "
         "averaged before the bad year)." % (
             marginal_product_now, harvest_normal / reference_hours))

    extra_hours_needed = additional_hours_to_close_a_shortfall(
        shortfall_kg, marginal_product_now)
    print("additional_hours_to_close_a_shortfall: %.0f extra hours of farm "
         "(labourer-trade) labour would close it - %.1f%% of the ENTIRE "
         "peacetime labourer pool (%.0f h), just to claw back a 10%% "
         "weather loss, because diminishing returns make the last hour "
         "on already-worked land produce far less than the average hour "
         "did." % (extra_hours_needed,
                   100.0 * extra_hours_needed / baseline_hours_required["labourer"],
                   baseline_hours_required["labourer"]))

    craft_slack_hours = sum(settled_workforce[trade] - baseline_hours_required[trade]
                            for trade in settled_workforce if trade != "labourer")
    print("The WHOLE craft sector's slack (every hour smith, furnaceman, "
         "potter, mason, millwright and carpenter have beyond this plan's "
         "own baseline) totals only %.0f h - %.2f%% of what the shortfall "
         "needs. Even fully drained into farm work, crafts cannot answer "
         "a bad harvest in an economy this farm-heavy; that is not a "
         "limit of the search below, it is the physical shape of the "
         "economy." % (craft_slack_hours, 100.0 * craft_slack_hours / extra_hours_needed))

    shocked_hours_required = dict(baseline_hours_required)
    shocked_hours_required["labourer"] += extra_hours_needed
    workforce, periods_used, converged, history = solve_to_stable_allocation(
        settled_workforce, shocked_hours_required, tolerance_hours=1.0)
    print("\nReallocating the settled workforce toward the shocked demand, "
         "one year at a time (labourer only, for space):")
    for year_index in (0, 1, 4, 9, periods_used - 1):
        print(" year %2d: %s" % (year_index + 1, hours_line(history[year_index]["labourer"])))
    print("Converged (tightness reaches 1.0 within 1 hour) after %d "
         "year(s): %s - it CANNOT, because the craft sector this economy "
         "has is not big enough to feed it, which is the honest answer, "
         "not a search failure: the load-bearing response to a bad "
         "harvest in this model is sim.world.agriculture.Storage's own "
         "granary and sim.world.demography's nutrition-driven mortality, "
         "not occupational reallocation - see this module's docstring's "
         "WHAT THIS DOES NOT MODEL for why crafts are too small a pool "
         "to matter much against a farm-scale shock, and see SCENARIO 2 "
         "below for a shock reallocation CAN actually answer." % (
             periods_used, converged))

    print()
    print("=" * 78)
    print("SCENARIO 2: WAR RAISES DEMAND FOR IRON, SMITHS GO UP - AND "
         "OTHER CRAFT TRADES GIVE UP HOURS TO SUPPLY THEM")
    print("=" * 78)
    # data/production/ has no finished "sword" material of its own - it
    # covers MATERIALS, not fabricated end products - so this scenario
    # states the war's demand the way it actually reaches a smith: more
    # iron_bar_kg (the material a smith forges into blades and fittings),
    # the same smith-heavy recipe sim.solve_prices.py's own RENT_BEARING_
    # ORE_MATERIALS section names for the identical reason.
    war_output_levels = dict(baseline_output_levels)
    war_output_levels["iron_bar_kg"] = baseline_output_levels["iron_bar_kg"] * 2.0
    war_hours_required, war_contributors = labour_hours_required_by_trade(
        war_output_levels, production)
    print("Hours required once wartime iron output is DOUBLE peacetime:")
    for trade in sorted(war_hours_required):
        delta = war_hours_required[trade] - baseline_hours_required.get(trade, 0.0)
        print("  %-12s %9.0f h  (%+.0f h vs peacetime)" % (
            trade, war_hours_required[trade], delta))
    print("smith hours are pulled by: %r" % (war_contributors.get("smith"),))

    workforce, periods_used, converged, history = solve_to_stable_allocation(
        settled_workforce, war_hours_required, tolerance_hours=1.0)
    print("\nsmith, year by year - climbing every year, never in one jump, "
         "as OCCUPATIONAL_MOBILITY_RATE_PER_YEAR (%.0f%%) lets it:" % (
             OCCUPATIONAL_MOBILITY_RATE_PER_YEAR * 100.0))
    for year_index in (0, 1, 2, 4, 9, min(19, periods_used - 1)):
        print(" year %2d: %s" % (year_index + 1, hours_line(history[year_index]["smith"])))
    final_smith_hours = workforce.hours_by_trade["smith"]
    final_tightness = war_hours_required["smith"] / final_smith_hours
    print("After %d years this economy's OWN craft slack is exhausted: "
         "smith settles at %.0f h against %.0f h required (tightness "
         "%.3f) - reallocation alone closes %.0f%% of the gap and no "
         "more, because furnaceman is ALSO pulled by the same recipe "
         "(see its own delta above) and is drawing on the identical, "
         "small pool of craft slack. The remaining %.0f h of unmet "
         "demand is exactly the kind of persistent scarcity that (in a "
         "wired-in engine) should show up as a rising smith wage, an "
         "incentive for a founder to open a smithy school, or a push to "
         "import iron goods rather than smith them locally - none of "
         "which this module invents; it only says how large the gap "
         "still is." % (
             min(20, periods_used), final_smith_hours, war_hours_required["smith"],
             final_tightness, 100.0 * final_smith_hours / war_hours_required["smith"],
             war_hours_required["smith"] - final_smith_hours))
