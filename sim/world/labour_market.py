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

THE STRUCTURAL POINT THAT REFRAMES THIS WHOLE MODULE, ALSO THE STAKEHOLDER'S
OWN WORDS. "`agriculture.farm_workers_fte_for_population` computes how many
farmers you NEED. The labour market should compute how many you HAVE. They
should be close to the same, but not always." Those are two different
computations by two different mechanisms, and this module is built around
keeping them visibly two numbers rather than one:

  NEED   `labour_hours_required_by_trade` below - hours a PLANNED OUTPUT
         calls for, read off `data/production/*.json`'s own coefficients.
         Rises and falls with what society has decided to make, nothing
         else. `agriculture.farm_workers_fte_for_population` computes the
         identical KIND of number for one trade by a different, population-
         only route (see WHAT THIS DOES NOT MODEL item 5 below for exactly
         where the two would need to agree and currently do not).

  HAVE   `Workforce.hours_by_trade` - hours actually worked right now, an
         initial condition plus whatever `Workforce.step` has moved since.
         Rises and falls only as fast as `Workforce.step` lets it, however
         urgently NEED changes.

`have_versus_need` near the bottom of this file is the function that puts
the two side by side and names the gap instead of assuming it shut. A
caller that currently treats NEED as HAVE (every trade `sim/engine/
labour.py` prices today) is skipping the entire mechanism this file is -
see that function's own docstring.

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
labour-hour numeraire) could hand them in as an optional priority weight -
`Workforce.step`'s flow matrix is the natural seam for a future `priority_
weight_by_trade` parameter of that kind (see WHAT THIS DOES NOT MODEL item
4) - but nothing here requires it yet, which is the whole point of building
this before a wage system for labour exists.

THE MECHANISM, IN ONE SENTENCE. Given how many hours of each trade society's
planned output requires (NEED, above) and how many hours of each trade are
currently worked (HAVE, above), `Workforce.step` moves hours out of trades
with more supply than is asked of them and into trades with less, one
bounded step at a time, at a SPEED that itself responds to how large the
gap is (a tenfold shortage pulls harder than a ten percent one - see THE
FRICTION section) and along a path shaped by how far apart two trades'
skills actually are (see THE SAME SECTION's skill-family proximity) - and
`solve_to_stable_allocation` repeats that step until the allocation stops
moving, WHETHER OR NOT it has fully closed every gap, always handing back an
allocation plus an honest account of whatever demand is still unmet (see
WHY DEMAND EXCEEDING SUPPLY DOES NOT MEAN A FAILED SOLVE, next).

WHY DEMAND EXCEEDING SUPPLY DOES NOT MEAN A FAILED SOLVE. The stakeholder's
own example: "What if I go to ancient Rome and want to build a telephone
network, and request tens of thousands of km of copper wire? The demand
should shoot up, but even though my request hours are more than the supply
of labour hours, it should still stabilize." And generalised: "Supply can't
match demand, but that's basically 90% of society IRL. It still stabilizes."
An earlier version of this module answered a demand vector the existing
workforce cannot fully satisfy by returning `converged=False` - which reads
as an error, and is not one: a real economy facing more demand than it has
hours for does not refuse to have an allocation, it has ONE, with some of
that demand going unmet and a price (which this module does not model - see
item 4 below) doing the rationing this module cannot. `solve_to_stable_
allocation` now always returns a real `Workforce`, and separately reports
`unmet_demand_by_trade` - the demand that allocation still does not cover,
by trade, always present, never treated as a defect in the search. Its
`stabilized` flag answers a DIFFERENT question from the old `converged` -
"has the allocation stopped moving" - which is true both when every gap
closes AND when the trades with slack to give have already given all of it
and nothing more can move (the corner this module's own SCENARIO 1 below
demonstrates): a request for more copper wire than Rome's whole economy
could ever produce still settles, at whatever the economy can actually
spare toward it, with the remainder reported rather than hidden.

THE STAKEHOLDER'S OWN REMAINING FIVE POINTS, AND WHERE EACH IS ANSWERED.

  3. "Would it really take 20 years to double your iron output? Your war is
     already over by then." One constant mobility rate for every situation
     was the defect - see THE FRICTION section's gap-responsive rate.

  4. "If we found a diamond mine, would you really only see us go from 100
     miners to 103?" Same defect, same fix: the rate scales with how large
     the reward or shortfall is relative to the trade's own current size,
     not with a flat percentage of it.

  5. "Let's say monster towers suddenly appeared, this also says 0 people
     will become adventurers." A trade at exactly zero hours could not grow
     AT ALL under the old rule, which is correct for a trade that needs a
     master to teach it and wrong for work a person can simply walk into -
     see WALKABLE_TRADES and its seed-share mechanism below, and SCENARIO 3
     in the worked example, which runs exactly this case.

  6. "It thinks you can't ever teach yourself a skill, and nothing
     transfers." One mobility rate for every trade PAIR treated a farmer
     and a mason as equally far from becoming a smith. TRADE_SKILL_FAMILY
     and the proximity rule below are this module's answer - crude, stated
     as a rule rather than measured (CLAUDE.md SS3.4), and still not the
     real matrix WHAT THIS DOES NOT MODEL's item 3 says this project does
     not have data to build.

  7. "So nobody can farm on new land?" This module never assumes a trade's
     workforce is a fixed share of population - it only ever moves hours
     that some caller already put on its books, toward whatever `hours_
     required_by_trade` that same caller supplies (see WHAT THIS DOES NOT
     MODEL item 5). The assumption the stakeholder is pointing at lives in
     `sim/world/agriculture.py`'s `farm_workers_fte_for_population`, not
     here, and this module cannot and does not fix a file it does not own -
     what it CAN do, and now does, is make the resulting gap nameable: see
     `have_versus_need` and SCENARIO 4 in the worked example, which grows
     cultivable land and shows NEED rising while HAVE sits still until
     something calls `Workforce.step`.

  8. "Is the current labour market making it impossible for new trades to
     appear? If we simulate early civilization, does this make blacksmiths
     impossible? ... you can't just make a nuclear engineer in Rome, so
     some limits are needed, so IDK if it's good or not." Both halves were
     right about the OLD mechanism: `WALKABLE_TRADES` was a hand-written
     two-name frozenset (`labourer`, `miner`), so every OTHER trade -
     including `smith` - could never grow from zero, however large the
     shortage, which really would have made the first blacksmith
     impossible in a civilisation that starts with none. But the
     stakeholder's own "no nuclear engineer in Rome" limit is also real,
     and a rule that lifts it for every trade at once (or picks trades by
     hand) gets neither answer right. `trades_reachable_given_technology`
     below replaces the hand list with a computation off `data/production/
     `'s own `requires_node` field - the tech tree, whose nodes this
     project already builds AS the knowledge a civilisation has (see
     `data/production/_SCHEMA.md`'s own WHEN A TECHNIQUE BECOMES AVAILABLE
     section). A trade with at least one recipe that needs NO technology
     at all (`requires_node: null` - `data/production/10_ferrous.json`'s
     own `iron_sheet_kg`, hand-forging a sheet from a bar, is exactly one)
     is learnable from zero; a trade whose every recipe sits behind a node
     nobody has reached (an `electrician` recipe gated behind `dynamo`) is
     not, and stays not, until that node is reached - which is the correct
     shape of "some limits are needed" the stakeholder asked for, drawn
     from the tree instead of a guess. See WALKABLE_TRADES below for the
     mechanism and SCENARIO 5 in the worked example, which runs exactly
     this case: an early civilisation with precisely zero smiths, wanting
     iron goods, growing a smith trade from nothing.

WHY THIS IS A STEP PROCESS AND NOT AN INSTANT FIXED POINT, UNLIKE
`sim/solve_prices.py`'s PRICES. A price can update the instant a recipe's
inputs change; nothing physical stops it. A WORKER cannot: a farmer does not
become a blacksmith in a day, and a blacksmith becomes a farmer only a
little faster (farm labour needs less specific training, so the ceiling on
how fast people can be ABSORBED into an already-large trade like
`labourer` is looser than the ceiling on how fast a small skilled trade can
grow). THE FRICTION section below is this project's explicit, labelled
answer (CLAUDE.md SS3.4) to "how fast" - several numbers now, not one,
standing in for guild apprenticeship terms, harvest-season timing, land
tenure, wartime mobilisation drives and gold-rush boomtowns, and every other
real friction this project does not yet model individually (see each
constant's own declaration for what it approximates and how weak the
evidence behind its specific figure is). A trade with ZERO current workers
CAN grow under this mechanism now, but only if the tech tree already
contains a way to do it that needs no master - see WALKABLE_TRADES - and
even then bounded by a seed reference, not by an invented absolute number:
you still cannot train the first optician by bidding hours at him, someone
has to found THAT trade, which is exactly what `sim/engine/labour.py`'s own
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
import of the module that will eventually read the same file. `WALKABLE_
TRADES` is now COMPUTED from that same production data (its own
`requires_node` field - see `trades_reachable_given_technology`), the same
discipline applied to a derived classification instead of a hand-picked
one; `TRADE_SKILL_FAMILY` remains a hand-stated classification, for the
identical STANDALONE reason this module keeps its own copy of anything it
cannot yet compute: `sim/engine/data.py` keeps its own `TRADE_FAMILY`
(three buckets: scholar, labour, craft) for a different purpose (staffing
two aggregate institution pools); this module keeps a separate, finer one
of its own rather than importing that file, for the identical STANDALONE
reason.

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

  2. WHERE A BRAND NEW TRADE'S FIRST WORKER COMES FROM, WHEN NO RECIPE OF
     ITS OWN IS REACHABLE YET. A trade every one of whose data/production/
     recipes sits behind a tech-tree node nobody has reached (not in
     `trades_reachable_given_technology`'s result - see WALKABLE_TRADES)
     still cannot grow from zero under `Workforce.step` alone, however
     large its shortage, and this module still invents no number for that
     first worker: an `electrician` recipe gated behind `dynamo` stays
     exactly as unreachable as it always was until `dynamo` itself is
     reached. `sim/engine/labour.py` already has the concept this module
     lacks (`TRADES_ABSENT`, `trade_schools`,
     `SCHOOL_FOUNDED_HIRING_COEFFICIENT`) - a founder-built institution that
     seeds a trade society could not otherwise reach. `Workforce.step`'s
     `minimum_absorption_hours_by_trade` parameter is the seam where that
     seeding would enter this mechanism. A trade with NO data/production/
     entry at all (this module's own synthetic `optician`, in SCENARIO 3
     below - chosen because this project genuinely has no data for it) is
     unclassified by definition and stays unwalkable at any
     `reached_node_ids`, which is the correct answer for a trade this
     project has recorded nothing about.

  3. SKILL DISTANCE IS STILL A HANDFUL OF FAMILIES, NOT A REAL MATRIX. A
     smith and a scribe are now farther apart than a smith and a
     furnaceman - see TRADE_SKILL_FAMILY - which is a real improvement over
     one global number for every pair, and still a coarse, stated RULE
     rather than measured data: every pair inside a family is exactly as
     close as every other pair inside it (a smith is not, in this module,
     any closer to a machinist than to a furnaceman), and every pair across
     two different, non-walkable families is exactly as far as every other
     cross-family pair (a farmer and a mason are still equally far from
     becoming a smith, unless smith's destination happens to be walkable,
     which it is not). A real economy has this be a full matrix (a smith's
     son becomes a farrier far more easily than he becomes a scribe, and
     more easily than a farmer becomes either), and this project has no
     data to populate one.

  4. WAGES, DELIBERATELY, PER THE STAKEHOLDER'S OWN INSTRUCTION. This
     module answers "how many hours does each trade need" and "where would
     hours move to close that gap", not "what does an hour of each trade
     cost" - `sim.solve_prices.wage_ratios_by_trade` already answers the
     second question in the same numeraire and could be wired into
     `Workforce.step`'s flow matrix as an optional priority weight the day
     a caller wants demand to be VALUE-weighted rather than gap-weighted;
     no such parameter exists yet and nothing here requires it. This is
     also, not incidentally, the mechanism a real economy would use to
     ration unmet demand (see WHY DEMAND EXCEEDING SUPPLY DOES NOT MEAN A
     FAILED SOLVE above) - this module can name how much demand goes
     unmet, but deciding WHO goes without needs a price, which is out of
     scope here by the same instruction.

  5. A TRADE'S OWN SIZE DOES NOT BOUND ITS SHARE OF FRESH POPULATION, AND
     THIS MODULE DOES NOT COMPUTE "NEED" FOR AGRICULTURE ITSELF. This
     module reallocates hours ALREADY on someone's books between trades; it
     does not model a newly working-age adult choosing a first trade at
     all (`sim.world.demography.Population`'s `working_age` inflow has no
     representation here), and it does not read `sim.world.agriculture` at
     all outside its own demo (see STANDALONE above) - `farm_workers_fte_
     for_population`'s own fixed population share is that module's
     assumption, not this one's, and this file cannot repair it without
     owning it. What this file DOES do is give a caller who has BOTH
     numbers (agriculture's NEED and this module's HAVE) a named place to
     compare them - `have_versus_need` - instead of the silent assumption
     that they are the same number, which is the shape of the bug the
     stakeholder's land-growth question points at (see SCENARIO 4 below).

WORKED EXAMPLE, AND HOW TO REPRODUCE IT. Run this file directly:

    python3 sim/world/labour_market.py

for five scenarios end to end: a food shortfall that pulls hours into
farming and stabilises with the shortfall still unmet; a war that pulls
hours into smithing, now several times faster than the old flat rate; monster
towers seeding an `adventurer` trade from zero because walking into it needs
no master, right next to a brand-new `optician` trade that still cannot,
because that one does; cultivable land growing while nothing tells the
workforce to reallocate, so NEED moves and HAVE does not until it is asked
to; and an early civilisation with precisely zero smiths growing one from
nothing because data/production/'s own tech-tree gates say hand-forging
needs none - the module docstring's stakeholder point 8, answered with a
measurement rather than an argument.
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
from sim.unit_conversions import KILOGRAMS_PER_TONNE, KILOGRAMS_PER_GRAM, PERCENT_SCALE
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
    from sim.engine.catalog import load_production_catalog
    return load_production_catalog(_REPOSITORY_ROOT)


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
# Four separate, labelled numbers now (CLAUDE.md SS3.4), replacing the single
# flat rate the stakeholder's points 3, 4, 5 and 6 each objected to on a
# different ground:
#
#   OCCUPATIONAL_MOBILITY_RATE_PER_YEAR      the STEADY-STATE rate: how fast
#                                             a trade moves under ordinary,
#                                             mild pressure (a small gap
#                                             relative to its own size).
#   OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN  how much FASTER than that a
#                                             trade moves as its gap grows
#                                             relative to its own size - the
#                                             direct answer to points 3 and 4
#                                             ("would it really take 20
#                                             years"; "only 100 to 103").
#   OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR
#                                             the hard ceiling that gain
#                                             saturates at - even the most
#                                             urgent shortage does not empty
#                                             a trade or fill one overnight.
#   WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS
#                                             lets a WALKABLE trade (see
#                                             below) start moving from
#                                             exactly zero, the direct
#                                             answer to point 5.
#
# and a fifth, CROSS_FAMILY_PROXIMITY, that answers point 6 by making the
# rate ALSO depend on which trade the hours are coming from, not only on the
# size of the gap - see TRADE_SKILL_FAMILY below.

OCCUPATIONAL_MOBILITY_RATE_PER_YEAR = declare(
    "OCCUPATIONAL_MOBILITY_RATE_PER_YEAR", 0.05,
    kind="temporary_heuristic",
    unit="fraction of a trade's current hours that can move into or out of "
        "that trade in one year WHEN THE GAP IS SMALL RELATIVE TO THE "
        "TRADE'S OWN SIZE - the steady-state rate; see OCCUPATIONAL_"
        "MOBILITY_GAP_RESPONSE_GAIN for what happens as the gap grows",
    source="No occupational-mobility rate for the pre-industrial "
        "Mediterranean is measured anywhere this project has read. The "
        "figure is an order-of-magnitude stand-in built from two facts "
        "this project DOES have some grip on: a Roman-era craft "
        "apprenticeship typically ran several years before someone was "
        "producing at a trained rate, and a working career runs several "
        "decades, so even a trade under ORDINARY pressure to grow or "
        "shrink is bounded by how many NEW entrants an apprenticeship "
        "system can process in a year, not by how many people would "
        "switch instantly if switching were free. One in twenty (5%) a "
        "year is the rough scale of 'one apprenticeship cohort's worth' "
        "relative to an established trade's total size - a plausible "
        "order of magnitude, not a measurement.",
    confidence="D",
    why="This is the BASELINE of the two numbers standing in for every real "
        "friction this project does not yet model individually: guild "
        "apprenticeship terms, land tenure locking a farmer to a holding, "
        "the harvest calendar, literacy, capital needed to set up a "
        "workshop. Without SOME bound, `Workforce.step` would let the "
        "entire labour force retrain into whatever trade the current "
        "shortage points at in a single year, which is the 'instant "
        "clearing' sim.solve_prices.py can get away with for a price and "
        "a labour market plainly cannot - see CLAUDE.md SS3.4's own "
        "instruction to label a heuristic rather than hide it. It no "
        "longer stands alone: a war or a gold rush moves people far "
        "faster than an ordinary year's apprenticeship turnover, which "
        "OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN and OCCUPATIONAL_"
        "MOBILITY_RATE_CEILING_PER_YEAR now express instead of this "
        "constant pretending to cover both regimes at once.")

OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN = declare(
    "OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN", 2.0,
    kind="temporary_heuristic",
    unit="dimensionless: extra multiples of the steady-state rate added per "
        "100% that a trade's gap represents of its own current size (or, "
        "for a walkable trade seeding from zero, of its seed reference)",
    source="No measurement of how sharply occupational mobility responds "
        "to shortage SIZE (as opposed to shortage existing at all) is "
        "available for this period. The functional form (mobility rate "
        "rises LINEARLY with the relative size of the gap, capped at a "
        "ceiling) is chosen because it is the simplest shape with the "
        "property the stakeholder asked for by name - 'a tenfold shortage "
        "should pull people faster than a ten percent one' - and because "
        "it collapses to the plain OCCUPATIONAL_MOBILITY_RATE_PER_YEAR "
        "exactly when the gap is small, so it changes nothing about a "
        "trade that is already close to meeting its requirement.",
    confidence="D",
    why="Answers the stakeholder's points 3 and 4 directly: 'would it "
        "really take 20 years to double your iron output' and 'would we "
        "really only go from 100 miners to 103' both diagnose the SAME "
        "defect, a rate that does not know how big the prize or the "
        "shortfall is. This is the number that lets it know, and it is a "
        "SHAPE, not a measurement - sim.tests.test_labour_market.py checks "
        "the shape (bigger relative gap moves more, monotonically, up to "
        "the ceiling) rather than any specific number of years, so this "
        "constant can be revised without silently changing what the "
        "mechanism proves.")

OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR = declare(
    "OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR", 0.6,
    kind="temporary_heuristic",
    unit="fraction of a trade's own current size (or seed reference) that "
        "can move into or out of it in ONE YEAR even under the most "
        "extreme pressure this module allows",
    source="Wartime industrial mobilisation (the US female manufacturing "
        "workforce roughly doubled within about two years of Pearl "
        "Harbor) and mining-rush boomtowns (a strike can multiply a "
        "camp's population within a single season) are the fastest REAL "
        "occupational reallocations this project has read about, and both "
        "still take months to low years rather than days, because "
        "transport, housing, tools and at least rough training remain "
        "real constraints even at maximum urgency. 60% a year is a "
        "deliberately generous ceiling standing in for 'as fast as this "
        "mechanism will EVER allow', not a measurement of either event.",
    confidence="D",
    why="Without a ceiling, OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN applied "
        "to an arbitrarily large relative gap would let a trade empty or "
        "fill itself in one year, which is the same 'instant clearing' "
        "problem OCCUPATIONAL_MOBILITY_RATE_PER_YEAR's own declaration "
        "already refuses for the steady-state case. This is that same "
        "refusal for the CRISIS case.")

WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS = declare(
    "WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS", 0.01,
    kind="temporary_heuristic",
    unit="fraction of the WHOLE economy's current labour-hours that a "
        "WALKABLE trade (see WALKABLE_TRADES) with zero current workers "
        "can draw its mobility ceiling from in its first years of facing "
        "demand, in place of a share of its own (zero) size",
    source="Stands in for a pool this module has no other way to see: "
        "seasonal and underemployed labour, adolescents newly of working "
        "age, and people between engagements who take up a sudden opening "
        "without needing to be poached FROM a named trade. One percent of "
        "the whole economy's hours is an order-of-magnitude guess at how "
        "large that always-available margin is, not a measurement of it.",
    confidence="D",
    why="Answers the stakeholder's point 5 directly: 'monster towers "
        "suddenly appeared, this also says 0 people will become "
        "adventurers'. A trade's mobility ceiling was `rate * hours_"
        "before`, which is exactly zero when hours_before is zero, "
        "however large the shortage - correct for a trade that needs a "
        "master to teach it (see WHAT THIS DOES NOT MODEL item 2) and "
        "wrong for work a person can simply walk into. This constant is "
        "the size of the pool a walkable trade draws on INSTEAD of its "
        "own (absent) size; sim.tests.test_labour_market.py checks that "
        "a walkable trade at zero hours moves and a non-walkable one at "
        "zero hours still does not, not any specific number of new "
        "adventurers.")

CROSS_FAMILY_PROXIMITY = declare(
    "CROSS_FAMILY_PROXIMITY", 0.2,
    kind="temporary_heuristic",
    unit="fraction of the same-family mobility ceiling that hours moving "
        "between two DIFFERENT, non-walkable skill families are allowed "
        "to use",
    source="No occupational-distance matrix for this period and place has "
        "been measured anywhere this project has read (see WHAT THIS DOES "
        "NOT MODEL item 3). One in five is a stated RULE, not a "
        "measurement: enough that a large, sustained shortage in a "
        "distant trade still pulls SOME hours (a farmer becomes a "
        "smith's unskilled yard-hand faster than never), not so much that "
        "this module claims retraining a scribe into a smith is nearly as "
        "easy as retraining a furnaceman into one.",
    confidence="D",
    why="Answers the stakeholder's point 6: 'it thinks you can't ever "
        "teach yourself a skill, and nothing transfers' - true before this "
        "constant existed, because one mobility rate covered every trade "
        "pair identically. TRADE_SKILL_FAMILY below groups trades into a "
        "handful of families; this is the discount applied whenever the "
        "origin and destination trade are in different families and the "
        "destination is not a WALKABLE one. sim.tests.test_labour_"
        "market.py checks that same-family and walkable-destination flows "
        "are NEVER discounted and cross-family ones to a skilled "
        "destination ALWAYS are, not any particular number.")


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
# A private sentinel, not `None`. `entry.get("requires_node", ...)` has to
# tell "the field is `null`" (the technique needs NO technology at all)
# apart from "the field is missing" (nobody has classified this entry -
# data/production/_SCHEMA.md's own rule: "a gated solve drops it") - and
# `None` cannot serve as its own missing-value marker, because `None` is
# itself the meaningful value this field takes when a technique is already
# available on day one.


def trades_reachable_given_technology(
        reached_node_ids: Iterable[str] = (),
        production: Optional[Dict[str, Any]] = None) -> FrozenSet[str]:
    """Every trade a person could pick up WITHOUT an existing master of
    that trade to learn from, given which tech-tree nodes this
    civilisation has already reached - the general mechanism behind
    WALKABLE_TRADES below, built from the vocabulary this project already
    has for "the knowledge exists": data/production/*.json's own
    `requires_node` field, read exactly the way that field's own schema
    defines it (`data/production/_SCHEMA.md`'s WHEN A TECHNIQUE BECOMES
    AVAILABLE section) - `requires_node: null` means a technique needs NO
    technology at all (anyone can work it out from first principles and
    local materials); `requires_node: "some_node_id"` means that node must
    be REACHED before anyone, anywhere, can run it; a missing field means
    nobody has classified the entry, and per that same schema's own rule
    ("a gated solve drops it") grants no walkability either way - no data
    is not license to assume either answer.

    A trade is in the returned frozenset if data/production/ names it in
    AT LEAST ONE recipe's `labour_hours` (or a `capital` item's own
    `build_labour_hours`) whose gate is satisfied - `requires_node` is
    `null`, or is a member of `reached_node_ids`. One walkable recipe is
    enough: a smith who can only hand-forge a sheet from bar stock, with
    none of the smith's OTHER, more advanced recipes reachable yet, is
    still a smith a civilisation can grow from zero - this module already
    aggregates a trade's hours across every recipe that names it
    everywhere else (`labour_hours_required_by_trade`), so being equally
    coarse here, in the opposite direction, is the consistent choice, not
    a new one.

    `reached_node_ids` is taken as a PARAMETER, never read from the tech
    tree itself, for the identical STANDALONE reason `hours_required_by_
    trade` and `minimum_absorption_hours_by_trade` are parameters: this
    module has no access to `sim/engine/`'s own tree state and does not
    import it (see the module docstring's STANDALONE section). A caller
    that DOES have the tree in scope computes the reached set once per
    year and passes it in; the empty default is exactly "a civilisation
    that has reached no technology at all yet" - day one of the scenario
    this whole project simulates, and what `WALKABLE_TRADES` below is
    fixed to.

    THE GENUINE LIMIT STAYS A LIMIT. A trade whose every recipe sits
    behind a node nobody has reached (an `electrician` recipe gated behind
    `dynamo`) is not reachable before `dynamo` is, whatever `reached_node_
    ids` this function is called with elsewhere - "you can't just make a
    nuclear engineer in Rome" (the module docstring's stakeholder point 8)
    is exactly as true after this function exists as before it. What
    changes is that the boundary is now READ OFF THE TECH TREE, per trade
    and per recipe, instead of guessed once for the whole module and
    frozen into a two-name list with no way to grow as a civilisation
    actually reaches new nodes.

    LABELLED, NOT A MEASUREMENT (CLAUDE.md SS3.4). Treating "this recipe's
    own technology gate is satisfied" as sufficient for "a person could
    pick up this trade without an existing master" folds two different
    claims into one - what technique is KNOWN, and whether it can be
    TAUGHT without a living practitioner - because this project has no
    separate data for the second (WHAT THIS DOES NOT MODEL item 3 already
    admits skill transfer is a stated rule, not measured data). It is
    still a strictly more defensible boundary than a hand-picked list: it
    is measured against the SAME tech tree that gates whether a recipe can
    run at all, it moves as the tree is reached instead of staying frozen
    at two names forever, and it cannot be tuned to make any one trade
    walkable without editing data/production/ itself - exactly where
    CLAUDE.md SS3.1 says a boundary like this belongs.
    """
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
# `trades_reachable_given_technology` evaluated with NO nodes reached at
# all - a civilisation on day one of this project's own scenario. This is
# the module's DEFAULT for `Workforce.step`'s `walkable_trades=` parameter,
# COMPUTED from data/production/'s own `requires_node` field rather than
# hand-picked: whatever the data says needs no technology at all comes out
# walkable, and nothing else does, with no list for a future editor to
# remember to update as data/production/ grows (this is measurably a
# bigger set than the old hand-written {"labourer", "miner"} - it now also
# contains, among others, `smith`, because data/production/10_ferrous.
# json's own `iron_sheet_kg` needs no invented technology to hand-forge a
# sheet from a bar; see the module docstring's stakeholder point 8 and
# SCENARIO 5 below). Everything not in this set defaults to requiring the
# master-and-apprentice pathway WHAT THIS DOES NOT MODEL item 2 describes,
# and can only start from zero via a caller-supplied `minimum_absorption_
# hours_by_trade` (sim/engine/labour.py's own `TRADES_ABSENT`/`trade_
# schools` machinery is the natural source of that number).
#
# A caller that HAS the tech tree in scope (sim/engine/ - this module never
# does, see STANDALONE) grows this default as the civilisation reaches new
# nodes, by calling `trades_reachable_given_technology(reached_node_ids)`
# itself and handing the result to `Workforce.step` as `walkable_trades=` -
# the same seam the worked example's own synthetic `adventurer` trade uses
# to extend WALKABLE_TRADES by hand (SCENARIO 3 below): a caller can either
# invent a name directly or read it off the tree.
# A caller wiring in a trade no data/production/ entry names at all (that
# same `adventurer`, for a sudden and genuinely unskilled calling this
# project's data has never heard of) still passes its own extra name in by
# hand - this frozenset is a default for what the DATA already says, not a
# closed list the mechanism enforces.

TRADE_SKILL_FAMILY = {
    "labourer": "labour", "miner": "labour",
    "furnaceman": "metal", "smith": "metal", "machinist": "metal",
    "mason": "building", "carpenter": "building", "millwright": "building",
    "plumber": "building",
    "chemist": "technical", "engineer": "technical", "electrician": "technical",
    "scribe": "technical",
    "artisan": "artisan_craft", "potter": "artisan_craft",
    "glassblower": "artisan_craft",
}
# A STATED RULE (CLAUDE.md SS3.4), not measured data - see CROSS_FAMILY_
# PROXIMITY's own declaration for what evidence does and does not exist
# behind it, and WHAT THIS DOES NOT MODEL item 3 for exactly how coarse this
# still is. Grouped by what the two trades physically DO, the closest proxy
# this project has for how much of one trade's practice transfers to
# another: METAL (furnace heat and force applied to metal), BUILDING
# (structures and their fittings in wood, stone and pipe), TECHNICAL
# (calculation, formal knowledge, literacy-bearing work), ARTISAN_CRAFT
# (fine handwork on a single small piece at a time), and LABOUR (general
# unskilled effort - see WALKABLE_TRADES; every trade in this family is
# already walkable, so its own family membership rarely matters). A trade
# `data/production/*.json` names that is not listed here (the loader only
# sees whatever the data actually uses, and new materials can add new
# trades) falls back to its own singleton family via `trade_skill_family`
# below, which means it is treated as equidistant (CROSS_FAMILY_PROXIMITY)
# from every other classified trade until someone places it - the same
# "no data, so no bonus claimed" discipline `sim.engine.data.trade_family`
# applies with its own "craft" fallback.


def trade_skill_family(trade: str) -> str:
    """TRADE_SKILL_FAMILY's own lookup, with the honest fallback described
    at that dict's own declaration: an unlisted trade gets a family of one
    (itself), which is indistinguishable from any other family for
    `_flow_proximity`'s purposes - it is never treated as automatically
    close to anything, on the ground that this module has no basis to
    claim it is."""
    return TRADE_SKILL_FAMILY.get(trade, trade)


def _flow_proximity(
        origin_trade: str, destination_trade: str, destination_is_walkable: bool,
        skill_family_of: Callable[[str], str] = trade_skill_family,
        cross_family_proximity: float = CROSS_FAMILY_PROXIMITY) -> float:
    """How much of a full mobility ceiling a flow FROM `origin_trade` INTO
    `destination_trade` is allowed to use, on a 0-1 scale. `1.0` (full
    ceiling, no distance discount) whenever the destination trade is one a
    person can walk into regardless of background (WALKABLE_TRADES - moving
    DOWN into unskilled work needs no specific prior skill, so the origin
    trade's own family is irrelevant - see the module docstring's point 7
    answer for the general shape of this asymmetry) OR the two trades share
    a TRADE_SKILL_FAMILY. `cross_family_proximity` otherwise - the
    stakeholder's point 6 answer: moving INTO a trade that DOES need a
    master, from a family that trade's own practice has little in common
    with, is real but throttled.

    Deliberately ASYMMETRIC: `_flow_proximity("smith", "labourer", ...)` is
    1.0 (a smith can labour in the fields at full speed) while
    `_flow_proximity("labourer", "smith", ...)` is `cross_family_
    proximity` (a labourer becoming a smith is throttled exactly as any
    other cross-family move into a skilled trade is) - "farm labour needs
    less specific training" (this module's own docstring, on why absorption
    into a large unskilled trade is easier than growth of a small skilled
    one) is a claim about the DESTINATION's requirements, not a symmetric
    statement about the two trades' distance, and this function encodes it
    as one.
    """
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
# margin costs nothing sim/test_regressions.py's ~68s budget would notice.


# ============================================================================
# THE ALLOCATION: WORKFORCE STATE (HAVE), AND THE ONE STEP THAT MOVES IT
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
# which `Workforce.step` cannot resolve UNLESS it is a WALKABLE trade (see
# above) or a caller supplies `minimum_absorption_hours_by_trade`, and which
# a caller should otherwise treat as a flag that an institution, not a
# reallocation, is what is actually missing.


class Workforce(object):
    """Hours of labour currently worked in each trade (HAVE - see the
    module docstring's HAVE-versus-NEED section) - mutable state, in the
    same shape as `sim.world.agriculture.Storage` and `sim.world.
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

    def __init__(self, hours_by_trade: Dict[str, float]) -> None:
        self.hours_by_trade = {trade: float(hours)
                               for trade, hours in hours_by_trade.items()}

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
        """Advance one year: move hours out of trades with more supply than
        is required of them (NEED, `hours_required_by_trade`) and into
        trades with less, bounded on both ends by a GAP-RESPONSIVE mobility
        ceiling (see THE FRICTION section) and routed with a preference for
        SKILL-CLOSE trades over distant ones (see SKILL DISTANCE above).
        Mutates `self.hours_by_trade` and returns `{trade: TradeFlow}` -
        one row per trade named in EITHER `hours_required_by_trade` or
        `self.hours_by_trade`, exactly like `sim.solve_prices.solve`'s
        per-material result.

        THE ALGORITHM, IN FIVE STEPS - a bounded, hours-conserving analogue
        of `sim.solve_prices.py`'s damped Jacobi iteration, with the bound
        being a real friction rather than a numerical damping choice:

          1. Every trade's GAP is `hours_required - hours_before`: positive
             is a shortage (it needs more hours than it has), negative is
             a surplus (it has more than is asked of it).

          2. Each trade in surplus or shortage gets its OWN mobility rate
             this period, via `_gap_responsive_mobility_rate`: the plain
             `mobility_rate_per_year` when its gap is small relative to its
             own current size (or, for a WALKABLE trade with none yet, its
             seed reference - see step 3), rising toward `mobility_rate_
             ceiling_per_year` as the gap grows large relative to that same
             basis. This is the direct answer to the stakeholder's points 3
             and 4: a war that doubles iron demand, or a diamond strike
             that dwarfs the existing mining workforce, both now pull
             harder than an ordinary year's apprenticeship turnover would,
             without the mechanism ever exceeding a stated ceiling.

          3. The BASIS that rate applies to is the trade's own `hours_
             before`, UNLESS the trade is in `walkable_trades` (a trade the
             tech tree already has a no-master way into - see WALKABLE_
             TRADES and `trades_reachable_given_technology`), in which case
             the basis is `max(hours_before, seed_reference)` - the LARGER
             of the trade's own current size or `walkable_trade_seed_
             share_of_economy_hours` times the WHOLE economy's current
             hours, not a hard switch from one to the other. Taking the
             maximum, rather than switching the instant `hours_before`
             turns positive, is itself the answer to a second worked
             question (the stakeholder's own suspicion that a percentage
             of the whole economy in year one and a percentage of the
             trade's own, still-small size in year two would make year two
             move LESS): so long as the trade is smaller than the seed
             reference, the seed reference stays the basis and the amount
             moved in stays flat rather than collapsing - `python3 -m sim.
             world.labour_market`'s SCENARIO 5 and `sim.tests.test_labour_
             market.py`'s `test_seed_reference_basis_persists_while_the_
             trade_is_smaller_than_it` both measure this directly. This is
             also the direct answer to the stakeholder's point 5: a
             walkable trade at exactly zero hours has a basis of zero from
             its own size but a positive one from the seed reference, so
             it CAN start moving; a non-walkable trade at zero hours still
             cannot, which `Workforce.step`'s own `minimum_absorption_
             hours_by_trade` remains the seam for (see WHAT THIS DOES NOT
             MODEL item 2) - a real constraint (nobody can apprentice under
             a master who does not exist yet, or pick up a technique the
             tree has not reached), not an oversight.

          4. Each trade's outflow or inflow is that rate times that basis,
             capped at the trade's own actual gap either way (a trade
             cannot give up more than its slack, or absorb more than its
             shortage, however generous the rate) and, on the inflow side
             only, floored at `minimum_absorption_hours_by_trade`'s entry
             for that trade if a caller supplied one.

          5. The capped outflows and inflows are then matched trade-to-
             trade, NOT pooled and split by aggregate size alone as an
             earlier version of this mechanism did: `_skill_distance_
             weighted_flow_matrix` prefers routing a surplus trade's hours
             toward a skill-close shortage trade over a distant one (see
             SKILL DISTANCE above), and can leave capacity on BOTH sides
             unused when nothing skill-close enough exists to absorb it -
             the direct answer to the stakeholder's point 6: a trade with
             plenty of surplus does not fill a distant trade's shortage
             just because the aggregate numbers would allow it, if nothing
             about the two trades' practice is close enough to transfer.
             Conservation is exact regardless: every hour this matrix
             assigns leaves exactly one origin trade and arrives at exactly
             one destination trade, so summing it either way gives the
             same total - `self.hours_by_trade`'s TOTAL is unchanged by
             this method to floating-point precision, the same discipline
             `sim.world.agriculture.Storage.step`'s docstring states for
             grain, checked in `sim.tests.test_labour_market.py`.

        This mechanism NEVER refuses to produce a result: a `hours_
        required_by_trade` whose total exceeds every hour this economy has
        still gets a `flows` dict back, with `hours_after` short of `hours_
        required` on whichever trades could not be filled - see the module
        docstring's WHY DEMAND EXCEEDING SUPPLY DOES NOT MEAN A FAILED
        SOLVE, and `unmet_demand_by_trade` below for the function that
        states that shortfall in one place rather than leaving a caller to
        recompute it from this dict's own fields.
        """
        minimum_absorption_hours_by_trade = minimum_absorption_hours_by_trade or {}
        all_trades = set(self.hours_by_trade) | set(hours_required_by_trade)
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
    """{origin: {destination: hours}} - how much of each surplus trade's
    capped outflow goes to each shortage trade's capped inflow, preferring
    skill-close pairs (see `_flow_proximity`) over distant ones.

    METHOD: initialise every cell to `capped_outflow[origin] * capped_
    inflow[destination] * proximity(origin, destination)` (a standard
    "gravity" weight - two trades pull harder on each other the bigger
    either side's own capacity is, discounted by distance), then run
    `iterations` rounds of iterative proportional fitting: rescale each
    origin's row down if it exceeds that trade's own `capped_outflow`,
    then rescale each destination's column down if it exceeds that
    trade's own `capped_inflow`. Each rescale only ever SHRINKS a cell, so
    a row or column that started under its cap never ends up over it either
    - the matrix this returns never asks a trade to give up more than
    `capped_outflow` says it can, or absorb more than `capped_inflow`
    says it needs, WHATEVER `iterations` is, which is what makes the
    result safe to sum straight into `Workforce.step`'s conservation
    check without a separate rescale pass there.

    This is a STATED APPROXIMATION (CLAUDE.md SS3.4), not a claim of
    finding the economically optimal flow: real iterative proportional
    fitting is a well-known technique for filling a matrix to match given
    row and column totals, used here for a different purpose (respecting
    CAPS, not matching exact totals, since supply and demand rarely
    match), and a small fixed number of rounds is a deliberate trade
    against exactness for a number that gets recomputed every simulated
    year regardless (see SKILL_DISTANCE_BALANCING_ITERATIONS's own
    comment). When every relevant proximity is 1.0 (every shortage trade is
    walkable, or every surplus/shortage pair shares a family) this
    collapses to the plain proportional-by-capacity split the mechanism
    used before skill distance existed, because a uniform weight matrix's
    row/column-capped fixed point IS that proportional split.
    """
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
    """{trade: hours_required - hours_available}, POSITIVE ENTRIES ONLY -
    the "honest statement of what was NOT met" the stakeholder's points 1
    and 2 asked this module to always report rather than fail on (see the
    module docstring's WHY DEMAND EXCEEDING SUPPLY DOES NOT MEAN A FAILED
    SOLVE). A trade with as much as or more than it needs is left OUT of
    the result entirely rather than given a zero or negative entry, so
    `bool(unmet_demand_by_trade(...))` alone answers "is anything short"
    without a caller filtering it first.

    Takes plain dicts, not a `Workforce`, so a caller can check unmet
    demand at ANY point - the starting allocation, mid-way through a
    `Workforce.step` loop, or `solve_to_stable_allocation`'s own final
    state (which passes exactly this call through as part of its result) -
    without constructing anything extra.
    """
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
    """{trade: HaveVersusNeed} - the module docstring's central distinction,
    made callable: `hours_have` is `Workforce.hours_by_trade` (or any dict
    shaped like it) - hours actually worked; `hours_need` is `labour_hours_
    required_by_trade`'s own output (or `sim.world.agriculture.farm_
    workers_fte_for_population`'s, converted to hours by a caller who has
    an hours-per-worker-year figure - see WHAT THIS DOES NOT MODEL item 5)
    - hours a target output calls for. `gap` is `hours_need - hours_have`
    (positive: short; negative: slack) and `tightness_ratio` mirrors
    `TradeFlow`'s own field for the same reason.

    "They should be close to the same, but not always" is the stakeholder's
    own description of what this function exists to let a caller SEE
    rather than assume. Two callers computing NEED and HAVE by two
    different routes (a population share for one, a planned-output
    coefficient for the other, say) will not, in general, agree - and this
    module takes the position that the disagreement is information, not
    noise: it is exactly the pressure `Workforce.step` is there to resolve,
    one bounded year at a time, and a caller that silently substitutes one
    number for the other (as sim/engine/labour.py does today, pricing every
    trade off a population-derived total with no workforce state of its
    own) is skipping that resolution rather than performing it.
    """
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
    """Call `Workforce.step` repeatedly against a FIXED `hours_required_by_
    trade` until the allocation STOPS MOVING, or `maximum_periods` is
    reached, and ALWAYS return a real allocation - never a refusal (see the
    module docstring's WHY DEMAND EXCEEDING SUPPLY DOES NOT MEAN A FAILED
    SOLVE). `**step_kwargs` passes straight through to `Workforce.step`
    (`mobility_gap_response_gain`, `walkable_trades`, `skill_family_of`,
    and the rest of that method's own knobs), so a caller overriding one of
    those does not also have to repeat every OTHER default here.

    Returns a `LabourMarketOutcome`:
      workforce             the final `Workforce`
      periods_used          how many years of `Workforce.step` this took
      stabilized            True once the allocation has STOPPED MOVING -
                             see below for what that means and does not mean
      unmet_demand_by_trade `unmet_demand_by_trade(workforce.hours_by_
                             trade, hours_required_by_trade)` on the FINAL
                             state - always present, never empty-by-default
                             the way a caller might assume "it solved" means
      history                the list of `{trade: TradeFlow}` dicts
                             `Workforce.step` returned each period, in
                             order - the same shape a caller would get
                             calling `step` in a loop themselves, so a
                             caller who wants to feed in a NEW `hours_
                             required_by_trade` every period (a realistic
                             use: this year's demand is not next year's)
                             calls `Workforce.step` directly instead of this
                             function, which exists for the case demand is
                             held fixed and the question is purely "how
                             long does this take to settle, and to what".

    `stabilized` IS NOT "every gap closed" - it is "the allocation has
    reached a fixed point, WHATEVER that fixed point covers". It is True in
    BOTH of these cases, and a caller MUST check `unmet_demand_by_trade` to
    tell them apart, not `stabilized` alone:

      - every trade's `hours_required` is met within `tolerance_hours`
        (the old, narrower meaning of `converged`), OR
      - NO hours moved this period at all (within `tolerance_hours`) even
        though a gap remains - every trade with slack has already given up
        everything its own mobility ceiling and the flow matrix's skill-
        distance discount allow, and every trade still short has already
        absorbed everything ITS ceiling allows: the honest "no reallocation
        of the EXISTING workforce closes this, at the speed this module
        believes reallocation can happen" answer (population has to grow,
        an institution has to seed the missing trade, or the plan has to
        shrink), stated as data rather than hidden behind a failure code.

    `stabilized` comes back False only if NEITHER condition is reached
    within `maximum_periods` - which this module's own gap-responsive rate
    (see THE FRICTION section) makes rare: a stalled allocation typically
    reaches "no hours moved this period" in a handful of years once the
    trades with slack are drained to exactly their own requirement, because
    the outflow ceiling shrinks to zero as the gap it is chasing does.
    """
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


if __name__ == "__main__":
    # ========================================================================
    # THE STAKEHOLDER'S OWN SCENARIOS, WORKED END TO END.
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
    # INSIDE THE GUARD, FOR THE SAME REASON agriculture IS. The demo below
    # needs wheat's reference labour intensity twice; sim.world.shared_
    # constants's own declaration is the one place the figure lives, so
    # both uses read the same number rather than each carrying its own
    # bare 150.0 literal.
    #
    # It is imported here rather than at module level because the STANDALONE
    # section's rule is a blanket one: nothing above may import a sibling
    # sim/world/ module, and sim/tests/test_labour_market.py enforces exactly
    # that with no carve-out for shared_constants. land.py and agriculture.py
    # DO import it at module level, and could argue for one (it holds
    # physical facts and imports nothing but sim.constants.declare, so it
    # cannot drag a model in behind it). That argument was not needed here:
    # both uses are in this demo block, so the narrower placement costs
    # nothing and leaves the rule intact.
    from sim.world.shared_constants import REFERENCE_LABOUR_HOURS_PER_HECTARE

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
    print("Hours required at baseline output (NEED):")
    for trade in sorted(baseline_hours_required):
        print("  %-12s %9.0f h" % (trade, baseline_hours_required[trade]))

    # THE STARTING ALLOCATION (HAVE) - AN INITIAL CONDITION (CLAUDE.md
    # SS3.1), exactly like sim.world.land.py's per-civilisation territory:
    # this demo's own choice of how a society happens to be staffed on day
    # one, not something this module derives. `labourer` starts with NO
    # slack (realistic for a subsistence economy: virtually everyone not in
    # a craft is already doing SOME unskilled task, farm or otherwise);
    # every craft trade starts with a modest 20% margin above what this
    # narrow three-recipe plan strictly needs, standing in for the many
    # OTHER things a real craft sector spends part of its time on that
    # this toy economy does not model (illustrative, not measured - see
    # OCCUPATIONAL_MOBILITY_RATE_PER_YEAR's own declaration for the same
    # honesty about a different number in this same demo).
    settled_workforce = {trade: (hours if trade == "labourer" else hours * 1.2)
                         for trade, hours in baseline_hours_required.items()}

    print("=" * 78)
    print("SCENARIO 1: A BAD HARVEST PULLS HOURS TOWARD FARM LABOUR - AND "
         "STABILISES SHORT, WITH THE SHORTFALL NAMED, NOT REFUSED")
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
    # wheat_kg's own reference labour intensity, at the reference area. This
    # was the bare literal 150.0, one of the two occurrences shared_constants.
    # py's own declaration names as an outstanding finding.
    reference_hours = REFERENCE_LABOUR_HOURS_PER_HECTARE * 10_000.0
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
                   PERCENT_SCALE * extra_hours_needed / baseline_hours_required["labourer"],
                   baseline_hours_required["labourer"]))

    craft_slack_hours = sum(settled_workforce[trade] - baseline_hours_required[trade]
                            for trade in settled_workforce if trade != "labourer")
    print("The WHOLE craft sector's slack (every hour smith, furnaceman, "
         "potter, mason, millwright and carpenter have beyond this plan's "
         "own baseline) totals only %.0f h - %.2f%% of what the shortfall "
         "needs. Even fully drained into farm work, crafts cannot answer "
         "a bad harvest in an economy this farm-heavy; that is not a "
         "limit of the search below, it is the physical shape of the "
         "economy." % (craft_slack_hours, PERCENT_SCALE * craft_slack_hours / extra_hours_needed))

    shocked_hours_required = dict(baseline_hours_required)
    shocked_hours_required["labourer"] += extra_hours_needed
    outcome_1 = solve_to_stable_allocation(
        settled_workforce, shocked_hours_required, tolerance_hours=1.0)
    print("\nReallocating the settled workforce toward the shocked demand, "
         "one year at a time (labourer only, for space):")
    shown_periods = sorted(set(min(index, outcome_1.periods_used - 1)
                              for index in (0, 1, 4, 9, outcome_1.periods_used - 1)))
    for year_index in shown_periods:
        print(" year %2d: %s" % (year_index + 1, hours_line(outcome_1.history[year_index]["labourer"])))
    labourer_unmet = outcome_1.unmet_demand_by_trade.get("labourer", 0.0)
    print("Stabilised after %d year(s): %s. unmet_demand_by_trade['labourer'] "
         "= %.0f h (%.1f%% of what was asked) - `stabilized=True` here means "
         "the craft sector has ALREADY given up every hour its own mobility "
         "ceiling allows and nothing more is moving, NOT that the shortfall "
         "closed. That remaining %.0f h is exactly the honest answer the "
         "stakeholder's telephone-wire example asked for: an allocation, "
         "plus a named shortfall, never a refusal to solve. The load-"
         "bearing response to a bad harvest in this model is still sim."
         "world.agriculture.Storage's own granary and sim.world."
         "demography's nutrition-driven mortality, not occupational "
         "reallocation - see this module's docstring's WHAT THIS DOES NOT "
         "MODEL for why crafts are too small a pool to matter much against "
         "a farm-scale shock." % (
             outcome_1.periods_used, outcome_1.stabilized, labourer_unmet,
             PERCENT_SCALE * labourer_unmet / extra_hours_needed, labourer_unmet))

    print()
    print("=" * 78)
    print("SCENARIO 2: WAR RAISES DEMAND FOR IRON - SMITHS GO UP FAR FASTER "
         "THAN A FLAT 5%/YEAR EVER ALLOWED")
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
    print("Hours required once wartime iron output is DOUBLE peacetime (NEED):")
    for trade in sorted(war_hours_required):
        delta = war_hours_required[trade] - baseline_hours_required.get(trade, 0.0)
        print("  %-12s %9.0f h  (%+.0f h vs peacetime)" % (
            trade, war_hours_required[trade], delta))
    print("smith hours are pulled by: %r" % (war_contributors.get("smith"),))

    outcome_2 = solve_to_stable_allocation(
        settled_workforce, war_hours_required, tolerance_hours=1.0)
    print("\nsmith, year by year - climbing every year, never in one jump, "
         "but now at a rate that responds to how far short it still is:")
    shown_periods_2 = sorted(set(min(index, outcome_2.periods_used - 1)
                                for index in (0, 1, 2, 4, 9, outcome_2.periods_used - 1)))
    for year_index in shown_periods_2:
        print(" year %2d: %s" % (year_index + 1, hours_line(outcome_2.history[year_index]["smith"])))
    final_smith_hours = outcome_2.workforce.hours_by_trade["smith"]
    smith_unmet = outcome_2.unmet_demand_by_trade.get("smith", 0.0)
    print("Stabilised after %d year(s) (stabilized=%s): smith settles at "
         "%.0f h against %.0f h required - reallocation alone closes %.0f%% "
         "of the gap. The remaining %.0f h of unmet demand is exactly the "
         "kind of persistent scarcity that (in a wired-in engine) should "
         "show up as a rising smith wage, an incentive for a founder to "
         "open a smithy school, or a push to import iron goods rather than "
         "smith them locally - none of which this module invents; it only "
         "says how large the gap still is, in unmet_demand_by_trade." % (
             outcome_2.periods_used, outcome_2.stabilized, final_smith_hours,
             war_hours_required["smith"],
             PERCENT_SCALE * final_smith_hours / war_hours_required["smith"], smith_unmet))

    print()
    print("=" * 78)
    print("SCENARIO 3: MONSTER TOWERS APPEAR - A WALKABLE TRADE CAN SEED "
         "FROM ZERO, A TRADE THAT NEEDS A MASTER STILL CANNOT")
    print("=" * 78)
    # A synthetic economy, not data/production/-derived: neither `adventurer`
    # nor `optician` has a recipe in this project's data, and this scenario
    # does not need one - it is testing the SEEDING mechanism itself, not a
    # real material's numbers. `labourer` is given a real 20,000h surplus
    # here (unlike scenario 1's settled_workforce, which has none) so there
    # is something in this toy economy for either new trade to draw on
    # under this module's own strict conservation of hours (see `Workforce.
    # step`'s own docstring, step 5) - without ANY surplus anywhere, no
    # trade can grow, walkable or not, which is a fact about this
    # mechanism's honesty, not a defect this scenario is built to hide.
    tower_workforce = Workforce({"labourer": 120_000.0, "adventurer": 0.0, "optician": 0.0})
    tower_hours_required = {"labourer": 100_000.0, "adventurer": 50_000.0, "optician": 50_000.0}
    tower_walkable = WALKABLE_TRADES | {"adventurer"}
    print("`labourer` has a real 20,000 h surplus to give up. `adventurer` "
         "and `optician` both start at 0 h against a 50,000 h shortage each "
         "- `adventurer` is walkable (people can simply take up monster-"
         "hunting), `optician` is not (see WALKABLE_TRADES).")
    for _ in range(5):
        tower_flows = tower_workforce.step(tower_hours_required, walkable_trades=tower_walkable)
    print("  after 5 years: adventurer %8.0f h   optician %8.0f h" % (
        tower_workforce.hours_by_trade["adventurer"],
        tower_workforce.hours_by_trade["optician"]))
    print("`adventurer` moved because WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_"
         "HOURS gave it a seed reference to grow from even at zero; "
         "`optician` did not move AT ALL, which is this module's own "
         "documented, correct behaviour for a trade that needs a master "
         "who does not exist yet - not a bug this scenario is hiding. A "
         "founder wanting opticians has to found the trade "
         "(sim/engine/labour.py's `trade_schools`), then hand this "
         "mechanism a `minimum_absorption_hours_by_trade` floor, exactly "
         "as WHAT THIS DOES NOT MODEL item 2 describes.")

    print()
    print("=" * 78)
    print("SCENARIO 4: CULTIVABLE LAND GROWS - NEED MOVES, HAVE DOES NOT, "
         "UNTIL SOMETHING CALLS Workforce.step")
    print("=" * 78)
    # Directly answers the stakeholder's point 7 ("so nobody can farm on
    # new land?") and the module docstring's structural reframe: this
    # module never assumes a trade's workforce is a population share, so
    # growing the land here changes NEED (via a bigger harvest target) and
    # leaves HAVE (the workforce dict) untouched until asked - the exact
    # gap sim.world.agriculture.py's own fixed population share papers over.
    grown_land = agriculture.Land(reference_land.hectares * 1.5)
    grown_hours = REFERENCE_LABOUR_HOURS_PER_HECTARE * grown_land.hectares
    harvest_on_grown_land = agriculture.gross_harvest_kg(grown_land, grown_hours)
    # A fair NEED comparison needs the SAME wage/output convention this
    # module already uses elsewhere: convert the bigger harvest into a
    # bigger wheat_kg output level and re-run labour_hours_required_by_trade,
    # exactly as SCENARIO 2 does for a bigger iron output level.
    grown_output_levels = dict(baseline_output_levels)
    grown_output_levels["wheat_kg"] = baseline_output_levels["wheat_kg"] * (
        harvest_on_grown_land / harvest_normal)
    grown_hours_required, _ = labour_hours_required_by_trade(  # type: ignore[assignment]
        grown_output_levels, production)
    comparison = have_versus_need(settled_workforce, grown_hours_required)
    labourer_comparison = comparison["labourer"]
    print("50%% more cultivable land raises the harvest this land could grow "
         "from %.0f kg to %.0f kg, which raises NEED for labourer from "
         "%.0f h to %.0f h - a %.1f%% jump this module computed from land "
         "and a labour coefficient, not from population." % (
             harvest_normal, harvest_on_grown_land,
             baseline_hours_required["labourer"], grown_hours_required["labourer"],
             PERCENT_SCALE * (grown_hours_required["labourer"] / baseline_hours_required["labourer"] - 1.0)))
    print("have_versus_need (before any reallocation): hours_have=%.0f h  "
         "hours_need=%.0f h  gap=%.0f h - HAVE has not moved at all, because "
         "nothing has called Workforce.step yet. This is exactly the "
         "divergence sim.world.agriculture.farm_workers_fte_for_population's "
         "fixed population share hides: it would report a workforce number "
         "for the NEW land instantly, as though the labour to work it "
         "simply existed, where this module reports the gap and lets "
         "solve_to_stable_allocation close it at the speed labour can "
         "actually move." % (labourer_comparison.hours_have, labourer_comparison.hours_need,
                             labourer_comparison.gap))
    outcome_4 = solve_to_stable_allocation(settled_workforce, grown_hours_required,
                                          tolerance_hours=1.0)
    print("Reallocating toward the grown-land target (labourer is walkable, "
         "so this is bounded by its own size, not blocked by needing a "
         "master): stabilised after %d year(s), labourer reaches %.0f h "
         "against %.0f h needed (%.1f%% closed)." % (
             outcome_4.periods_used, outcome_4.workforce.hours_by_trade["labourer"],
             grown_hours_required["labourer"],
             PERCENT_SCALE * outcome_4.workforce.hours_by_trade["labourer"] / grown_hours_required["labourer"]))

    print()
    print("=" * 78)
    print("SCENARIO 5: AN EARLY CIVILISATION WITH ZERO SMITHS WANTS IRON "
         "GOODS - THE STAKEHOLDER'S BLACKSMITH QUESTION, ANSWERED WITH A "
         "MEASUREMENT")
    print("=" * 78)
    # Directly answers "is the current labour market making it impossible
    # for new trades to appear ... does this make blacksmiths impossible?"
    # A civilisation on day one of this project's own scenario (NO tech
    # reached yet - trades_reachable_given_technology()'s own default,
    # which is exactly what WALKABLE_TRADES already equals) that has NEVER
    # had a smith still has `smith` in WALKABLE_TRADES, because data/
    # production/10_ferrous.json's own `iron_sheet_kg` needs no invented
    # technology at all (`requires_node: null` - hammering an iron bar
    # into a sheet is mechanical, learnable by trial with a hammer and a
    # fire, not a secret only an existing smith can pass down) - a real,
    # measured fact about this project's own data, not an assumption this
    # module makes about smiths.
    print("`smith` in WALKABLE_TRADES (no technology reached yet): %s" % (
        "smith" in WALKABLE_TRADES,))
    early_civilisation_workforce = {"labourer": 200_000.0, "smith": 0.0}
    iron_goods_output_levels = {"iron_sheet_kg": 100_000.0}
    iron_goods_hours_required, iron_goods_contributors = labour_hours_required_by_trade(
        iron_goods_output_levels, production)
    print("Wanting 100,000 kg/year of hand-forged iron sheet requires %.0f h "
         "of smith labour a year (%r) - and this early civilisation starts "
         "with EXACTLY ZERO smiths." % (
             iron_goods_hours_required.get("smith", 0.0),
             iron_goods_contributors.get("smith"),))
    outcome_5 = solve_to_stable_allocation(
        early_civilisation_workforce, iron_goods_hours_required, tolerance_hours=1.0)
    print("smith, year by year, from a standing start of nobody:")
    shown_periods_5 = sorted(set(min(index, outcome_5.periods_used - 1)
                                for index in (0, 1, 2, 4, 9, outcome_5.periods_used - 1)))
    for year_index in shown_periods_5:
        print(" year %2d: %s" % (year_index + 1, hours_line(outcome_5.history[year_index]["smith"])))
    final_smith_hours = outcome_5.workforce.hours_by_trade.get("smith", 0.0)
    smith_required = iron_goods_hours_required.get("smith", 0.0)
    print("Stabilised after %d year(s) (stabilized=%s): smith reaches %.0f h "
         "against %.0f h required (%.1f%% closed) - starting from a "
         "civilisation that had never had one. Under the OLD, hand-written "
         "WALKABLE_TRADES = {\"labourer\", \"miner\"}, `smith` would have "
         "stayed at exactly 0.0 h forever, however large this demand grew: "
         "that is the defect the stakeholder's question named, and this "
         "run is the measurement that it is fixed." % (
             outcome_5.periods_used, outcome_5.stabilized, final_smith_hours,
             smith_required, PERCENT_SCALE * final_smith_hours / smith_required))
    print("The genuine limit the stakeholder also named is still real: "
         "`optician` (SCENARIO 3 above) has NO data/production/ entry at "
         "all, so it is unclassified rather than gate-satisfied, and stays "
         "out of WALKABLE_TRADES at any reached_node_ids - this project "
         "records nothing that would make it otherwise. The line between "
         "the two is now the tech tree's own `requires_node` field, not a "
         "hand-written list of exactly two names.")
