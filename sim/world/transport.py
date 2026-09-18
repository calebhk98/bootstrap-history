"""Freight: how far a load of cargo moves for how much feed, how many driver
hours, and how much of a vehicle's working life, per tonne-kilometre.

WHAT THIS IS FOR. Every other cost in this project eventually needs to move
something from where it is made to where it is used, and until now nothing
in the simulation has had an opinion on what that costs beyond a number
copied into `data/prices.json`. This module answers "what does it take to
move one tonne one kilometre" from physics and animal biology alone: a
draught animal's tractive effort against rolling resistance and gradient, a
pack animal's carrying capacity as a fraction of its own body weight, and
buoyancy's removal of the weight-bearing term that makes water transport an
order of magnitude cheaper than a cart on the same team. No prices, no
wages, no economy anywhere in this file - see NOT A MONEY FIGURE below for
why, and what it does instead.

STANDALONE ON PURPOSE. Nothing here imports `sim/engine/`, `sim/world/
agriculture.py` or `sim/world/demography.py`. This module needs none of
them: freight cost is a question about physics and biology, not about
prices or population, and see `sim/world/__init__.py` for why a package
built this way survives other agents editing those modules concurrently -
a module with no dependency on those paths cannot be broken by their edits,
and cannot break their tests either. Where this module happens to declare
a constant another of those files also declares under a similar name (human
caloric need, the value of an hour, the acceleration of gravity), it is
declared again here rather than imported, for the same reason agriculture.py
gives for its own HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY: a cross-import
between standalone modules is exactly the wiring none of them are supposed
to do yet.

NOT A MONEY FIGURE. `sim/solve_prices.py`'s numeraire is one hour of
unskilled labour (see its own docstring, "PRICE SOLVER - numeraire is one
hour of unskilled..."), and this module's job stops one step short of a
price: every function here returns PHYSICAL quantities per tonne-km -
kilograms of animal feed, hours of a driver's attention, a fraction of a
vehicle's service life consumed - packaged as `FreightPhysicalInputs`. It
does not multiply feed by a grain price or a driver-hour by a wage, because
this project does not have a working grain price or wage yet (that is
exactly the gap `ENDOGENOUS_COSTS_AND_DOMAINS.md` Part 2 exists to close).
Handing back hours and kilograms rather than an invented "cost" means this
module can be built and trusted now, and wired into a price the day the
price solver can read `data/production/`-style physical inputs at all -
see `sim/world/__init__.py`'s reasoning for why standalone-first pays off.

THE PHYSICS, IN ONE PARAGRAPH. A draught animal can sustain a pull of
roughly a tenth of its own body weight for a working day; that pull has to
overcome rolling resistance (a coefficient times the weight of vehicle plus
cargo - the SAME coefficient a Roman paved road, a dry dirt track and a
mud season give wildly different values for, which is the entire reason
roads get built) plus gradient (the same coefficient-style term, but on the
combined weight of vehicle, cargo AND the animals themselves, because they
are climbing too). Solve that balance for the cargo mass and multiply by the
distance the animal can walk in its working day, and a tonne-km figure falls
out with no historical number fed in anywhere. Water removes the
weight-bearing term entirely - a hull's cargo is held up by buoyancy, not by
wheels pressed against the ground, so the resistance a towing animal has to
overcome is a much smaller hull-drag term with no dependence on total
weight the way rolling resistance has - which is the physical reason a horse
that can pull one or two tonnes on a road can tow a great many tonnes on a
canal. See `WATER_TRANSPORT_RESISTANCE_COEFFICIENT_AT_TOW_SPEED`'s own
declaration for exactly where that number is a genuine derivation and where
it is a labelled stand-in for a proper quadratic hull-drag model.

THE ANIMAL'S OWN FEED AS A LOAD. `maximum_one_way_range_before_self_
defeating_km` answers the question that gives pre-industrial land transport
its economic range limit: past some distance, hauling enough feed for the
whole trip consumes the team's entire spare pulling capacity, and cargo
delivered falls to zero even though the team never stops moving. That
distance is not stated anywhere in this file - it is solved for, from the
same tractive-effort balance and the same feed-per-day figure every other
function here uses. See that function's docstring for the exact algebra and
what it deliberately does not model (a return leg, resupply along the
route).

WHAT THIS MODULE DOES NOT DO. No routing or pathfinding, no road network, no
ports or harbours as objects, no wiring into `sim/engine/`, and nothing
involving money - all explicitly out of scope for the task this module
answers. It also does not model: a cart's wheels sinking into mud as a
function of ground pressure (mud is one fixed rolling-resistance coefficient
here, not a physics-of-soil-mechanics model); load-dependent vehicle wear
(the wear rate below is stated per kilometre travelled, not per kilogram
carried, which understates how much a heavy load accelerates axle and wheel
wear relative to a light one); more than one driver regardless of team size
(a four-ox wagon almost certainly needed more supervision than a one-ox
cart, and this module charges both the same one driver's hours); and
seasonal or daily variation in an animal's condition, road quality or
weather, all of which `sim/world/agriculture.py`'s `draw_weather_multiplier`
suggests a template for if this module ever needs one.

CALIBRATION TARGETS, read ONLY by `sim/tests/test_transport.py`, never by
this file's own functions - see the section below the physical constants.
Diocletian's Price Edict (301 AD) prices land freight, per the classic
reading, at roughly one to two orders of magnitude more than sea freight per
unit distance, and the standard economic-history claim (Finley, THE ANCIENT
ECONOMY, and others building on the Edict) is that grain could not travel
far overland before its delivered cost became prohibitive. Both are checked
against, honestly, and never tuned to - see the test module for the
comparison and the reading of where this module's numbers land relative to
each.
"""
import collections

from sim.constants import declare

# ============================================================================
# PHYSICAL CONSTANTS
# ============================================================================

GRAVITATIONAL_ACCELERATION_M_PER_S2 = declare(
    "GRAVITATIONAL_ACCELERATION_M_PER_S2", 9.81,
    kind="physical_constant",
    unit="m/s^2",
    source="Standard gravity.",
    confidence="A",
    why="Converts every mass in this module (animal body weight, vehicle "
        "self-weight, cargo) into the force an animal actually has to "
        "generate or resist - tractive effort, rolling resistance and "
        "gradient are all forces, and mass alone is not one.")

JOULES_PER_KCAL = declare(
    "JOULES_PER_KCAL", 4184.0,
    kind="physical_constant",
    unit="joules/kcal",
    source="Definition of the (thermochemical) kilocalorie.",
    confidence="A",
    why="The single conversion this module needs to move between mechanical "
        "work (a force moving a cargo a distance, in joules) and animal "
        "feed (a calorie intake, in kcal) - see MUSCULAR_EFFICIENCY_OF_"
        "DRAUGHT_WORK for the other half of that conversion.")

# ============================================================================
# DRAUGHT ANIMAL METABOLISM
# ============================================================================
# An animal eats to do two different things: stay alive (maintenance) and do
# external mechanical work (hauling, climbing). Maintenance is derived from
# body mass via the standard interspecific mammalian scaling law rather than
# stated per species, so the model has a real mechanism for "a bigger animal
# eats more even standing still" rather than a table of invented numbers.

KLEIBER_BASAL_METABOLIC_COEFFICIENT_KCAL_PER_DAY = declare(
    "KLEIBER_BASAL_METABOLIC_COEFFICIENT_KCAL_PER_DAY", 70.0,
    kind="biological_parameter",
    unit="kcal/day per kg^0.75",
    source="Kleiber's law (Kleiber 1932, 'Body size and metabolism'): "
           "basal metabolic rate across mammals from mouse to elephant "
           "fits BMR (kcal/day) = 70 * mass_kg^0.75 to within a few "
           "percent - the standard interspecific scaling constant, not "
           "fitted for this project.",
    confidence="B",
    why="Lets this module derive how much an ox eats simply to exist from "
        "its body mass, the same physical fact for any species, rather "
        "than inventing a separate 'oxen eat X kg/day' number with no "
        "mechanism behind it.")

KLEIBER_MASS_EXPONENT = declare(
    "KLEIBER_MASS_EXPONENT", 0.75,
    kind="biological_parameter",
    unit="dimensionless (exponent on body mass in kg)",
    source="The '3/4-power law' of metabolic scaling - among the most "
           "widely replicated empirical relationships in comparative "
           "physiology, holding from unicellular organisms to whales.",
    confidence="A",
    why="Why a heavier draught animal (a horse relative to a mule) does "
        "not need proportionally more feed just to stand around: "
        "maintenance metabolism scales sub-linearly with mass.")

FIELD_METABOLIC_RATE_MULTIPLIER_OVER_BMR = declare(
    "FIELD_METABOLIC_RATE_MULTIPLIER_OVER_BMR", 2.5,
    kind="engineering_estimate",
    unit="multiple of basal metabolic rate (dimensionless)",
    source="Comparative field-metabolic-rate studies of free-ranging "
           "mammals (the doubly-labelled-water literature surveyed by "
           "Nagy 1994, 2005) typically find sustained daily energy "
           "expenditure at 2-4x measured resting BMR, from digestion "
           "(the specific dynamic action of processing a bulky, "
           "fibrous forage diet), thermoregulation and baseline "
           "standing/walking activity, before any harnessed WORK is "
           "added.",
    confidence="C",
    why="KLEIBER_BASAL_METABOLIC_COEFFICIENT_KCAL_PER_DAY gives a "
        "laboratory RESTING rate; this converts it into what a working "
        "animal actually has to eat each day just to live and stand in a "
        "field, before a single hour in harness. It is an average across "
        "studied mammal species generally, not measured for oxen, horses "
        "or mules specifically - the study that would derive an "
        "ox-specific figure does not exist inside this project.")

MUSCULAR_EFFICIENCY_OF_DRAUGHT_WORK = declare(
    "MUSCULAR_EFFICIENCY_OF_DRAUGHT_WORK", 0.20,
    kind="biological_parameter",
    unit="dimensionless (mechanical work out / metabolic energy in)",
    source="Exercise physiology of sustained large-muscle-group work "
           "(walking, hauling) in mammals generally reports gross "
           "mechanical efficiency in the 20-25% range, the remainder "
           "released as heat.",
    confidence="C",
    why="The second half of the mechanical-work-to-feed conversion: how "
        "many kcal of feed one joule of USEFUL pulling or climbing work "
        "actually costs an animal, after the four-fifths of its metabolic "
        "effort that becomes heat rather than motion.")

FEED_ENERGY_DENSITY_KCAL_PER_KG = declare(
    "FEED_ENERGY_DENSITY_KCAL_PER_KG", 2400.0,
    kind="engineering_estimate",
    unit="kcal/kg",
    source="A working draught ration mixing hay (roughly 1,800 kcal/kg "
           "dry matter) with a grain supplement (roughly 3,300-3,500 "
           "kcal/kg for oats or barley) for an animal doing sustained "
           "hauling work; 2,400 sits toward the hay-heavy end of what "
           "such a mixed ration implies.",
    confidence="C",
    why="Converts every feed requirement this module computes from kcal "
        "into kilograms - the physical unit `sim/solve_prices.py`'s "
        "numeraire (an hour of unskilled labour) can eventually be asked "
        "to price, the same role WHEAT_ENERGY_KCAL_PER_KG plays in "
        "sim/world/agriculture.py.")

# ============================================================================
# ANIMAL TABLE
# ============================================================================
# Each animal is a bundle of independently-sourced physical facts: how heavy
# it is (sets its maintenance cost via Kleiber's law, and its own share of
# gradient-climbing work), how much of its own weight it can sustain as a
# pull or a pack load, how fast it walks, and how many hours a day it can
# actually be worked. None of these is fitted to reproduce a transport cost -
# they are the same order-of-magnitude figures found across draught-animal
# husbandry and veterinary literature.

Animal = collections.namedtuple(
    "Animal",
    ["name", "body_mass_kg", "sustained_pull_fraction_of_bodyweight",
     "pack_load_fraction_of_bodyweight", "walking_speed_km_per_hour",
     "working_hours_per_day"])

OX_BODY_MASS_KG = declare(
    "OX_BODY_MASS_KG", 550.0,
    kind="engineering_estimate",
    unit="kg",
    source="Mature draught oxen of pre-industrial Mediterranean and "
           "European breeds are commonly given at roughly 450-650 kg "
           "live weight; 550 is the midpoint.",
    confidence="C",
    why="Drives the ox's maintenance feed (via Kleiber's law), its own "
        "share of gradient-climbing work, and its sustained pull in "
        "absolute newtons together with the fraction below.")

OX_SUSTAINED_PULL_FRACTION_OF_BODYWEIGHT = declare(
    "OX_SUSTAINED_PULL_FRACTION_OF_BODYWEIGHT", 0.11,
    kind="engineering_estimate",
    unit="fraction of body weight (dimensionless)",
    source="Draught-animal engineering literature commonly gives a "
           "SUSTAINED (all-day) pull of roughly 10-15% of body weight for "
           "oxen and horses, well below the 20-30%+ they can exert briefly; "
           "0.11 sits near the low end of that range, the conservative "
           "reading for a figure this module treats as a hard daily "
           "ceiling rather than a peak.",
    confidence="C",
    why="The other half of the ox's tractive-force ceiling: multiplied by "
        "body weight, this is the force an ox TEAM can be relied on to "
        "generate all day, which is what MAX_CARGO_MASS_KG below is "
        "solved against.")

OX_PACK_LOAD_FRACTION_OF_BODYWEIGHT = declare(
    "OX_PACK_LOAD_FRACTION_OF_BODYWEIGHT", 0.15,
    kind="temporary_heuristic",
    unit="fraction of body weight (dimensionless)",
    source=None,
    confidence="D",
    why="Oxen were rarely used as pack animals historically (mules and "
        "horses were the standard choice - see the mule and horse "
        "entries below), so no sourced figure specific to oxen-as-pack-"
        "carriers was found; this is a plausible placeholder in line "
        "with the mule and horse figures, kept only so `Animal` has a "
        "complete, uniform interface, and marked temporary_heuristic "
        "rather than engineering_estimate for exactly that reason. Not "
        "exercised by this module's own headline comparisons.")

OX_WALKING_SPEED_KM_PER_HOUR = declare(
    "OX_WALKING_SPEED_KM_PER_HOUR", 3.0,
    kind="engineering_estimate",
    unit="km/hour",
    source="Oxen under load are consistently reported as slower walkers "
           "than horses, typically 2.5-3.5 km/h.",
    confidence="C",
    why="Sets how far an ox team covers per working hour - the other "
        "factor, alongside working hours per day, that turns a per-day "
        "cargo mass into a per-day tonne-km figure.")

OX_WORKING_HOURS_PER_DAY = declare(
    "OX_WORKING_HOURS_PER_DAY", 6.0,
    kind="engineering_estimate",
    unit="hours/day",
    source="Draught oxen historically worked shorter days than horses - "
           "commonly cited at 5-6 hours of actual pulling - needing more "
           "time for rumination (oxen are ruminants; horses are not) and "
           "rest between bouts.",
    confidence="C",
    why="The other factor in distance covered per day; also sets driver "
        "hours charged per tonne-km, since one driver's attention for the "
        "whole working day is charged against whatever the team hauls "
        "that day.")

OX = Animal(
    name="ox",
    body_mass_kg=OX_BODY_MASS_KG,
    sustained_pull_fraction_of_bodyweight=OX_SUSTAINED_PULL_FRACTION_OF_BODYWEIGHT,
    pack_load_fraction_of_bodyweight=OX_PACK_LOAD_FRACTION_OF_BODYWEIGHT,
    walking_speed_km_per_hour=OX_WALKING_SPEED_KM_PER_HOUR,
    working_hours_per_day=OX_WORKING_HOURS_PER_DAY)

HORSE_BODY_MASS_KG = declare(
    "HORSE_BODY_MASS_KG", 450.0,
    kind="engineering_estimate",
    unit="kg",
    source="Pre-industrial draught and pack horses were substantially "
           "smaller than the heavy draught breeds (Shire, Percheron) bred "
           "from the medieval period onward for exactly this work; "
           "ancient- and early-medieval-period horses are commonly put at "
           "roughly 300-500 kg live weight. 450 is toward the upper end, "
           "reflecting a horse selected and fed for haulage rather than a "
           "riding animal.",
    confidence="C",
    why="Same role as the ox's body mass: drives maintenance feed and "
        "gradient work.")

HORSE_SUSTAINED_PULL_FRACTION_OF_BODYWEIGHT = declare(
    "HORSE_SUSTAINED_PULL_FRACTION_OF_BODYWEIGHT", 0.10,
    kind="engineering_estimate",
    unit="fraction of body weight (dimensionless)",
    source="Same draught-engineering literature and range as the ox's "
           "figure; taken very slightly lower here on the general finding "
           "that oxen sustain a marginally higher fraction of body weight "
           "in a full day's steady pull, while a horse's advantage is "
           "speed and stamina rather than peak fraction pulled.",
    confidence="C",
    why="Same role as OX_SUSTAINED_PULL_FRACTION_OF_BODYWEIGHT, for the "
        "horse.")

HORSE_PACK_LOAD_FRACTION_OF_BODYWEIGHT = declare(
    "HORSE_PACK_LOAD_FRACTION_OF_BODYWEIGHT", 0.20,
    kind="engineering_estimate",
    unit="fraction of body weight (dimensionless)",
    source="Pack-animal husbandry literature (military and civilian "
           "packing manuals alike) commonly gives sustained multi-day "
           "pack loads of roughly a fifth of a horse's body weight, "
           "somewhat below what a mule sustains at the same relative "
           "load - see MULE_PACK_LOAD_FRACTION_OF_BODYWEIGHT.",
    confidence="C",
    why="What a horse can carry on its own back rather than pull behind "
        "it - the number PACK transport is solved against, with no "
        "vehicle, no wheels and no rolling-resistance surface at all.")

HORSE_WALKING_SPEED_KM_PER_HOUR = declare(
    "HORSE_WALKING_SPEED_KM_PER_HOUR", 4.5,
    kind="engineering_estimate",
    unit="km/hour",
    source="A loaded horse's sustained walking pace is commonly given at "
           "roughly 4-5 km/h, faster than an ox's.",
    confidence="C",
    why="Same role as the ox's walking speed.")

HORSE_WORKING_HOURS_PER_DAY = declare(
    "HORSE_WORKING_HOURS_PER_DAY", 8.0,
    kind="engineering_estimate",
    unit="hours/day",
    source="Horses, non-ruminants with faster digestion and no cud to "
           "chew, are consistently worked longer days than oxen in "
           "draught-animal comparisons - commonly 8 hours of steady "
           "work.",
    confidence="C",
    why="Same role as the ox's working hours.")

HORSE = Animal(
    name="horse",
    body_mass_kg=HORSE_BODY_MASS_KG,
    sustained_pull_fraction_of_bodyweight=HORSE_SUSTAINED_PULL_FRACTION_OF_BODYWEIGHT,
    pack_load_fraction_of_bodyweight=HORSE_PACK_LOAD_FRACTION_OF_BODYWEIGHT,
    walking_speed_km_per_hour=HORSE_WALKING_SPEED_KM_PER_HOUR,
    working_hours_per_day=HORSE_WORKING_HOURS_PER_DAY)

MULE_BODY_MASS_KG = declare(
    "MULE_BODY_MASS_KG", 350.0,
    kind="engineering_estimate",
    unit="kg",
    source="Mules (horse-donkey hybrids) bred for pack work are smaller "
           "than draught horses, commonly 300-400 kg.",
    confidence="C",
    why="Same role as the other animals' body mass.")

MULE_SUSTAINED_PULL_FRACTION_OF_BODYWEIGHT = declare(
    "MULE_SUSTAINED_PULL_FRACTION_OF_BODYWEIGHT", 0.11,
    kind="engineering_estimate",
    unit="fraction of body weight (dimensionless)",
    source="Mules were used to pull carts historically, though less "
           "commonly than for packing; taken level with the ox's figure "
           "in the absence of a documented reason to place it elsewhere "
           "in the same 10-15% range.",
    confidence="D",
    why="Completes `Animal`'s interface for a mule pulling a cart, which "
        "this module's own headline comparisons do not exercise - packing "
        "is the mule's documented strength (see MULE_PACK_LOAD_FRACTION_"
        "OF_BODYWEIGHT) and is what this module actually uses it for.")

MULE_PACK_LOAD_FRACTION_OF_BODYWEIGHT = declare(
    "MULE_PACK_LOAD_FRACTION_OF_BODYWEIGHT", 0.25,
    kind="engineering_estimate",
    unit="fraction of body weight (dimensionless)",
    source="Pack-animal literature (veterinary and military packing "
           "manuals alike) consistently credits mules with the best "
           "sustained load-to-body-weight ratio of any common pack "
           "animal, commonly cited at roughly 20-30% of body weight over "
           "multi-day travel, ahead of horses and donkeys.",
    confidence="C",
    why="This is the number that makes a mule train, not a horse train, "
        "the standard historical choice for mountain and off-road cargo - "
        "no wheels, no rolling-resistance surface at all, and the highest "
        "carrying fraction of the three animals this module tables.")

MULE_WALKING_SPEED_KM_PER_HOUR = declare(
    "MULE_WALKING_SPEED_KM_PER_HOUR", 4.0,
    kind="engineering_estimate",
    unit="km/hour",
    source="Between the ox's and the horse's pace in most pack-animal "
           "comparisons.",
    confidence="C",
    why="Same role as the other animals' walking speed.")

MULE_WORKING_HOURS_PER_DAY = declare(
    "MULE_WORKING_HOURS_PER_DAY", 8.0,
    kind="engineering_estimate",
    unit="hours/day",
    source="Non-ruminant like the horse; worked comparable hours in pack "
           "trains.",
    confidence="C",
    why="Same role as the other animals' working hours.")

MULE = Animal(
    name="mule",
    body_mass_kg=MULE_BODY_MASS_KG,
    sustained_pull_fraction_of_bodyweight=MULE_SUSTAINED_PULL_FRACTION_OF_BODYWEIGHT,
    pack_load_fraction_of_bodyweight=MULE_PACK_LOAD_FRACTION_OF_BODYWEIGHT,
    walking_speed_km_per_hour=MULE_WALKING_SPEED_KM_PER_HOUR,
    working_hours_per_day=MULE_WORKING_HOURS_PER_DAY)

DEFAULT_DRAUGHT_ANIMAL = OX
DEFAULT_PACK_ANIMAL = MULE

# ============================================================================
# VEHICLE TABLE
# ============================================================================
# A vehicle contributes two things: dead weight the team has to haul or
# carry before any cargo at all, and a service life that turns distance
# travelled into a fraction of the vehicle worn out. Neither service-life
# figure below has a real citation - no fatigue-life study of an ancient
# cart wheel exists inside this project - so both are `temporary_heuristic`,
# unlike almost everything else in this file. See the module docstring's
# WHAT THIS MODULE DOES NOT DO for what the resulting wear figure leaves out
# (it does not scale with load, which understates a heavy wagon's true wear
# relative to a light one).

Vehicle = collections.namedtuple(
    "Vehicle", ["name", "self_mass_kg", "service_life_km"])

PACK_SADDLE_MASS_KG = declare(
    "PACK_SADDLE_MASS_KG", 15.0,
    kind="engineering_estimate",
    unit="kg",
    source="A wood-framed pack saddle with panniers or girth rigging is "
           "a small fraction of the animal's own body weight - on the "
           "order of 10-20 kg for a loaded rig, before cargo.",
    confidence="C",
    why="Dead weight a pack animal carries before any cargo - subtracted "
        "from MULE_PACK_LOAD_FRACTION_OF_BODYWEIGHT's implied capacity the "
        "same way a cart's self-weight is subtracted from what a team can "
        "pull.")

PACK_SADDLE_SERVICE_LIFE_KM = declare(
    "PACK_SADDLE_SERVICE_LIFE_KM", 8000.0,
    kind="temporary_heuristic",
    unit="km before the rig needs substantial rebuilding",
    source=None,
    confidence="D",
    why="No fatigue-life or wear-rate study of a leather-and-wood pack "
        "rig exists inside this project; this is an order-of-magnitude "
        "placeholder (a season or two of regular use) pending one, which "
        "is why it is a temporary_heuristic and not an engineering_"
        "estimate like the saddle's mass.")

PACK_SADDLE = Vehicle(
    name="pack saddle", self_mass_kg=PACK_SADDLE_MASS_KG,
    service_life_km=PACK_SADDLE_SERVICE_LIFE_KM)

CART_SELF_MASS_KG = declare(
    "CART_SELF_MASS_KG", 200.0,
    kind="engineering_estimate",
    unit="kg",
    source="A two-wheeled wood-and-iron cart of the kind pulled by one or "
           "two draught animals is commonly put at roughly 150-250 kg "
           "empty.",
    confidence="C",
    why="Dead weight the team hauls before any cargo, in exactly the "
        "same tractive-force balance as the cargo itself - see "
        "max_cargo_mass_kg.")

CART_SERVICE_LIFE_KM = declare(
    "CART_SERVICE_LIFE_KM", 4000.0,
    kind="temporary_heuristic",
    unit="km before major repair (wheel or axle replacement)",
    source=None,
    confidence="D",
    why="Same status as PACK_SADDLE_SERVICE_LIFE_KM: an invented order-of-"
        "magnitude placeholder, not a measured wheel or axle fatigue "
        "life, pending a real structural-wear model. Historical accounts "
        "agree carts needed frequent wheel and axle repair; none supply a "
        "kilometre figure this module could use instead.")

CART = Vehicle(
    name="two-wheeled cart", self_mass_kg=CART_SELF_MASS_KG,
    service_life_km=CART_SERVICE_LIFE_KM)

WAGON_SELF_MASS_KG = declare(
    "WAGON_SELF_MASS_KG", 500.0,
    kind="engineering_estimate",
    unit="kg",
    source="A four-wheeled wagon built for a larger team (four or more "
           "draught animals) is heavier than a two-wheeled cart by roughly "
           "two to three times, commonly put at 400-600 kg empty.",
    confidence="C",
    why="Same role as the cart's self-mass. NOTE A FINDING THIS PRODUCES "
        "RATHER THAN ASSUMES: with team pull exactly linear in team size "
        "(see sustained_pull_newtons), one 4-ox wagon (500 kg dead "
        "weight) actually hauls slightly LESS cargo than two 2-ox carts "
        "(400 kg dead weight combined) using the same four oxen - "
        "2.53 t versus 2.63 t on DIRT_TRACK, see sim/tests/test_transport."
        "py. This module has no mechanism that would make a bigger "
        "vehicle more efficient per animal (no economy from fewer, "
        "larger wheels spreading load, no coordination cost for driving "
        "several separate carts) - it is recorded here as an honest gap "
        "rather than corrected by inventing one, exactly the kind of "
        "finding CLAUDE.md SS3.2 asks this project to write down instead "
        "of paper over.")

WAGON_SERVICE_LIFE_KM = declare(
    "WAGON_SERVICE_LIFE_KM", 5000.0,
    kind="temporary_heuristic",
    unit="km before major repair",
    source=None,
    confidence="D",
    why="Same status as CART_SERVICE_LIFE_KM - an invented placeholder, "
        "somewhat higher than the cart's on the (unverified) reasoning "
        "that a wagon's heavier construction is also a sturdier one.")

WAGON = Vehicle(
    name="four-wheeled wagon", self_mass_kg=WAGON_SELF_MASS_KG,
    service_life_km=WAGON_SERVICE_LIFE_KM)

BARGE_SELF_MASS_KG = declare(
    "BARGE_SELF_MASS_KG", 3000.0,
    kind="engineering_estimate",
    unit="kg",
    source="A small wooden river or canal barge suited to animal towing "
           "(as opposed to a seagoing hull) is commonly on the order of a "
           "few tonnes empty.",
    confidence="D",
    why="Enters the SAME tractive-force balance as a cart's self-mass, "
        "against a much smaller resistance coefficient (see "
        "WATER_TRANSPORT_RESISTANCE_COEFFICIENT_AT_TOW_SPEED) - the hull's "
        "own weight is supported by buoyancy, not by the towing animal, "
        "so it only matters here through the resistance it adds, not "
        "through the animal having to lift it.")

BARGE_SERVICE_LIFE_KM = declare(
    "BARGE_SERVICE_LIFE_KM", 15000.0,
    kind="temporary_heuristic",
    unit="km before major repair",
    source=None,
    confidence="D",
    why="Same invented-placeholder status as the land vehicles' service "
        "lives, set higher on the (unverified) reasoning that a hull in "
        "water suffers less mechanical wear per kilometre than a wheel "
        "and axle under load on a rough surface - a real hull-fatigue and "
        "rot-rate model would replace this.")

BARGE = Vehicle(
    name="towed barge", self_mass_kg=BARGE_SELF_MASS_KG,
    service_life_km=BARGE_SERVICE_LIFE_KM)

# ============================================================================
# SURFACE TABLE: rolling resistance, the thing that makes a road a road
# ============================================================================
# A rolling-resistance coefficient is force needed to keep a wheel rolling,
# divided by the weight pressing it into the ground - the standard vehicle-
# dynamics way to state how much a surface costs a wheeled vehicle, reused
# here unchanged rather than reinvented. These three surfaces are the same
# wheel (wood, iron-tired) on three different Roman-era road conditions; the
# coefficient is what differs, and multiplying by weight is what makes that
# difference show up as cargo capacity in max_cargo_mass_kg below.

Surface = collections.namedtuple(
    "Surface", ["name", "rolling_resistance_coefficient"])

PAVED_ROAD_ROLLING_RESISTANCE_COEFFICIENT = declare(
    "PAVED_ROAD_ROLLING_RESISTANCE_COEFFICIENT", 0.025,
    kind="engineering_estimate",
    unit="dimensionless (resisting force / weight on the wheel)",
    source="Standard vehicle-dynamics rolling-resistance-coefficient "
           "tables give roughly 0.01-0.03 for a rigid (wood-and-iron) "
           "wheel on a hard, smooth, well-maintained surface such as a "
           "Roman-style stone-paved via; taken near the middle of that "
           "range.",
    confidence="C",
    why="Why a paved road is worth building: the same team that can pull "
        "this coefficient's worth of load stalls at three to four times "
        "less cargo on the dirt-track figure below, purely from the "
        "surface changing.")

DIRT_TRACK_ROLLING_RESISTANCE_COEFFICIENT = declare(
    "DIRT_TRACK_ROLLING_RESISTANCE_COEFFICIENT", 0.08,
    kind="engineering_estimate",
    unit="dimensionless (resisting force / weight on the wheel)",
    source="The same class of rolling-resistance tables gives roughly "
           "0.06-0.10 for a rigid wheel on a firm, dry, unpaved earth "
           "road.",
    confidence="C",
    why="The ordinary, unimproved-road case most freight in this period "
        "actually moved over - most of the network was this, not "
        "PAVED_ROAD_ROLLING_RESISTANCE_COEFFICIENT's figure.")

MUD_ROLLING_RESISTANCE_COEFFICIENT = declare(
    "MUD_ROLLING_RESISTANCE_COEFFICIENT", 0.30,
    kind="engineering_estimate",
    unit="dimensionless (resisting force / weight on the wheel)",
    source="The same tables put a wheel in wet, rutted, unimproved "
           "ground at roughly 0.2-0.4 or worse; taken near the middle, "
           "acknowledging real mud can be substantially worse (to the "
           "point of immobilising a wheeled vehicle entirely, which this "
           "single fixed coefficient cannot represent - a true soil-"
           "mechanics model of wheel sinkage is out of scope here).",
    confidence="D",
    why="The season-of-the-year fact that made much of the pre-modern "
        "road network seasonal: the same team, the same vehicle, on the "
        "same route, hauling a fraction of what it hauls at "
        "DIRT_TRACK_ROLLING_RESISTANCE_COEFFICIENT once the ground is "
        "wet.")

PAVED_ROAD = Surface(
    name="paved road", rolling_resistance_coefficient=PAVED_ROAD_ROLLING_RESISTANCE_COEFFICIENT)
DIRT_TRACK = Surface(
    name="dirt track", rolling_resistance_coefficient=DIRT_TRACK_ROLLING_RESISTANCE_COEFFICIENT)
MUD = Surface(name="mud", rolling_resistance_coefficient=MUD_ROLLING_RESISTANCE_COEFFICIENT)

WATER_TRANSPORT_RESISTANCE_COEFFICIENT_AT_TOW_SPEED = declare(
    "WATER_TRANSPORT_RESISTANCE_COEFFICIENT_AT_TOW_SPEED", 0.004,
    kind="temporary_heuristic",
    unit="dimensionless (resisting force / weight of hull plus cargo, at "
         "a walking tow speed)",
    source="Naval-architecture treatments of slow displacement hulls "
           "(the regime a towed barge or canal boat operates in, well "
           "below hull speed) commonly express hull resistance at such "
           "speeds as a 'specific resistance' of roughly a few kilograms "
           "of towing force per tonne of displacement, i.e. a resistance-"
           "to-weight ratio on the order of 0.002-0.01 - one to two "
           "orders of magnitude below any wheeled-vehicle coefficient "
           "above, because buoyancy, not a wheel pressed into the "
           "ground, is what supports the weight.",
    confidence="D",
    why="THE reason water transport is transformationally cheaper than "
        "land transport in this module, so it earns the same scrutiny as "
        "the number it is replacing an assumption with. This IS the "
        "physical mechanism (buoyancy removes weight-bearing resistance, "
        "leaving only a much smaller viscous/wave-making drag term) but "
        "the NUMBER is a labelled stand-in: real hull drag scales with "
        "the SQUARE of speed and with wetted surface area and hull shape, "
        "none of which this module models. Treating it as a single fixed "
        "coefficient of weight, exactly like a rolling-resistance "
        "coefficient, is a linearisation valid only near the one "
        "reference towing speed this module actually uses (an animal's "
        "own walking pace) - it is not a claim that water resistance "
        "scales with weight the way rolling resistance genuinely does. "
        "The mechanism that would derive this properly is a wetted-area "
        "and Reynolds/Froude-number hull-drag calculation, which does "
        "not exist in this project; marked temporary_heuristic rather "
        "than engineering_estimate for exactly that reason, even though "
        "the ORDER OF MAGNITUDE is a real, sourced naval-architecture "
        "figure.")

CALM_WATER = Surface(
    name="calm water (canal or slow river)",
    rolling_resistance_coefficient=WATER_TRANSPORT_RESISTANCE_COEFFICIENT_AT_TOW_SPEED)

# ============================================================================
# ILLUSTRATIVE GEOGRAPHY DEFAULTS
# ============================================================================
# Grade and river current are properties of a PLACE, exactly like
# sim/world/agriculture.py's Land.quality - they are legitimate inputs under
# CLAUDE.md SS3.1 ("geography... and initial conditions"), passed as plain
# function arguments everywhere in this module rather than baked in as
# defaults. The two figures below exist only so this module's own __main__
# demonstration and sim/tests/test_transport.py have a concrete, sourced
# example to run against - no function in this module reads them itself.

TYPICAL_MOUNTAIN_PASS_GRADE_FRACTION = declare(
    "TYPICAL_MOUNTAIN_PASS_GRADE_FRACTION", 0.08,
    kind="engineering_estimate",
    unit="dimensionless (rise/run)",
    source="An 8% grade is a commonly cited upper bound for a graded "
           "pre-modern mule track or pass road intended for laden animal "
           "traffic - steeper stretches existed but forced switchbacks or "
           "unloading.",
    confidence="D",
    why="An illustrative worked example for this module's __main__ block "
        "and test suite, not a value read by any production function - "
        "the actual grade of any real route is geography this module "
        "takes as a parameter, never as a constant of its own.")

TYPICAL_NAVIGABLE_RIVER_CURRENT_KM_PER_HOUR = declare(
    "TYPICAL_NAVIGABLE_RIVER_CURRENT_KM_PER_HOUR", 4.0,
    kind="engineering_estimate",
    unit="km/hour",
    source="Rivers historically used for animal-towed traffic (as opposed "
           "to rapids unsuitable for towing at all) commonly run in the "
           "rough range of 2-6 km/h of current at normal flow.",
    confidence="D",
    why="Same illustrative role as TYPICAL_MOUNTAIN_PASS_GRADE_FRACTION - "
        "a worked example for __main__ and the tests, not a value any "
        "production function reads on its own.")

# ============================================================================
# CALIBRATION TARGETS - never inputs to anything above. Read only by
# sim/tests/test_transport.py, to report the headline comparison honestly;
# nothing in this file's own functions reads them, and they must never be
# adjusted to make a computed figure agree, matching sim/world/agriculture.
# py's identical discipline for HISTORICAL_FARM_POPULATION_SHARE_LOW/HIGH.
# ============================================================================

LAND_TO_SEA_FREIGHT_COST_RATIO_LOW = declare(
    "LAND_TO_SEA_FREIGHT_COST_RATIO_LOW", 10.0,
    kind="calibration_target",
    unit="dimensionless (ratio of cost per unit distance)",
    source="The classic reading of Diocletian's Edict of Maximum Prices "
           "(301 AD) freight-price schedules, as discussed by Roman "
           "economic historians (e.g. Duncan-Jones, THE ECONOMY OF THE "
           "ROMAN EMPIRE), puts land freight at very roughly one to two "
           "orders of magnitude dearer per unit distance than sea "
           "freight across the Mediterranean.",
    confidence="C",
    why="The low end of the range this module's own land-versus-water "
        "physical-input ratios are checked against in sim/tests/test_"
        "transport.py - never tuned to, only reported against.")

LAND_TO_SEA_FREIGHT_COST_RATIO_HIGH = declare(
    "LAND_TO_SEA_FREIGHT_COST_RATIO_HIGH", 100.0,
    kind="calibration_target",
    unit="dimensionless (ratio of cost per unit distance)",
    source="Same as LAND_TO_SEA_FREIGHT_COST_RATIO_LOW.",
    confidence="C",
    why="The high end of the same range.")

HISTORICAL_MAX_ECONOMIC_LAND_HAUL_KM_LOW = declare(
    "HISTORICAL_MAX_ECONOMIC_LAND_HAUL_KM_LOW", 75.0,
    kind="calibration_target",
    unit="km",
    source="The classic economic-history claim (M.I. Finley, THE ANCIENT "
           "ECONOMY, building on the same Edict evidence) that grain "
           "roughly doubled in delivered cost for roughly every 50-100 "
           "Roman miles (about 75-150 km) hauled overland, which is the "
           "usual basis for saying grain 'could not travel far overland' "
           "at all.",
    confidence="C",
    why="The low end of the range `maximum_one_way_range_before_self_"
        "defeating_km`'s output is checked against in sim/tests/test_"
        "transport.py - never tuned to.")

HISTORICAL_MAX_ECONOMIC_LAND_HAUL_KM_HIGH = declare(
    "HISTORICAL_MAX_ECONOMIC_LAND_HAUL_KM_HIGH", 300.0,
    kind="calibration_target",
    unit="km",
    source="Generous upper reading of the same literature, allowing for "
           "higher-value bulk goods (not grain specifically) that could "
           "bear a longer overland haul before becoming uneconomic.",
    confidence="C",
    why="The high end of the same range.")


# ============================================================================
# THE PHYSICS
# ============================================================================

def maintenance_kcal_per_day(animal):
    """What `animal` needs to eat to simply exist for a day, doing no
    harnessed work at all - Kleiber's law scaled up from a resting basal
    rate to a real animal standing in a field. See FIELD_METABOLIC_RATE_
    MULTIPLIER_OVER_BMR's declaration for exactly what that scaling step
    represents and how sourced it is.
    """
    basal = (KLEIBER_BASAL_METABOLIC_COEFFICIENT_KCAL_PER_DAY
              * (animal.body_mass_kg ** KLEIBER_MASS_EXPONENT))
    return basal * FIELD_METABOLIC_RATE_MULTIPLIER_OVER_BMR


def sustained_pull_newtons(animal, team_size=1):
    """The tractive force a team of `team_size` animals can be relied on to
    generate for a full working day - not a peak or a burst figure. Linear
    in team size, which ignores real losses from animals in a team not
    pulling in perfect concert (harnessing and coordination losses that
    grow, in practice, with team size); treated here as a limitation to be
    named rather than an unlabelled fudge factor, since no sourced
    team-size efficiency curve was available to correct it with.
    """
    if team_size <= 0:
        raise ValueError("team_size must be positive: %r" % (team_size,))
    return (team_size * animal.body_mass_kg * GRAVITATIONAL_ACCELERATION_M_PER_S2
            * animal.sustained_pull_fraction_of_bodyweight)


def required_tractive_force_newtons(mass_experiencing_resistance_kg,
                                     rolling_resistance_coefficient,
                                     mass_experiencing_gradient_kg,
                                     grade_fraction=0.0):
    """The force a team has to generate to keep a load moving at a steady
    pace: a rolling-resistance term (coefficient times the weight actually
    pressed onto the wheels - vehicle plus cargo, not the animals, whose
    feet are not wheels) plus a gradient term (weight times grade,
    small-angle approximation sin(theta) ~= tan(theta) = grade, which is
    accurate to a fraction of a percent at any grade a laden vehicle could
    plausibly climb). The gradient term uses a SEPARATE mass argument
    because climbing is real work against gravity done by the vehicle,
    cargo AND the animals' own bodies together, while rolling resistance
    is a wheel-and-surface fact that the animals' own weight does not
    contribute to.
    """
    rolling_force = (mass_experiencing_resistance_kg
                      * GRAVITATIONAL_ACCELERATION_M_PER_S2
                      * rolling_resistance_coefficient)
    gradient_force = (mass_experiencing_gradient_kg
                       * GRAVITATIONAL_ACCELERATION_M_PER_S2 * grade_fraction)
    return rolling_force + gradient_force


def max_cargo_mass_kg(animal, team_size, vehicle, surface, grade_fraction=0.0):
    """How much cargo a team can haul, sustained, on `surface` at
    `grade_fraction` - the balance point where required tractive force
    (rolling resistance on vehicle-plus-cargo, plus gradient on vehicle,
    cargo AND the team's own bodies) exactly equals what the team can
    sustain all day.

    Solved directly rather than iterated. The balance is

        team_pull = GRAVITY
                  * ( (vehicle_mass + cargo_mass)
                        * (rolling_resistance + grade_fraction)
                      + team_mass * grade_fraction )

    which rearranges to give the cargo the team can actually haul:

        cargo_mass = ( team_pull / GRAVITY
                       - team_mass * grade_fraction )
                     / (rolling_resistance + grade_fraction)
                     - vehicle_mass

    Clamped at zero: a team that cannot even move its OWN empty vehicle at
    this grade and surface (a steep-enough mountain grade against a cart's
    dead weight, say) hauls no cargo at all rather than a negative amount -
    see the module's __main__ block for exactly this collapse demonstrated
    for CART on TYPICAL_MOUNTAIN_PASS_GRADE_FRACTION, which is the
    mechanism behind 'mountains are different for wheeled vehicles' this
    module is meant to produce without being told so directly.
    """
    denominator = surface.rolling_resistance_coefficient + grade_fraction
    if denominator <= 0.0:
        raise ValueError(
            "surface.rolling_resistance_coefficient + grade_fraction must "
            "be positive (a downhill grade steeper than the surface's own "
            "rolling resistance would let a vehicle roll away unpowered, "
            "which is a braking problem, not a traction one, and outside "
            "this module's scope): %r" % (denominator,))
    team_pull = sustained_pull_newtons(animal, team_size)
    team_mass_kg = team_size * animal.body_mass_kg
    vehicle_and_cargo_mass_kg = (
        (team_pull / GRAVITATIONAL_ACCELERATION_M_PER_S2
         - team_mass_kg * grade_fraction) / denominator)
    return max(0.0, vehicle_and_cargo_mass_kg - vehicle.self_mass_kg)


def max_pack_load_kg(animal, team_size=1):
    """How much cargo a string of `team_size` pack animals can carry on
    their own backs. No vehicle, no wheels, no rolling-resistance surface
    at all - a pack animal's route is limited by grade (see
    pack_climb_work_joules_per_day) and by nothing else this module
    represents, which is the physical reason pack trains, not carts, are
    the historical answer to a mountain route: there is no surface
    coefficient here for a mountain trail to make worse.
    """
    if team_size <= 0:
        raise ValueError("team_size must be positive: %r" % (team_size,))
    return team_size * animal.body_mass_kg * animal.pack_load_fraction_of_bodyweight


def distance_per_day_km(animal, ground_speed_km_per_hour=None):
    """How far `animal` covers in one working day, at its own walking pace
    unless a different GROUND speed is supplied - see barge_freight_
    physical_inputs for why a towed boat's ground speed differs from the
    towing animal's own walking pace (river current).
    """
    speed = (animal.walking_speed_km_per_hour if ground_speed_km_per_hour is None
              else ground_speed_km_per_hour)
    return speed * animal.working_hours_per_day


FreightPhysicalInputs = collections.namedtuple(
    "FreightPhysicalInputs",
    ["mode", "cargo_tonnes", "distance_per_day_km", "tonne_km_per_day",
     "feed_kg_per_day", "feed_kg_per_tonne_km", "driver_hours_per_tonne_km",
     "vehicle_wear_fraction_per_tonne_km"])


def _feed_kg_from_work_and_maintenance(maintenance_kcal, work_joules):
    work_kcal_equivalent = work_joules / JOULES_PER_KCAL
    feed_kcal_for_work = work_kcal_equivalent / MUSCULAR_EFFICIENCY_OF_DRAUGHT_WORK
    return (maintenance_kcal + feed_kcal_for_work) / FEED_ENERGY_DENSITY_KCAL_PER_KG


def draught_freight_physical_inputs(animal, team_size, vehicle, surface,
                                     grade_fraction=0.0, load_fraction=1.0):
    """Physical inputs per tonne-km for a wheeled vehicle (CART or WAGON)
    hauled by `team_size` of `animal` over `surface` at `grade_fraction`,
    loaded to `load_fraction` of what the team can sustain (see
    max_cargo_mass_kg).

    Returns a FreightPhysicalInputs: kilograms of feed, hours of a single
    driver's attention, and the fraction of the vehicle's service life
    consumed, ALL per tonne-km actually delivered - never a money figure,
    see the module docstring's NOT A MONEY FIGURE section for why.
    """
    if not (0.0 < load_fraction <= 1.0):
        raise ValueError("load_fraction must be in (0, 1]: %r" % (load_fraction,))
    max_cargo_kg = max_cargo_mass_kg(animal, team_size, vehicle, surface, grade_fraction)
    cargo_kg = max_cargo_kg * load_fraction
    if cargo_kg <= 0.0:
        raise ValueError(
            "this team cannot haul any cargo at all on %s at grade %.3f - "
            "even its own vehicle exceeds what it can pull" % (surface.name, grade_fraction))

    team_mass_kg = team_size * animal.body_mass_kg
    vehicle_and_cargo_mass_kg = vehicle.self_mass_kg + cargo_kg
    tractive_force_n = required_tractive_force_newtons(
        mass_experiencing_resistance_kg=vehicle_and_cargo_mass_kg,
        rolling_resistance_coefficient=surface.rolling_resistance_coefficient,
        mass_experiencing_gradient_kg=vehicle_and_cargo_mass_kg + team_mass_kg,
        grade_fraction=grade_fraction)

    distance_km = distance_per_day_km(animal)
    work_joules = tractive_force_n * distance_km * 1000.0
    feed_kg = _feed_kg_from_work_and_maintenance(
        team_size * maintenance_kcal_per_day(animal), work_joules)

    cargo_tonnes = cargo_kg / 1000.0
    tonne_km_per_day = cargo_tonnes * distance_km
    driver_hours_per_day = animal.working_hours_per_day  # one driver; see module docstring

    return FreightPhysicalInputs(
        mode="%s pulled by %d %s(s) on %s" % (vehicle.name, team_size, animal.name, surface.name),
        cargo_tonnes=cargo_tonnes,
        distance_per_day_km=distance_km,
        tonne_km_per_day=tonne_km_per_day,
        feed_kg_per_day=feed_kg,
        feed_kg_per_tonne_km=feed_kg / tonne_km_per_day,
        driver_hours_per_tonne_km=driver_hours_per_day / tonne_km_per_day,
        vehicle_wear_fraction_per_tonne_km=(
            1.0 / (vehicle.service_life_km * cargo_tonnes)))


def pack_climb_work_joules_per_day(animal, team_size, cargo_kg, grade_fraction,
                                    distance_km):
    """Extra mechanical work `team_size` pack animals do climbing, carrying
    `cargo_kg` total, over `distance_km` at `grade_fraction`. Genuine
    physics (lifting a mass against gravity costs mass * g * height, exact,
    not an approximation the way rolling resistance's coefficient is), and
    the reason this module charges a pack train MORE feed on a mountain
    route without needing a surface coefficient to do it - see
    pack_freight_physical_inputs.

    A negative `grade_fraction` (descending) returns zero rather than a
    negative work figure: animal muscle is not a generator, and going
    downhill does not refund calories the way a mechanical brake dissipates
    them - it is a real limitation of this module that a round trip up and
    back down a pass therefore costs the FULL climb twice (once each way)
    rather than netting to zero, which is physically correct for a living
    animal walking down a slope under its own control, not a modelling
    shortcut.
    """
    if grade_fraction <= 0.0:
        return 0.0
    total_mass_kg = team_size * animal.body_mass_kg + cargo_kg
    vertical_rise_m = distance_km * 1000.0 * grade_fraction
    return total_mass_kg * GRAVITATIONAL_ACCELERATION_M_PER_S2 * vertical_rise_m


def pack_freight_physical_inputs(animal, team_size, vehicle=PACK_SADDLE,
                                  grade_fraction=0.0, load_fraction=1.0):
    """Physical inputs per tonne-km for a string of `team_size` pack
    animals, loaded to `load_fraction` of max_pack_load_kg, over a route at
    `grade_fraction`. No `surface` parameter at all - see max_pack_load_kg
    for why: a pack animal's feet are not a wheel, so this module has no
    rolling-resistance term for them to be charged. Only the gradient's
    real lifting work enters the feed calculation.
    """
    if not (0.0 < load_fraction <= 1.0):
        raise ValueError("load_fraction must be in (0, 1]: %r" % (load_fraction,))
    max_load_kg = max_pack_load_kg(animal, team_size) - team_size * vehicle.self_mass_kg
    max_load_kg = max(0.0, max_load_kg)
    cargo_kg = max_load_kg * load_fraction
    if cargo_kg <= 0.0:
        raise ValueError(
            "this string of pack animals cannot carry any cargo at all - "
            "the saddle rigging alone exceeds what they can bear")

    distance_km = distance_per_day_km(animal)
    climb_work_joules = pack_climb_work_joules_per_day(
        animal, team_size, cargo_kg, grade_fraction, distance_km)
    feed_kg = _feed_kg_from_work_and_maintenance(
        team_size * maintenance_kcal_per_day(animal), climb_work_joules)

    cargo_tonnes = cargo_kg / 1000.0
    tonne_km_per_day = cargo_tonnes * distance_km
    driver_hours_per_day = animal.working_hours_per_day  # one handler; see module docstring

    return FreightPhysicalInputs(
        mode="%d pack %s(s) at grade %.3f" % (team_size, animal.name, grade_fraction),
        cargo_tonnes=cargo_tonnes,
        distance_per_day_km=distance_km,
        tonne_km_per_day=tonne_km_per_day,
        feed_kg_per_day=feed_kg,
        feed_kg_per_tonne_km=feed_kg / tonne_km_per_day,
        driver_hours_per_tonne_km=driver_hours_per_day / tonne_km_per_day,
        vehicle_wear_fraction_per_tonne_km=(
            team_size / (vehicle.service_life_km * cargo_tonnes)))


def barge_freight_physical_inputs(animal, team_size, vehicle=BARGE,
                                   surface=CALM_WATER, current_km_per_hour=0.0,
                                   load_fraction=1.0):
    """Physical inputs per tonne-km for a barge towed by `team_size` of
    `animal` walking a towpath at their own walking pace, on water offering
    `surface`'s resistance coefficient (CALM_WATER by default - see
    WATER_TRANSPORT_RESISTANCE_COEFFICIENT_AT_TOW_SPEED), with a current of
    `current_km_per_hour` (positive = flowing the direction of travel,
    i.e. downstream; negative = against the direction of travel, i.e.
    upstream).

    THE MECHANISM FOR WHY UPSTREAM AND DOWNSTREAM DIFFER, without inventing
    a separate number for each: the animal's own muscular work depends on
    how far the HULL moves THROUGH THE WATER - the tow rope's tension is
    set by drag on the hull relative to the water it sits in, not relative
    to the bank - and the hull moves through the water at essentially the
    animal's own walking pace regardless of current (that IS what pulling a
    taut rope at a fixed pace means). Current does not change that work at
    all. What it changes is how much GROUND the boat covers for that same
    work: downstream, the current adds free ground speed on top of the tow
    speed; upstream, it subtracts. So tonne-km delivered per unit of feed
    is higher downstream and lower upstream for IDENTICAL animal effort -
    exactly the asymmetry real towed river traffic shows, derived rather
    than stated. If the current exceeds the tow speed upstream, ground
    speed would be zero or negative and this raises ValueError: towing
    against a current faster than a walking pace is not something more
    feed can fix, which is physically correct (real upstream haulage
    against a fast current needed relays, poling or portage, not more
    horses on the same rope).
    """
    if not (0.0 < load_fraction <= 1.0):
        raise ValueError("load_fraction must be in (0, 1]: %r" % (load_fraction,))
    max_cargo_kg = max_cargo_mass_kg(animal, team_size, vehicle, surface, grade_fraction=0.0)
    cargo_kg = max_cargo_kg * load_fraction
    if cargo_kg <= 0.0:
        raise ValueError(
            "this team cannot tow any cargo at all on %s - even the barge's "
            "own weight exceeds what it can tow" % (surface.name,))

    hull_speed_through_water_km_per_hour = animal.walking_speed_km_per_hour
    ground_speed_km_per_hour = hull_speed_through_water_km_per_hour + current_km_per_hour
    if ground_speed_km_per_hour <= 0.0:
        raise ValueError(
            "current (%.2f km/h) meets or exceeds the tow speed (%.2f km/h): "
            "towing upstream against this current cannot make headway at "
            "all by this mechanism - it needs relays, poling or portage, "
            "none of which this module models" % (
                -current_km_per_hour, hull_speed_through_water_km_per_hour))

    vehicle_and_cargo_mass_kg = vehicle.self_mass_kg + cargo_kg
    tractive_force_n = required_tractive_force_newtons(
        mass_experiencing_resistance_kg=vehicle_and_cargo_mass_kg,
        rolling_resistance_coefficient=surface.rolling_resistance_coefficient,
        mass_experiencing_gradient_kg=0.0, grade_fraction=0.0)

    water_distance_km = distance_per_day_km(animal, hull_speed_through_water_km_per_hour)
    work_joules = tractive_force_n * water_distance_km * 1000.0
    feed_kg = _feed_kg_from_work_and_maintenance(
        team_size * maintenance_kcal_per_day(animal), work_joules)

    ground_distance_km = distance_per_day_km(animal, ground_speed_km_per_hour)
    cargo_tonnes = cargo_kg / 1000.0
    tonne_km_per_day = cargo_tonnes * ground_distance_km
    driver_hours_per_day = animal.working_hours_per_day

    return FreightPhysicalInputs(
        mode="%s towed by %d %s(s) on %s (current %.1f km/h)" % (
            vehicle.name, team_size, animal.name, surface.name, current_km_per_hour),
        cargo_tonnes=cargo_tonnes,
        distance_per_day_km=ground_distance_km,
        tonne_km_per_day=tonne_km_per_day,
        feed_kg_per_day=feed_kg,
        feed_kg_per_tonne_km=feed_kg / tonne_km_per_day,
        driver_hours_per_tonne_km=driver_hours_per_day / tonne_km_per_day,
        vehicle_wear_fraction_per_tonne_km=(
            1.0 / (vehicle.service_life_km * cargo_tonnes)))


def maximum_one_way_range_before_self_defeating_km(
        animal, team_size, vehicle, surface, grade_fraction=0.0):
    """The one-way distance at which a fully-laden team, carrying its OWN
    feed for the whole trip instead of finding fodder along the way, has
    exactly zero cargo capacity left over - the physical origin of pre-
    industrial land transport's economic range limit, derived rather than
    stated (see the module docstring's THE ANIMAL'S OWN FEED AS A LOAD).

    THE ALGEBRA. At the team's maximum sustained load, `max_cargo_mass_kg`
    gives the total mass (vehicle + cargo) the team can pull; call the
    cargo-and-feed allowance A = max_cargo_mass_kg(...) (the vehicle's own
    weight is already subtracted). If the team eats `feed_kg_per_day` while
    hauling that same maximum load - itself computed from the tractive
    force needed to haul exactly A - then over D km at `distance_per_day_
    km(animal)` km/day, the trip takes D / distance_per_day days and
    consumes `feed_kg_per_day * days` kg of feed, which must be carried
    from departure since no fodder is assumed available en route. Cargo
    actually delivered is A minus that feed weight; it reaches zero at

        D* = A * distance_per_day_km / feed_kg_per_day

    WHAT THIS DELIBERATELY DOES NOT MODEL, so the honest limits are named
    rather than hidden in a clean-looking formula: (1) it is ONE-WAY only -
    a real round trip either forages for feed on the return leg or has to
    carry twice as much, which would halve this figure; (2) it holds the
    tractive force (and so the feed rate) fixed at what hauling the FULL
    load A requires, when in reality the load - and so the force needed
    and the feed burned - falls every day as feed is eaten, which would
    let the team travel slightly FARTHER than D* before running out; the
    two simplifications point in opposite directions and neither is sized
    against the other, so D* should be read as an order-of-magnitude
    figure, not a precise one. See sim/tests/test_transport.py for the
    comparison against the historical range this is checked against, never
    tuned to.
    """
    max_load_kg = max_cargo_mass_kg(animal, team_size, vehicle, surface, grade_fraction)
    if max_load_kg <= 0.0:
        return 0.0

    team_mass_kg = team_size * animal.body_mass_kg
    vehicle_and_full_load_mass_kg = vehicle.self_mass_kg + max_load_kg
    tractive_force_n = required_tractive_force_newtons(
        mass_experiencing_resistance_kg=vehicle_and_full_load_mass_kg,
        rolling_resistance_coefficient=surface.rolling_resistance_coefficient,
        mass_experiencing_gradient_kg=vehicle_and_full_load_mass_kg + team_mass_kg,
        grade_fraction=grade_fraction)

    distance_km = distance_per_day_km(animal)
    work_joules = tractive_force_n * distance_km * 1000.0
    feed_kg_per_day = _feed_kg_from_work_and_maintenance(
        team_size * maintenance_kcal_per_day(animal), work_joules)

    return max_load_kg * distance_km / feed_kg_per_day


if __name__ == "__main__":
    # A human-readable readout, the same kind of thing sim/world/
    # agriculture.py's own __main__ block prints - see the module docstring
    # for the reading of what these numbers mean and where they disagree
    # with the calibration range.
    ox_cart_paved = draught_freight_physical_inputs(OX, 2, CART, PAVED_ROAD)
    ox_cart_dirt = draught_freight_physical_inputs(OX, 2, CART, DIRT_TRACK)
    ox_cart_mud = draught_freight_physical_inputs(OX, 2, CART, MUD)
    ox_wagon_dirt = draught_freight_physical_inputs(OX, 4, WAGON, DIRT_TRACK)
    mule_pack = pack_freight_physical_inputs(MULE, 1)
    mule_pack_mountain = pack_freight_physical_inputs(
        MULE, 1, grade_fraction=TYPICAL_MOUNTAIN_PASS_GRADE_FRACTION)
    horse_barge_calm = barge_freight_physical_inputs(HORSE, 1, current_km_per_hour=0.0)
    horse_barge_downstream = barge_freight_physical_inputs(
        HORSE, 1, current_km_per_hour=TYPICAL_NAVIGABLE_RIVER_CURRENT_KM_PER_HOUR)
    horse_barge_upstream = barge_freight_physical_inputs(
        HORSE, 1, current_km_per_hour=-TYPICAL_NAVIGABLE_RIVER_CURRENT_KM_PER_HOUR)

    def _line(inputs):
        print("  %-58s cargo %5.2f t  %6.1f t-km/day  feed %6.3f kg/t-km  "
              "driver %6.3f h/t-km  wear %.2e /t-km"
              % (inputs.mode, inputs.cargo_tonnes, inputs.tonne_km_per_day,
                 inputs.feed_kg_per_tonne_km, inputs.driver_hours_per_tonne_km,
                 inputs.vehicle_wear_fraction_per_tonne_km))

    print("LAND, WHEELED (2 oxen, cart, by surface):")
    _line(ox_cart_paved)
    _line(ox_cart_dirt)
    _line(ox_cart_mud)
    print("LAND, WHEELED (4 oxen, wagon, dirt track):")
    _line(ox_wagon_dirt)
    print("LAND, PACK (1 mule, no vehicle, no road):")
    _line(mule_pack)
    _line(mule_pack_mountain)
    print("WATER (1 horse towing a barge):")
    _line(horse_barge_calm)
    _line(horse_barge_downstream)
    _line(horse_barge_upstream)

    print()
    cart_dirt_cap = max_cargo_mass_kg(OX, 2, CART, DIRT_TRACK,
                                       TYPICAL_MOUNTAIN_PASS_GRADE_FRACTION)
    print("2-ox cart on dirt track at an %.0f%% mountain-pass grade can haul: "
          "%.1f kg - the grade nearly defeats the team on its own, before "
          "any cargo (compare to %.0f kg with no grade, and to the mule "
          "pack's unaffected 70 kg above)"
          % (100.0 * TYPICAL_MOUNTAIN_PASS_GRADE_FRACTION, cart_dirt_cap,
             max_cargo_mass_kg(OX, 2, CART, DIRT_TRACK, 0.0)))

    print()
    print("feed_kg_per_tonne_km ratio, dirt cart : calm-water barge = %.1f"
          % (ox_cart_dirt.feed_kg_per_tonne_km / horse_barge_calm.feed_kg_per_tonne_km))
    print("driver_hours_per_tonne_km ratio, dirt cart : calm-water barge = %.1f"
          % (ox_cart_dirt.driver_hours_per_tonne_km
             / horse_barge_calm.driver_hours_per_tonne_km))
    print("calibration target (Diocletian's Edict, land:sea): %.0f-%.0fx"
          % (LAND_TO_SEA_FREIGHT_COST_RATIO_LOW, LAND_TO_SEA_FREIGHT_COST_RATIO_HIGH))

    print()
    range_paved = maximum_one_way_range_before_self_defeating_km(OX, 2, CART, PAVED_ROAD)
    range_dirt = maximum_one_way_range_before_self_defeating_km(OX, 2, CART, DIRT_TRACK)
    range_mud = maximum_one_way_range_before_self_defeating_km(OX, 2, CART, MUD)
    print("one-way self-defeating range, 2-ox cart, no fodder en route:")
    print("  paved road: %8.0f km" % range_paved)
    print("  dirt track: %8.0f km" % range_dirt)
    print("  mud:        %8.0f km" % range_mud)
    print("calibration target (historical max economic land haul): %.0f-%.0f km"
          % (HISTORICAL_MAX_ECONOMIC_LAND_HAUL_KM_LOW,
             HISTORICAL_MAX_ECONOMIC_LAND_HAUL_KM_HIGH))
