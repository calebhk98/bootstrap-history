"""Grain: how much land, labour, technique and weather turn into food, and
how much labour that took.

WHAT THIS IS FOR. Agricultural surplus is the constraint on everything else
in a pre-industrial economy: it decides what fraction of a population can do
anything other than grow food, which decides how many people can be
soldiers, artisans, scholars or builders. `sim/engine/` currently has no
food system at all - farms are revenue nodes, exactly like a workshop, with
no physical land, no labour-to-yield relationship and no concept of a bad
harvest. This module is what makes "how many people can this land support,
and how many of them are free to do something else" a computed answer
instead of an assumption baked into `data/prices.json`.

STANDALONE ON PURPOSE. Nothing here imports from `sim/engine/`, and nothing
in `sim/engine/` imports this. See `sim/world/__init__.py` for why the
package as a whole is built this way while other agents edit `sim/engine/`,
`data/branches/`, `data/production/` and `data/tech_tree.json` concurrently:
a module with no dependency on those paths cannot be broken by their edits,
and cannot break their tests either. `sim/world/demography.py` (built in
parallel, not touched by this file) is the intended CONSUMER on the
population side: it takes a plain `food_available_calories_per_day` number
and treats it as exogenous. `Storage.step` below hands back exactly that
number (`food_available_kcal_per_day` in `YearFlows`) for the day someone
wires the two together - this file does not do that wiring itself.

THE TWO CONSUMERS THIS IS SHAPED FOR. (1) The demography model: birth and
death rates there respond to calories per person, so this module's job is to
turn land+labour+weather into a believable calorie stream, including the bad
years. (2) The labour market: the whole point of a farming surplus is that
it is what FREES a worker to do anything else, so this module also reports
the marginal product of the last hour of farm labour applied - the number a
labour market would need to decide whether one more hour on the farm is
worth more than that hour spent elsewhere.

ONE CROP. Wheat, following the instruction to not model a dozen crops and
`data/production/40_organics.json`, which already carries the tree's own
wheat numbers. Multiple crops, crop rotation choices and livestock are all
real and all future work; a single staple is enough to make the central
property - diminishing returns to labour on fixed land - visible and
testable, and that property, not crop variety, is what a pre-industrial
population ceiling actually comes from.

ARITHMETIC CORRECTION TO data/production/40_organics.json, MADE THERE RATHER
THAN WORKED AROUND HERE. That file's `wheat_kg` entry used to set its yield
at 800 kg/ha and call it net of seed, while deriving it in the same paragraph
as "4-5 fold [return] on the seed sown... at a seeding rate around 150-180
kg/ha". Fold-return is measured against the seed sown, so that arithmetic
produces a GROSS harvest and the seed is inside it; 800 was a defensible
gross figure and an indefensible net one, and the two readings differ by 28%.
The entry now states 577.5 kg/ha (4.5 fold on 165 kg/ha, less the 165 kg/ha
of seed corn), which is what this module computes, so the file and this
module now agree by construction rather than by coincidence -
`sim/tests/test_agriculture.py`'s DataConsistencyTests reads the file and
checks it, so the two cannot drift apart unnoticed.

The physically right form of that entry lists seed among wheat's own inputs
and outputs the gross 742.5 kg/ha, which would make seed corn a visible first
claim on the harvest (and a famine eating next year's seed a representable
event). It is written net instead because `sim/solve_prices.py`'s
resolvability pass refuses any material that appears among its own inputs -
see Complaints/31.

ON THE HEADLINE NUMBER (see `fraction_of_population_that_must_farm` and
`sim/tests/test_agriculture.py`). Computed from the constants below - seed
rate, fold return, reference labour per hectare, spoilage, human caloric
need, wheat's calorie density, the length of the harvest window and how
much one worker can reap inside it - one full-time farm worker produces
enough NET food to feed roughly five people, so about 21% of a population
has to farm. The pre-industrial figure every society actually shows is
80-90% (CLAUDE.md SS3.2's own calibration target). Nothing here is tuned to
close that gap, and the gap is now four-fold rather than the seventeen-fold
this module first computed. What closed the larger part of it was one
mechanism, added after the fact and worth stating plainly because it is not
where the first reading looked:

  THE BINDING CONSTRAINT IS THE HARVEST WINDOW, NOT THE FARMING YEAR. Grain
  ripens and is then lost to shattering and lodging within two or three
  weeks, and a worker reaping by sickle covers on the order of a tenth of a
  hectare a day. Twenty-one days times 0.1 ha/day caps one worker at about
  2.1 cropped hectares, against the 9.3 ha the same worker's 1,400 annual
  hours would otherwise buy at 150 h/ha. The annual-hours ceiling is
  therefore slack by more than four to one and does not bind at all:
  REFERENCE_LABOUR_HOURS_PER_HECTARE could be doubled, or the farming year
  lengthened, and this module's headline number would not move by a single
  percentage point. That is the finding. See
  `hectares_cropped_per_farm_worker`.

  FALLOW IS A LAND FACT, NOT A LABOUR ONE, AND CHANGES THIS NUMBER BY
  NOTHING. Two-field rotation leaves half a holding idle each year, so a
  worker cropping 2.1 ha needs a 4.2 ha holding - recorded in
  `holding_hectares_required_per_farm_worker` and FALLOW_SHARE_OF_HOLDING.
  It is tempting to read that halving as halving output per worker and so
  doubling the farm population share; that is wrong here, because land is
  not what limits this worker. The same 2.1 ha get cropped either way.
  Fallow only starts costing output once land per head is short, which is
  missing mechanism (b) below. Wiring it into the headline figure now would
  be double-counting a constraint that is not yet binding.

What is still missing, and where the remaining factor of about four is
likely hiding, in the order this module would bet on:

  (a) THE TWO SIDES OF THE COMPARISON ARE NOT IN THE SAME UNITS. This
      module computes full-time-equivalent farm WORKERS as a share of total
      population. The historical 80-90% counts everyone LIVING IN a farming
      household - children, the elderly, the household members doing
      spinning and tool repair rather than field work. In a pre-industrial
      age structure, working-age adults are roughly 40-50% of a population,
      so an FTE-worker share of 21% corresponds to something near half the
      population living on farms before any other mechanism is added. This
      is the single biggest term in the residual and it is not a modelling
      error in either number - it is a mismatch that the test comparing
      them should stop pretending is not there. Fixing it properly needs a
      dependency ratio, which belongs to sim/world/demography.py, and this
      module deliberately does not import that one (see the SHAPE note).
  (b) NO LAND SCARCITY. This module answers "how much can a worker with
      unlimited access to land produce", when the historical constraint was
      usually how much arable existed per head. Land-per-capita is a
      geography and demography fact, not something a bottom-up production
      function can supply itself, and it is what would make (b) and the
      fallow above start to bite.
  (c) SINGLE STAPLE. Wheat only. The lower-yielding land - viticulture,
      olives, pasture, fishing - that historically absorbed much of the
      rural population is absent, as is the fodder land that draught oxen
      eat, which on a real farm is a large claim on the holding.
  (d) REFERENCE_LABOUR_HOURS_PER_HECTARE PROBABLY UNDERCOUNTS. Still true,
      and the harvest constants give independent evidence for it: reaping
      alone at 0.1 ha/day is on the order of 100 h/ha, which does not fit
      inside a 150 h/ha total that also has to cover cross-ploughing,
      sowing, weeding, threshing and winnowing. It no longer matters to the
      headline number, because that ceiling is slack - but it would matter
      to any cost computed from those hours, which is what
      data/production/40_organics.json feeds.

SHAPE.
    Land          hectares plus a quality multiplier - not all land is
                  equal, and that difference is what makes the extensive
                  margin (worse land, brought under the plough when better
                  land runs out) a real, representable choice later.
    Yield         a Cobb-Douglas function of land and labour, constant
                  returns to scale in the two together but with an
                  output elasticity on labour below 1, which is exactly
                  what makes the marginal product of an additional hour of
                  labour on FIXED land fall as more hours are added - see
                  LABOUR_OUTPUT_ELASTICITY's declaration for why this
                  specific functional form and not some other diminishing
                  curve.
    Weather       one multiplicative draw per year, deterministic given a
                  seed (an ordinary `random.Random` owned by `Storage`),
                  not a daily process.
    Storage       a running stock of grain. Each year: seed leaves it to be
                  sown, harvest enters it, consumption and spoilage leave
                  it, next year's seed is set aside, and whatever remains
                  is the free carryover banked against a future bad year.
                  `YearFlows` is the exact accounting of that cycle - see
                  `Storage.step` for the identity `sim/tests/test_
                  agriculture.py`'s conservation check verifies every year.
"""
import collections
import random

from sim.constants import declare

# ============================================================================
# SEED AND YIELD BIOLOGY
# ============================================================================
# These two numbers are Roman-wheat-specific facts about the crop and the
# sowing practice, not properties of this simulation. Both are read from
# data/production/40_organics.json's wheat_kg entry (itself sourced to
# Columella and modern archaeobotanical estimates for Roman Italy), and from
# the same range the task that produced this module names independently:
# "Roman wheat returned something like four to five times the seed sown on
# decent land, around a tonne per hectare gross." See the module docstring's
# ARITHMETIC CORRECTION section for the gross-versus-net question these
# two numbers used to disagree on, and where it was settled.

SEED_SOWING_RATE_KG_PER_HA = declare(
    "SEED_SOWING_RATE_KG_PER_HA", 165.0,
    kind="engineering_estimate",
    unit="kg seed/hectare",
    source="data/production/40_organics.json wheat_kg entry: broadcast "
           "sowing rate for ancient Mediterranean wheat under an ard, "
           "given there as \"around 150-180 kg/ha\"; taken here as the "
           "midpoint of that stated range.",
    confidence="B",
    why="Sets how much of every harvest must be paid back to the ground "
        "before anything is food, and is the yardstick fold-return is "
        "quoted against - 'four to five times the seed sown' means nothing "
        "without this number.")

FOLD_RETURN_ON_SEED_SOWN = declare(
    "FOLD_RETURN_ON_SEED_SOWN", 4.5,
    kind="biological_parameter",
    unit="kg reaped / kg sown (dimensionless)",
    source="Columella's own figures and modern archaeobotanical estimates "
           "for Roman Italy, both giving roughly 4-5 fold return under an "
           "ard without heavy manuring; same range independently named in "
           "data/production/40_organics.json and in the task that produced "
           "this module. Taken as the midpoint.",
    confidence="B",
    why="The crop's biological response to being sown at all, at reference "
        "labour and average land quality in an average year - the single "
        "number a wheat-only agriculture model is least excused for "
        "getting wrong, since everything downstream (surplus, population "
        "ceiling, the fraction who can leave farming) scales off it.")

GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA = (
    SEED_SOWING_RATE_KG_PER_HA * FOLD_RETURN_ON_SEED_SOWN)
# 742.5 kg/ha - inside the 700-900 kg/ha range data/production/40_organics.json
# itself derives from the same fold-return arithmetic. Not a `declare()`:
# it is arithmetic on two already-declared numbers, not a fact of its own.

# ============================================================================
# LABOUR AND TECHNIQUE
# ============================================================================

REFERENCE_LABOUR_HOURS_PER_HECTARE = declare(
    "REFERENCE_LABOUR_HOURS_PER_HECTARE", 150.0,
    kind="engineering_estimate",
    unit="labourer-hours/hectare/season",
    source="data/production/40_organics.json wheat_kg entry, "
           "labour_hours.labourer: \"cross-ploughing, broadcast sowing, "
           "weeding, sickle reaping, and threshing/winnowing by flail or "
           "ox-treading\" aggregated to about 150 hours/ha.",
    confidence="B",
    why="The labour intensity GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA is "
        "quoted at, and the anchor the Cobb-Douglas yield curve below is "
        "calibrated against. See the module docstring's headline-number "
        "section: this is this module's leading suspect for why the "
        "computed farm-population share comes out far below the "
        "historical 80-90% - a figure covering only cross-ploughing "
        "through winnowing, with no line for cartage, tool upkeep, fallow-"
        "field ploughing or seasonal idle time, is a plausible way to "
        "undercount total pre-mechanical field labour by several times.")

LABOUR_OUTPUT_ELASTICITY = declare(
    "LABOUR_OUTPUT_ELASTICITY", 0.5,
    kind="temporary_heuristic",
    unit="dimensionless (Cobb-Douglas exponent on labour)",
    source=None,
    confidence="C",
    why="The curve shape that makes doubling labour on fixed land yield "
        "less than double the output - Cobb-Douglas in land and labour, "
        "constant returns to the two together, is the standard textbook "
        "way to model exactly that, and agricultural-economics estimates "
        "of labour's output elasticity typically fall in the 0.3-0.6 "
        "range. 0.5 (output scales with the square root of labour hours) "
        "is the midpoint of that range, not a number derived for Roman "
        "wheat specifically - the mechanism that would derive it (an "
        "actual labour-allocation study across ploughing/weeding/harvest "
        "sub-tasks) does not exist yet, which is what makes this a "
        "temporary_heuristic rather than an engineering_estimate.")

ANNUAL_LABOUR_HOURS_PER_FARM_WORKER = declare(
    "ANNUAL_LABOUR_HOURS_PER_FARM_WORKER", 1400.0,
    kind="temporary_heuristic",
    unit="hours/worker/year",
    source=None,
    confidence="C",
    why="How many hours one adult can give to field work across a year, "
        "used only to turn a per-hectare labour requirement into a "
        "hectares-per-worker figure for the headline calibration check. "
        "Pre-industrial farm labour is famously seasonal - concentrated "
        "bursts at ploughing, sowing and harvest separated by slack winter "
        "and midsummer stretches - and 1,200-1,500 hours/year is the "
        "rough order of magnitude that shows up across historical "
        "agricultural-labour estimates for that pattern; 1,400 is a "
        "round midpoint, not a sourced figure for Roman Italy, and is "
        "marked temporary_heuristic rather than engineering_estimate for "
        "exactly that reason - a real seasonal labour calendar (a fixed "
        "number of ploughing days, sowing days, harvest days that cannot "
        "be worked around by adding hands) would derive this instead of "
        "assuming it.")

# ============================================================================
# SEASONALITY: THE HARVEST WINDOW
# ============================================================================
# ANNUAL_LABOUR_HOURS_PER_FARM_WORKER above treats a farm worker's year as a
# single pool of hours that can be spent on any hectare at any time. That is
# the assumption that makes this module's headline number come out at 4.8%,
# and it is wrong for a reason that is biological rather than economic: grain
# does not wait. A wheat field is ready to cut within a span of days, and a
# stand left standing past it shatters at the ear, lodges in wind and rain,
# and is eaten where it stands. Reaping, binding and carting therefore have
# to happen inside a window fixed by the crop, and no amount of slack winter
# time can be moved into it.
#
# So there are two separate ceilings on how much land one worker can crop,
# and the binding one is whichever is smaller:
#
#   annual-hours ceiling    ANNUAL_LABOUR_HOURS_PER_FARM_WORKER
#                           / REFERENCE_LABOUR_HOURS_PER_HECTARE
#   harvest-window ceiling  HARVEST_WINDOW_DAYS
#                           * HECTARES_REAPED_PER_WORKER_DAY
#
# At the constants declared here the second is roughly four times tighter,
# which is the finding: adding hours to the farming year does not raise
# output per worker at all while the harvest window binds. See
# `hectares_cropped_per_farm_worker`.

HARVEST_WINDOW_DAYS = declare(
    "HARVEST_WINDOW_DAYS", 21.0,
    kind="biological_parameter",
    unit="days/year",
    source="The interval between a wheat stand reaching cutting ripeness "
           "and losing grain to shattering, lodging and birds is commonly "
           "given as two to three weeks for landrace cereals cut by hand; "
           "taken here as the upper end of that span, which is the "
           "generous reading for output per worker.",
    confidence="B",
    why="The crop, not the calendar, decides how long the harvest lasts. "
        "This is the length of the one bottleneck a farm cannot schedule "
        "around, and multiplied by HECTARES_REAPED_PER_WORKER_DAY it is "
        "the ceiling on how much land a worker can actually bring in. A "
        "later, real seasonal calendar would derive this from sowing date "
        "and degree-days rather than stating it.")

HECTARES_REAPED_PER_WORKER_DAY = declare(
    "HECTARES_REAPED_PER_WORKER_DAY", 0.10,
    kind="engineering_estimate",
    unit="hectares/worker/day",
    source="Hand reaping with a sickle, including binding into sheaves, is "
           "repeatedly given in pre-mechanical agricultural accounts at "
           "roughly a quarter to a third of an acre per man-day, i.e. "
           "0.10-0.13 ha; taken at the low end, the sickle rather than the "
           "faster scythe, which is what a grain harvest in this period "
           "used (the scythe was a hay tool).",
    confidence="B",
    why="Turns the harvest window from a span of days into an area. Note "
        "what this figure implies about the labour total above: reaping "
        "alone at this rate is on the order of 100 hours per hectare, "
        "which does not fit inside REFERENCE_LABOUR_HOURS_PER_HECTARE's "
        "150 h/ha alongside cross-ploughing, sowing, weeding, threshing "
        "and winnowing. That is independent evidence for the docstring's "
        "suspicion (a) that the 150 h/ha aggregate undercounts, and it is "
        "recorded here rather than acted on, because correcting it means "
        "re-deriving data/production/40_organics.json's labour line from "
        "its sub-tasks, not editing a number in this file.")

# ============================================================================
# ROTATION AND FALLOW
# ============================================================================
# A worker's CROPPED hectares and a farm's TOTAL hectares are not the same
# number, and the difference is the fallow. Under the two-field rotation of
# this period, half a holding lies idle each year to recover nitrogen and to
# let a bare-fallow ploughing kill the weeds that would otherwise take the
# next crop; without heavy manuring there is no way to skip it and keep the
# yield. data/production/40_organics.json states the same halving and says
# explicitly that it "belongs wherever the sim decides how much total land a
# farm needs" - here.
#
# WHAT THIS DOES AND DOES NOT CHANGE. Fallow doubles the land a farm worker
# needs; it does NOT reduce how much food that worker produces, because in
# this module land is not the binding constraint - the harvest window is. A
# worker who crops 2.1 ha needs a 4.2 ha holding and grows exactly as much
# either way. Fallow only starts costing output once land per head runs
# short, i.e. once the land-scarcity mechanism the docstring names as
# missing (b) exists. It is declared now because the land requirement is
# real today and is what a geography or land-allocation domain will need
# from this module; it is deliberately NOT wired into
# fraction_of_population_that_must_farm(), and wiring it in there would be
# double-counting a constraint that is not yet binding.

FALLOW_SHARE_OF_HOLDING = declare(
    "FALLOW_SHARE_OF_HOLDING", 0.5,
    kind="engineering_estimate",
    unit="fraction of holding idle in any one year (dimensionless)",
    source="The two-field rotation - one year cropped, one year bare "
           "fallow - is the standard Mediterranean practice of this "
           "period, named in data/production/40_organics.json's wheat_kg "
           "yield_basis. The later three-field rotation drops the idle "
           "share to one third, which is why this is a property of the "
           "TECHNIQUE and a thing an agricultural improvement should be "
           "able to change, not a constant of nature.",
    confidence="B",
    why="Converts cropped area into the land a farm must actually hold. "
        "Nitrogen and weed pressure, not custom, are why the idle year "
        "exists, so a civilisation that gets legume rotation or reliable "
        "manuring should get this number down and free the land - which "
        "is only representable if the fallow is a named share rather than "
        "baked into a yield figure.")

# ============================================================================
# WEATHER
# ============================================================================
# One multiplicative draw per year, not a daily process - see Storage.step.
# The mean sits at 1.0 (an average year reproduces the reference yield); the
# spread and the clipping bounds are what makes a bad year a bad year rather
# than a rounding error.

WEATHER_YIELD_STDEV_FRACTION = declare(
    "WEATHER_YIELD_STDEV_FRACTION", 0.20,
    kind="engineering_estimate",
    unit="fraction of mean yield (dimensionless standard deviation)",
    source="Order-of-magnitude figure from agricultural-history literature "
           "on pre-industrial cereal yield variability, which commonly "
           "reports year-to-year coefficients of variation in roughly the "
           "15-25% band for rain-fed Mediterranean and temperate grain.",
    confidence="C",
    why="How much one year's weather can move the harvest away from the "
        "reference yield before technique or land quality are considered "
        "at all - this is the whole mechanism behind 'a bad year cuts "
        "output', so it has to be wide enough to bite.")

WEATHER_FLOOR_MULTIPLIER = declare(
    "WEATHER_FLOOR_MULTIPLIER", 0.15,
    kind="temporary_heuristic",
    unit="fraction of mean yield (dimensionless)",
    source=None,
    confidence="D",
    why="A Gaussian draw has no natural floor and can go negative, which a "
        "harvest cannot. This clips the worst year to 15% of normal rather "
        "than zero, on the reasoning that total, literal crop failure "
        "across an entire hectare is rare even in famine years (some "
        "gleaning, some resowing, some partial stand always survives) - "
        "but the specific number is an invented safety clip, not a "
        "modelled drought or blight mechanism, pending one.")

WEATHER_CEILING_MULTIPLIER = declare(
    "WEATHER_CEILING_MULTIPLIER", 1.3,
    kind="temporary_heuristic",
    unit="fraction of mean yield (dimensionless)",
    source=None,
    confidence="D",
    why="Symmetric-ish upside clip on the same Gaussian draw, on the "
        "reasoning that a single exceptional year cannot outrun the land's "
        "own biological ceiling by an unbounded amount. Invented, like the "
        "floor, pending an actual weather/climate model with its own "
        "upper bound.")

# ============================================================================
# STORAGE AND SPOILAGE
# ============================================================================

GRAIN_SPOILAGE_RATE_PER_YEAR = declare(
    "GRAIN_SPOILAGE_RATE_PER_YEAR", 0.08,
    kind="engineering_estimate",
    unit="fraction of stored grain lost/year (dimensionless)",
    source="Commonly cited range for ancient/medieval grain storage loss "
           "to pests, rot and rodents (pit silos and raised granaries) is "
           "roughly 5-15% per annum; taken as a round figure inside that "
           "range.",
    confidence="C",
    why="What a granary costs you for keeping grain past this year's "
        "harvest, which is what makes carrying a buffer stock against a "
        "bad year a real trade-off rather than a free option. Applies "
        "after this year's consumption is drawn, to whatever is left "
        "sitting in storage - see Storage.step.")

# ============================================================================
# HUMAN FOOD DEMAND
# ============================================================================

DAYS_PER_YEAR = declare(
    "DAYS_PER_YEAR", 365.25,
    kind="physical_constant",
    unit="days/year",
    source="Julian calendar year average.",
    confidence="A",
    why="Converts every annual figure in this module to and from a daily "
        "rate - in particular, what Storage.step hands demography.py as "
        "food_available_calories_per_day.")

HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY = declare(
    "HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY", 2200.0,
    kind="biological_parameter",
    unit="kcal/adult/day",
    source="FAO minimum dietary energy requirement, adult average - the "
           "same figure and source sim/world/demography.py's own "
           "SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY uses. Declared "
           "again here under a different name, deliberately, rather than "
           "imported from that module: the two modules are built and "
           "tested standalone (see this module's docstring), and a cross-"
           "import between them would be exactly the wiring neither of "
           "them is supposed to do yet.",
    confidence="B",
    why="The denominator of how much land one person's diet requires. "
        "Kept independent of demography.py's identical constant so this "
        "module has no import-time dependency on a file another agent is "
        "actively writing.")

WHEAT_ENERGY_KCAL_PER_KG = declare(
    "WHEAT_ENERGY_KCAL_PER_KG", 3400.0,
    kind="biological_parameter",
    unit="kcal/kg",
    source="Standard food-composition figures for whole wheat grain "
           "(on the order of 3,300-3,400 kcal/kg); matches the figure "
           "named in the task that produced this module.",
    confidence="A",
    why="Converts between kilograms of grain (what this module produces "
        "and moves through storage) and calories (what a person, and "
        "demography.py's nutrition ratio, actually needs).")

# ============================================================================
# CALIBRATION TARGETS - never inputs to anything above. See sim/constants.py:
# "an observation used to CHECK the model." These two numbers are used only
# in sim/tests/test_agriculture.py, to report the headline discrepancy the
# module docstring describes; nothing in this file's production code reads
# them, and they must never be adjusted to make a computed figure agree.
# ============================================================================

HISTORICAL_FARM_POPULATION_SHARE_LOW = declare(
    "HISTORICAL_FARM_POPULATION_SHARE_LOW", 0.80,
    kind="calibration_target",
    unit="fraction of population (dimensionless)",
    source="CLAUDE.md SS3.2 / the task that produced this module: "
           "pre-industrial societies typically show 80-90% of the "
           "population engaged in farming.",
    confidence="B",
    why="The low end of the range this module's computed "
        "fraction_of_population_that_must_farm() is checked against, "
        "never tuned to.")

HISTORICAL_FARM_POPULATION_SHARE_HIGH = declare(
    "HISTORICAL_FARM_POPULATION_SHARE_HIGH", 0.90,
    kind="calibration_target",
    unit="fraction of population (dimensionless)",
    source="Same as HISTORICAL_FARM_POPULATION_SHARE_LOW.",
    confidence="B",
    why="The high end of the same range.")


def annual_food_demand_kg_per_person():
    """One person's grain-equivalent food need for a year, in kilograms.

    A single-staple simplification, same as the rest of this module: real
    pre-industrial diets were not 100% grain calories (legumes, oil, wine,
    some meat and dairy filled in the rest), which this module cannot
    represent with one crop. That simplification runs in the direction of
    UNDERSTATING how much land a real diet needs, since grain is generally
    the highest-yield-per-hectare calorie source available - see the module
    docstring's headline-number reading for how this bears on the computed
    farm-population share coming out low rather than high.
    """
    return (HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY * DAYS_PER_YEAR
            / WHEAT_ENERGY_KCAL_PER_KG)


class Land(object):
    """A parcel of ground: how big, and how good.

    `quality` is a plain multiplier on yield, 1.0 being the "decent land"
    baseline data/production/40_organics.json's own wheat entry describes.
    Nothing here enforces a range - a quality of 0.5 (poor, marginal land)
    or 1.3 (an unusually good river-silt field) are both legitimate inputs.
    This is deliberately the only place land heterogeneity lives: the
    EXTENSIVE MARGIN (bringing worse land under the plough once the best
    land is fully worked) is a real and important later feature, and it
    only has somewhere to attach because quality is a property of the land,
    not folded into a single society-wide yield number.
    """

    __slots__ = ("hectares", "quality")

    def __init__(self, hectares, quality=1.0):
        if hectares < 0:
            raise ValueError("hectares cannot be negative: %r" % (hectares,))
        if quality <= 0:
            raise ValueError("quality must be positive: %r" % (quality,))
        self.hectares = float(hectares)
        self.quality = float(quality)

    def __repr__(self):
        return "Land(hectares=%.4f, quality=%.4f)" % (self.hectares, self.quality)


def draw_weather_multiplier(rng):
    """One year's weather, as a single multiplier on yield.

    Not a daily process - see the module docstring's SHAPE section for why
    an annual draw is enough here. `rng` is an ordinary `random.Random`
    owned by the caller (`Storage` keeps one per instance), so the same
    seed reproduces the same sequence of years exactly, every time, in the
    same process - see sim/tests/test_agriculture.py's determinism check.
    """
    draw = rng.gauss(1.0, WEATHER_YIELD_STDEV_FRACTION)
    return max(WEATHER_FLOOR_MULTIPLIER, min(WEATHER_CEILING_MULTIPLIER, draw))


def _total_factor_productivity_per_ha():
    """The Cobb-Douglas scale constant, chosen so that farming `Land` of
    quality 1.0 at exactly REFERENCE_LABOUR_HOURS_PER_HECTARE hours/hectare,
    with technique and weather both at 1.0, reproduces
    GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA exactly. See gross_harvest_kg
    for the full expression this feeds.
    """
    return (GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA
            / (REFERENCE_LABOUR_HOURS_PER_HECTARE ** LABOUR_OUTPUT_ELASTICITY))


def gross_harvest_kg(land, labour_hours, technique_multiplier=1.0,
                      weather_multiplier=1.0):
    """Grain reaped from `land` this season, in kilograms, BEFORE seed is
    paid back or anything is eaten or spoiled - the same "gross" the module
    docstring's DISAGREEMENT section discusses.

    The functional form is Cobb-Douglas in land and labour: constant
    returns to scale in the two together (double both and you double the
    harvest, which is just saying a second, identical field worked the
    same way produces the same as the first), but LABOUR_OUTPUT_ELASTICITY
    < 1 means that on a FIXED parcel, output grows slower than labour does.
    That is the single most important property this module has to get
    right: a linear yield-to-labour relationship would never produce a
    population ceiling, because a large enough population working small
    enough plots would always find some marginal-but-positive use for one
    more hour, right up to the point that fails to happen in reality.

    `land.quality`, `technique_multiplier` and `weather_multiplier` all
    enter as plain multipliers on top of the land/labour curve - none of
    them changes its SHAPE (the diminishing-returns property holds at any
    quality, technique or weather draw), only its level.
    """
    if labour_hours <= 0.0 or land.hectares <= 0.0:
        return 0.0
    total_factor_productivity = _total_factor_productivity_per_ha()
    per_land_component = land.hectares ** (1.0 - LABOUR_OUTPUT_ELASTICITY)
    per_labour_component = labour_hours ** LABOUR_OUTPUT_ELASTICITY
    return (total_factor_productivity * per_land_component * per_labour_component
            * land.quality * technique_multiplier * weather_multiplier)


def marginal_product_of_labour_kg_per_hour(land, labour_hours,
                                            technique_multiplier=1.0,
                                            weather_multiplier=1.0):
    """Extra kilograms of grain the NEXT hour of labour on `land` would add,
    at the current `labour_hours` already applied.

    Closed form rather than a finite difference: for
    harvest = TFP * H^(1-a) * L^a * (other multipliers), d(harvest)/dL =
    a * TFP * H^(1-a) * L^(a-1) * (...) = a * harvest / L. This is exactly
    what the labour market needs to decide whether one more hour of a
    worker's time is worth more on the farm or somewhere else - "the
    surplus is what frees a worker to do anything else" only has a hiring
    boundary once something can say what the marginal farm hour is worth in
    grain. It falls strictly as labour_hours rises (LABOUR_OUTPUT_ELASTICITY
    < 1), which is the same diminishing-returns property gross_harvest_kg
    has, stated as a rate instead of a level - see
    sim/tests/test_agriculture.py's diminishing-returns check, which tests
    this function directly rather than inferring monotonicity from harvest
    totals.
    """
    if labour_hours <= 0.0:
        raise ValueError("marginal product is undefined at zero labour hours")
    harvest = gross_harvest_kg(land, labour_hours, technique_multiplier,
                               weather_multiplier)
    return LABOUR_OUTPUT_ELASTICITY * harvest / labour_hours


YearFlows = collections.namedtuple(
    "YearFlows",
    ["weather_multiplier", "labour_hours_applied", "seed_sown_kg",
     "gross_harvest_kg", "food_demand_kg", "consumption_kg",
     "food_shortfall_kg", "spoilage_kg", "seed_retained_kg", "carryover_kg",
     "stock_before_kg", "stock_after_kg", "food_available_kcal_per_day",
     "marginal_product_last_hour_kg_per_hour"])


class Storage(object):
    """Grain in the granary, and the one-year cycle that moves it.

    `stock_kg` is the only state. Everything else (which land, how much
    labour, what technique, how many mouths) is passed into `step()` fresh
    each year, exactly like sim/world/demography.py's `Population.step` -
    the two modules were built independently but ended up with the same
    shape (mutate one small piece of state in place, return an immutable
    record of the flows that produced the new state) because it is the
    natural shape for "advance one tick of an otherwise stateless process".
    """

    def __init__(self, stock_kg=0.0, seed=None):
        self.stock_kg = float(stock_kg)
        self._random = random.Random(seed)

    def __repr__(self):
        return "Storage(stock_kg=%.4f)" % (self.stock_kg,)

    def step(self, land, labour_hours, population, technique_multiplier=1.0,
             hectares_next_year=None):
        """Advance one year: sow, grow, harvest, eat, spoil, retain next
        year's seed, bank whatever is left. Mutates `self.stock_kg` and
        returns the exact flows that moved it.

        ORDER OF OPERATIONS (fixed, so the same inputs always give the same
        answer regardless of what order someone might otherwise compute
        things in - see sim/world/demography.py's `Population.step` for the
        same discipline applied to births and deaths):

          1. Seed leaves storage to be sown, at SEED_SOWING_RATE_KG_PER_HA
             times `land.hectares`. This can drive `self.stock_kg` negative
             if not enough was banked - sowing still happens in full rather
             than being silently capped, because a household that plants
             less than it needs to because it already ate its seed corn is
             not a bug, it is the mechanism by which one bad harvest
             becomes two. Nothing here forbids that state; it just makes it
             visible in `carryover_kg` and `stock_after_kg`.
          2. This year's weather is drawn (`draw_weather_multiplier`) and
             the harvest is computed from what was just sown, at the given
             labour and technique. The harvest enters storage.
          3. Consumption is drawn from storage up to `food_demand_kg`
             (population's need for the full year, from
             `annual_food_demand_kg_per_person`) or up to whatever storage
             actually holds, whichever is smaller - `food_shortfall_kg` is
             the gap when storage cannot cover the full year's need.
          4. Spoilage is GRAIN_SPOILAGE_RATE_PER_YEAR of whatever remains
             after consumption - it applies to the SURPLUS sitting in the
             granary, not to what has already been eaten or was never
             harvested.
          5. Next year's seed (SEED_SOWING_RATE_KG_PER_HA times
             `hectares_next_year`, defaulting to this year's `land.hectares`
             if the planted area is not changing) is set aside. What is
             left after that is `carryover_kg`: the free buffer this
             household is banking against a future bad year. It can be
             negative - see step 1.

        The identity `stock_before_kg + gross_harvest_kg - seed_sown_kg -
        consumption_kg - spoilage_kg - seed_retained_kg == stock_after_kg`
        holds EXACTLY, every year, by construction (every step above either
        adds to `self.stock_kg` or subtracts from it, and nothing is
        double-counted) - see sim/tests/test_agriculture.py's conservation
        check.
        """
        stock_before_kg = self.stock_kg
        if hectares_next_year is None:
            hectares_next_year = land.hectares

        seed_sown_kg = SEED_SOWING_RATE_KG_PER_HA * land.hectares
        self.stock_kg -= seed_sown_kg

        weather_multiplier = draw_weather_multiplier(self._random)
        harvest_kg = gross_harvest_kg(land, labour_hours, technique_multiplier,
                                      weather_multiplier)
        self.stock_kg += harvest_kg

        food_demand_kg = population * annual_food_demand_kg_per_person()
        consumption_kg = max(0.0, min(food_demand_kg, self.stock_kg))
        food_shortfall_kg = max(0.0, food_demand_kg - consumption_kg)
        self.stock_kg -= consumption_kg

        spoilage_kg = max(0.0, self.stock_kg) * GRAIN_SPOILAGE_RATE_PER_YEAR
        self.stock_kg -= spoilage_kg

        seed_retained_kg = SEED_SOWING_RATE_KG_PER_HA * hectares_next_year
        self.stock_kg -= seed_retained_kg

        carryover_kg = self.stock_kg
        stock_after_kg = self.stock_kg

        if labour_hours > 0.0:
            marginal_product = marginal_product_of_labour_kg_per_hour(
                land, labour_hours, technique_multiplier, weather_multiplier)
        else:
            marginal_product = 0.0

        food_available_kcal_per_day = (
            consumption_kg * WHEAT_ENERGY_KCAL_PER_KG / DAYS_PER_YEAR)

        return YearFlows(
            weather_multiplier=weather_multiplier,
            labour_hours_applied=labour_hours,
            seed_sown_kg=seed_sown_kg,
            gross_harvest_kg=harvest_kg,
            food_demand_kg=food_demand_kg,
            consumption_kg=consumption_kg,
            food_shortfall_kg=food_shortfall_kg,
            spoilage_kg=spoilage_kg,
            seed_retained_kg=seed_retained_kg,
            carryover_kg=carryover_kg,
            stock_before_kg=stock_before_kg,
            stock_after_kg=stock_after_kg,
            food_available_kcal_per_day=food_available_kcal_per_day,
            marginal_product_last_hour_kg_per_hour=marginal_product)


def hectares_per_worker_annual_hours_ceiling():
    """One of the two ceilings on a farm worker's cropped area: total hours
    in the farming year divided by hours needed per hectare. This is the
    only ceiling this module originally had, and treating it as the answer
    is what produced the 4.8% headline figure. See
    `hectares_cropped_per_farm_worker`.
    """
    return ANNUAL_LABOUR_HOURS_PER_FARM_WORKER / REFERENCE_LABOUR_HOURS_PER_HECTARE


def hectares_per_worker_harvest_window_ceiling():
    """The other ceiling: how much a worker can reap before the standing
    crop is lost. Days in the window times hectares reaped per day - see
    the SEASONALITY section above for why the window is a fact about the
    crop rather than about the farmer's schedule.
    """
    return HARVEST_WINDOW_DAYS * HECTARES_REAPED_PER_WORKER_DAY


def hectares_cropped_per_farm_worker():
    """How many hectares one farm worker actually brings in, in a year:
    the smaller of the two ceilings above, because a constraint you can
    satisfy is not a constraint.

    At the constants declared in this file the harvest window is the
    binding one by roughly four to one, and that is the substantive
    finding: adding hours to the farming year, or shifting
    REFERENCE_LABOUR_HOURS_PER_HECTARE, changes this number not at all
    while the window binds. Anything that raises output per worker here
    has to raise HECTARES_REAPED_PER_WORKER_DAY (a better tool - the
    scythe, later the cradle, later the reaper) or lengthen
    HARVEST_WINDOW_DAYS (staggered sowing dates, or two crops with
    different ripening times), which is the correct shape: those are what
    historically moved it.
    """
    return min(hectares_per_worker_annual_hours_ceiling(),
               hectares_per_worker_harvest_window_ceiling())


def holding_hectares_required_per_farm_worker():
    """How much land the farm must HOLD to keep one worker cropping - the
    cropped area grossed up for the fallow that is idle this year. See the
    ROTATION AND FALLOW section for why this is a land requirement and not
    a reduction in output: nothing below reads it, deliberately.
    """
    return hectares_cropped_per_farm_worker() / (1.0 - FALLOW_SHARE_OF_HOLDING)


def fraction_of_population_that_must_farm():
    """The headline calibration figure: what share of a population must be
    farmers to feed the whole population, computed purely from this
    module's declared constants at reference land quality, technique and an
    average weather year - no calibration_target anywhere in this
    computation, by construction (HISTORICAL_FARM_POPULATION_SHARE_LOW/HIGH
    are read by the test that CHECKS this number, never by this function).

    output_per_worker_kg is how much food (net of seed, net of spoilage) one
    full-time farm worker produces in a year; annual_food_demand_kg_per_
    person is how much food one person (including that worker) needs.
    Their ratio is the number of people one farm worker can feed, and its
    reciprocal is the fraction of a population that has to farm.

    See the module docstring's ON THE HEADLINE NUMBER section for the
    result this produces (roughly 21%, still well below the 80-90%
    pre-industrial societies actually show) and for the four named
    reasons the remainder of that gap is not a defect in this
    arithmetic. Note in particular reason (a): this function counts
    full-time-equivalent WORKERS, and the 80-90% target counts everyone
    living in a farming household, so the two are not directly
    comparable as they stand.
    """
    net_yield_after_seed_kg_per_ha = (
        GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA - SEED_SOWING_RATE_KG_PER_HA)
    food_available_per_ha_kg = (
        net_yield_after_seed_kg_per_ha * (1.0 - GRAIN_SPOILAGE_RATE_PER_YEAR))
    output_per_worker_kg = (
        hectares_cropped_per_farm_worker() * food_available_per_ha_kg)
    return annual_food_demand_kg_per_person() / output_per_worker_kg


if __name__ == "__main__":
    # A quick, human-readable readout - the same kind of thing
    # sim/constants.py and sim/audit_costs.py print on demand, for whoever
    # next wants to see this module's headline number without opening a
    # test file.
    fraction = fraction_of_population_that_must_farm()
    print("gross yield at reference labour: %.1f kg/ha"
          % GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA)
    print("net of seed, net of spoilage:     %.1f kg/ha"
          % ((GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA - SEED_SOWING_RATE_KG_PER_HA)
             * (1.0 - GRAIN_SPOILAGE_RATE_PER_YEAR)))
    print("hectares one worker could work on annual hours alone: %.2f"
          % hectares_per_worker_annual_hours_ceiling())
    print("hectares one worker can reap inside the harvest window: %.2f"
          % hectares_per_worker_harvest_window_ceiling())
    print("hectares actually cropped per worker (the binding one): %.2f"
          % hectares_cropped_per_farm_worker())
    print("holding needed per worker, grossed up for fallow: %.2f ha"
          % holding_hectares_required_per_farm_worker())
    print("people fed per full-time farm worker: %.1f"
          % (1.0 / fraction))
    print("fraction of population that must farm: %.1f%%" % (100.0 * fraction))
    print("historical calibration target:        %.0f-%.0f%%"
          % (100.0 * HISTORICAL_FARM_POPULATION_SHARE_LOW,
             100.0 * HISTORICAL_FARM_POPULATION_SHARE_HIGH))
