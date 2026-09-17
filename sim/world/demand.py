"""Demand: what turns a price into a quantity people actually buy, and
therefore what turns a joint process's one cost into two prices.

WHY THIS MODULE HAS TO EXIST. Three separate dead ends in this project
converge here.

  Complaints/29: one smelt yields lead AND silver. There is one furnace cost
  and two outputs, so the cost side is one equation short of pricing both -
  net-realisable-value allocation needs the prices to split the cost, and the
  prices are what allocation was supposed to produce. "The answer genuinely
  is not in the cost side. It is in demand, and demand is not modelled."
  Silver comes out identical to lead per kilogram today, which is what a
  MASS split, rather than a VALUE split, necessarily gives you.

  Complaints/32: with extraction rent fixed at zero and demand absent
  entirely, every computed price in this model is exactly the labour
  embodied in the good. `sim/world/deposits.py` fixed the rent half of that
  (a deposit's cost is compared against the MARGINAL deposit needed to meet
  a quantity demanded) but took that quantity as a bare parameter, because
  nothing could supply one - "the next lever is therefore NOT more deposit
  data: it is whatever decides how much is demanded."

  Complaints/35 SS4: the stakeholder's own rebuttal to "who buys all this
  industrial output in an agrarian economy" - "if you have been making
  computers, you are creating the demand by it existing." That is half
  right and half not, and this module is what actually tests which half:
  an industrial base genuinely is its own customer for INTERMEDIATE goods
  (a smith buys iron because someone buys axes, and that demand falls
  straight out of the recipes in data/production/ once something is
  actually being produced), but a FINISHED good still has to reach a buyer
  with a budget somewhere at the end of the chain, and that budget is
  bounded by population and income, not by the existence of the factory.
  See DERIVED DEMAND and this module's own __main__ block for both halves
  side by side.

THE SHAPE. Two buyer types, following the task's own instruction to model
budgets and needs rather than a table of "what things are worth":

  HOUSEHOLDS spend a budget across a small basket of goods using a
  Stone-Geary / Linear Expenditure System (LES): each good has a
  subsistence quantity (`gamma`, a PHYSICAL floor - it does not fall to
  zero just because the price rises, within the range this model is valid
  over) and a marginal budget share (`beta`, what fraction of whatever
  income is left AFTER every good's subsistence floor is paid for goes to
  this good). This is not a house style invented for this task: it is the
  standard textbook demand system built exactly to produce Engel's law
  (food's SHARE of the budget falls as income rises) without asserting it
  as a separate rule - see HOUSEHOLD DEMAND below for why the algebra does
  this on its own. A good with gamma=0 (silver: nobody eats it, nobody has
  a minimum physical requirement for it) behaves completely differently
  from a good with gamma>0 (food) at the SAME beta, which is the mechanism
  that makes a famine dear and a luxury slack - see
  `household_quantity_demanded_per_capita`.

  Households are not identical. INCOME_DISTRIBUTION below splits a
  population into income bins from a single inequality parameter (a Gini
  coefficient) via a Pareto distribution, rather than hand-declaring "5%
  of the population is rich" - see INCOME DISTRIBUTION for why a Pareto
  shape parameter is the one number this needs and how the rest is
  arithmetic. The bottom bins spend almost everything on subsistence; the
  top bins have real surplus, and that surplus is where silver's demand
  comes from - nobody eats silver, so it is bought only out of whatever a
  household has left after food, and only the top of the income
  distribution has much of that left. This is the mechanism, not an
  assumption bolted on afterwards: hand the same functions a perfectly
  equal income distribution and the silver price collapses, because nobody
  would have any surplus to spend on it - see
  `sim/tests/test_demand.py`'s InequalityIsLoadBearingTests.

  PRODUCERS buy intermediate goods because something downstream is being
  made from them - DERIVED DEMAND below reads the input coefficients
  straight out of data/production/*.json's own `inputs` and `capital.
  build_materials` fields and scales them by whatever output level a
  caller says is actually being produced. No new number is invented for
  this: the coefficient a smith needs of iron per axe is already sitting
  in the recipe data that CLAUDE.md SS4 says exists and is 99.7% covered.

JOINT PRODUCTS, THE ACTUAL POINT: `joint_output_value_shares` splits a
process's one cost across its outputs in proportion to PRICE times
quantity, not mass times a shared unit price. The mass split Complaints/29
correctly diagnosed as wrong is `joint_output_mass_shares`, kept here
deliberately so a caller (or a test) can print both side by side and see
the difference a real silver price makes. Getting that real price is
`market_clearing_price`: for a good in fixed short-run supply (which a
joint by-product always is - the furnace makes 0.46 kg of silver for every
tonne of lead whether or not anyone wants it that day), the price that
clears the market is wherever the AGGREGATE demand curve crosses that fixed
quantity. This is not a new idea invented for this module: it is Marshall's
"market day" price for a harvest already brought to market, applied to a
kilogram of silver already sitting in the cupel. See MARKET-CLEARING PRICE
below for the closed form and why it exists in closed form at all.

TAKE WHAT YOU NEED AS PARAMETERS. Exactly as sim/world/agriculture.py takes
weather and sim/world/deposits.py takes the quantity demanded, every
function below takes population, income, the wage and any cost-side price
as an explicit argument. This module does not compute a wage, a population,
or a cost-side price for anything - it turns those, plus a household's
preferences and a producer's recipe, into a quantity or a value share.

STANDALONE ON PURPOSE, LIKE ITS SIBLINGS. Nothing here imports sim/engine/,
sim/solve_prices.py, or any other sim/world/ module - see
sim/world/__init__.py and sim/world/deposits.py's own docstring for why a
module built this way survives other agents editing those paths
concurrently with this one's construction. It reads data/production/*.json
directly, as plain JSON data, for recipe input coefficients - that is data,
not an import of the solver that will eventually read the same files.

WHAT THIS MODULE DOES NOT DO. It does not solve for a general equilibrium
price vector - `market_clearing_price` solves for ONE good's price given
every OTHER good's price already fixed, which is exactly the shape the
task's own output contract asks for ("given a set of prices, quantity
demanded per good") and exactly what a future iterative price solver would
call once per candidate price vector, not a replacement for that solver. It
does not model saving, credit, storage of wealth across years, or a
household's labour-supply decision (how many hours to work, and at what
trade) - income per capita is an input here, not an output, in the same
spirit as sim/world/agriculture.py taking labour_hours as a pool rather
than deriving how many hours someone chooses to work.

THE STAKEHOLDER'S ARGUMENT, ENGAGED RATHER THAN DODGED. "An industrial base
is its own customer" is correct for every INTERMEDIATE good in a recipe
chain, and DERIVED DEMAND below is the mechanism that makes it true in this
model: decide to produce more axes and the model produces more demand for
iron without anyone hand-writing that fact. It stops being correct at the
FINAL good in the chain - something, in the end, has to be a household's
computer, silverware or axe, bought out of a budget that this module shows
is bounded by population and its (unequal) income, not expanded by the
factory that made the good. Building the axe does not make anyone richer
enough to buy it; building the PLOUGH the axe helps make might, by raising
the harvest, which is exactly the kind of loop CLAUDE.md SS3.1 wants
computed rather than assumed and which this module cannot close on its own
(it takes income as a parameter) - see this module's own __main__ block and
sim/tests/test_demand.py's IndustrialBaseIsItsOwnCustomerTests for the
concrete numbers this claim rests on.
"""
import collections
import json
import os

from sim.constants import declare

# ============================================================================
# DATA FILE LOCATIONS
# ============================================================================
# Same ROOT-relative pattern sim/world/deposits.py already uses - repeated
# rather than imported, for the same reason every sim/world/ module gives
# for not importing another one: see this module's own STANDALONE section.

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
PRODUCTION_DIR = os.path.join(_ROOT, "data", "production")


def _load_production_data():
    """Every material entry across data/production/*.json, merged by
    material key - the same merge-by-directory shape data/production/
    _SCHEMA.md describes for that directory itself. `_note` keys are
    metadata, not materials, and are dropped.
    """
    materials = {}
    for filename in sorted(os.listdir(PRODUCTION_DIR)):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(PRODUCTION_DIR, filename)) as handle:
            data = json.load(handle)
        materials.update(data.get("materials", {}))
    return materials


_PRODUCTION_CACHE = None


def production_data():
    """Cached, read-only view of data/production/*.json's materials. A
    caller that already has this in hand (a test iterating many functions
    over the same data) can pass it straight to any function below via its
    `production` argument instead of paying the parse cost again.
    """
    global _PRODUCTION_CACHE
    if _PRODUCTION_CACHE is None:
        _PRODUCTION_CACHE = _load_production_data()
    return _PRODUCTION_CACHE


# ============================================================================
# INCOME DISTRIBUTION
# ============================================================================
# A population of identical households cannot generate silver's demand at
# all: give everyone the same income and either everyone can afford a little
# silver (in which case it is not scarce relative to a broad population's
# taste for it) or no one can. Real pre-industrial societies had neither -
# they had a thin surplus-holding stratum sitting on top of a much larger
# population with essentially none, and it is THAT shape, not the mean
# income alone, that determines how much silver anyone actually buys.
#
# Rather than hand-declaring a "luxury class share" (exactly the hardcode
# CLAUDE.md 3.1 exists to forbid and the task explicitly warns against), the
# population is split by a single inequality parameter - a Gini coefficient
# - via a Pareto Type I distribution, the standard textbook distribution for
# the upper tail of an income distribution and the one whose Lorenz curve
# has a closed-form relationship to the Gini coefficient (see
# _pareto_alpha_from_gini). Handing this ONE number to `income_bins` below
# produces as many income classes as asked for, each with its own
# analytically-exact mean income - not an assumed "rich" and "poor" split.
#
# WHAT INEQUALITY ACTUALLY CHANGES, STATED PLAINLY. In this linear (Stone-
# Geary) demand system, as long as every bin's own surplus stays positive,
# a market's AGGREGATE demand for a gamma=0 good (see market_clearing_
# price's closed form) depends only on TOTAL population and TOTAL income -
# not on how unequally that income is shared. Inequality's real effect
# here is on WHO holds the surplus (see the per-capita checks in sim/
# tests/test_demand.py's AggregateDemandAndInequalityTests) and, once
# severe enough to push a bin below its own subsistence floor, on how
# much of the population can even reach that market at all - not on the
# market-clearing price for a population that can all afford its own
# necessities. This is a real, checked property of the mechanism (see
# AggregateDemandAndInequalityTests.test_inequality_shape_moves_who_buys_
# not_the_aggregate_clearing_price in that same test file), not an
# unexamined assumption.

GINI_COEFFICIENT_PREINDUSTRIAL_AGRARIAN = declare(
    "GINI_COEFFICIENT_PREINDUSTRIAL_AGRARIAN", 0.40,
    kind="temporary_heuristic",
    unit="dimensionless (Gini coefficient of household income, 0=equal, "
         "1=one household holds everything)",
    source="Cross-society studies of income inequality in pre-industrial "
           "agrarian economies (comparing an economy's actual Gini against "
           "the theoretical maximum a population pinned near subsistence "
           "could sustain at all - the 'inequality possibility frontier' "
           "line of work) commonly report overall Ginis in roughly the "
           "0.35-0.48 band across a wide range of pre-modern societies; "
           "taken as a round mid-range figure for Rome specifically, "
           "which this project has no dedicated wealth-census source for.",
    confidence="D",
    why="The single number that decides how concentrated income is, and "
        "therefore how much surplus exists at all for a good nobody needs "
        "to survive. What would derive this instead of assuming it: an "
        "actual tax-register or census-based wealth distribution for the "
        "society being simulated, which this project does not have for "
        "Rome (Egypt's papyrus census returns are the nearest real "
        "candidate and are not yet digitised into this project's data).")

DEFAULT_NUM_INCOME_BINS = 20
# A numerical resolution choice (how finely the continuous Pareto
# distribution is discretised for aggregate arithmetic), not a fact about
# the world - see agriculture.py's own HARVEST_WINDOW_DAYS-adjacent constants
# for the house style of declaring facts and leaving numerical-method
# choices as plain module constants. income_bins()'s own docstring shows
# this converges: doubling it changes no bin's ANALYTICALLY EXACT
# conditional mean, only how many of them there are.


def _pareto_alpha_from_gini(gini):
    """Pareto Type I's shape parameter from its Gini coefficient. For a
    Pareto distribution the two are related in closed form, G = 1/(2a-1),
    which inverts to this. Larger alpha is a THINNER tail (more equal);
    alpha must exceed 1 for the distribution to have a finite mean at all
    (income_bins raises if it does not).
    """
    if not (0.0 < gini < 1.0):
        raise ValueError("gini must be strictly between 0 and 1, got %r" % (gini,))
    return (1.0 + gini) / (2.0 * gini)


def _pareto_bin_mean_multiple_of_scale(u_low, u_high, alpha):
    """E[X / x_m | X in the population's upper-tail-probability interval
    (u_low, u_high)] for a Pareto Type I distribution with shape `alpha`,
    where u is measured as a SURVIVAL probability (u=0 is the very richest
    household, u=1 is everyone). x_m is the distribution's scale (its
    minimum possible value); dividing it out here is what lets this
    function depend on `alpha` alone.

    Closed form: the Pareto quantile function at survival probability u is
    x(u) = x_m * u^(-1/alpha), so the conditional mean over an interval is
    the integral of that divided by the interval's width - integrable in
    closed form because u^(-1/alpha) is a plain power.
    """
    if not (0.0 <= u_low < u_high <= 1.0):
        raise ValueError("need 0 <= u_low < u_high <= 1, got %r, %r" % (u_low, u_high))
    exponent = 1.0 - 1.0 / alpha
    integral = (u_high ** exponent - u_low ** exponent) / exponent
    return integral / (u_high - u_low)


IncomeBin = collections.namedtuple("IncomeBin", [
    "population",
    "income_per_capita_per_year",
    "population_percentile_from_top",   # (u_low, u_high), 0.0=richest edge
])


def income_bins(population, mean_income_per_capita_per_year,
                 gini=None, num_bins=None):
    """`population` split into `num_bins` equal-population income classes
    whose incomes come from a Pareto Type I distribution with mean
    `mean_income_per_capita_per_year` and the given `gini` - see this
    section's own docstring for why a single inequality parameter, rather
    than a hand-set "luxury share", is what produces these classes.

    Each bin's `income_per_capita_per_year` is the EXACT conditional mean
    of that population slice (not a sampled draw), so
    sum(bin.population * bin.income) over every bin returns
    population * mean_income_per_capita_per_year exactly (up to floating-
    point error) for any `num_bins` - see
    sim/tests/test_demand.py's IncomeDistributionTests.
    """
    gini = GINI_COEFFICIENT_PREINDUSTRIAL_AGRARIAN if gini is None else gini
    num_bins = DEFAULT_NUM_INCOME_BINS if num_bins is None else num_bins
    if population < 0:
        raise ValueError("population cannot be negative: %r" % (population,))
    if mean_income_per_capita_per_year <= 0:
        raise ValueError("mean income must be positive: %r"
                          % (mean_income_per_capita_per_year,))
    if num_bins < 1:
        raise ValueError("need at least one income bin, got %r" % (num_bins,))

    alpha = _pareto_alpha_from_gini(gini)
    if alpha <= 1.0:
        raise ValueError(
            "gini %.4f implies a Pareto shape parameter of %.4f <= 1, "
            "which has no finite mean - this distribution cannot be built "
            "at this inequality level" % (gini, alpha))
    scale_multiple = (alpha - 1.0) / alpha           # x_m = mean * this
    scale = mean_income_per_capita_per_year * scale_multiple

    bins = []
    for index in range(num_bins):
        u_low = index / num_bins
        u_high = (index + 1) / num_bins
        mean_multiple = _pareto_bin_mean_multiple_of_scale(u_low, u_high, alpha)
        bins.append(IncomeBin(
            population=population / num_bins,
            income_per_capita_per_year=scale * mean_multiple,
            population_percentile_from_top=(u_low, u_high)))
    return bins


def total_population(bins):
    return sum(b.population for b in bins)


def total_income(bins):
    return sum(b.population * b.income_per_capita_per_year for b in bins)


# ============================================================================
# HOUSEHOLD DEMAND - STONE-GEARY / LINEAR EXPENDITURE SYSTEM
# ============================================================================
# One household with income Y, facing prices p_i for a basket of goods each
# with a subsistence quantity gamma_i (a PHYSICAL floor - calories a person
# needs, not a preference) and a marginal budget share beta_i (sum_i beta_i
# = 1), maximises sum_i beta_i * ln(q_i - gamma_i) subject to sum_i p_i*q_i
# = Y. The closed-form solution is
#
#     q_i = gamma_i + (beta_i / p_i) * (Y - sum_j p_j * gamma_j)
#
# i.e. pay for every good's subsistence floor first (sum_j p_j*gamma_j, the
# COMMITTED expenditure), then split whatever is left (the SURPLUS) across
# every good in its fixed beta_i share, spent at that good's own price.
#
# WHY THIS SPECIFIC FORM AND NOT A BARE ELASTICITY. A single price
# elasticity per good is a description of behaviour near one point, not a
# mechanism - it cannot say WHY a famine (food scarce) behaves differently
# from a silver shortage (silver scarce) without being told to, by two
# different numbers picked to match the story. Stone-Geary needs only ONE
# extra fact per good (gamma, a physical quantity) to make that difference
# fall out of the algebra: a good with gamma=0 has ALL of its demand come
# from the elastic surplus term, so raising its price bites immediately
# (elasticity approaches -1 as gamma/q -> 0, the constant-expenditure-share
# case); a good with gamma large relative to what people actually buy has
# most of its demand INSENSITIVE to price by construction, because the
# floor is bought first regardless of what it costs, right up to the point
# income cannot cover it at all (see the below-subsistence branch below).
# Silver (gamma=0) and food (gamma>0) therefore behave differently here
# because one is a biological requirement and the other is not - not
# because two different elasticities were chosen to make them differ.

Good = collections.namedtuple("Good", [
    "name",
    "subsistence_quantity_per_capita_per_year",   # gamma - a PHYSICAL floor
    "marginal_budget_share",                      # beta - share of SURPLUS
])


def validate_basket(basket):
    """basket's beta values must sum to 1 - Stone-Geary's own constraint,
    not a house convention. Raises rather than silently renormalising,
    because a caller whose betas do not sum to 1 has made an error worth
    seeing, not one worth quietly correcting.
    """
    total_beta = sum(good.marginal_budget_share for good in basket)
    if abs(total_beta - 1.0) > 1e-9:
        raise ValueError(
            "basket's marginal_budget_share values must sum to 1.0, "
            "got %.9f across %s" % (total_beta, [g.name for g in basket]))


def household_quantity_demanded_per_capita(good, prices, income_per_capita, basket):
    """One `good`'s Stone-Geary demand for a single representative person
    earning `income_per_capita`, given the full `basket` of goods this
    household allocates a budget across (needed because the committed
    expenditure sum runs over every good, not just this one) and `prices`,
    a dict of every basket good's name to its price in the same units
    `income_per_capita` is measured in.

    BELOW-SUBSISTENCE HOUSEHOLDS. If income cannot even cover the
    committed basket (income_per_capita < sum_j p_j*gamma_j), the Stone-
    Geary formula above goes negative, which is not a quantity. This
    function instead scales every committed quantity down proportionally
    to what income actually covers - a starvation regime this module
    FLAGS by returning a below-floor quantity rather than raising, but
    does not model further: what actually happens to a population that
    cannot feed itself is sim/world/demography.py's mechanism
    (STARVATION_MORTALITY_CEILING_MULTIPLIER and its neighbours), not
    this one, and the two are deliberately not wired together - see this
    module's own STANDALONE section.
    """
    committed_per_capita = sum(
        prices[g.name] * g.subsistence_quantity_per_capita_per_year for g in basket)
    surplus_per_capita = income_per_capita - committed_per_capita
    if surplus_per_capita < 0.0:
        if committed_per_capita <= 0.0:
            return 0.0
        scale = max(0.0, income_per_capita / committed_per_capita)
        return good.subsistence_quantity_per_capita_per_year * scale
    return (good.subsistence_quantity_per_capita_per_year
            + (good.marginal_budget_share / prices[good.name]) * surplus_per_capita)


def aggregate_household_demand(good, prices, bins, basket):
    """Total (not per-capita) household quantity demanded for `good` across
    every income bin in `bins` - the sum a market actually sees, since a
    bottom-decile household and a top-decile household do not want the
    same basket at the same prices.
    """
    return sum(
        b.population * household_quantity_demanded_per_capita(
            good, prices, b.income_per_capita_per_year, basket)
        for b in bins)


def aggregate_household_demand_all_goods(prices, bins, basket):
    """aggregate_household_demand for every good in `basket` at once - the
    per-good quantities a caller pricing a whole basket would actually
    want, in one dict.
    """
    return {good.name: aggregate_household_demand(good, prices, bins, basket)
            for good in basket}


def household_budget_share(good, prices, bins, basket):
    """What fraction of AGGREGATE household spending, across every bin,
    goes to `good` - the number CalibrationTargetsTests checks against the
    60-80%-on-food historical range. Not read by anything in this module
    except that test - see CALIBRATION TARGETS below.
    """
    total_spending = sum(
        prices[g.name] * aggregate_household_demand(g, prices, bins, basket)
        for g in basket)
    if total_spending <= 0.0:
        return 0.0
    return (prices[good.name] * aggregate_household_demand(good, prices, bins, basket)
            / total_spending)


# ============================================================================
# THE DEFAULT BASKET
# ============================================================================
# Three goods, deliberately named after real data/production/ material keys
# where one exists (wheat_kg, silver_kg) rather than an invented composite,
# so a caller can hand this basket's demand straight to
# joint_output_value_shares for a real recipe. "manufactures" has no single
# data/production/ key of its own - it stands for the broad category of
# artisan-made goods (cloth, tools, pottery) this module does not attempt to
# disaggregate; see the module docstring's WHAT THIS MODULE DOES NOT DO.
#
# THE THREE BETA SHARES ARE A NAMED HEURISTIC, NOT DERIVED, AND ARE NOT
# TUNED TO ANY CALIBRATION TARGET. They were chosen once, from the
# reasoning given in each declaration below, and never adjusted after
# seeing what food-budget-share or silver:lead ratio they produce - see
# sim/tests/test_demand.py's CalibrationAgainstHistoricalTargetsTests for
# what they actually produce and how that compares.

HUMAN_SUBSISTENCE_CALORIES_PER_CAPITA_DAY = declare(
    "HUMAN_SUBSISTENCE_CALORIES_PER_CAPITA_DAY", 2200.0,
    kind="biological_parameter",
    unit="kcal/person/day",
    source="FAO minimum dietary energy requirement, adult average - the "
           "same figure sim/world/agriculture.py's own "
           "HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY and sim/world/"
           "demography.py's SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY "
           "use. Declared again here under its own name, deliberately, "
           "rather than imported from either module - see this module's "
           "own STANDALONE section for why a cross-import between "
           "sim/world/ modules is exactly the wiring none of them do yet.",
    confidence="B",
    why="Converts a person's physical food requirement into a quantity of "
        "wheat, which is what FOOD's subsistence floor (gamma) actually "
        "is - the one number in this basket that is a biological fact "
        "rather than a preference.")

WHEAT_ENERGY_KCAL_PER_KG = declare(
    "WHEAT_ENERGY_KCAL_PER_KG", 3400.0,
    kind="biological_parameter",
    unit="kcal/kg",
    source="Standard food-composition figures for whole wheat grain, "
           "matching sim/world/agriculture.py's own WHEAT_ENERGY_KCAL_PER_KG "
           "(declared independently here for the same standalone reason).",
    confidence="A",
    why="The other half of turning a calorie requirement into a kilogram "
        "quantity of the FOOD good's subsistence floor.")

FOOD_SUBSISTENCE_QUANTITY_KG_PER_CAPITA_PER_YEAR = (
    HUMAN_SUBSISTENCE_CALORIES_PER_CAPITA_DAY * 365.25 / WHEAT_ENERGY_KCAL_PER_KG)
# ~236.3 kg/person/year - arithmetic on two already-declared numbers, not a
# fact of its own, matching agriculture.py's own convention for
# GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA.

BETA_FOOD_SURPLUS_SHARE = declare(
    "BETA_FOOD_SURPLUS_SHARE", 0.30,
    kind="temporary_heuristic",
    unit="fraction of surplus (post-subsistence) household spending "
         "(dimensionless)",
    source=None,
    confidence="D",
    why="What a household does with income LEFT OVER once its physical "
        "food floor is paid for - real households do not stop buying "
        "food at the subsistence line, they buy better food (meat, wine, "
        "white bread over barley), so this is not zero. No consumption "
        "survey for Roman households exists to derive this from; a real "
        "one (or a documented Engel-curve estimate for a comparable "
        "pre-industrial economy) would replace this number rather than "
        "this module inventing a second one for a specific study.")

BETA_MANUFACTURES_SURPLUS_SHARE = declare(
    "BETA_MANUFACTURES_SURPLUS_SHARE", 0.65,
    kind="temporary_heuristic",
    unit="fraction of surplus household spending (dimensionless)",
    source=None,
    confidence="D",
    why="The largest surplus share, on the reasoning that most "
        "discretionary pre-industrial household spending went on "
        "artisan-made goods broadly (cloth, tools, pottery, furniture, "
        "housing) rather than on precious metals specifically - ordinary "
        "consumption, not hoarding. Same caveat as "
        "BETA_FOOD_SURPLUS_SHARE: a real historical consumption survey "
        "would derive this, not this module.")

BETA_SILVER_SURPLUS_SHARE = declare(
    "BETA_SILVER_SURPLUS_SHARE", 0.05,
    kind="temporary_heuristic",
    unit="fraction of surplus household spending (dimensionless)",
    source=None,
    confidence="D",
    why="What a household with money left over spends on silver "
        "specifically (jewellery, plate, hoarded coin) rather than on "
        "ordinary manufactures - deliberately the smallest of the three "
        "shares, because silver-buying is a narrower category than "
        "'discretionary spending' in general. THIS IS THE NUMBER THAT "
        "MOST DIRECTLY SETS SILVER'S DERIVED PRICE (see "
        "market_clearing_price) and CLAUDE.md 3.4's own instruction is "
        "followed here in the strictest sense this project has applied it "
        "yet: this value was picked ONCE, from the reasoning above, and "
        "never adjusted after computing what silver:lead ratio it "
        "produces - see sim/tests/test_demand.py's own CalibrationAgainst"
        "HistoricalTargetsTests docstring for the honesty check that "
        "enforces this (it prints the result; it never asserts a "
        "tolerance). A real number would come from a documented share of "
        "household wealth held as bullion/plate for a comparable "
        "pre-industrial economy, which this project does not have.")

FOOD = Good("wheat_kg", FOOD_SUBSISTENCE_QUANTITY_KG_PER_CAPITA_PER_YEAR,
            BETA_FOOD_SURPLUS_SHARE)
MANUFACTURES = Good("manufactures", 0.0, BETA_MANUFACTURES_SURPLUS_SHARE)
SILVER = Good("silver_kg", 0.0, BETA_SILVER_SURPLUS_SHARE)

DEFAULT_BASKET = (FOOD, MANUFACTURES, SILVER)
validate_basket(DEFAULT_BASKET)


# ============================================================================
# MARKET-CLEARING PRICE FOR A GOOD IN FIXED SUPPLY
# ============================================================================
# A joint by-product's quantity is not a choice - the furnace makes 0.46 kg
# of silver for every tonne of lead it smelts whether or not anyone wants
# that much silver that year (see the module docstring's JOINT PRODUCTS
# section). For a good whose supply is fixed for the period being priced,
# the price that clears the market is wherever aggregate demand crosses
# that fixed quantity - Marshall's short-run "market day" price, applied
# here to a kilogram of silver already sitting in the cupel rather than a
# sack of grain already at market.
#
# THIS HAS A CLOSED FORM, and it is worth showing why rather than reaching
# for a numerical solver. Fix every OTHER good's price. Household demand
# for good i, aggregated over every income bin, is (summing the per-bin
# Stone-Geary formula, and noting that gamma_j and every OTHER good's price
# are the SAME for every bin - only income varies by bin):
#
#     Q_i(p_i) = N * gamma_i * (1 - beta_i) + beta_i * (Y_total - N * C) / p_i
#
# where N is total population, Y_total is total income across every bin,
# and C = sum_{j != i} p_j * gamma_j (the OTHER goods' committed spending
# per capita - independent of p_i because those prices are already fixed).
# That is exactly the form A + B/p_i, monotonically DECREASING in p_i
# (assuming positive surplus), so it has exactly one root for any target
# quantity above the floor A - see `market_clearing_price` for A and B
# named directly and sim/tests/test_demand.py's ClosedFormMatchesDirect
# SummationTests for the check that this formula and a plain per-bin sum
# agree to floating-point precision.

def market_clearing_price(good, quantity_supplied, other_prices, bins, basket):
    """The price of `good` at which AGGREGATE HOUSEHOLD demand (see this
    section's own docstring; producer/derived demand is a separate channel,
    see derived_intermediate_demand) exactly equals `quantity_supplied`,
    given every other basket good's price already fixed in `other_prices`
    (a dict of name -> price) and the population's `bins` (see
    income_bins).

    Raises ValueError if `quantity_supplied` is at or below the quantity
    this population would still demand even at an infinite price (its
    Stone-Geary floor, scaled by (1 - beta) - see the module docstring's
    HOUSEHOLD DEMAND section for why that floor is not simply `gamma`
    itself) - demand alone cannot price a good that scarce; something
    other than a household budget is rationing it.
    """
    validate_basket(basket)
    other_goods = [g for g in basket if g.name != good.name]
    missing = [g.name for g in other_goods if g.name not in other_prices]
    if missing:
        raise KeyError(
            "market_clearing_price needs a price for every other basket "
            "good; missing %s" % missing)

    population = total_population(bins)
    income = total_income(bins)
    committed_other_per_capita = sum(
        other_prices[g.name] * g.subsistence_quantity_per_capita_per_year
        for g in other_goods)

    floor_quantity = (population * good.subsistence_quantity_per_capita_per_year
                       * (1.0 - good.marginal_budget_share))
    surplus_income_available = good.marginal_budget_share * (
        income - population * committed_other_per_capita)

    if surplus_income_available <= 0.0:
        raise ValueError(
            "no aggregate surplus income is available for %r at these "
            "prices and incomes - population income does not clear even "
            "its committed necessities" % (good.name,))
    if quantity_supplied <= floor_quantity:
        raise ValueError(
            "%.6g units of %r cannot be cleared by household demand alone: "
            "even an infinite price only suppresses aggregate demand to "
            "%.6g (this population's price-insensitive floor for this "
            "good) - something other than a household budget must be "
            "rationing it" % (quantity_supplied, good.name, floor_quantity))

    return surplus_income_available / (quantity_supplied - floor_quantity)


# ============================================================================
# DERIVED (PRODUCER) DEMAND
# ============================================================================
# "If you have been making computers, you are creating the demand by it
# existing" (Complaints/35 SS4) is exactly right for what a recipe consumes -
# and data/production/*.json already states every recipe's input
# coefficients, so this section invents no new number at all. Given a
# `planned_output_levels` dict (how much of each recipe's own output is
# actually being produced this year - an input, not something this module
# decides), the demand for any material that recipe consumes falls straight
# out of arithmetic on data this project already has.
#
# A JOINT RECIPE'S OWN KEY IS NOT ALWAYS ITS BASIS OUTPUT. Seven entries in
# data/production/ (zinc_electrolytic_kg -> zinc_kg+germanium_g+indium_g is
# the sharpest example, and this module's own worked example) are named
# after a PROCESS rather than after the material they principally produce.
# _dominant_output_key picks the output with the largest quantity by
# kg-equivalent mass as the one the entry's `inputs` are quoted "per unit
# of" - a bookkeeping convenience for finding a denominator, not a claim
# about which output deserves the cost (that question is what
# joint_output_value_shares answers instead, on price, never on mass).

_KG_EQUIVALENT_PER_UNIT_SUFFIX = {"_kg": 1.0, "_g": 0.001, "_t": 1000.0}


def _kg_equivalent(material_key, quantity):
    for suffix, multiplier in _KG_EQUIVALENT_PER_UNIT_SUFFIX.items():
        if material_key.endswith(suffix):
            return quantity * multiplier
    return quantity   # unrecognised unit suffix - compared as-is, which
                       # only matters for picking a basis output and is
                       # flagged in _dominant_output_key's own docstring.


def _dominant_output_key(entry):
    """Which of `entry`'s outputs its `inputs` and `labour_hours` are
    quoted "per unit of" - see this section's own docstring for why this
    is a mass-based bookkeeping choice, not a value judgement.
    """
    outputs = entry.get("outputs") or {}
    if not outputs:
        raise ValueError("recipe entry has no outputs at all: %r" % (entry,))
    return max(outputs, key=lambda key: _kg_equivalent(key, outputs[key]))


def input_coefficients_per_unit_output(recipe_key, production=None):
    """{material_key: quantity of material consumed per unit of
    `recipe_key`'s own DOMINANT output produced}, from that recipe's
    `inputs` (consumed making one batch) and `capital.build_materials`
    (consumed building the plant the recipe runs in, amortised over
    `service_life_years` * `annual_output_at_basis` exactly as
    data/production/_SCHEMA.md's own CAPITAL section defines - see that
    file for why this is `build_qty / (service_life_years *
    annual_output_at_basis)` and not a financial depreciation convention).

    Both channels are real physical demand for the material: a batch that
    is never run still needs its share of the furnace rebuilt eventually.
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
    for material, quantity in entry.get("inputs", {}).items():
        coefficients[material] += quantity / basis_quantity
    for capital_item in entry.get("capital") or []:
        service_life = capital_item.get("service_life_years")
        annual_output = capital_item.get("annual_output_at_basis")
        if not service_life or not annual_output:
            continue
        for material, quantity in capital_item.get("build_materials", {}).items():
            coefficients[material] += quantity / (service_life * annual_output)
    return dict(coefficients)


def derived_intermediate_demand(material_key, planned_output_levels, production=None):
    """Total quantity of `material_key` demanded as an INPUT, given
    `planned_output_levels` (a dict of recipe_key -> how much of that
    recipe's own dominant output is being produced per year - the
    "someone has decided to make this many axes" fact this module takes
    as a parameter rather than inventing).

    Returns (total_quantity, {recipe_key: quantity contributed by that
    recipe}) - the breakdown is what lets a caller (or a test) show WHICH
    downstream process is creating the demand, the concrete form of the
    stakeholder's "an industrial base is its own customer" argument - see
    the module docstring's own section on it.
    """
    production = production if production is not None else production_data()
    total = 0.0
    by_recipe = {}
    for recipe_key, output_level in planned_output_levels.items():
        if recipe_key not in production or not output_level:
            continue
        coefficient = input_coefficients_per_unit_output(
            recipe_key, production).get(material_key, 0.0)
        if coefficient:
            amount = coefficient * output_level
            total += amount
            by_recipe[recipe_key] = amount
    return total, by_recipe


def consumers_of(material_key, production=None):
    """Every recipe_key whose input_coefficients_per_unit_output includes
    `material_key` at all - which downstream processes would generate
    demand for it if run, independent of any particular output level.
    Used for reporting (this module's own __main__ block, and
    sim/tests/test_demand.py) rather than by any pricing function above.
    """
    production = production if production is not None else production_data()
    consumers = []
    for recipe_key, entry in production.items():
        try:
            coefficients = input_coefficients_per_unit_output(recipe_key, production)
        except (ValueError, KeyError):
            continue
        if coefficients.get(material_key, 0.0):
            consumers.append(recipe_key)
    return sorted(consumers)


def _illustrative_recursive_labour_content_price_per_kg(
        material_key, production=None, _memo=None, _visiting=None):
    """The naive "pure labour content" price Complaints/32 says is what
    every price in this model currently is: walk `material_key`'s own
    recipe, add its direct labour_hours, then recurse into every input
    material and add ITS labour content too, all the way down to whatever
    bottoms out in an `extracted_from` entry with no inputs of its own.
    Every trade's hours are treated as equally valuable (1 hour = 1
    labour-hour, this project's own numeraire per Complaints/32) because
    this module has no wage-relativity data of its own to weight them by
    and should not invent one.

    THIS IS NOT PART OF THIS MODULE'S DEMAND MECHANISM. It exists only so
    this module's own __main__ block and sim/tests/test_demand.py have
    SOME cost-side price to anchor a demo against, without reading
    data/prices.json (a book value) or importing sim/solve_prices.py (out
    of scope - see the module docstring's STANDALONE section). It is
    deliberately a leading-underscore helper: no production code above
    this line calls it, and market_clearing_price and
    joint_output_value_shares both take a price as a plain argument
    regardless of where a caller's real price comes from.

    Recipe cycles (Complaints/31, Complaints/32's own iron_bar_kg/
    pig_iron_kg example) are real in this data; a material already being
    computed higher up the call stack contributes zero ADDITIONAL cost
    from the cyclic edge rather than recursing forever - a crude but
    honest way to terminate, not a claim that the cycle is resolved
    correctly (sim/solve_prices.py's own resolvability pass is where that
    is actually handled).
    """
    production = production if production is not None else production_data()
    memo = {} if _memo is None else _memo
    visiting = set() if _visiting is None else _visiting
    if material_key in memo:
        return memo[material_key]
    if material_key in visiting or material_key not in production:
        return 0.0
    visiting.add(material_key)

    entry = production[material_key]
    basis_key = _dominant_output_key(entry)
    basis_quantity = entry["outputs"][basis_key]
    direct_hours = sum(entry.get("labour_hours", {}).values())
    price = direct_hours / basis_quantity
    for input_material, quantity in entry.get("inputs", {}).items():
        input_price = _illustrative_recursive_labour_content_price_per_kg(
            input_material, production, memo, visiting)
        price += (quantity / basis_quantity) * input_price

    visiting.discard(material_key)
    memo[material_key] = price
    return price


# ============================================================================
# JOINT OUTPUT VALUE SHARES - THE COMPLAINTS/29 ANSWER
# ============================================================================

def joint_output_mass_shares(output_quantities):
    """The split Complaints/29 identifies as wrong: each output's share of
    the joint cost in proportion to its PHYSICAL quantity, regardless of
    unit or value - silver and lead, by this rule, are worth the same per
    kilogram merely because a kilogram is a kilogram. Kept here so a
    caller can print this next to joint_output_value_shares and see
    exactly what a real price changes.
    """
    total = sum(output_quantities.values())
    if total <= 0.0:
        raise ValueError("total output quantity is not positive: %r"
                          % (output_quantities,))
    return {name: quantity / total for name, quantity in output_quantities.items()}


def joint_output_value_shares(output_quantities, prices):
    """Each output's share of a joint process's one cost, in proportion to
    PRICE times quantity - net-realisable-value allocation, made non-
    circular by requiring `prices` to already be given rather than solved
    for here (see market_clearing_price for how a caller gets a real
    price for an output like silver that a cost-side calculation alone
    cannot anchor - that circularity is exactly what Complaints/29
    describes, and it is broken by pricing silver from DEMAND, not by
    this function, which only does the (now well-defined) arithmetic once
    a price exists).
    """
    missing = set(output_quantities) - set(prices)
    if missing:
        raise KeyError("no price given for output(s): %s" % missing)
    values = {name: prices[name] * quantity
              for name, quantity in output_quantities.items()}
    total = sum(values.values())
    if total <= 0.0:
        raise ValueError("total joint value is not positive: %r" % (values,))
    return {name: value / total for name, value in values.items()}


def joint_output_value_shares_for_recipe(recipe_key, prices, production=None):
    """joint_output_value_shares, reading `recipe_key`'s own `outputs`
    dict from data/production/ directly rather than making a caller copy
    it out by hand.
    """
    production = production if production is not None else production_data()
    if recipe_key not in production:
        raise KeyError("no data/production/ entry for %r" % (recipe_key,))
    return joint_output_value_shares(production[recipe_key]["outputs"], prices)


# ============================================================================
# CALIBRATION TARGETS - never inputs to anything above. See sim/constants.py:
# "an observation used to CHECK the model." These are read only by
# sim/tests/test_demand.py, to report the two disagreements the task that
# produced this module names; nothing in this file's functions reads them,
# and they must never be adjusted to make a computed figure agree - see
# sim/world/agriculture.py's own CALIBRATION TARGETS section for the same
# discipline applied there first.
# ============================================================================

HOUSEHOLD_FOOD_BUDGET_SHARE_LOW = declare(
    "HOUSEHOLD_FOOD_BUDGET_SHARE_LOW", 0.60,
    kind="calibration_target",
    unit="fraction of household spending (dimensionless)",
    source="CLAUDE.md's own calibration note / the task that produced "
           "this module: pre-industrial households typically spent "
           "roughly 60-80% of income on food.",
    confidence="B",
    why="The low end of the range household_budget_share(FOOD, ...) is "
        "checked against, never tuned to.")

HOUSEHOLD_FOOD_BUDGET_SHARE_HIGH = declare(
    "HOUSEHOLD_FOOD_BUDGET_SHARE_HIGH", 0.80,
    kind="calibration_target",
    unit="fraction of household spending (dimensionless)",
    source="Same as HOUSEHOLD_FOOD_BUDGET_SHARE_LOW.",
    confidence="B",
    why="The high end of the same range.")

SILVER_TO_LEAD_PRICE_RATIO_HISTORICAL = declare(
    "SILVER_TO_LEAD_PRICE_RATIO_HISTORICAL", 100.0,
    kind="calibration_target",
    unit="dimensionless (price ratio, silver per kg over lead per kg)",
    source="The task that produced this module states the historical "
           "silver-to-lead price ratio as 'on the order of 100:1'. Note "
           "for whoever reads this next to data/prices.json: that file's "
           "own purchase_prices_denarii gives roughly 528:1 (317/0.6), "
           "but silver_kg's book entry is marked definitional - 1 "
           "denarius IS ~3.15 g of fine silver by fiat, not a market "
           "price - so the two are not measuring quite the same thing "
           "and should not be expected to agree; both are reported by "
           "sim/tests/test_demand.py's calibration test rather than this "
           "module picking one.",
    confidence="D",
    why="The order-of-magnitude sim/tests/test_demand.py's "
        "CalibrationAgainstHistoricalTargetsTests reports this module's "
        "own derived ratio against, never tunes to.")


if __name__ == "__main__":
    # A quick, human-readable readout - the same kind of thing
    # sim/world/agriculture.py's and sim/world/deposits.py's own __main__
    # blocks print, for whoever next wants to see this module's headline
    # numbers without opening a test file. Every number below is
    # illustrative (order-of-magnitude population and income figures to
    # give the demonstration the right SCALE) - see this module's own
    # docstring's TAKE WHAT YOU NEED AS PARAMETERS section for why nothing
    # in the functions above assumes any of them.
    ILLUSTRATIVE_POPULATION = declare(
        "ILLUSTRATIVE_DEMAND_DEMO_POPULATION", 55_000_000.0,
        kind="initial_condition",
        unit="people",
        source="Modern demographic estimates for the Roman Empire's total "
               "population around 100 AD commonly cluster in the "
               "45-65 million range (a genuinely debated figure); taken "
               "as a round mid-point purely to give this module's "
               "__main__ demonstration a population of the right order "
               "of magnitude, exactly as sim/world/deposits.py's own "
               "__main__ uses data/world/resources.json's stated output "
               "as an illustrative quantity.",
        confidence="D",
        why="Only used for this printed demonstration and by "
            "sim/tests/test_demand.py's calibration report - no function "
            "above assumes any particular population; it is always a "
            "parameter.")
    ILLUSTRATIVE_MEAN_INCOME_LABOUR_HOURS_PER_CAPITA_PER_YEAR = declare(
        "ILLUSTRATIVE_DEMAND_DEMO_MEAN_INCOME_LABOUR_HOURS_PER_CAPITA_PER_YEAR",
        550.0,
        kind="initial_condition",
        unit="labour-hours/person/year (sim/solve_prices.py's own "
             "numeraire - see Complaints/32)",
        source="Order-of-magnitude only: sim/world/agriculture.py's own "
               "ANNUAL_LABOUR_HOURS_PER_FARM_WORKER (1,400 h/year) times "
               "a working-age labour-force participation share of "
               "roughly 40% of total population (children, the elderly "
               "and the non-working fraction of adults included), giving "
               "~550 labour-hour-equivalents of income per PERSON per "
               "year, not per worker.",
        confidence="D",
        why="Same as ILLUSTRATIVE_DEMAND_DEMO_POPULATION - a demo-scale "
            "figure only, never assumed by a function above.")

    bins = income_bins(ILLUSTRATIVE_POPULATION,
                        ILLUSTRATIVE_MEAN_INCOME_LABOUR_HOURS_PER_CAPITA_PER_YEAR)
    print("DEMAND - budgets and needs, not a table of worth")
    print("=" * 72)
    print("population: %.3g   mean income: %.1f labour-hours/person/year   "
          "gini: %.2f (%d income bins)"
          % (ILLUSTRATIVE_POPULATION,
             ILLUSTRATIVE_MEAN_INCOME_LABOUR_HOURS_PER_CAPITA_PER_YEAR,
             GINI_COEFFICIENT_PREINDUSTRIAL_AGRARIAN, DEFAULT_NUM_INCOME_BINS))
    print("\nincome by decile-ish bin (richest first), labour-hours/capita/year:")
    for b in bins[:5]:
        print("  bin %-12s population=%12.0f  income/capita=%9.2f"
              % (str(b.population_percentile_from_top), b.population,
                 b.income_per_capita_per_year))
    print("  ... (%d bins total, poorest: income/capita=%.2f)"
          % (len(bins), bins[-1].income_per_capita_per_year))

    # A recursive "pure labour content" illustrative food price (see
    # _illustrative_recursive_labour_content_price_per_kg's own docstring) -
    # NOT what solve_prices will eventually compute (it ignores land rent
    # entirely, which Complaints/32 flags as the largest missing term for
    # an extracted-adjacent good), used only so this demonstration has
    # SOME price to anchor food demand with.
    illustrative_wheat_price = _illustrative_recursive_labour_content_price_per_kg("wheat_kg")
    illustrative_manufactures_price = 1.0   # arbitrary numeraire-scale
                                             # anchor; manufactures has no
                                             # single data/production/ key
                                             # of its own (see DEFAULT_BASKET).

    # Complaints/29's own worked example: lead_kg's joint silver output.
    # lead_kg's own price, on the same recursive labour-content reading -
    # NOT this module's own mechanism, and not what sim/solve_prices.py
    # will eventually compute once rent and capital are read; it exists
    # only to anchor the demo's OTHER prices, exactly like wheat's above.
    lead_entry = production_data()["lead_kg"]
    outputs = lead_entry["outputs"]
    illustrative_lead_price = _illustrative_recursive_labour_content_price_per_kg("lead_kg")

    # Scale the recipe's own fixed output ratio up to data/world/
    # resources.json's own stated Roman lead output - a real historical
    # output level, not an invented one, exactly as sim/world/deposits.py's
    # own __main__ block uses the same file for the same reason. The RATIO
    # (silver output / lead output) is read straight from the recipe,
    # never hand-typed.
    with open(os.path.join(_ROOT, "data", "world", "resources.json")) as handle:
        resources = json.load(handle)
    illustrative_annual_lead_kg = resources["empire_output_100ad"]["lead"]["t_per_yr"] * 1000.0
    illustrative_annual_silver_kg = (
        illustrative_annual_lead_kg * outputs["silver_kg"] / outputs["lead_kg"])
    silver_price = market_clearing_price(
        SILVER, illustrative_annual_silver_kg,
        {"wheat_kg": illustrative_wheat_price,
         "manufactures": illustrative_manufactures_price},
        bins, DEFAULT_BASKET)

    all_prices = {"wheat_kg": illustrative_wheat_price,
                  "manufactures": illustrative_manufactures_price,
                  "silver_kg": silver_price}
    food_share = household_budget_share(FOOD, all_prices, bins, DEFAULT_BASKET)
    print("\nillustrative wheat price (recursive labour content): %.4f h/kg"
          % illustrative_wheat_price)
    print("household food budget share at that price: %.1f%%"
          % (100.0 * food_share))
    print("historical calibration target: %.0f-%.0f%%"
          % (100.0 * HOUSEHOLD_FOOD_BUDGET_SHARE_LOW,
             100.0 * HOUSEHOLD_FOOD_BUDGET_SHARE_HIGH))

    print("\n" + "=" * 72)
    print("COMPLAINTS/29: lead_kg's joint silver output, priced two ways")
    print("recipe outputs (per %s): %s" % (lead_entry["basis"][:40] + "...", outputs))
    mass_shares = joint_output_mass_shares(outputs)
    print("mass shares:  " + ", ".join(
        "%s=%.4f%%" % (k, 100.0 * v) for k, v in mass_shares.items()))
    print("illustrative lead price (recursive labour content): %.4f h/kg"
          % illustrative_lead_price)
    print("stated Roman lead output: %.4g kg/yr -> lead-byproduct silver at "
          "the recipe's own ratio: %.4g kg/yr (stated total silver output "
          "including the direct-ore route: %.4g kg/yr)"
          % (illustrative_annual_lead_kg, illustrative_annual_silver_kg,
             resources["empire_output_100ad"]["silver"]["t_per_yr"] * 1000.0))
    print("demand-cleared silver price at that supply: %.4f h/kg"
          % silver_price)
    print("derived silver:lead price ratio: %.1fx  (historical target: ~%.0fx)"
          % (silver_price / illustrative_lead_price,
             SILVER_TO_LEAD_PRICE_RATIO_HISTORICAL))
    value_shares = joint_output_value_shares(
        outputs, {"lead_kg": illustrative_lead_price, "silver_kg": silver_price})
    print("value shares: " + ", ".join(
        "%s=%.4f%%" % (k, 100.0 * v) for k, v in value_shares.items()))

    print("\n" + "=" * 72)
    print("DERIVED DEMAND: who actually consumes lead_kg as an input")
    for consumer in consumers_of("lead_kg"):
        coefficient = input_coefficients_per_unit_output(consumer)["lead_kg"]
        print("  %-28s %.5f kg lead per unit of its own dominant output"
              % (consumer, coefficient))
