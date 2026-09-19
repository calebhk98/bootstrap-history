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

THIS FILE AND ITS SIBLINGS, AND WHY THIS SPLIT LOOKS DIFFERENT. This module
was 2,238 total / 1,696 code lines, over the project's roughly-1,000-code-
line target for a file, and the single file every agent touching farming had
to collide in. Split on 2026-09-18 into subject files, the same way
`sim/engine/society.py` was split into `society_hazards.py`,
`society_state_pressure.py`, `society_adoption.py` and `society_diffusion.py`
- see that file for the pattern this one copies. Three siblings hold the
functions and classes:

    agriculture_yield.py     the production function itself: `Land`, one
                              year's weather draw, the harvest-window
                              helpers, `gross_harvest_kg` and `marginal_
                              product_of_labour_kg_per_hour`.
    agriculture_storage.py   the granary: `annual_food_demand_kg_per_
                              person`, `granary_capacity_kg`, `YearFlows`,
                              `Storage` and `stock_to_carry_forward_kg`.
    agriculture_labour.py    sizing a farm worker's land and a civilisation's
                              farm from its population: `hectares_cropped_
                              per_farm_worker` and its two ceilings, `holding_
                              hectares_required_per_farm_worker`, `fraction_
                              of_population_that_must_farm`, `farm_workers_
                              fte_for_population`, `farmland_for_population`.

EVERYTHING THIS FILE DECLARES STAYED HERE, UNLIKE `society.py`'s SPLIT,
WHICH MOVED EVERYTHING OUT. `society.py` is 45 lines because every method it
held moved to a sibling; this file could not do the same with its constants,
for a reason specific to how this project's numbers are tracked rather than
to this split's own judgement. `sim/constants.py`'s `_import_declaring_
modules()` keeps an explicit list of every module that calls `declare()`,
by dotted name, and `sim/tests/test_constants_burndown.py`'s
`test_every_declaring_module_under_sim_world_is_in_the_list` fails if any
`sim/world/*.py` file contains the literal text `declare(` without its own
dotted name in that list - a number declared in an unlisted file goes
missing from the burndown silently, which is the exact bug that test exists
to catch (see its own docstring). The brief this split was done under owns
only this file and new files under `sim/world/`, and forbids editing
anything else, `sim/constants.py` included. So every `declare()` call this
module makes - which is effectively everything from SEED AND YIELD BIOLOGY
below through CALIBRATION TARGETS, the bulk of what is left of this file -
had to stay in the one file already on that list: this one. The `Crop`/
`Soil`/`Rotation`/`Toolkit`/`StorageTechnique` namedtuple types and the named
table instances built from them (`WHEAT`, `POTATOES`, `RICE`, the soils, the
rotations, the toolkits, the storage techniques) stayed here for the same
reason they are grouped with the constants at all: they are the SAME
subject, declared numbers gathered into named bundles, and moving the
instance-construction lines to a sibling on their own would have grouped by
size rather than by subject, which the brief this split was done under says
explicitly not to do. The result is that this file, not any sibling, is the
one still over the target line count - see this task's own report for the
measured total - and that is the honest shape of this particular split, not
an oversight: every subject that COULD move without touching a file outside
this split's ownership did.

THE IMPORT SURFACE IS UNCHANGED. Every name this module exported before the
split - every declared constant, `Crop`/`Soil`/`Rotation`/`Toolkit`/
`StorageTechnique` and their table instances, `Land`, `Storage`, `YearFlows`,
and every function - is still reachable as `agriculture.<name>` afterward.
The relative imports just above the `if __name__ == "__main__":` block below
pull the three siblings' names back into this module's own namespace for
exactly that reason; nothing anywhere else in the repository needed to
change an import or an attribute access for this split to be invisible to it.
"""
import collections
import random
from typing import Optional

from sim.constants import declare
from sim.world.shared_constants import (
    ANNUAL_LABOUR_HOURS_PER_FARM_WORKER,
    FALLOW_SHARE_OF_HOLDING,
    LABOUR_OUTPUT_ELASTICITY,
    REFERENCE_LABOUR_HOURS_PER_HECTARE,
    SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY,
    WHEAT_ENERGY_KCAL_PER_KG,
)
# THE SIX NAMES ABOVE ARE NOT RE-DECLARED BELOW (one of them,
# SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY, is given this file's
# own historical public name, HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY,
# by a plain assignment where it used to be declared - see that spot
# below). Each used to be its own
# `declare()` call in this file, independently, with a value that happened
# to match sim/world/land.py's own independent copy of the same physical
# fact under a DIFFERENT name (LABOUR_OUTPUT_ELASTICITY /
# LAND_LABOUR_OUTPUT_ELASTICITY, and three more pairs like it - see
# sim/world/shared_constants.py's own module docstring for the incident and
# the full inventory). Importing them from one shared declaration means
# there is exactly one number to change and no second copy that can
# silently disagree with it - the STANDALONE property this file and
# land.py both keep (see this file's own docstring) is unaffected, because
# sim/world/shared_constants.py imports nothing but sim.constants.declare,
# the same as this file already does. This file's own historical public
# names for these five values (assigned just below, where each used to be
# declared) are kept unchanged, so every existing caller and test that
# reads e.g. `agriculture.LABOUR_OUTPUT_ELASTICITY` is unaffected.

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

# REFERENCE_LABOUR_HOURS_PER_HECTARE, LABOUR_OUTPUT_ELASTICITY and
# ANNUAL_LABOUR_HOURS_PER_FARM_WORKER used to each be declared here. All
# three are now imported from sim.world.shared_constants (see this file's
# top-of-file import comment) because sim/world/land.py's own LABOUR
# INTENSITY section needs the identical Cobb-Douglas physics and used to
# duplicate all three under LAND_-prefixed names rather than import this
# file (land.py is STANDALONE and may not). One declaration, imported by
# both, replaces two that had to be kept equal by hand. The names below are
# unchanged from this module's history - REFERENCE_LABOUR_HOURS_PER_HECTARE
# is still the labour intensity GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA
# is quoted at and the anchor the Cobb-Douglas yield curve below is
# calibrated against (see the module docstring's headline-number section
# for why it is this module's leading suspect for the computed
# farm-population share coming out far below the historical 80-90%);
# LABOUR_OUTPUT_ELASTICITY is still the curve shape that makes doubling
# labour on fixed land yield less than double the output;
# ANNUAL_LABOUR_HOURS_PER_FARM_WORKER is still how many hours one adult can
# give to field work across a year, used only to turn a per-hectare labour
# requirement into a hectares-per-worker figure for the headline
# calibration check. See sim/world/shared_constants.py for the full
# provenance and why paragraphs, which are not duplicated here for the same
# reason the numbers themselves no longer are.

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

# FALLOW_SHARE_OF_HOLDING used to be declared here. It is now imported from
# sim.world.shared_constants (see this file's top-of-file import comment):
# sim/world/land.py needs this exact fraction too, and used to declare its
# own reciprocal transform of it (FALLOW_HOLDING_MULTIPLIER = 1 / (1 -
# fallow_share)) as an independently-set number rather than a derived one -
# the HARD case of the same quantity duplicated under a different name AND
# a different unit, not merely a different name. See
# sim/world/shared_constants.py's own LAND USE section for the full
# provenance and why land.py's copy is now arithmetic on this declaration
# instead of a second `declare()` call. This name and its role are
# otherwise unchanged: it still converts cropped area into the land a farm
# must actually hold, and the later three-field rotation's own, DIFFERENT
# idle share is still THREE_FIELD_FALLOW_SHARE_OF_HOLDING below, declared
# separately because it names a different technique, not a duplicate of
# this one.

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

MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE = declare(
    "MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE", 1.75,
    unit="dimensionless (annual grain a person eats in a year of plenty, as a "
         "multiple of what the same person eats at bare subsistence)",
    kind="biological_parameter",
    source="Subsistence here is the roughly 2,000 kcal a day this project "
           "already uses. A person doing sustained heavy agricultural labour "
           "eats on the order of 3,500 to 4,000 kcal a day, which is where "
           "1.75 comes from. It is a ceiling on what a HUMAN can usefully "
           "eat, not on what a household can acquire - grain beyond it goes "
           "to livestock, brewing, seed or market rather than into a person.",
    why="Without a ceiling above subsistence the model had no way to say a "
        "population ate WELL. Consumption was min(demand, stock), so the "
        "nutrition ratio could never exceed 1.0 however full the granary "
        "was, and a good year therefore bought nothing while a bad year "
        "still cost lives. That one-sidedness is what Complaints/45 is "
        "about, and the granary only fixed half of it - it banked the grain "
        "and then never let anyone eat it.")


GRANARY_CAPACITY_YEARS_OF_DEMAND = declare(
    "GRANARY_CAPACITY_YEARS_OF_DEMAND", 1.0,
    kind="engineering_estimate",
    unit="years of a population's own annual food demand (dimensionless)",
    source="Documented pre-modern and early-modern grain-reserve stocking "
           "targets cluster in the six-to-twelve-month range - e.g. an "
           "1886 proposal for a government-held UK wheat reserve specified "
           "6 or alternatively 12 months' consumption, and Egyptian and "
           "Roman practice (storing surplus 'years of plenty' against "
           "'years of scarcity'; the annona's horrea) describes the same "
           "kind of target without giving a precise figure. Taken at the "
           "generous (12-month) end of that documented range, the same "
           "'generous reading' convention HARVEST_WINDOW_DAYS's own "
           "declaration uses when a range rather than a point is all the "
           "sourcing gives.",
    confidence="C",
    why="A granary is a physical structure, not an unlimited ledger entry: "
        "past some size, more grain does not fit in the pits and raised "
        "floors a settlement has actually built, and a surplus beyond that "
        "is not banked - it is sold off, fed to livestock, left to rot in "
        "the open, or (mechanically the same to this module) simply never "
        "harvested in from the field. This is DIFFERENT from "
        "GRAIN_SPOILAGE_RATE_PER_YEAR just above: spoilage is the ongoing "
        "cost of keeping grain that IS stored; this is the ceiling on how "
        "much can be stored in the first place. Expressed as a multiple of "
        "annual demand (rather than a fixed tonnage) so it scales with "
        "population automatically, the same way farmland_for_population "
        "does. Applied at the engine boundary (Sim._demographic_recovery in "
        "sim/engine/core.py), not inside Storage.step itself: whether a "
        "surplus fits in existing storage infrastructure is a fact about "
        "the CIVILISATION's built capacity, not about the abstract "
        "sow-grow-harvest-eat-spoil cycle this class models, and keeping it "
        "out of Storage.step also keeps that class's own conservation "
        "identity (stock_before_kg + harvest - seed - consumption - "
        "spoilage - seed_retained == stock_after_kg, sim/tests/"
        "test_agriculture.py's own check) exactly as it always was - the "
        "cap is a policy choice about what carries INTO next year's "
        "Storage, not a new term inside one year's accounting. TEMPORARY_"
        "HEURISTIC IN SPIRIT EVEN THOUGH THE SOURCE IS REAL (CLAUDE.md "
        "SS3.4): the 6-12 month figures above are policy TARGETS people "
        "recommended holding, not a measured archaeological capacity for "
        "Roman-Italian farm storage specifically. Replace with an actual "
        "capacity figure (horreum floor area per capita, or a peasant "
        "household's granary volume) if one is ever sourced.")

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

# HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY keeps this module's own
# historical public name, but the VALUE now comes from sim.world.
# shared_constants's SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY (see
# this file's top-of-file import) rather than a second `declare()` call.
# sim/world/land.py needs the identical figure (formerly under its own
# LAND_HUMAN_CALORIC_NEED_KCAL_PER_DAY name) and now imports the same
# shared declaration; sim/world/demand.py, sim/world/demography.py and
# sim/world/military_logistics.py still declare it independently under
# their own names (out of this change's ownership - see
# sim/world/shared_constants.py's own WHAT DOES NOT BELONG HERE section and
# sim/tests/test_shared_constants.py for how a future drift there is still
# caught).
HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY = (
    SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY)

# WHEAT_ENERGY_KCAL_PER_KG used to be declared here too; it is now imported
# directly under this same name from sim.world.shared_constants (see the
# top-of-file import), for the identical reason.

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

# ============================================================================
# COMPOSITION POINT - everything below used to be defined here, in this
# file. It now lives in three sibling modules, grouped by subject rather
# than by size (see this file's own docstring, "THIS FILE AND ITS SIBLINGS,
# AND WHY THIS SPLIT LOOKS DIFFERENT", for what each one holds and why the
# constants and tables above did not move with them). These imports pull
# every one of those names back into THIS module's namespace, so that
# `agriculture.gross_harvest_kg`, `agriculture.Storage`,
# `agriculture.fraction_of_population_that_must_farm` and every other name
# this module exported before the split keep resolving exactly as they did,
# with no edit needed anywhere else in the repository.
#
# ORDER MATTERS HERE, AND IS NOT ALPHABETICAL. Each sibling's own top-level
# imports reach back into THIS module (`sim.world.agriculture` / bare
# `world.agriculture`, whichever name this file is currently loading under -
# see sim/world/agriculture.py's own STANDALONE ON PURPOSE section and
# CLAUDE.md SS6's "world.agriculture vs sim.world.agriculture" note) for the
# constants and tables declared above. That reach-back only resolves because,
# by the time Python executes the imports below, every name above this point
# already exists as an attribute of this (still executing) module - the
# ordinary, well-understood pattern for a partially-initialized parent
# handing values to a child it is about to import, not the genuinely broken
# shape of two siblings each waiting on the other to finish (see
# agriculture_yield.py's own comment on the one place that shape would have
# arisen here, and how it is avoided). agriculture_yield has no dependency on
# the other two siblings at import time and loads first; agriculture_storage
# depends on agriculture_yield; agriculture_labour depends on both.
from .agriculture_yield import (
    Land,
    _max_hectares_harvestable_by_labour,
    draw_weather_multiplier,
    gross_harvest_kg,
    hectares_reaped_per_worker_hour,
    marginal_product_of_labour_kg_per_hour,
    max_hectares_reapable_by_crew,
)
from .agriculture_storage import (
    Storage,
    YearFlows,
    annual_food_demand_kg_per_person,
    granary_capacity_kg,
    stock_to_carry_forward_kg,
)
from .agriculture_labour import (
    farm_workers_fte_for_population,
    farmland_for_population,
    fraction_of_population_that_must_farm,
    hectares_cropped_per_farm_worker,
    hectares_per_worker_annual_hours_ceiling,
    hectares_per_worker_harvest_window_ceiling,
    holding_hectares_required_per_farm_worker,
)


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
