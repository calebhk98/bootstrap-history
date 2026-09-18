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

ONE CROP BY DEFAULT, NOT ONE CROP BY CONSTRUCTION. The module started with
wheat as the only representable crop, following the instruction to not model
a dozen crops and `data/production/40_organics.json`, which already carries
the tree's own wheat numbers. That was too rigid: the stakeholder's own
objection is that fertiliser, rotation, a better crop, better land, better
draught power and better storage all have to be able to change the answer,
and a module with every parameter hardcoded to one crop-soil-technique
combination cannot represent any of them (CLAUDE.md SS3.1). So the numbers
below are now organised as small tables - `Crop`, `Soil`, `Rotation`,
`Toolkit`, `StorageTechnique` - each one a named bundle of declared numbers
for one instance of that axis (wheat vs potatoes vs rice; ordinary
Mediterranean loam vs Ukrainian chernozem vs arctic tundra; two-field vs
three-field vs Nile flood-recession farming; ard-and-ox vs horse-collar-and-
mouldboard vs a mechanical reaper; a pit silo vs a refrigerated store).
Every function below takes these as optional arguments and defaults to the
ORIGINAL wheat/ordinary-soil/two-field/ard-and-sickle/pit-silo combination,
so the headline number this module has always reported is unchanged -
`sim/tests/test_agriculture.py` pins that. Diminishing returns to labour on
fixed land is still the one property that has to hold at every combination,
and it does, because every table just rescales the same Cobb-Douglas curve;
see `gross_harvest_kg`.

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

THE HARVEST WINDOW NOW ALSO BINDS gross_harvest_kg, NOT ONLY THE HEADLINE
CALIBRATION. HARVEST_WINDOW_DAYS and HECTARES_REAPED_PER_WORKER_DAY used to be
read only by `hectares_per_worker_harvest_window_ceiling`, which feeds the
headline calibration function - `gross_harvest_kg`, the function `Storage.
step` actually calls every year, never saw them, so it would gladly turn an
arbitrarily large pool of labour_hours applied to an arbitrarily large `Land`
into a harvest no crew could physically have reaped inside a real harvest
season. `gross_harvest_kg` now converts its `labour_hours` pool into
worker-year-equivalents (dividing by ANNUAL_LABOUR_HOURS_PER_FARM_WORKER, the
same conversion `hectares_cropped_per_farm_worker` already uses) and caps the
LAND that actually contributes to the harvest at what that many workers could
crop inside the window - see `_max_hectares_harvestable_by_labour`. This is
why an actor with unlimited hours (autonomous labour; a robot) does not get
an unlimited harvest from a fixed crew size: more hours from the SAME
worker-equivalents cannot buy more reaped area once the window and the
reaping rate are already saturated, only more worker-equivalents can, and
those still each carry the same per-worker cap. Loosening the cap needs a
higher HECTARES_REAPED_PER_WORKER_DAY (a better reaping tool) or more
HARVEST_WINDOW_DAYS (staggered ripening) - not more hours on the same crew.

SHAPE.
    Crop          a named bundle: how much planting material a hectare
                  needs, its fold-return on that material, its calories per
                  kilogram, how many days its harvest can be spread over
                  before loss, and its own labour and reaping-rate baseline
                  under a reference toolkit. Wheat is the default; see the
                  CROP TABLE section.
    Soil          a named bundle: a yield quality multiplier and a weather
                  variability, both properties of a PLACE rather than of
                  the crop grown there or the technique used to grow it.
                  See the SOIL TABLE section for why "no growing season"
                  (arctic) and "no water" (desert) are recorded as the same
                  kind of scalar as poor fertility even though they are a
                  different physical thing - this module cannot yet tell
                  them apart, and says so.
    Rotation      a named bundle: the fallow share of a holding and a
                  soil-fertility yield multiplier, moving together because
                  both come from the same underlying fact - nitrogen. Two-
                  field, three-field and Nile flood-recession farming are
                  three points on the same axis, not three special cases.
    Toolkit       a named bundle: a labour-hours multiplier (tools and
                  draught power that speed up ploughing/sowing/weeding), a
                  reaping-rate multiplier (tools that speed up the harvest
                  specifically, which is what the harvest window responds
                  to) and a ploughing-yield multiplier (a mouldboard turning
                  the soil better than an ard). The horse collar and the
                  scythe are two different toolkits because they change two
                  different multipliers.
    StorageTechnique  a named bundle: a spoilage rate. A pit silo, a raised
                  granary and a refrigerated store differ only here.
    Land          hectares plus a quality multiplier - not all land is
                  equal, and that difference is what makes the extensive
                  margin (worse land, brought under the plough when better
                  land runs out) a real, representable choice later. A
                  `Soil`'s `quality_multiplier` is what a caller hands to
                  `Land(hectares, quality=...)`; `Land` itself stays a plain
                  number so nothing here forces a caller to name a `Soil` at
                  all.
    Yield         a Cobb-Douglas function of land and labour, constant
                  returns to scale in the two together but with an
                  output elasticity on labour below 1, which is exactly
                  what makes the marginal product of an additional hour of
                  labour on FIXED land fall as more hours are added - see
                  LABOUR_OUTPUT_ELASTICITY's declaration for why this
                  specific functional form and not some other diminishing
                  curve. The `Crop` and `Toolkit` in force change the curve's
                  scale and its labour reference point; they never change
                  this shape.
    Weather       one multiplicative draw per year, deterministic given a
                  seed (an ordinary `random.Random` owned by `Storage`),
                  not a daily process. Its spread is a `Soil` property.
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

HOURS_PER_DAY = declare(
    "HOURS_PER_DAY", 24.0,
    kind="physical_constant",
    unit="hours/day",
    source="One rotation of the Earth.",
    confidence="A",
    why="The hard ceiling on how much any actor - human, animal or "
        "autonomous - can work in a day. It is here so that the harvest "
        "cap cannot be beaten by handing it an absurd hours-per-day "
        "figure: a robot that never sleeps gets 24, not 30.")

HARVEST_WORKING_DAY_HOURS = declare(
    "HARVEST_WORKING_DAY_HOURS", 10.0,
    kind="engineering_estimate",
    unit="hours/worker/day",
    source="The reaping rates this module uses are quoted per MAN-DAY, and "
           "a harvest man-day in pre-mechanical agriculture is a long one - "
           "dawn to dusk, because the window is short and the weather "
           "decides. Ten hours is the round figure that the quarter-acre-"
           "per-man-day reaping rate is conventionally understood against.",
    confidence="C",
    why="The bridge between a rate quoted PER DAY and a labour pool "
        "measured in HOURS. Without it there is no way to ask what an "
        "actor that works more hours per day can reap, because the per-day "
        "rate silently assumes a human working day. "
        "HECTARES_REAPED_PER_WORKER_DAY divided by this is the "
        "instantaneous reaping rate in hectares per hour, and the product "
        "of the two is unchanged, so declaring it moves no existing "
        "number. See `max_hectares_reapable_by_crew`.")

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
# CROP, SOIL, ROTATION, TOOLKIT AND STORAGE-TECHNIQUE TABLES
# ============================================================================
# Everything above this line is a scalar constant for wheat, on ordinary
# Mediterranean soil, under two-field rotation, worked with an ard and a
# sickle, stored in a pit silo. That is one point in a much larger space,
# and the stakeholder's objection (recorded in the task that produced this
# section) is exactly CLAUDE.md SS3.1: a better crop, a better rotation, a
# better tool or better storage all have to be able to change the answer,
# and none of them could while every parameter was a single number.
#
# The five tables below give each axis its own named bundle of numbers. Each
# bundle is a `collections.namedtuple` rather than a bare dict so a caller
# gets an AttributeError instead of a silent KeyError typo, and so `declare`
# still has one clearly-named constant per number - a table is a way of
# GROUPING declared numbers, not an escape from declaring them.
#
# THE DEFAULT OF EACH TABLE REPRODUCES THE ORIGINAL SCALARS EXACTLY. Every
# function below (`gross_harvest_kg`, `hectares_cropped_per_farm_worker`,
# `fraction_of_population_that_must_farm`, ...) takes these as optional
# keyword arguments defaulting to DEFAULT_CROP / DEFAULT_SOIL / DEFAULT_
# ROTATION / DEFAULT_TOOLKIT / DEFAULT_STORAGE_TECHNIQUE, built from the
# already-declared constants above rather than new numbers, so calling any
# function with no table arguments at all computes bit-for-bit what this
# module always computed. `sim/tests/test_agriculture.py`'s pinned 0.21181
# is what proves that.


Crop = collections.namedtuple("Crop", [
    "name",
    "planting_material_kg_per_ha",           # seed grain, seed tubers, ...
    "fold_return_on_planting_material",       # kg harvested / kg planted
    "energy_kcal_per_kg",
    "harvest_window_days",
    "base_labour_hours_per_hectare",          # under this crop's OWN
                                               # reference toolkit
    "base_hectares_reaped_per_worker_day",    # under that same toolkit
])

Soil = collections.namedtuple("Soil", [
    "name",
    "quality_multiplier",        # plain multiplier on yield - fed to
                                  # Land(hectares, quality=...)
    "weather_stdev_fraction",    # how much one year's weather can move the
                                  # harvest away from reference, at this place
    "limiting_factor",           # documentation only, not read by any
                                  # computation: "fertility", "growing_season"
                                  # or "water" - see the SOIL TABLE section
                                  # for why this matters even unused.
])

Rotation = collections.namedtuple("Rotation", [
    "name",
    "fallow_share_of_holding",           # land fact - see ROTATION AND
                                          # FALLOW above; never read by
                                          # fraction_of_population_that_
                                          # must_farm, only by the holding
                                          # calculation.
    "soil_fertility_yield_multiplier",   # the OTHER half of the same
                                          # nitrogen fact: less fallow
                                          # needed and higher yield both
                                          # come from more nitrogen reaching
                                          # the field, whether from a
                                          # legume fallow, manure, guano or
                                          # a river's silt.
])

Toolkit = collections.namedtuple("Toolkit", [
    "name",
    "labour_hours_multiplier",       # tools/draught power that speed up
                                      # ploughing, sowing and weeding
    "reaping_rate_multiplier",       # tools that speed up the HARVEST
                                      # specifically - what the harvest
                                      # window's ceiling responds to
    "ploughing_yield_multiplier",    # a mouldboard turning and burying
                                      # weeds/stubble better than an ard;
                                      # a yield effect independent of the
                                      # labour saved
])

StorageTechnique = collections.namedtuple("StorageTechnique", [
    "name",
    "spoilage_rate_per_year",
])


DEFAULT_CROP = Crop(
    name="wheat",
    planting_material_kg_per_ha=SEED_SOWING_RATE_KG_PER_HA,
    fold_return_on_planting_material=FOLD_RETURN_ON_SEED_SOWN,
    energy_kcal_per_kg=WHEAT_ENERGY_KCAL_PER_KG,
    harvest_window_days=HARVEST_WINDOW_DAYS,
    base_labour_hours_per_hectare=REFERENCE_LABOUR_HOURS_PER_HECTARE,
    base_hectares_reaped_per_worker_day=HECTARES_REAPED_PER_WORKER_DAY)

DEFAULT_SOIL = Soil(
    name="ordinary_mediterranean_loam",
    quality_multiplier=1.0,
    weather_stdev_fraction=WEATHER_YIELD_STDEV_FRACTION,
    limiting_factor="fertility")

DEFAULT_ROTATION = Rotation(
    name="two_field",
    fallow_share_of_holding=FALLOW_SHARE_OF_HOLDING,
    soil_fertility_yield_multiplier=1.0)

DEFAULT_TOOLKIT = Toolkit(
    name="ard_and_ox_with_sickle",
    labour_hours_multiplier=1.0,
    reaping_rate_multiplier=1.0,
    ploughing_yield_multiplier=1.0)

DEFAULT_STORAGE_TECHNIQUE = StorageTechnique(
    name="pit_silo_or_raised_granary",
    spoilage_rate_per_year=GRAIN_SPOILAGE_RATE_PER_YEAR)


# ----------------------------------------------------------------------
# CROP TABLE - alternatives to wheat.
#
# FOLD_RETURN_ON_SEED_SOWN and SEED_SOWING_RATE_KG_PER_HA were declared
# above as if they were facts of agriculture in general; they are facts
# about wheat. Potatoes are not sown from true seed at all - they are
# grown from seed TUBERS, a fraction of a previous harvest set aside the
# same way seed grain is - and yield several times wheat's calories per
# hectare from a much smaller "seed" input. Rice under paddy cultivation is
# transplanted from a small nursery bed, so its "seed" per hectare of FINAL
# field is tiny and its fold-return figure correspondingly huge; that is a
# real property of the technique, not an error.
#
# NEITHER of these is a claim that irrigation or paddy engineering is
# modelled - it explicitly is not (see this module's NON-GOALS in the task
# that produced it). Rice's numbers below assume the water is already
# there; they describe what a hectare of already-flooded paddy does, not
# how the flooding happens.
# ----------------------------------------------------------------------

POTATO_PLANTING_MATERIAL_KG_PER_HA = declare(
    "POTATO_PLANTING_MATERIAL_KG_PER_HA", 1600.0,
    kind="engineering_estimate",
    unit="kg seed tubers/hectare",
    source="Pre-mechanical seed-potato planting rates are commonly given in "
           "the 1,200-2,000 kg/ha range (whole or cut tubers spaced by "
           "hand); taken as a round midpoint.",
    confidence="C",
    why="Potato's equivalent of SEED_SOWING_RATE_KG_PER_HA - what a hectare "
        "must be planted with before anything is harvested - but of seed "
        "TUBERS, not seed grain, which is why potatoes need their own "
        "planting-material number rather than reusing wheat's.")

POTATO_FOLD_RETURN_ON_SEED_TUBERS = declare(
    "POTATO_FOLD_RETURN_ON_SEED_TUBERS", 8.0,
    kind="engineering_estimate",
    unit="kg harvested / kg seed tuber planted (dimensionless)",
    source="Early modern/pre-mechanical potato accounts commonly report "
           "roughly eight- to tenfold return by weight on seed tubers "
           "planted; taken at the low end of that range. At "
           "POTATO_PLANTING_MATERIAL_KG_PER_HA this implies about 12.8 "
           "t/ha gross, inside the commonly cited 10-15 t/ha range for "
           "pre-modern potato cultivation - an independent sanity check, "
           "not something this number was tuned to hit.",
    confidence="C",
    why="Potato's equivalent of FOLD_RETURN_ON_SEED_SOWN - the crop's own "
        "biological response to being planted at all - stated separately "
        "because it is a different multiple of a different base, not "
        "because potatoes are 'better wheat'.")

POTATO_ENERGY_KCAL_PER_KG = declare(
    "POTATO_ENERGY_KCAL_PER_KG", 770.0,
    kind="biological_parameter",
    unit="kcal/kg",
    source="Standard food-composition figures for raw potato (roughly "
           "750-790 kcal/kg, mostly water and starch).",
    confidence="B",
    why="Converts kilograms of potato into the same calorie currency wheat "
        "is measured in, so annual_food_demand_kg_per_person and the "
        "headline farm-population share can be computed for either crop on "
        "the same footing. Note this is under a THIRD of wheat's kcal/kg - "
        "potatoes need more kilograms, not fewer, to feed the same person; "
        "their advantage is calories per HECTARE, which comes from the "
        "yield side, not this number.")

POTATO_HARVEST_WINDOW_DAYS = declare(
    "POTATO_HARVEST_WINDOW_DAYS", 45.0,
    kind="biological_parameter",
    unit="days/year",
    source="Tubers left in the ground do not shatter or lodge the way a "
           "standing grain crop does; the practical limit is the first "
           "hard frost or a wet autumn making the ground unworkable, which "
           "commonly gives several weeks of workable lifting time rather "
           "than wheat's two to three - taken here as roughly double "
           "HARVEST_WINDOW_DAYS.",
    confidence="C",
    why="Potato's equivalent of HARVEST_WINDOW_DAYS. A longer window for "
        "the same reaping rate loosens the harvest-window ceiling on its "
        "own, independent of the labour-hours story - see "
        "hectares_per_worker_harvest_window_ceiling.")

POTATO_BASE_LABOUR_HOURS_PER_HECTARE = declare(
    "POTATO_BASE_LABOUR_HOURS_PER_HECTARE", 350.0,
    kind="engineering_estimate",
    unit="labourer-hours/hectare/season",
    source="Pre-mechanical potato cultivation (ridging, repeated hilling, "
           "hand digging at lifting) is commonly cited at several times "
           "wheat's labour intensity; taken at roughly double "
           "REFERENCE_LABOUR_HOURS_PER_HECTARE.",
    confidence="C",
    why="Potato's equivalent of REFERENCE_LABOUR_HOURS_PER_HECTARE under "
        "the SAME reference toolkit (hand tools, draught-animal ploughing) "
        "wheat is quoted under - higher because hilling and hand-digging "
        "tubers has no equivalent step in a cereal's labour calendar.")

POTATO_BASE_HECTARES_REAPED_PER_WORKER_DAY = declare(
    "POTATO_BASE_HECTARES_REAPED_PER_WORKER_DAY", 0.05,
    kind="engineering_estimate",
    unit="hectares/worker/day",
    source="Hand-digging tubers is slower per unit area than cutting "
           "standing stalks with a sickle; taken at half "
           "HECTARES_REAPED_PER_WORKER_DAY for lack of a more specific "
           "figure.",
    confidence="D",
    why="Potato's equivalent of HECTARES_REAPED_PER_WORKER_DAY. Combined "
        "with the much longer POTATO_HARVEST_WINDOW_DAYS, this is what "
        "hectares_per_worker_harvest_window_ceiling multiplies for a "
        "potato scenario.")

RICE_PLANTING_MATERIAL_KG_PER_HA = declare(
    "RICE_PLANTING_MATERIAL_KG_PER_HA", 50.0,
    kind="engineering_estimate",
    unit="kg seed/hectare (of transplanted field)",
    source="Transplanted paddy rice raises seedlings in a small nursery "
           "bed and transplants them into the main field, so the seed "
           "used per hectare of FINAL field is much lower than a broadcast "
           "cereal's - commonly cited in the tens of kg/ha rather than "
           "wheat's 150-180.",
    confidence="C",
    why="Rice's equivalent of SEED_SOWING_RATE_KG_PER_HA. Deliberately "
        "small: this is what transplanting buys agronomically, and it is "
        "why rice's fold-return figure below looks implausibly large next "
        "to wheat's until this denominator is accounted for.")

RICE_FOLD_RETURN_ON_SEED_SOWN = declare(
    "RICE_FOLD_RETURN_ON_SEED_SOWN", 50.0,
    kind="engineering_estimate",
    unit="kg reaped / kg sown (dimensionless)",
    source="At RICE_PLANTING_MATERIAL_KG_PER_HA, a pre-modern paddy yield "
           "in the commonly cited 2-3 t/ha (brown rice) range implies a "
           "fold-return on the order of 40-60; taken as a round midpoint. "
           "The large multiple is an artefact of transplanting's tiny seed "
           "requirement, not a claim that rice out-yields wheat fifty to "
           "one in calories - it does not, see RICE_ENERGY_KCAL_PER_KG "
           "and the gross-yield figure this implies (~2,500 kg/ha, inside "
           "the cited range).",
    confidence="C",
    why="Rice's equivalent of FOLD_RETURN_ON_SEED_SOWN, kept as its own "
        "number rather than assumed equal to wheat's precisely because the "
        "two crops' sowing practices differ enough that the same multiple "
        "would mean different things.")

RICE_ENERGY_KCAL_PER_KG = declare(
    "RICE_ENERGY_KCAL_PER_KG", 3600.0,
    kind="biological_parameter",
    unit="kcal/kg",
    source="Standard food-composition figures for milled/brown rice, "
           "close to but slightly above wheat grain's.",
    confidence="B",
    why="Converts kilograms of rice into the same calorie currency as "
        "wheat and potatoes.")

RICE_HARVEST_WINDOW_DAYS = declare(
    "RICE_HARVEST_WINDOW_DAYS", 25.0,
    kind="biological_parameter",
    unit="days/year",
    source="Paddy rice ripens and can shatter or lodge similarly to "
           "wheat, on a comparable multi-week timescale; taken slightly "
           "above HARVEST_WINDOW_DAYS on the reasoning that standing water "
           "in the paddy buffers the stand somewhat against wind-lodging.",
    confidence="C",
    why="Rice's equivalent of HARVEST_WINDOW_DAYS.")

RICE_BASE_LABOUR_HOURS_PER_HECTARE = declare(
    "RICE_BASE_LABOUR_HOURS_PER_HECTARE", 800.0,
    kind="engineering_estimate",
    unit="labourer-hours/hectare/season",
    source="Traditional transplanted wet-rice cultivation (nursery-bed "
           "raising, transplanting, standing-water weeding, harvest) is "
           "repeatedly cited in agricultural-history literature at several "
           "times a rain-fed cereal's labour intensity; taken at roughly "
           "five times REFERENCE_LABOUR_HOURS_PER_HECTARE, excluding the "
           "labour of building and maintaining the paddy's water works "
           "themselves, which is irrigation engineering and out of this "
           "module's scope.",
    confidence="C",
    why="Rice's equivalent of REFERENCE_LABOUR_HOURS_PER_HECTARE. The "
        "single biggest reason wet-rice civilisations historically "
        "supported very dense farm populations on small holdings: not "
        "because rice needs less land per calorie, but because it demands "
        "so much more labour per hectare that a given amount of farm "
        "labour covers much less ground.")

RICE_BASE_HECTARES_REAPED_PER_WORKER_DAY = declare(
    "RICE_BASE_HECTARES_REAPED_PER_WORKER_DAY", 0.08,
    kind="engineering_estimate",
    unit="hectares/worker/day",
    source="Rice is cut by sickle much as wheat is; taken slightly below "
           "HECTARES_REAPED_PER_WORKER_DAY for the wetter footing and "
           "bundling-for-drying step paddy harvest usually adds.",
    confidence="D",
    why="Rice's equivalent of HECTARES_REAPED_PER_WORKER_DAY.")

WHEAT = DEFAULT_CROP

POTATOES = Crop(
    name="potatoes",
    planting_material_kg_per_ha=POTATO_PLANTING_MATERIAL_KG_PER_HA,
    fold_return_on_planting_material=POTATO_FOLD_RETURN_ON_SEED_TUBERS,
    energy_kcal_per_kg=POTATO_ENERGY_KCAL_PER_KG,
    harvest_window_days=POTATO_HARVEST_WINDOW_DAYS,
    base_labour_hours_per_hectare=POTATO_BASE_LABOUR_HOURS_PER_HECTARE,
    base_hectares_reaped_per_worker_day=POTATO_BASE_HECTARES_REAPED_PER_WORKER_DAY)

RICE = Crop(
    name="rice",
    planting_material_kg_per_ha=RICE_PLANTING_MATERIAL_KG_PER_HA,
    fold_return_on_planting_material=RICE_FOLD_RETURN_ON_SEED_SOWN,
    energy_kcal_per_kg=RICE_ENERGY_KCAL_PER_KG,
    harvest_window_days=RICE_HARVEST_WINDOW_DAYS,
    base_labour_hours_per_hectare=RICE_BASE_LABOUR_HOURS_PER_HECTARE,
    base_hectares_reaped_per_worker_day=RICE_BASE_HECTARES_REAPED_PER_WORKER_DAY)


# ----------------------------------------------------------------------
# SOIL TABLE - alternatives to ordinary Mediterranean loam.
#
# Arctic and desert land are NOT "low quality land" in the sense poor or
# stony soil is - they are, respectively, no growing season and no water,
# which are different physical constraints this module cannot yet tell
# apart from fertility. Folding all three into one `quality_multiplier`
# is a known simplification, not a claim that permafrost is just very poor
# dirt; `limiting_factor` records which constraint is actually meant so a
# later climate/hydrology model (explicitly out of this module's scope)
# has somewhere to plug in without a rename. Every number below is
# `temporary_heuristic` or low-confidence for exactly this reason, except
# where a fertility-only comparison (chernozem vs ordinary loam) is being
# made and the usual engineering_estimate discipline applies.
# ----------------------------------------------------------------------

CHERNOZEM_QUALITY_MULTIPLIER = declare(
    "CHERNOZEM_QUALITY_MULTIPLIER", 1.4,
    kind="engineering_estimate",
    unit="fraction of reference yield (dimensionless)",
    source="Chernozem ('black earth') soils, of which the Ukrainian steppe "
           "is the type example, are repeatedly described in agronomy "
           "literature as among the most naturally fertile in the world, "
           "with historical grain yields commonly exceeding ordinary loam "
           "by roughly 30-50%; taken as a round midpoint.",
    confidence="C",
    why="The stakeholder's own example of exceptional land, fed straight "
        "into the SAME land.quality multiplier the module already had - "
        "this is a genuine fertility fact about a PLACE, unlike the arctic "
        "and desert entries below, so it earns the higher confidence and "
        "the engineering_estimate kind.")

CHERNOZEM_WEATHER_STDEV_FRACTION = declare(
    "CHERNOZEM_WEATHER_STDEV_FRACTION", 0.25,
    kind="temporary_heuristic",
    unit="fraction of mean yield (dimensionless standard deviation)",
    source=None,
    confidence="D",
    why="A continental steppe climate lacks the Mediterranean's winter-rain "
        "buffering, which plausibly widens year-to-year yield swings "
        "somewhat above WEATHER_YIELD_STDEV_FRACTION; the actual figure "
        "needs regional precipitation-variability data this module does "
        "not have, so this is a directional placeholder, not a measurement.")

ARCTIC_QUALITY_MULTIPLIER = declare(
    "ARCTIC_QUALITY_MULTIPLIER", 0.05,
    kind="temporary_heuristic",
    unit="fraction of reference yield (dimensionless)",
    source=None,
    confidence="D",
    why="Arctic land's limiting factor is growing-season LENGTH - frost-"
        "free days - not soil mineral fertility, and this module has no "
        "degree-day or frost-date model to represent that properly (an "
        "explicit non-goal of the task that produced this table). Folding "
        "'almost no viable growing season' into the same scalar as 'poor "
        "soil' is a real distortion, recorded here rather than hidden: "
        "limiting_factor='growing_season' is what a later climate model "
        "should read instead of this number.")

ARCTIC_WEATHER_STDEV_FRACTION = declare(
    "ARCTIC_WEATHER_STDEV_FRACTION", 0.45,
    kind="temporary_heuristic",
    unit="fraction of mean yield (dimensionless standard deviation)",
    source=None,
    confidence="D",
    why="A short, marginal growing season swings a harvest between usable "
        "and total loss far more than a temperate year does; a placeholder "
        "in the right direction, not a measured figure for any specific "
        "population.")

DESERT_QUALITY_MULTIPLIER = declare(
    "DESERT_QUALITY_MULTIPLIER", 0.03,
    kind="temporary_heuristic",
    unit="fraction of reference yield (dimensionless)",
    source=None,
    confidence="D",
    why="Desert land's limiting factor is WATER, not soil fertility, and "
        "this module has no hydrology model to represent that (irrigation "
        "engineering is an explicit non-goal). Without irrigation, "
        "rain-fed cropland in a desert barely produces at all; this "
        "scalar is a crude stand-in for that absence, not a fertility "
        "judgement - limiting_factor='water' says so.")

DESERT_WEATHER_STDEV_FRACTION = declare(
    "DESERT_WEATHER_STDEV_FRACTION", 0.50,
    kind="temporary_heuristic",
    unit="fraction of mean yield (dimensionless standard deviation)",
    source=None,
    confidence="D",
    why="Erratic rainfall is the defining feature of dry farming, not a "
        "side effect of it; a placeholder pending a real hydrological "
        "model of arid precipitation.")

MOUNTAIN_QUALITY_MULTIPLIER = declare(
    "MOUNTAIN_QUALITY_MULTIPLIER", 0.4,
    kind="temporary_heuristic",
    unit="fraction of reference yield (dimensionless)",
    source=None,
    confidence="D",
    why="Mountain land's limiting factors are slope, thin/rocky soil and a "
        "shortened growing season from altitude - a bundle this single "
        "scalar cannot separate, less severe than arctic or desert's "
        "near-total exclusion but still well below ordinary lowland, "
        "pending a real terrain/elevation model.")

MOUNTAIN_WEATHER_STDEV_FRACTION = declare(
    "MOUNTAIN_WEATHER_STDEV_FRACTION", 0.30,
    kind="temporary_heuristic",
    unit="fraction of mean yield (dimensionless standard deviation)",
    source=None,
    confidence="D",
    why="Altitude adds frost-timing risk on top of ordinary rainfall "
        "variability; a placeholder in the right direction.")

ORDINARY_MEDITERRANEAN_LOAM = DEFAULT_SOIL

UKRAINIAN_CHERNOZEM = Soil(
    name="ukrainian_chernozem",
    quality_multiplier=CHERNOZEM_QUALITY_MULTIPLIER,
    weather_stdev_fraction=CHERNOZEM_WEATHER_STDEV_FRACTION,
    limiting_factor="fertility")

ARCTIC_TUNDRA = Soil(
    name="arctic_tundra",
    quality_multiplier=ARCTIC_QUALITY_MULTIPLIER,
    weather_stdev_fraction=ARCTIC_WEATHER_STDEV_FRACTION,
    limiting_factor="growing_season")

DESERT = Soil(
    name="desert",
    quality_multiplier=DESERT_QUALITY_MULTIPLIER,
    weather_stdev_fraction=DESERT_WEATHER_STDEV_FRACTION,
    limiting_factor="water")

MOUNTAIN = Soil(
    name="mountain",
    quality_multiplier=MOUNTAIN_QUALITY_MULTIPLIER,
    weather_stdev_fraction=MOUNTAIN_WEATHER_STDEV_FRACTION,
    limiting_factor="terrain")


# ----------------------------------------------------------------------
# ROTATION TABLE - alternatives to two-field.
#
# Fallow exists because nitrogen is scarce: a bare-fallow year lets soil
# nitrogen recover and lets ploughing kill weeds that would otherwise take
# the next crop. Manure, a legume fallow crop, guano and (much later)
# synthetic nitrogen are all ways of putting nitrogen back WITHOUT idling
# the land, which is why each entry below moves fallow_share_of_holding
# DOWN and soil_fertility_yield_multiplier UP together, through the same
# field pairing, rather than as three unrelated special cases.
# ----------------------------------------------------------------------

THREE_FIELD_FALLOW_SHARE_OF_HOLDING = declare(
    "THREE_FIELD_FALLOW_SHARE_OF_HOLDING", 1.0 / 3.0,
    kind="engineering_estimate",
    unit="fraction of holding idle in any one year (dimensionless)",
    source="The medieval three-field rotation (winter grain / spring grain "
           "or legume / fallow) is the standard successor to two-field, "
           "named in FALLOW_SHARE_OF_HOLDING's own declaration as the "
           "reason this has to be a changeable technique property.",
    confidence="B",
    why="Adding a spring-sown field alongside the fallow drops the idle "
        "share from a half to a third without eliminating fallow "
        "altogether - the middle point on the same fallow axis two-field "
        "and Nile flood-recession farming sit at the ends of.")

THREE_FIELD_SOIL_FERTILITY_YIELD_MULTIPLIER = declare(
    "THREE_FIELD_SOIL_FERTILITY_YIELD_MULTIPLIER", 1.15,
    kind="temporary_heuristic",
    unit="fraction of reference yield (dimensionless)",
    source=None,
    confidence="D",
    why="The three-field system's spring field commonly carried a legume "
        "(peas, beans, vetch), whose root-nodule nitrogen fixation raises "
        "the following grain crop's yield above a bare fallow's. The real "
        "mechanism is a nitrogen mass balance (how much N a legume fixes "
        "per hectare versus how much a bare fallow year recovers by "
        "mineralisation alone) that does not exist in this module yet; "
        "this number is a placeholder in the right direction, paired with "
        "the fallow reduction above because both come from the same extra "
        "nitrogen.")

NILE_FLOOD_RECESSION_FALLOW_SHARE_OF_HOLDING = declare(
    "NILE_FLOOD_RECESSION_FALLOW_SHARE_OF_HOLDING", 0.02,
    kind="engineering_estimate",
    unit="fraction of holding idle in any one year (dimensionless)",
    source="Egyptological accounts of the annual Nile inundation "
           "describe fresh silt being deposited across the flood plain "
           "every year, letting land be cropped continuously without a "
           "fallow year; taken as a small residual rather than exactly "
           "zero for basin-irrigation scheduling and the desert-margin "
           "strip that floods unreliably.",
    confidence="C",
    why="The other named example (with Ukrainian chernozem) of exceptional "
        "land, and the one FALLOW_SHARE_OF_HOLDING's own declaration "
        "already names: a river doing every year, for free, what a farmer "
        "otherwise buys with an idle field.")

NILE_FLOOD_RECESSION_SOIL_FERTILITY_YIELD_MULTIPLIER = declare(
    "NILE_FLOOD_RECESSION_SOIL_FERTILITY_YIELD_MULTIPLIER", 1.4,
    kind="engineering_estimate",
    unit="fraction of reference yield (dimensionless)",
    source="Comparisons of Nile valley grain yields against rain-fed "
           "Mediterranean land commonly cite a 30-50% advantage from "
           "annual silt replenishment; taken as a round midpoint, "
           "matching CHERNOZEM_QUALITY_MULTIPLIER's figure since both "
           "describe the same kind of advantage (naturally replenished "
           "fertility) by a different mechanism (river silt vs parent "
           "soil).",
    confidence="C",
    why="The silt is both why the fallow can be skipped AND why the "
        "unfallowed yield itself is higher than bare-fallow farming would "
        "give even without skipping it - the same pairing as the "
        "three-field entry above, for the same nitrogen-and-mineral "
        "reason, at the strong end of the axis rather than the middle.")

TWO_FIELD = DEFAULT_ROTATION

THREE_FIELD = Rotation(
    name="three_field",
    fallow_share_of_holding=THREE_FIELD_FALLOW_SHARE_OF_HOLDING,
    soil_fertility_yield_multiplier=THREE_FIELD_SOIL_FERTILITY_YIELD_MULTIPLIER)

NILE_FLOOD_RECESSION = Rotation(
    name="nile_flood_recession",
    fallow_share_of_holding=NILE_FLOOD_RECESSION_FALLOW_SHARE_OF_HOLDING,
    soil_fertility_yield_multiplier=NILE_FLOOD_RECESSION_SOIL_FERTILITY_YIELD_MULTIPLIER)


# ----------------------------------------------------------------------
# TOOLKIT TABLE - alternatives to an ard behind an ox, cut with a sickle.
#
# The horse collar is the stakeholder's own example. A throat-and-girth
# harness chokes a horse under a heavy load, which is why draught oxen (slow
# but able to push against a yoke with their shoulders) dominated until a
# RIGID COLLAR let a horse apply its full pulling power without strangling -
# after which a horse-and-mouldboard combination ploughs measurably faster
# than an ox-and-ard one. That is a LABOUR-HOURS effect (less time per
# hectare of ploughing) and, separately, a YIELD effect (a mouldboard turns
# and buries weeds/stubble more completely than a scratch-ard, which is why
# cross-ploughing existed at all). A scythe, by contrast, changes neither of
# those - it changes how fast a worker can REAP, which is what the harvest
# window's ceiling responds to. That is why this table has three separate
# multipliers rather than one: the horse collar and the scythe are
# different toolkits because they move different ones of the three.
# ----------------------------------------------------------------------

HORSE_COLLAR_LABOUR_HOURS_MULTIPLIER = declare(
    "HORSE_COLLAR_LABOUR_HOURS_MULTIPLIER", 0.7,
    kind="temporary_heuristic",
    unit="fraction of REFERENCE_LABOUR_HOURS_PER_HECTARE (dimensionless)",
    source=None,
    confidence="D",
    why="A horse in a rigid collar pulling a mouldboard plough covers "
        "ground faster than an ox behind an ard on the same land; economic-"
        "history accounts of the medieval 'agricultural revolution' "
        "commonly describe 30-50% less time per hectare of ploughing from "
        "the combination. 0.7 (30% fewer hours) is a conservative reading "
        "of that range - a real derivation would need the animals' "
        "comparative pulling power, ground speed and the plough's width, "
        "none of which this module models, hence temporary_heuristic.")

HORSE_COLLAR_PLOUGHING_YIELD_MULTIPLIER = declare(
    "HORSE_COLLAR_PLOUGHING_YIELD_MULTIPLIER", 1.05,
    kind="temporary_heuristic",
    unit="fraction of reference yield (dimensionless)",
    source=None,
    confidence="D",
    why="A mouldboard turns and buries the previous stubble and weeds in "
        "one pass, which cross-ploughing with an ard only approximates; "
        "better weed suppression and organic-matter incorporation "
        "plausibly raises yield some modest amount independent of the "
        "labour saved. The size of that effect needs a real tillage trial, "
        "not an economic-history estimate, hence temporary_heuristic - the "
        "number is deliberately modest so it cannot be mistaken for the "
        "main effect, which is the labour saving above.")

SCYTHE_AND_CRADLE_REAPING_RATE_MULTIPLIER = declare(
    "SCYTHE_AND_CRADLE_REAPING_RATE_MULTIPLIER", 2.0,
    kind="engineering_estimate",
    unit="fraction of HECTARES_REAPED_PER_WORKER_DAY (dimensionless)",
    source="Agricultural-history accounts of the cradle scythe replacing "
           "the sickle for grain harvest (widespread by the 18th-19th "
           "century in Europe and North America) commonly report roughly "
           "double the area cut per worker-day.",
    confidence="C",
    why="Acts on exactly the rate HECTARES_REAPED_PER_WORKER_DAY was "
        "declared to be - unlike the horse collar, this toolkit changes "
        "nothing about ploughing, only how fast a worker can reap, which "
        "is what should, and does, loosen the harvest-window ceiling "
        "directly. See hectares_per_worker_harvest_window_ceiling and "
        "the ToolkitAxisTests in sim/tests/test_agriculture.py.")

MECHANICAL_REAPER_REAPING_RATE_MULTIPLIER = declare(
    "MECHANICAL_REAPER_REAPING_RATE_MULTIPLIER", 10.0,
    kind="engineering_estimate",
    unit="fraction of HECTARES_REAPED_PER_WORKER_DAY (dimensionless)",
    source="19th-century horse-drawn mechanical reaper accounts (the "
           "McCormick-type reaper and its contemporaries) commonly cite "
           "roughly an order-of-magnitude increase in area cut per "
           "worker-day over hand reaping with a sickle or scythe.",
    confidence="C",
    why="The clearest demonstration this module can give of its own "
        "central finding: the harvest window, not the farming year, binds "
        "output per worker at hand-tool reaping rates, and mechanising "
        "REAPING specifically - not ploughing, not threshing - is what "
        "historically broke that ceiling.")

ARD_AND_OX_WITH_SICKLE = DEFAULT_TOOLKIT

HORSE_COLLAR_AND_MOULDBOARD = Toolkit(
    name="horse_collar_and_mouldboard",
    labour_hours_multiplier=HORSE_COLLAR_LABOUR_HOURS_MULTIPLIER,
    reaping_rate_multiplier=1.0,  # unaffected: this toolkit changes
                                  # ploughing, not reaping - see the
                                  # TOOLKIT TABLE section above.
    ploughing_yield_multiplier=HORSE_COLLAR_PLOUGHING_YIELD_MULTIPLIER)

SCYTHE_AND_CRADLE = Toolkit(
    name="scythe_and_cradle",
    labour_hours_multiplier=1.0,  # unaffected: a scythe changes reaping,
                                  # not ploughing/sowing/weeding.
    reaping_rate_multiplier=SCYTHE_AND_CRADLE_REAPING_RATE_MULTIPLIER,
    ploughing_yield_multiplier=1.0)

MECHANICAL_REAPER = Toolkit(
    name="mechanical_reaper",
    labour_hours_multiplier=1.0,  # the reaper's labour saving is entirely
                                  # in the reaping RATE below; ploughing,
                                  # sowing and threshing are unchanged.
    reaping_rate_multiplier=MECHANICAL_REAPER_REAPING_RATE_MULTIPLIER,
    ploughing_yield_multiplier=1.0)


# ----------------------------------------------------------------------
# STORAGE-TECHNIQUE TABLE - alternatives to a pit silo or raised granary.
# ----------------------------------------------------------------------

REFRIGERATED_STORE_SPOILAGE_RATE_PER_YEAR = declare(
    "REFRIGERATED_STORE_SPOILAGE_RATE_PER_YEAR", 0.015,
    kind="engineering_estimate",
    unit="fraction of stored grain lost/year (dimensionless)",
    source="Modern refrigerated or controlled-atmosphere grain storage "
           "loss figures are commonly quoted below 2%/year, against "
           "GRAIN_SPOILAGE_RATE_PER_YEAR's 5-15% range for pit silos and "
           "raised granaries.",
    confidence="C",
    why="Shows storage technique acting on exactly the axis "
        "GRAIN_SPOILAGE_RATE_PER_YEAR was declared for, independent of "
        "yield - more of a good year's harvest actually reaches "
        "consumption in a later bad year rather than rotting away in the "
        "granary.")

PIT_SILO_OR_RAISED_GRANARY = DEFAULT_STORAGE_TECHNIQUE

REFRIGERATED_STORE = StorageTechnique(
    name="refrigerated_store",
    spoilage_rate_per_year=REFRIGERATED_STORE_SPOILAGE_RATE_PER_YEAR)


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


def annual_food_demand_kg_per_person(crop=None):
    """One person's food need for a year, in kilograms of `crop` (default
    wheat).

    A single-staple simplification, same as the rest of this module: real
    pre-industrial diets were not 100% grain calories (legumes, oil, wine,
    some meat and dairy filled in the rest), which this module cannot
    represent with one crop at a time. That simplification runs in the
    direction of UNDERSTATING how much land a real diet needs, since grain
    is generally the highest-yield-per-hectare calorie source available -
    see the module docstring's headline-number reading for how this bears
    on the computed farm-population share coming out low rather than high.
    """
    crop = crop or DEFAULT_CROP
    return (HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY * DAYS_PER_YEAR
            / crop.energy_kcal_per_kg)


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


def draw_weather_multiplier(rng, weather_stdev_fraction=WEATHER_YIELD_STDEV_FRACTION):
    """One year's weather, as a single multiplier on yield.

    Not a daily process - see the module docstring's SHAPE section for why
    an annual draw is enough here. `rng` is an ordinary `random.Random`
    owned by the caller (`Storage` keeps one per instance), so the same
    seed reproduces the same sequence of years exactly, every time, in the
    same process - see sim/tests/test_agriculture.py's determinism check.

    `weather_stdev_fraction` defaults to the reference (ordinary
    Mediterranean loam) figure but is a `Soil` property - see the SOIL
    TABLE section - since how much one year's weather can move a harvest
    is a fact about a PLACE, not about agriculture in general. The clip
    bounds (WEATHER_FLOOR_MULTIPLIER, WEATHER_CEILING_MULTIPLIER) are not
    parametrised the same way: nothing in the task this module answers to
    asked for them to vary by place, and they are a safety clip on an
    otherwise-unbounded Gaussian rather than a climate fact.
    """
    draw = rng.gauss(1.0, weather_stdev_fraction)
    return max(WEATHER_FLOOR_MULTIPLIER, min(WEATHER_CEILING_MULTIPLIER, draw))


def _max_hectares_harvestable_by_labour(labour_hours, crop, toolkit,
                                        worker_count=None,
                                        hours_per_worker_day=None):
    """How much land the harvest window and the reaping rate let
    `labour_hours` worth of workers actually bring in this season - the fix
    for the defect the module docstring's "THE HARVEST WINDOW NOW ALSO
    BINDS" section describes.

    `gross_harvest_kg` takes a POOL of hours, but HARVEST_WINDOW_DAYS and
    HECTARES_REAPED_PER_WORKER_DAY are stated per WORKER-DAY, so the pool
    has to be converted to worker-equivalents before either ceiling means
    anything. The conversion used is division by
    ANNUAL_LABOUR_HOURS_PER_FARM_WORKER - the SAME conversion
    `hectares_per_worker_annual_hours_ceiling` already uses - on the
    reasoning that a pool of hours is indistinguishable, in this module,
    from that many worker-years of a single worker's time; the model has no
    way to tell "one worker given unlimited hours" apart from "many workers
    each given a normal year", and does not need to for the answer to be
    honest: EITHER way, the workers implied by the pool are still each
    capped at `hectares_cropped_per_farm_worker` hectares, because that cap
    is itself the smaller of the annual-hours ceiling and the harvest-
    window ceiling. An actor with unlimited hours (autonomous labour; a
    robot) gets unlimited worker-equivalents from this division, and can
    therefore still reap unlimited land in the limit - that is the
    physically correct answer for adding unlimited WORKERS - but it cannot
    reap more land than that many worker-equivalents' share of the window
    allows just by working any one of them harder, which is the bug this
    replaces: a large `labour_hours` on a large `Land` no longer produces a
    harvest bigger than the implied crew could have physically reaped.

    THE ABOVE REASONING IS WRONG WHERE IT MATTERS MOST, AND THE CORRECTION
    IS `worker_count`. "A pool of hours is indistinguishable from that many
    worker-years" holds for the annual-hours ceiling and fails for the
    harvest-window one, because the window is CALENDAR TIME. Twenty-one days
    is twenty-one days however many hours an actor is willing to work; one
    reaper can only be in one field at a time, and the hours it has outside
    the window cannot reap anything. Dividing annual hours by a human's
    annual hours smears a whole year's labour into three weeks.

    Measured, at the constants declared in this file: one actor working
    every hour of the year (8,760 h) comes out of the division at 6.26
    worker-equivalents and is allowed 13.14 ha, where the window physics
    allow 21 days x 24 h x 0.01 ha/h = 5.04 ha. The model overstates by
    2.61x, and it overstates in exactly the direction that flatters
    autonomous labour - which is the case this correction was asked for.

    So: pass `worker_count` whenever the actors are not ordinary humans
    working an ordinary farming year, and the cap is computed from calendar
    time instead. Leaving it None keeps the worker-equivalent derivation,
    which is exactly right for the default case and is why every existing
    number in this module is unmoved by this change.
    """
    if labour_hours <= 0.0:
        return 0.0
    if worker_count is not None:
        return max_hectares_reapable_by_crew(
            worker_count, hours_per_worker_day=hours_per_worker_day,
            crop=crop, toolkit=toolkit)
    worker_equivalents = labour_hours / ANNUAL_LABOUR_HOURS_PER_FARM_WORKER
    return worker_equivalents * hectares_cropped_per_farm_worker(crop, toolkit)


def hectares_reaped_per_worker_hour(crop=None, toolkit=None):
    """The instantaneous reaping rate: hectares one worker brings in per
    hour actually spent reaping. The per-DAY rate divided by the length of
    a harvest working day, so the two are the same fact stated twice and
    neither can drift from the other.
    """
    crop = crop or DEFAULT_CROP
    toolkit = toolkit or DEFAULT_TOOLKIT
    per_day = (crop.base_hectares_reaped_per_worker_day
               * toolkit.reaping_rate_multiplier)
    return per_day / HARVEST_WORKING_DAY_HOURS


def max_hectares_reapable_by_crew(worker_count, hours_per_worker_day=None,
                                  crop=None, toolkit=None):
    """The physically correct harvest cap: how much a crew of
    `worker_count` can actually bring in, from calendar time.

        crew size  x  window days  x  hours worked per day  x  ha per hour

    Every term is a real quantity rather than an accounting convenience,
    which is what makes this the form that answers the awkward questions:

    - AUTONOMOUS LABOUR (a robot, or anything that does not sleep) raises
      `hours_per_worker_day` toward 24 and gets a proportional gain, capped
      at 2.4x a ten-hour human. It does NOT get to multiply its capacity by
      working the other eleven months harder, which is what the
      worker-equivalent derivation wrongly allowed.
    - A BETTER TOOL raises the hectares-per-hour term (scythe, cradle,
      mechanical reaper) and is the only thing that lifts the ceiling
      without more bodies or longer days.
    - A CROP WITH A LONGER OR STAGGERED RIPENING raises the window term.

    Passing the default ten-hour day for one worker reproduces
    `hectares_per_worker_harvest_window_ceiling()` exactly, by construction:
    21 days x 10 h x 0.01 ha/h = 2.1 ha. That identity is asserted in
    sim/tests/test_agriculture.py so the two cannot drift apart.
    """
    crop = crop or DEFAULT_CROP
    if hours_per_worker_day is None:
        hours_per_worker_day = HARVEST_WORKING_DAY_HOURS
    hours_per_worker_day = min(hours_per_worker_day, HOURS_PER_DAY)
    return (worker_count * crop.harvest_window_days * hours_per_worker_day
            * hectares_reaped_per_worker_hour(crop, toolkit))


def gross_harvest_kg(land, labour_hours, technique_multiplier=1.0,
                      weather_multiplier=1.0, crop=None, toolkit=None,
                      rotation=None, worker_count=None, hours_per_worker_day=None):
    """Grain (or `crop`) reaped from `land` this season, in kilograms,
    BEFORE seed is paid back or anything is eaten or spoiled - the same
    "gross" the module docstring's DISAGREEMENT section discusses.

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

    THE LAND SIDE OF THE CURVE IS CAPPED AT WHAT THE LABOUR POOL CAN
    ACTUALLY REAP INSIDE THE HARVEST WINDOW - see
    `_max_hectares_harvestable_by_labour`. `land.hectares` is what a farm
    HOLDS; the smaller of `land.hectares` and that cap is what actually
    gets reaped and enters the Cobb-Douglas land term. Only the LAND term
    is capped this way, not `labour_hours` itself: extra hours applied to
    the land that DOES get reaped (weeding it more, say) still raise
    output through the ordinary diminishing-returns labour term, only
    extra hours cannot buy MORE reaped area once the window and rate are
    already saturated for the given number of worker-equivalents.

    `crop` and `toolkit` (see the CROP TABLE and TOOLKIT TABLE sections)
    replace what used to be single wheat-and-ard constants: `crop` sets
    the fold-return, the planting-material rate and the reference labour
    and reaping-rate baseline; `toolkit` rescales that baseline (labour-
    hours multiplier, reaping-rate multiplier) and contributes its own
    ploughing-yield multiplier. `rotation` contributes only its soil-
    fertility yield multiplier here - its fallow share is a LAND
    requirement, read by `holding_hectares_required_per_farm_worker`, never
    by this function (see the ROTATION AND FALLOW section).

    `land.quality`, `technique_multiplier` and `weather_multiplier` all
    enter as plain multipliers on top of the land/labour curve - none of
    them changes its SHAPE (the diminishing-returns property holds at any
    quality, technique or weather draw), only its level.

    `worker_count`/`hours_per_worker_day` are the SAME override
    `_max_hectares_harvestable_by_labour` already accepts, threaded through
    here rather than left reachable only from that private helper. WHY A
    CALLER WHO KNOWS ITS WORKFORCE SHOULD ALWAYS PASS `worker_count`, NOT
    ONLY WHEN THE ACTORS ARE UNUSUAL: `_max_hectares_harvestable_by_labour`
    otherwise has to GUESS the workforce back out of `labour_hours` by
    dividing by ANNUAL_LABOUR_HOURS_PER_FARM_WORKER (1,400) - a guess that
    is only exact when `labour_hours` was ITSELF built as `worker_count *
    1,400`. `labour_hours` here also drives the Cobb-Douglas LABOUR term,
    which sim/tests/test_agriculture.py's own
    HarvestWindowBindsGrossHarvestTests calibrates in the OTHER convention -
    hours actually worked, `REFERENCE_LABOUR_HOURS_PER_HECTARE` (150) times
    hectares actually worked - and 150 h/ha and 1,400 h/worker/year do not
    agree (that gap IS the module's own "harvest window leaves the annual-
    hours ceiling slack by 4:1" finding). A caller that sizes `labour_hours`
    to satisfy one convention and lets this function guess the workforce
    from it via the OTHER is silently double-counting or under-counting the
    window cap - not a bug in either convention alone, only in combining
    them without saying which one a known workforce should be read against.
    Passing `worker_count` explicitly (when it is known - engine-side
    callers with an actual headcount, not the module's own scalar tests)
    sidesteps the guess entirely: `worker_count` alone decides the window
    cap, `labour_hours` alone decides the labour-term intensity, and a
    caller is then responsible for making the two agree - see
    sim/engine/core.py's `_demographic_recovery` for the one place this
    project does that today.
    """
    crop = crop or DEFAULT_CROP
    toolkit = toolkit or DEFAULT_TOOLKIT
    rotation = rotation or DEFAULT_ROTATION
    if labour_hours <= 0.0 or land.hectares <= 0.0:
        return 0.0
    effective_hectares = min(
        land.hectares,
        _max_hectares_harvestable_by_labour(
            labour_hours, crop, toolkit, worker_count=worker_count,
            hours_per_worker_day=hours_per_worker_day))
    if effective_hectares <= 0.0:
        return 0.0

    reference_labour_hours_per_hectare = (
        crop.base_labour_hours_per_hectare * toolkit.labour_hours_multiplier)
    gross_yield_at_reference_labour_kg_per_ha = (
        crop.planting_material_kg_per_ha * crop.fold_return_on_planting_material)
    total_factor_productivity = (
        gross_yield_at_reference_labour_kg_per_ha
        / (reference_labour_hours_per_hectare ** LABOUR_OUTPUT_ELASTICITY))

    per_land_component = effective_hectares ** (1.0 - LABOUR_OUTPUT_ELASTICITY)
    per_labour_component = labour_hours ** LABOUR_OUTPUT_ELASTICITY
    fertility_multiplier = (
        toolkit.ploughing_yield_multiplier * rotation.soil_fertility_yield_multiplier)
    return (total_factor_productivity * per_land_component * per_labour_component
            * land.quality * fertility_multiplier
            * technique_multiplier * weather_multiplier)


def marginal_product_of_labour_kg_per_hour(land, labour_hours,
                                            technique_multiplier=1.0,
                                            weather_multiplier=1.0,
                                            crop=None, toolkit=None,
                                            rotation=None, worker_count=None,
                                            hours_per_worker_day=None):
    """Extra kilograms of grain the NEXT hour of labour on `land` would add,
    at the current `labour_hours` already applied.

    Closed form rather than a finite difference. The harvest is
    Cobb-Douglas in effective hectares and labour hours:

        harvest = productivity
                * effective_hectares ** (1 - labour_elasticity)
                * labour_hours ** labour_elasticity
                * (other multipliers)

    Differentiating with respect to labour_hours, everything that does not
    depend on it survives untouched, and the power rule turns the labour
    term into labour_elasticity times itself over labour_hours. So the
    whole expression collapses to

        extra harvest per extra hour
            = labour_elasticity * harvest / labour_hours

    which needs no separate evaluation of the production function. This
    still holds with the harvest-window cap in `gross_harvest_kg`, PROVIDED
    the extra hour does not itself push `labour_hours` past the point where
    more worker-equivalents would unlock more reapable land - that is,
    EFFECTIVE HECTARES is being held fixed for this derivative, exactly as
    `land.hectares` used to be. That is the ordinary calculus
    approximation this closed form always made; it is now conditioned on
    the window not being the very thing about to change, which is true for
    any actual next hour (an infinitesimal addition to a large pool does
    not cross a worker-equivalent threshold). This is exactly what the
    labour market needs to decide whether one more hour of a worker's time
    is worth more on the farm or somewhere else - "the surplus is what
    frees a worker to do anything else" only has a hiring boundary once
    something can say what the marginal farm hour is worth in grain. It
    falls strictly as labour_hours rises (LABOUR_OUTPUT_ELASTICITY < 1),
    which is the same diminishing-returns property gross_harvest_kg has,
    stated as a rate instead of a level - see sim/tests/test_agriculture.
    py's diminishing-returns check, which tests this function directly
    rather than inferring monotonicity from harvest totals.
    """
    if labour_hours <= 0.0:
        raise ValueError("marginal product is undefined at zero labour hours")
    harvest = gross_harvest_kg(land, labour_hours, technique_multiplier,
                               weather_multiplier, crop, toolkit, rotation,
                               worker_count=worker_count,
                               hours_per_worker_day=hours_per_worker_day)
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
             hectares_next_year=None, crop=None, soil=None, rotation=None,
             toolkit=None, storage_technique=None, worker_count=None,
             hours_per_worker_day=None):
        """Advance one year: sow, grow, harvest, eat, spoil, retain next
        year's seed, bank whatever is left. Mutates `self.stock_kg` and
        returns the exact flows that moved it.

        `crop`, `soil`, `rotation`, `toolkit` and `storage_technique` each
        default to the original wheat/ordinary-loam/two-field/ard-and-
        sickle/pit-silo combination (see the CROP/SOIL/ROTATION/TOOLKIT/
        STORAGE-TECHNIQUE TABLE sections) so calling `step` exactly as
        before reproduces exactly what it always computed.

        `worker_count`/`hours_per_worker_day` are forwarded verbatim to
        `gross_harvest_kg` - see that function's own docstring for why a
        caller that knows its actual workforce should pass `worker_count`
        rather than let the harvest-window cap guess one back out of
        `labour_hours`.

        ORDER OF OPERATIONS (fixed, so the same inputs always give the same
        answer regardless of what order someone might otherwise compute
        things in - see sim/world/demography.py's `Population.step` for the
        same discipline applied to births and deaths):

          1. Seed leaves storage to be sown, at `crop.planting_material_kg_
             per_ha` (SEED_SOWING_RATE_KG_PER_HA by default) times
             `land.hectares`. This can drive `self.stock_kg` negative
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
          4. Spoilage is `storage_technique.spoilage_rate_per_year`
             (GRAIN_SPOILAGE_RATE_PER_YEAR by default) of whatever remains
             after consumption - it applies to the SURPLUS sitting in the
             granary, not to what has already been eaten or was never
             harvested.
          5. Next year's seed (`crop.planting_material_kg_per_ha` times
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
        crop = crop or DEFAULT_CROP
        soil = soil or DEFAULT_SOIL
        rotation = rotation or DEFAULT_ROTATION
        toolkit = toolkit or DEFAULT_TOOLKIT
        storage_technique = storage_technique or DEFAULT_STORAGE_TECHNIQUE

        stock_before_kg = self.stock_kg
        if hectares_next_year is None:
            hectares_next_year = land.hectares

        seed_sown_kg = crop.planting_material_kg_per_ha * land.hectares
        self.stock_kg -= seed_sown_kg

        weather_multiplier = draw_weather_multiplier(
            self._random, soil.weather_stdev_fraction)
        harvest_kg = gross_harvest_kg(land, labour_hours, technique_multiplier,
                                      weather_multiplier, crop, toolkit, rotation,
                                      worker_count=worker_count,
                                      hours_per_worker_day=hours_per_worker_day)
        self.stock_kg += harvest_kg

        food_demand_kg = population * annual_food_demand_kg_per_person(crop)
        consumption_kg = max(0.0, min(food_demand_kg, self.stock_kg))
        food_shortfall_kg = max(0.0, food_demand_kg - consumption_kg)
        self.stock_kg -= consumption_kg

        spoilage_kg = max(0.0, self.stock_kg) * storage_technique.spoilage_rate_per_year
        self.stock_kg -= spoilage_kg

        seed_retained_kg = crop.planting_material_kg_per_ha * hectares_next_year
        self.stock_kg -= seed_retained_kg

        carryover_kg = self.stock_kg
        stock_after_kg = self.stock_kg

        if labour_hours > 0.0:
            marginal_product = marginal_product_of_labour_kg_per_hour(
                land, labour_hours, technique_multiplier, weather_multiplier,
                crop, toolkit, rotation, worker_count=worker_count,
                hours_per_worker_day=hours_per_worker_day)
        else:
            marginal_product = 0.0

        food_available_kcal_per_day = (
            consumption_kg * crop.energy_kcal_per_kg / DAYS_PER_YEAR)

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


def hectares_per_worker_annual_hours_ceiling(crop=None, toolkit=None):
    """One of the two ceilings on a farm worker's cropped area: total hours
    in the farming year divided by hours needed per hectare. This is the
    only ceiling this module originally had, and treating it as the answer
    is what produced the 4.8% headline figure. See
    `hectares_cropped_per_farm_worker`.

    `crop` and `toolkit` default to wheat and the ard-and-sickle baseline;
    `toolkit.labour_hours_multiplier` rescales the hours-per-hectare figure
    (a horse collar needs fewer hours to plough the same land), which is
    why this ceiling, unlike the harvest-window one below, responds to a
    labour-saving TOOLKIT and not to a better REAPING tool specifically.
    """
    crop = crop or DEFAULT_CROP
    toolkit = toolkit or DEFAULT_TOOLKIT
    return (ANNUAL_LABOUR_HOURS_PER_FARM_WORKER
            / (crop.base_labour_hours_per_hectare * toolkit.labour_hours_multiplier))


def hectares_per_worker_harvest_window_ceiling(crop=None, toolkit=None):
    """The other ceiling: how much a worker can reap before the standing
    crop is lost. Days in the window times hectares reaped per day - see
    the SEASONALITY section above for why the window is a fact about the
    crop rather than about the farmer's schedule.

    `crop` sets both the window's length and the reference reaping rate;
    `toolkit.reaping_rate_multiplier` rescales the rate (a scythe, a
    mechanical reaper) without touching the window's length, which is a
    biological fact about the crop, not something a better tool changes.
    """
    crop = crop or DEFAULT_CROP
    toolkit = toolkit or DEFAULT_TOOLKIT
    return (crop.harvest_window_days
            * crop.base_hectares_reaped_per_worker_day
            * toolkit.reaping_rate_multiplier)


def hectares_cropped_per_farm_worker(crop=None, toolkit=None):
    """How many hectares one farm worker actually brings in, in a year:
    the smaller of the two ceilings above, because a constraint you can
    satisfy is not a constraint.

    At the DEFAULT constants declared in this file the harvest window is
    the binding one by roughly four to one, and that is the substantive
    finding: adding hours to the farming year, or shifting
    REFERENCE_LABOUR_HOURS_PER_HECTARE (or a toolkit that only touches
    `labour_hours_multiplier`, such as HORSE_COLLAR_AND_MOULDBOARD), changes
    this number not at all while the window binds. Anything that raises
    output per worker here has to raise the reaping rate (a better tool -
    SCYTHE_AND_CRADLE, MECHANICAL_REAPER) or lengthen the harvest window
    (a crop with a longer one, or staggered sowing dates), which is the
    correct shape: those are what historically moved it. See the
    ToolkitAxisTests in sim/tests/test_agriculture.py for both directions
    demonstrated.
    """
    return min(hectares_per_worker_annual_hours_ceiling(crop, toolkit),
               hectares_per_worker_harvest_window_ceiling(crop, toolkit))


def holding_hectares_required_per_farm_worker(crop=None, toolkit=None,
                                               rotation=None):
    """How much land the farm must HOLD to keep one worker cropping - the
    cropped area grossed up for the fallow that is idle this year. See the
    ROTATION AND FALLOW section for why this is a land requirement and not
    a reduction in output: fraction_of_population_that_must_farm never
    reads it, deliberately.
    """
    rotation = rotation or DEFAULT_ROTATION
    return (hectares_cropped_per_farm_worker(crop, toolkit)
            / (1.0 - rotation.fallow_share_of_holding))


def fraction_of_population_that_must_farm(crop=None, soil=None, rotation=None,
                                           toolkit=None, storage_technique=None):
    """The headline calibration figure: what share of a population must be
    farmers to feed the whole population, computed purely from this
    module's declared constants at reference land quality, technique and an
    average weather year - no calibration_target anywhere in this
    computation, by construction (HISTORICAL_FARM_POPULATION_SHARE_LOW/HIGH
    are read by the test that CHECKS this number, never by this function).

    `crop`, `soil`, `rotation`, `toolkit` and `storage_technique` each
    default to the original wheat/ordinary-loam/two-field/ard-and-sickle/
    pit-silo combination, so calling this with no arguments reproduces the
    pinned 0.21181 exactly - see sim/tests/test_agriculture.py's
    HeadlineCalibrationTests. `soil` and `rotation` here contribute ONLY
    their yield multipliers (`quality_multiplier`,
    `soil_fertility_yield_multiplier`); the idle-land share a rotation
    carries is a LAND requirement, not a food-output one, and is never
    read here - see holding_hectares_required_per_farm_worker and the
    module's rotation-and-idle-land section for why applying it here would
    double-count a constraint that is not binding.

    output_per_worker_kg is how much food (net of seed, net of spoilage) one
    full-time farm worker produces in a year; annual_food_demand_kg_per_
    person is how much food one person (including that worker) needs.
    Their ratio is the number of people one farm worker can feed, and its
    reciprocal is the fraction of a population that has to farm.

    See the module docstring's ON THE HEADLINE NUMBER section for the
    result this produces at the defaults (roughly 21%, still well below the
    80-90% pre-industrial societies actually show) and for the four named
    reasons the remainder of that gap is not a defect in this
    arithmetic. Note in particular reason (a): this function counts
    full-time-equivalent WORKERS, and the 80-90% target counts everyone
    living in a farming household, so the two are not directly
    comparable as they stand.
    """
    crop = crop or DEFAULT_CROP
    soil = soil or DEFAULT_SOIL
    rotation = rotation or DEFAULT_ROTATION
    toolkit = toolkit or DEFAULT_TOOLKIT
    storage_technique = storage_technique or DEFAULT_STORAGE_TECHNIQUE

    gross_yield_at_reference_labour_kg_per_ha = (
        crop.planting_material_kg_per_ha * crop.fold_return_on_planting_material)
    fertility_multiplier = (
        toolkit.ploughing_yield_multiplier * rotation.soil_fertility_yield_multiplier
        * soil.quality_multiplier)
    net_yield_after_seed_kg_per_ha = (
        gross_yield_at_reference_labour_kg_per_ha * fertility_multiplier
        - crop.planting_material_kg_per_ha)
    food_available_per_ha_kg = (
        net_yield_after_seed_kg_per_ha
        * (1.0 - storage_technique.spoilage_rate_per_year))
    output_per_worker_kg = (
        hectares_cropped_per_farm_worker(crop, toolkit) * food_available_per_ha_kg)
    return annual_food_demand_kg_per_person(crop) / output_per_worker_kg


# ============================================================================
# SIZING A CIVILISATION'S FARM FROM ITS POPULATION - THE ENGINE'S OWN SEAM
# ============================================================================
# The two functions below are what `sim/engine/core.py` calls to turn "how
# many people are there" into "how much land, worked by how many hands" -
# the wiring this module's own docstring names as the day someone connects
# it to sim/world/demography.py. They live here, not in core.py, on the
# same reasoning as everything else in this module (CLAUDE.md SS4's "make
# the founder's mechanisms general enough that other actors can use them"):
# sizing a plausible farm from a population is a fact about AGRICULTURE, not
# about the engine, and putting it here means any future actor (a rival
# household, a second civilisation, a what-if branch) gets the same sizing
# logic for free rather than a second copy living in core.py.
#
# `adult_equivalent_population` IN BOTH FUNCTIONS, DELIBERATELY NOT A FLAT
# HEADCOUNT. See sim/engine/core.py's `_adult_equivalent_population` for the
# full reasoning (WIRING_MILESTONE_4.md SS4.3): a caller is expected to pass
# `self.children * CHILD_CALORIE_EQUIVALENT + self.working_age + self.elderly
# * ELDERLY_CALORIE_EQUIVALENT` (sim/world/demography.py's own weighting),
# not `Population.total`. Nothing here enforces that - this module still
# does not import demography.py (see the module docstring's STANDALONE ON
# PURPOSE section) - so a caller that passes a flat headcount instead gets a
# workforce and a landholding sized for MORE people than actually need
# feeding, not a crash; the two functions below cannot detect the
# difference from a plain float, which is exactly why the decision has to
# be documented at the boundary that CAN see both conventions.

def farm_workers_fte_for_population(adult_equivalent_population, crop=None, soil=None,
                                    rotation=None, toolkit=None, storage_technique=None):
    """How many full-time-equivalent farm workers a population of
    `adult_equivalent_population` needs, at reference technique and an
    average weather year, to feed itself: `fraction_of_population_that_
    must_farm() * adult_equivalent_population`.

    NO FURTHER DEPENDENCY-RATIO CORRECTION BELONGS HERE (see
    `fraction_of_population_that_must_farm`'s own docstring, reason (a),
    for the gap this resolves). That reason exists only when comparing this
    module's FTE-worker share against the HISTORICAL_FARM_POPULATION_SHARE_
    LOW/HIGH calibration target, which counts every person living in a
    farming household. This function is not doing that comparison - it is
    answering "how many workers does this module's own production function
    say are needed", and `fraction_of_population_that_must_farm`'s
    numerator (workers) and denominator (population) are already both
    anchored to the same flat-ration convention `annual_food_demand_kg_per_
    person` uses, so multiplying straight through is consistent as long as
    the population handed in uses that SAME convention - which is exactly
    what passing an adult-equivalent count (see the section note above),
    not a flat headcount, achieves.
    """
    fraction = fraction_of_population_that_must_farm(
        crop, soil, rotation, toolkit, storage_technique)
    return fraction * adult_equivalent_population


def farmland_for_population(adult_equivalent_population, crop=None, soil=None,
                            rotation=None, toolkit=None, storage_technique=None):
    """A `Land` parcel sized so that the workforce
    `farm_workers_fte_for_population` implies can each crop their full
    `hectares_cropped_per_farm_worker` share - i.e. land is NOT the binding
    constraint at reference labour, technique and an average weather year,
    only the harvest window and diminishing returns to labour are (the
    module's own headline finding). This is the natural way to seed a
    civilisation's arable endowment from nothing but its population: an
    INITIAL CONDITION (how much land is already cleared and worked - see
    CLAUDE.md SS3.1's own allowed category, the same one a starting
    population or a starting set of open mines belongs to), not a result
    this module computes on its own account from anything the game
    measures. A caller that wants extensive-margin land scarcity to bite
    later should hold this `Land` fixed rather than resizing it as
    population changes - see sim/engine/core.py's own comment on why
    `farm_land` is constructed once, not every year.

    `land.quality` is left at the default (1.0, decent land) here
    regardless of `soil`: `soil.quality_multiplier` is a YIELD multiplier on
    however many hectares exist, not a LAND-AREA requirement, so it plays no
    part in how much land gets allocated - see the SOIL TABLE section and
    `Land`'s own docstring. A caller modelling worse land should build the
    `Land` directly with `quality=soil.quality_multiplier` instead of
    relying on this function to do it implicitly.
    """
    workers_fte = farm_workers_fte_for_population(
        adult_equivalent_population, crop, soil, rotation, toolkit, storage_technique)
    hectares = hectares_cropped_per_farm_worker(crop, toolkit) * workers_fte
    return Land(hectares)


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
