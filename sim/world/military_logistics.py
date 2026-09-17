"""What an army physically eats, drinks, wears out and shoots - and how far
from a supply base it can therefore operate.

THE POINT. The project's stakeholder scenario is a founder handing 100 AD
Rome a modern rifle. CLAUDE.md SS3.3 says an intervention like that has to
propagate through normal rules rather than get a bespoke "modern weapons win"
branch: a rifle is an object with an ammunition and maintenance requirement,
exactly like a sword and shield are, and the war it changes is decided by
what that requirement does to food, fodder, iron and labour - things the rest
of this simulation already knows how to produce (sim/world/agriculture.py's
grain, a metals-production chain this module does not touch but assumes
exists). Nothing here is fought or won; this module only answers what an
army of a given size, marching at a given rate, armed with a given weapon,
costs to keep in the field, and how far from its supply base that cost lets
it go before the supply train is eating more than it delivers. That distance
- not army size, not weapon lethality - is the number pre-modern and
early-modern warfare was actually bounded by, which is why campaigns hugged
rivers and coasts and sieges starved besiegers as often as the besieged.

STANDALONE ON PURPOSE, LIKE ITS SIBLINGS. Nothing here imports from
sim/engine/, sim/world/agriculture.py or sim/world/transport.py, and nothing
in those modules imports this. See sim/world/__init__.py for the shared
reason: other agents are editing sim/engine/, sim/world/agriculture.py,
sim/world/transport.py, sim/treetool.py and sim/constants.py concurrently
with this file's construction, and a module with no dependency on those
paths cannot be broken by their edits or break their tests, whichever lands
first. Where this module needs a number agriculture.py already owns (the
energy content of grain, a human's baseline caloric need), it redeclares
that number under its own name rather than importing it - the same choice
agriculture.py made relative to demography.py, and for the identical reason:
see WHEAT_ENERGY_KCAL_PER_KG's declaration there and GRAIN_ENERGY_KCAL_PER_KG
here. Where this module needs a number that belongs to agriculture.py's own
domain and varies by place and technique - the agricultural surplus per
square kilometre a foraging army could live off - it is a PARAMETER passed
into this module's functions, never a constant declared here: see
sustainable_foraging_army_size()'s own docstring.

ONE ANIMAL, ONE ENGAGEMENT. Like agriculture.py's "one crop", this module
picks one representative pack/draught animal (a mule-sized equid, the
standard baggage-train animal of both the Roman impedimenta and early-modern
armies) rather than modelling oxen, camels and horse-drawn wagons
separately, and one representative unit of combat - "an engagement" - rather
than a modelled campaign calendar of marches, sieges and battles at
different intensities. Both are real simplifications; see WHERE THIS MODEL
IS WRONG below for what they cost.

SHAPE.
    Ration          a soldier's daily energy need at campaign exertion
                     (marching under load, not sedentary), turned into
                     kilograms of grain the same way agriculture.py turns a
                     population's energy need into kilograms of wheat, and
                     into litres of water using a documented desert-heat
                     multiplier on a temperate-climate baseline.
    Baggage train    pack animals carry their own fodder as well as whatever
                     cargo they deliver, so the further a supply column has
                     to travel from base, the more of its own load it eats
                     getting there and back. That is a break-even structure,
                     identical in shape to a freight run's - see
                     pack_animal_max_one_way_days() for the closed form and
                     why it falls out of the animal's mass, appetite and
                     load capacity rather than being asserted.
    Foraging         the alternative to carrying food: an army marching
                     through a territory can eat the standing surplus of the
                     strip of land it and its foragers can reach each day,
                     which makes its sustainable size a function of that
                     land's surplus per square kilometre and how fast the
                     army covers new ground - see
                     sustainable_foraging_army_size().
    Equipment        kilograms of worked iron a soldier's arms and armour
                     represent, and the fraction of that stock a campaign
                     season consumes through breakage, corrosion and combat
                     loss - a standing claim on metal production, not a
                     one-off purchase.
    Firearm          the same ammunition-and-maintenance shape as any other
                     equipment claim, applied to a weapon that consumes mass
                     per shot instead of durability per year. Two examples
                     are declared - a flintlock musket and a modern service
                     rifle - specifically so the intervention scenario this
                     module exists for can be run through the SAME functions
                     with different numbers, per CLAUDE.md SS3.3, rather
                     than "modern weapon" getting its own code path.

WHAT THIS MODEL DOES NOT DO (see also NON-GOALS in the task this module
answers to): no combat resolution, no casualties, no morale, no recruitment,
no pay, no money anywhere in this file. It does not decide who wins a war;
it decides what fighting one costs in food, fodder, iron and ammunition, and
how far from a supply base that cost can be sustained.

WHERE THIS MODEL IS WRONG, stated plainly rather than left for someone else
to discover:

  (a) ONE SUPPLY LEG, NOT A RELAY CHAIN. pack_animal_max_one_way_days()
      models a single column travelling directly from a fixed base to the
      deployed force and back. Real pre-modern logistics extended reach
      well past this by staging supplies through a chain of forward
      depots, each resupplied in turn - the single-leg model here is the
      pessimistic, no-depots baseline, and is why its "zero-net" range
      comes out ABOVE the historical few-days figure at all only because
      that figure already reflects the friction (roads, terrain, security)
      a flat mass/appetite ratio cannot see, not because depots make things
      worse. See CALIBRATION TARGETS below for the actual comparison.
  (b) NO TERRAIN. One march rate, one fodder appetite, everywhere. Roads,
      mountains, mud season, and the difference between grassland and
      desert for foraging are all absent; ARMY_MARCH_RATE_KM_PER_DAY and
      PACK_ANIMAL_DAILY_FORAGE_FRACTION_OF_BODY_MASS are averages standing
      in for a real geography this project already has (data/ has terrain
      and civilisation geography) but this module does not read.
  (c) FORAGING IGNORES DEPLETION AND RESISTANCE. sustainable_foraging_army_
      size() treats the strip of land an army crosses as a fixed surplus
      available for the taking. Real foraging strips a route bare for the
      rest of a season (no army can march the same road twice on forage
      alone), meets local resistance and hoarding, and this module has no
      state that would let a second army's passage see a depleted number -
      it is a snapshot capacity, not a renewable one.
  (d) ONE ANIMAL, ONE ENGAGEMENT. Named above; costs real precision for
      wagon-based trains (higher capacity, lower speed, road-bound) and for
      campaigns with many small skirmishes rather than one round of combat.
  (e) EQUIPMENT REPLACEMENT RATE IS INVENTED.
      ANNUAL_EQUIPMENT_REPLACEMENT_FRACTION has no real source - see its own
      declaration - because the mechanism that would derive it (a fatigue
      and corrosion model for worked iron under field conditions, plus a
      combat-loss rate this project has no way to compute without modelling
      combat) does not exist. It is marked temporary_heuristic for exactly
      that reason.
  (f) THE MARCHING ENERGY MULTIPLIER IS A TABLE LOOKUP, NOT A BIOMECHANICAL
      MODEL. MARCHING_PHYSICAL_ACTIVITY_LEVEL_MULTIPLIER takes a single
      point from a broad FAO/WHO/UNU activity-level band rather than
      computing energy cost from body mass, load mass, terrain and pace
      (the Pandolf/Givoni-Goldman load-carriage equations exist for this
      and are not used here) - see ration_kg_grain_per_day()'s own
      docstring for what this produces and how it compares to the
      documented Roman ration.
"""
import collections

from sim.constants import declare

# ============================================================================
# HUMAN RATION
# ============================================================================
# A soldier on campaign is not a sedentary person: marching under load for
# hours a day costs substantially more energy than the subsistence figure
# agriculture.py and demography.py both use for an ordinary civilian. The
# baseline below is redeclared, deliberately, rather than imported from
# either module - see the module docstring's STANDALONE section.

SEDENTARY_ENERGY_REQUIREMENT_KCAL_PER_DAY = declare(
    "SEDENTARY_ENERGY_REQUIREMENT_KCAL_PER_DAY", 2200.0,
    kind="biological_parameter",
    unit="kcal/adult/day",
    source="FAO minimum dietary energy requirement, adult average - the "
           "same figure sim/world/agriculture.py's HUMAN_ENERGY_REQUIREMENT_"
           "KCAL_PER_ADULT_DAY and sim/world/demography.py's SUBSISTENCE_"
           "CALORIES_PER_ADULT_EQUIVALENT_DAY both use. Declared again here "
           "under its own name rather than imported, for the same reason "
           "agriculture.py gives for not importing demography.py's copy: "
           "this module is built and tested standalone.",
    confidence="B",
    why="The baseline this module scales up by the marching activity "
        "multiplier below - the campaign ration is this number times "
        "exertion, not a figure invented separately from ordinary human "
        "energy need.")

MARCHING_PHYSICAL_ACTIVITY_LEVEL_MULTIPLIER = declare(
    "MARCHING_PHYSICAL_ACTIVITY_LEVEL_MULTIPLIER", 2.0,
    kind="engineering_estimate",
    unit="dimensionless (ratio to sedentary energy requirement)",
    source="FAO/WHO/UNU (2004) \"Human Energy Requirements\" physical "
           "activity level (PAL) tables place sustained heavy physical "
           "work - marching for hours under a load being a standard "
           "example given in that literature - in the \"vigorous\" band, "
           "roughly PAL 2.00-2.40 relative to a sedentary baseline. Taken "
           "at the low end of that band on the reasoning that a campaign "
           "day is not spent marching for its entire length (making and "
           "breaking camp, standing watch and waiting are lower-intensity "
           "time mixed into the same day).",
    confidence="C",
    why="Converts a sedentary energy requirement into a marching one - see "
        "ration_kg_grain_per_day()'s own docstring for the comparison this "
        "produces against the documented Roman grain ration, and for why a "
        "single PAL multiplier is a coarse stand-in for the Pandolf/Givoni-"
        "Goldman load-carriage equations that would derive this from body "
        "mass, load mass, terrain and pace instead of a table lookup.")

GRAIN_ENERGY_KCAL_PER_KG = declare(
    "GRAIN_ENERGY_KCAL_PER_KG", 3400.0,
    kind="biological_parameter",
    unit="kcal/kg",
    source="Standard food-composition figures for whole wheat grain, "
           "matching sim/world/agriculture.py's WHEAT_ENERGY_KCAL_PER_KG "
           "exactly - declared again here under its own name rather than "
           "imported, for the reason given in this module's docstring.",
    confidence="A",
    why="Converts a soldier's daily energy requirement into kilograms of "
        "grain, which is the unit the baggage-train and foraging "
        "calculations below both need.")

WATER_REQUIREMENT_TEMPERATE_MARCH_LITERS_PER_DAY = declare(
    "WATER_REQUIREMENT_TEMPERATE_MARCH_LITERS_PER_DAY", 3.5,
    kind="biological_parameter",
    unit="litres/person/day",
    source="Military and exercise physiology literature on sustained heavy "
           "exertion in a temperate climate commonly gives a water "
           "requirement in the 3-5 litre/day range for marching under "
           "load, well above the roughly 2-3 litre/day sedentary figure; "
           "taken near the low end of that range.",
    confidence="C",
    why="The temperate-climate baseline the desert multiplier below scales "
        "up - water, not food, is what the module docstring's THE POINT "
        "names as the actual limiting resource on a desert march, so this "
        "number and the next one are what let that claim be checked rather "
        "than asserted.")

DESERT_HEAT_WATER_MULTIPLIER = declare(
    "DESERT_HEAT_WATER_MULTIPLIER", 2.5,
    kind="engineering_estimate",
    unit="dimensionless (ratio to the temperate-march water requirement)",
    source="Military field guidance on water needs under heavy exertion in "
           "hot, arid conditions commonly cites requirements reaching "
           "roughly 8-12 litres/day in extreme desert heat, some 2-3 times "
           "a temperate-climate marching requirement; taken at the low end "
           "of that ratio.",
    confidence="C",
    why="Turns the temperate baseline into the desert-march figure the "
        "module docstring's THE POINT paragraph calls out: water's much "
        "higher volume-to-calorie ratio than grain is exactly what makes "
        "it, not food, the thing that sets how far a desert column can "
        "range from a well or river.")


def soldier_campaign_energy_requirement_kcal_per_day():
    """A soldier's energy need at campaign exertion: the sedentary baseline
    scaled by the marching activity-level multiplier. Not a `declare()` of
    its own - arithmetic on two already-declared numbers, the same
    convention agriculture.py uses for GROSS_YIELD_AT_REFERENCE_LABOUR_KG_
    PER_HA."""
    return (SEDENTARY_ENERGY_REQUIREMENT_KCAL_PER_DAY
            * MARCHING_PHYSICAL_ACTIVITY_LEVEL_MULTIPLIER)


def ration_kg_grain_per_day():
    """A soldier's daily food need, in kilograms of grain, at campaign
    exertion.

    ON THE COMPARISON TO THE DOCUMENTED ROMAN RATION (see CALIBRATION
    TARGETS below for the sourced range, and sim/tests/test_military_
    logistics.py's calibration tests for the exact numbers this produces).
    This function comes out ABOVE the documented ~0.75-0.95 kg/day Roman
    grain ration, by roughly a third to two-thirds depending on exactly
    where MARCHING_PHYSICAL_ACTIVITY_LEVEL_MULTIPLIER sits in its own
    declared range. Nothing here is tuned to close that gap - the two most
    likely reasons for it, in the order this module would bet on:

      (a) A REAL DIET WAS NOT 100% GRAIN CALORIES. The same single-staple
          simplification agriculture.py names for civilian diets applies
          here more sharply, because a Roman ration in the field is
          independently documented to include wine, bacon or lard, and
          sour wine or vinegar (posca) alongside the grain allowance -
          calories this function has nowhere to put, so it prices the
          WHOLE requirement in grain and overstates the grain component
          specifically.
      (b) THE PAL MULTIPLIER TREATS EVERY CAMPAIGN DAY AS A MARCHING DAY.
          A real campaign mixes marching days with garrison, siege and rest
          days at markedly lower exertion; averaged over a real campaign
          season the true multiplier is likely below the "vigorous" figure
          used here, which is itself the low end of its own cited band -
          see MARCHING_PHYSICAL_ACTIVITY_LEVEL_MULTIPLIER's declaration.

    Either mechanism would only be worth building once this module has a
    reason to distinguish grain-days from non-grain calories or marching
    days from static ones - both real, both future work.
    """
    return soldier_campaign_energy_requirement_kcal_per_day() / GRAIN_ENERGY_KCAL_PER_KG


def water_requirement_liters_per_day(desert=False):
    """A soldier's daily water need. `desert=True` applies the desert-heat
    multiplier; the temperate figure otherwise. See the module docstring's
    THE POINT paragraph for why this function, not the grain ration, is the
    one that actually binds a desert campaign's range from water."""
    liters = WATER_REQUIREMENT_TEMPERATE_MARCH_LITERS_PER_DAY
    if desert:
        liters *= DESERT_HEAT_WATER_MULTIPLIER
    return liters


# ============================================================================
# PACK AND DRAUGHT ANIMALS: THE BAGGAGE TRAIN'S OWN BREAK-EVEN RANGE
# ============================================================================
# The mechanism this section exists for: a pack animal that carries its own
# fodder for a round trip eats into the very load it is meant to deliver,
# and the further the round trip, the more of the load its own appetite
# consumes. At some distance the animal's fodder need for the round trip
# equals its entire carrying capacity - beyond that point it cannot even
# make the round trip carrying nothing else, let alone deliver cargo. This
# is the SAME break-even shape as a freight run's (a wagon whose fuel or
# feed cost exceeds the value of what it hauls stops paying for itself past
# some distance); see pack_animal_max_one_way_days() for the closed form.
#
# WHAT THIS MODELS. A fixed supply base and a force operating some distance
# away, resupplied by a column of pack animals that shuttles between the
# two - not a marching column that carries its whole train with it
# continuously (that is a related, harder problem: see WHERE THIS MODEL IS
# WRONG (a) above). "An army's maximum range from its supply base" in the
# task this module answers to is this shuttle distance.

PACK_ANIMAL_LIVE_MASS_KG = declare(
    "PACK_ANIMAL_LIVE_MASS_KG", 350.0,
    kind="biological_parameter",
    unit="kg",
    source="Typical live mass of a mule or a draught/pack horse of "
           "pre-modern and early-modern breeding (smaller than modern "
           "breeds, which run considerably heavier) - the standard "
           "baggage-train animal of both the Roman impedimenta and later "
           "early-modern armies.",
    confidence="C",
    why="The body the fodder appetite and load capacity below are both "
        "scaled from - see the module docstring's ONE ANIMAL simplification "
        "for why a single representative animal stands in for the mixed "
        "mules, horses and oxen a real baggage train used.")

PACK_ANIMAL_DAILY_FORAGE_FRACTION_OF_BODY_MASS = declare(
    "PACK_ANIMAL_DAILY_FORAGE_FRACTION_OF_BODY_MASS", 0.02,
    kind="biological_parameter",
    unit="fraction of live body mass/day (dry matter)",
    source="Equine nutrition literature gives dry-matter intake for a "
           "working (not merely resting) equid at roughly 2% of body mass "
           "per day, above the 1.5% or so maintenance figure for an "
           "animal at rest, reflecting the higher energy cost of daily "
           "work under load.",
    confidence="B",
    why="Sets the animal's own daily fodder claim - the mass this module's "
        "whole baggage-train argument turns on, since it is exactly what a "
        "long round trip has to carry for the animal itself rather than "
        "for the army.")

PACK_ANIMAL_LOAD_CAPACITY_FRACTION_OF_BODY_MASS = declare(
    "PACK_ANIMAL_LOAD_CAPACITY_FRACTION_OF_BODY_MASS", 0.30,
    kind="engineering_estimate",
    unit="fraction of live body mass (dimensionless)",
    source="Widely cited pack-animal load guidance puts a SUSTAINED daily "
           "marching load (as opposed to a short-haul maximum) at roughly "
           "a quarter to a third of the animal's own body mass, to avoid "
           "injury over a multi-day or multi-week march.",
    confidence="C",
    why="Sets the animal's total carrying capacity - the other half of the "
        "ratio (against the daily fodder claim above) that "
        "pack_animal_max_one_way_days() turns into a maximum range.")

ARMY_MARCH_RATE_KM_PER_DAY = declare(
    "ARMY_MARCH_RATE_KM_PER_DAY", 24.0,
    kind="engineering_estimate",
    unit="km/day",
    source="Vegetius's De Re Militari gives the Roman legion's \"ordinary "
           "march\" (iter iustum) as 20 Roman miles in five summer hours, "
           "about 29.6 km; sustained day-after-day campaign marching with "
           "a baggage train is generally described as running somewhat "
           "below a single day's unencumbered-pace figure. Taken inside "
           "the broad 20-32 km/day range CALIBRATION_LEGION_MARCH_RATE_"
           "KM_PER_DAY_LOW/HIGH records below.",
    confidence="C",
    why="The speed that turns every day-based figure in this module "
        "(pack-animal range, foraging corridor width) into a km-based one, "
        "and the pace this module assumes for both the supplied force and "
        "its resupply column alike.")


def pack_animal_daily_fodder_kg():
    """One pack animal's own daily fodder claim, in kilograms. Arithmetic
    on two already-declared numbers, not its own declaration."""
    return PACK_ANIMAL_LIVE_MASS_KG * PACK_ANIMAL_DAILY_FORAGE_FRACTION_OF_BODY_MASS


def pack_animal_load_capacity_kg():
    """One pack animal's total carrying capacity, in kilograms. Arithmetic,
    not its own declaration."""
    return PACK_ANIMAL_LIVE_MASS_KG * PACK_ANIMAL_LOAD_CAPACITY_FRACTION_OF_BODY_MASS


def pack_animal_max_one_way_days(delivered_fraction=0.0):
    """The maximum one-way travel time, in days, before a pack animal that
    carries its own fodder for the whole round trip delivers no more than
    `delivered_fraction` of its rated load capacity as actual cargo.

    THE DERIVATION. Let C be the animal's load capacity (kg) and F its
    daily fodder need (kg/day). A round trip of `days` days out and `days`
    days back costs the animal 2*days*F kg of fodder, which - since it is
    not foraging and carries everything itself - comes out of the same C kg
    it is capable of carrying. What is left over is deliverable cargo:

        delivered_cargo_kg = C - 2 * days * F

    Solving for the `days` at which delivered_cargo_kg falls to
    `delivered_fraction * C` gives:

        days = C * (1 - delivered_fraction) / (2 * F)

    At `delivered_fraction=0.0` (the default) this is the outer physical
    bound: the distance beyond which the column cannot even complete the
    round trip while delivering anything at all - literally the point
    named in the module docstring's THE POINT paragraph, "before the
    supply train is eating more than it delivers". This bound does not
    depend on how many animals the column has, only on one animal's own
    mass, appetite and load fraction - adding animals adds proportionally
    to both the capacity delivered and the fodder consumed, so the RATIO,
    and therefore the range, is unchanged. That is a genuine finding of
    this arithmetic, not an assumption: the range a supply line can reach
    is a property of the ANIMAL, not of how large an army it is trying to
    feed.

    See sim/tests/test_military_logistics.py's calibration tests, and this
    module's own CALIBRATION TARGETS section, for how this compares to the
    historically documented "a few days' march" limit - reported honestly,
    not tuned to match.
    """
    if not (0.0 <= delivered_fraction <= 1.0):
        raise ValueError(
            "delivered_fraction must be between 0 and 1: %r" % (delivered_fraction,))
    capacity = pack_animal_load_capacity_kg()
    fodder = pack_animal_daily_fodder_kg()
    return capacity * (1.0 - delivered_fraction) / (2.0 * fodder)


def pack_animal_max_one_way_range_km(delivered_fraction=0.0, march_rate_km_per_day=None):
    """`pack_animal_max_one_way_days()` converted to kilometres at
    `march_rate_km_per_day` (default ARMY_MARCH_RATE_KM_PER_DAY)."""
    march_rate = (ARMY_MARCH_RATE_KM_PER_DAY if march_rate_km_per_day is None
                  else march_rate_km_per_day)
    return march_rate * pack_animal_max_one_way_days(delivered_fraction)


def pack_animal_net_deliverable_cargo_kg(one_way_distance_km, march_rate_km_per_day=None):
    """How much cargo, net of the animal's own round-trip fodder, a single
    pack animal actually delivers over a given one-way distance. Floored at
    zero: beyond pack_animal_max_one_way_range_km(0.0), the animal cannot
    deliver a NEGATIVE amount of cargo - it simply cannot make the round
    trip at all without additional fodder from somewhere (foraging along
    the way, or a relay of forward depots - see WHERE THIS MODEL IS WRONG
    (a))."""
    if one_way_distance_km < 0.0:
        raise ValueError(
            "one_way_distance_km cannot be negative: %r" % (one_way_distance_km,))
    march_rate = (ARMY_MARCH_RATE_KM_PER_DAY if march_rate_km_per_day is None
                  else march_rate_km_per_day)
    days_one_way = one_way_distance_km / march_rate
    capacity = pack_animal_load_capacity_kg()
    fodder = pack_animal_daily_fodder_kg()
    return max(0.0, capacity - 2.0 * days_one_way * fodder)


def pack_animals_required_for_daily_delivery(daily_requirement_kg, one_way_distance_km,
                                              march_rate_km_per_day=None):
    """How many pack animals a column needs, in a continuous rotation, to
    deliver `daily_requirement_kg` of net cargo every day to a force
    stationed `one_way_distance_km` from base.

    Each animal is unavailable for the whole round trip (out, unload, back)
    before it can carry another load, so sustaining a steady daily delivery
    needs enough animals in the rotation to cover that whole round-trip
    duration: `daily_requirement_kg * round_trip_days /
    net_deliverable_cargo_per_animal_kg`. Returns `float("inf")` at or
    beyond the zero-delivery range, where no number of animals helps.
    """
    if daily_requirement_kg < 0.0:
        raise ValueError(
            "daily_requirement_kg cannot be negative: %r" % (daily_requirement_kg,))
    march_rate = (ARMY_MARCH_RATE_KM_PER_DAY if march_rate_km_per_day is None
                  else march_rate_km_per_day)
    net_cargo_per_animal = pack_animal_net_deliverable_cargo_kg(
        one_way_distance_km, march_rate)
    if net_cargo_per_animal <= 0.0:
        return float("inf")
    round_trip_days = 2.0 * one_way_distance_km / march_rate
    return daily_requirement_kg * round_trip_days / net_cargo_per_animal


# ============================================================================
# FORAGING: THE ALTERNATIVE TO CARRYING FOOD
# ============================================================================
# An army that lives off the land does not need a baggage train for food at
# all - it eats the surplus of the territory it and its foragers can reach.
# Its sustainable size is then set by how much surplus that territory has
# per unit area and how fast the army sweeps across fresh ground: a slow
# army over rich land can be large, a fast army over poor land small, and
# neither number is invented for this module - both come from elsewhere
# (agriculture's yield model; the march rate already declared above).

FORAGING_CORRIDOR_HALF_WIDTH_TO_MARCH_RATE_RATIO = declare(
    "FORAGING_CORRIDOR_HALF_WIDTH_TO_MARCH_RATE_RATIO", 0.5,
    kind="engineering_estimate",
    unit="dimensionless (fraction of one day's march rate)",
    source="A foraging party must travel out from the line of march, "
           "gather, and return before the column it belongs to has moved "
           "on too far to rejoin - roughly the same physical constraint "
           "that sets a pack animal's round-trip range, applied over a "
           "single day instead of a whole supply run. Taken here as half "
           "the day's march rate each side of the column (i.e. a forager "
           "on foot or horse covering, out and back, about as much ground "
           "in a day as the column itself advances), which is the "
           "simplest self-consistent choice rather than an independently "
           "measured foraging radius.",
    confidence="D",
    why="Ties the width of ground an army can strip bare to the SAME "
        "march-rate figure already governing the baggage-train "
        "calculation above, rather than inventing an unrelated foraging-"
        "radius constant - a forager's own out-and-back day is the same "
        "shape of problem as the pack train's round trip, just over one "
        "day instead of many.")


def foraging_corridor_width_km(march_rate_km_per_day=None):
    """The total width of ground (both sides of the line of march) an
    army's foragers can reach and return from within one day - see
    FORAGING_CORRIDOR_HALF_WIDTH_TO_MARCH_RATE_RATIO's declaration for the
    reasoning."""
    march_rate = (ARMY_MARCH_RATE_KM_PER_DAY if march_rate_km_per_day is None
                  else march_rate_km_per_day)
    return 2.0 * FORAGING_CORRIDOR_HALF_WIDTH_TO_MARCH_RATE_RATIO * march_rate


def sustainable_foraging_army_size(surplus_kg_per_square_km, march_rate_km_per_day=None,
                                    corridor_width_km=None,
                                    ration_kg_per_soldier_per_day=None):
    """How many soldiers a foraging army (no baggage train for food at all)
    can sustain indefinitely, given the agricultural surplus of the land it
    is crossing.

    `surplus_kg_per_square_km` is NOT a constant of this module - it is a
    STOCK (kilograms of storable grain surplus standing in the fields and
    granaries of one square kilometre, the accumulated result of a growing
    season) that an agriculture/geography domain would supply, varying by
    place and by season. This module deliberately does not import
    sim/world/agriculture.py to get one (see the module docstring's
    STANDALONE section) - it takes it as a plain argument, exactly as this
    project's task instructs, so wiring the two together later is the
    caller's job, not an import this module should not have.

    THE DERIVATION. Each day the army advances `march_rate_km_per_day`
    kilometres and its foragers can reach `corridor_width_km` of width
    (see foraging_corridor_width_km()) on either side of that line - so the
    army exposes `march_rate_km_per_day * corridor_width_km` square
    kilometres of FRESH ground each day, and can draw
    `march_rate_km_per_day * corridor_width_km * surplus_kg_per_square_km`
    kilograms of food from it (this module does not model re-crossing
    already-stripped ground - see WHERE THIS MODEL IS WRONG (c)). Setting
    that daily food draw equal to `army_size * ration_kg_per_soldier_per_day`
    and solving for army_size gives the sustainable size:

        army_size = (march_rate_km_per_day * corridor_width_km
                     * surplus_kg_per_square_km)
                    / ration_kg_per_soldier_per_day

    This is the property CLAUDE.md SS3.1 asks for directly: a foraging
    army's size is not asserted, it falls out of land, rate of march and
    ration, and if the ground is barren or the march is slow the formula
    hands back a small number without anything else needing to say so.
    """
    if surplus_kg_per_square_km < 0.0:
        raise ValueError(
            "surplus_kg_per_square_km cannot be negative: %r"
            % (surplus_kg_per_square_km,))
    march_rate = (ARMY_MARCH_RATE_KM_PER_DAY if march_rate_km_per_day is None
                  else march_rate_km_per_day)
    corridor = (foraging_corridor_width_km(march_rate) if corridor_width_km is None
                else corridor_width_km)
    ration = (ration_kg_grain_per_day() if ration_kg_per_soldier_per_day is None
              else ration_kg_per_soldier_per_day)
    daily_food_available_kg = march_rate * corridor * surplus_kg_per_square_km
    return daily_food_available_kg / ration


# ============================================================================
# EQUIPMENT: A STANDING CLAIM ON IRON
# ============================================================================
# An army is not a one-off purchase of arms and armour - it is a continuing
# draw on metal production, because equipment wears out, breaks and is lost
# in the field. This section states that draw as a stock (iron per soldier)
# and a rate (the fraction of that stock consumed per year of campaigning),
# so a metals-production domain (not built by this module) has a number to
# meet rather than an assumption that soldiers are equipped once and stay
# that way.

IRON_KG_PER_EQUIPPED_SOLDIER = declare(
    "IRON_KG_PER_EQUIPPED_SOLDIER", 7.0,
    kind="engineering_estimate",
    unit="kg worked iron/soldier",
    source="Sum of the worked-iron components of a Roman-style heavy "
           "infantryman's panoply - helmet, mail or scale shirt (the "
           "single largest component where one is worn), sword blade, "
           "spearhead(s), and shield boss and rim fittings - commonly "
           "estimated in aggregate at somewhere in the 5-9 kg range; "
           "taken near the middle of that range.",
    confidence="C",
    why="The stock this section treats as a standing claim on iron "
        "production: outfitting N soldiers costs N times this figure "
        "once, and keeping them equipped costs the replacement rate below "
        "times this figure every year after.")

ANNUAL_EQUIPMENT_REPLACEMENT_FRACTION = declare(
    "ANNUAL_EQUIPMENT_REPLACEMENT_FRACTION", 0.20,
    kind="temporary_heuristic",
    unit="fraction of IRON_KG_PER_EQUIPPED_SOLDIER replaced/year of "
         "campaigning",
    source=None,
    confidence="D",
    why="No real source underlies this figure. The mechanism that would "
        "derive it - a corrosion and fatigue rate for worked iron under "
        "field conditions, combined with a combat-loss and breakage rate "
        "this project cannot compute without a combat model, which is an "
        "explicit non-goal of this module - does not exist yet. Kept as a "
        "named, invented placeholder rather than an unstated assumption "
        "that equipment lasts forever, which is the more common and more "
        "wrong default.")


def annual_iron_replacement_kg_per_soldier():
    """The continuing annual iron claim one equipped soldier represents, on
    top of the one-off IRON_KG_PER_EQUIPPED_SOLDIER outfitting cost.
    Arithmetic on two declared numbers, not its own declaration."""
    return IRON_KG_PER_EQUIPPED_SOLDIER * ANNUAL_EQUIPMENT_REPLACEMENT_FRACTION


# ============================================================================
# FIREARMS: THE SAME STRUCTURE, DIFFERENT NUMBERS
# ============================================================================
# CLAUDE.md SS3.3: a firearm is an object with an ammunition and maintenance
# requirement, exactly like the sword and shield above, not a bespoke
# "modern weapon" branch. Firearm is one namedtuple; FLINTLOCK_MUSKET and
# MODERN_SERVICE_RIFLE are two instances of it, so the intervention scenario
# this module was built for - handing 100 AD Rome a modern rifle - runs
# through ammunition_mass_kg_per_soldier_per_engagement() and
# maintenance_items_per_soldier_per_engagement() with a different Firearm
# argument, not a different function.
#
# WHAT IS DELIBERATELY NOT HERE. No propellant formulation, no cartridge
# construction, no loading or firing procedure - the task this module
# answers to is explicit that this is not a weapons manual, and none of
# that is needed for logistics arithmetic. Every number below is a
# published consumption rate (mass per shot, shots per engagement, a
# maintenance item's service life), the same kind of public reference
# figure a ballistics table or a quartermaster's ledger would carry, never
# a recipe or a procedure.

Firearm = collections.namedtuple("Firearm", [
    "name",
    "consumable_mass_g_per_shot",   # powder + projectile (musket) or a
                                     # complete cartridge (modern rifle)
    "rounds_per_engagement",        # ammunition expended in one engagement
    "maintenance_items_per_shot",   # e.g. flints consumed per shot fired;
                                     # 0.0 where no such per-shot item exists
])

FLINTLOCK_MUSKET_POWDER_G_PER_SHOT = declare(
    "FLINTLOCK_MUSKET_POWDER_G_PER_SHOT", 10.0,
    kind="engineering_estimate",
    unit="g/shot",
    source="Standard paper-cartridge powder charges for 18th-century "
           "smoothbore infantry muskets are commonly given as roughly "
           "100-130 grains (about 6.5-8.4 g); taken slightly above that "
           "range to account for priming powder and loading waste.",
    confidence="C",
    why="Half of the consumable mass a musket shot represents - see "
        "FLINTLOCK_MUSKET below.")

FLINTLOCK_MUSKET_LEAD_G_PER_SHOT = declare(
    "FLINTLOCK_MUSKET_LEAD_G_PER_SHOT", 30.0,
    kind="engineering_estimate",
    unit="g/shot",
    source="A lead ball for a .69-.75 calibre smoothbore infantry musket "
           "of this period is commonly cited at roughly 28-35 g; taken "
           "near the middle of that range.",
    confidence="C",
    why="The other half of the consumable mass a musket shot represents.")

FLINTLOCK_MUSKET_ROUNDS_PER_ENGAGEMENT = declare(
    "FLINTLOCK_MUSKET_ROUNDS_PER_ENGAGEMENT", 30.0,
    kind="engineering_estimate",
    unit="rounds/soldier/engagement",
    source="Historical ammunition-expenditure accounts for 18th- and "
           "early-19th-century smoothbore infantry commonly cite roughly "
           "20-60 rounds fired per soldier in a single engagement; taken "
           "near the middle of that range.",
    confidence="C",
    why="How much of the per-shot consumable mass one engagement actually "
        "costs a soldier - the figure ammunition_mass_kg_per_soldier_per_"
        "engagement() multiplies by.")

FLINTLOCK_MUSKET_FLINT_LIFE_SHOTS = declare(
    "FLINTLOCK_MUSKET_FLINT_LIFE_SHOTS", 25.0,
    kind="engineering_estimate",
    unit="shots/flint",
    source="A gunflint is commonly cited as serviceable for roughly 20-30 "
           "shots before it chips too badly to spark reliably and needs "
           "replacing or reknapping; taken near the middle of that range.",
    confidence="C",
    why="The MAINTENANCE half of a flintlock musket's consumption profile, "
        "distinct from the ammunition it fires - CLAUDE.md SS3.3's "
        "'ammunition and maintenance requirement' names both explicitly, "
        "and a musket without a serviceable flint cannot fire regardless "
        "of how much powder and lead its bearer is carrying.")

FLINTLOCK_MUSKET = Firearm(
    name="flintlock musket",
    consumable_mass_g_per_shot=(
        FLINTLOCK_MUSKET_POWDER_G_PER_SHOT + FLINTLOCK_MUSKET_LEAD_G_PER_SHOT),
    rounds_per_engagement=FLINTLOCK_MUSKET_ROUNDS_PER_ENGAGEMENT,
    maintenance_items_per_shot=1.0 / FLINTLOCK_MUSKET_FLINT_LIFE_SHOTS)

MODERN_RIFLE_CARTRIDGE_MASS_G_PER_SHOT = declare(
    "MODERN_RIFLE_CARTRIDGE_MASS_G_PER_SHOT", 12.0,
    kind="engineering_estimate",
    unit="g/shot",
    source="A complete standard 5.56x45mm service-rifle cartridge (case, "
           "propellant, primer and bullet together) is commonly published "
           "at approximately 12 g - an ordinary ballistics-reference "
           "figure, not a design detail of any weapon.",
    confidence="B",
    why="The modern side of the SAME structure as the musket above - "
        "consumable mass per shot is a published, unitary figure for a "
        "complete cartridge rather than split into a powder charge and a "
        "separately-loaded ball, because that is how the object is "
        "actually carried and consumed.")

MODERN_RIFLE_ROUNDS_PER_ENGAGEMENT = declare(
    "MODERN_RIFLE_ROUNDS_PER_ENGAGEMENT", 120.0,
    kind="temporary_heuristic",
    unit="rounds/soldier/engagement",
    source=None,
    confidence="D",
    why="Modern infantry ammunition-expenditure studies report riflemen "
        "firing many times more rounds per engagement than pre-modern "
        "infantry (automatic and semi-automatic fire, suppressive fire "
        "doctrine, far lower per-round mass and recoil making high "
        "volumes of fire practical) but the reports this module's author "
        "could ground a specific figure in vary by an order of magnitude "
        "depending on engagement type and doctrine; 120 is an "
        "order-of-magnitude placeholder pending a sourced figure, not a "
        "number read off a specific study. Marked temporary_heuristic, "
        "unlike its musket counterpart, for exactly that reason.")

MODERN_SERVICE_RIFLE = Firearm(
    name="modern service rifle",
    consumable_mass_g_per_shot=MODERN_RIFLE_CARTRIDGE_MASS_G_PER_SHOT,
    rounds_per_engagement=MODERN_RIFLE_ROUNDS_PER_ENGAGEMENT,
    maintenance_items_per_shot=0.0)
# 0.0: a cartridge weapon has no per-shot consumable analogous to a flint -
# its maintenance burden (cleaning supplies, spare parts, barrel wear) is
# real but is not a per-shot mass claim on the baggage train the way a
# flint is, and modelling it would need a different unit (a fixed mass per
# unit of TIME or rounds-fired-lifetime, not per shot) that this module
# does not yet have a use for.


def ammunition_mass_kg_per_soldier_per_engagement(firearm):
    """One soldier's ammunition mass burden for one engagement, in
    kilograms - the same MASS the baggage-train functions above have to
    move, whichever Firearm is passed in."""
    return firearm.consumable_mass_g_per_shot * firearm.rounds_per_engagement / 1000.0


def maintenance_items_per_soldier_per_engagement(firearm):
    """How many of the firearm's per-shot maintenance item (flints, for the
    musket; none, for the modern cartridge rifle) one engagement consumes
    per soldier."""
    return firearm.maintenance_items_per_shot * firearm.rounds_per_engagement


# ============================================================================
# PUTTING IT TOGETHER: ONE DAY'S SUPPLY REQUIREMENT
# ============================================================================

DailySupplyRequirement = collections.namedtuple(
    "DailySupplyRequirement",
    ["army_size", "grain_kg", "water_kg", "ammunition_kg", "total_kg"])


def daily_supply_requirement_kg(army_size, desert=False, firearm=None,
                                 engagements_per_day=0.0):
    """The total mass an army of `army_size` soldiers needs delivered (or
    foraged) in one day: grain at `ration_kg_grain_per_day()`, water at
    `water_requirement_liters_per_day()` (1 litre of water masses 1 kg -
    WATER_DENSITY_KG_PER_LITER below), and - if `firearm` is given and
    `engagements_per_day` is nonzero - the ammunition mass an average day
    of that much combat intensity would burn.

    `engagements_per_day` is a plain multiplier on
    ammunition_mass_kg_per_soldier_per_engagement(), not a new declared
    constant: this module has no campaign-tempo model (see WHERE THIS
    MODEL IS WRONG (d)), so a caller who wants "one engagement every three
    days" passes 1.0/3.0 rather than this module inventing a tempo of its
    own.
    """
    if army_size < 0.0:
        raise ValueError("army_size cannot be negative: %r" % (army_size,))
    grain_kg = army_size * ration_kg_grain_per_day()
    water_kg = army_size * water_requirement_liters_per_day(desert) * WATER_DENSITY_KG_PER_LITER
    ammunition_kg = 0.0
    if firearm is not None and engagements_per_day:
        ammunition_kg = (army_size * engagements_per_day
                         * ammunition_mass_kg_per_soldier_per_engagement(firearm))
    total_kg = grain_kg + water_kg + ammunition_kg
    return DailySupplyRequirement(
        army_size=army_size, grain_kg=grain_kg, water_kg=water_kg,
        ammunition_kg=ammunition_kg, total_kg=total_kg)


WATER_DENSITY_KG_PER_LITER = declare(
    "WATER_DENSITY_KG_PER_LITER", 1.0,
    kind="physical_constant",
    unit="kg/litre",
    source="Density of fresh water at ordinary temperature, to the "
           "precision this module needs.",
    confidence="A",
    why="Converts the water ration from volume (what a person drinks) to "
        "mass (what a pack animal or a soldier's own kit has to carry) - "
        "every other mass figure in this module is in kilograms, and "
        "water is no exception once it has to be carried rather than "
        "drunk on the spot from a river or well.")


# ============================================================================
# CALIBRATION TARGETS - never read by any function above, only by
# sim/tests/test_military_logistics.py, to report how this module's derived
# figures compare to documented historical ranges. See sim/constants.py:
# "an observation used to CHECK the model." Nothing above is tuned to make
# these pass.
# ============================================================================

CALIBRATION_LEGION_RATION_KG_GRAIN_PER_DAY_LOW = declare(
    "CALIBRATION_LEGION_RATION_KG_GRAIN_PER_DAY_LOW", 0.75,
    kind="calibration_target",
    unit="kg grain/soldier/day",
    source="Secondary literature on Roman military logistics (e.g. J. "
           "Roth, The Logistics of the Roman Army at War) commonly gives a "
           "standard wheat ration on the order of 830-850 g/soldier/day, "
           "consistent with the widely-cited conversion of Polybius's "
           "figure of two-thirds of an Attic medimnos of wheat per month; "
           "taken with headroom below that figure as the low end of a "
           "documented range rather than a single point.",
    confidence="C",
    why="The low end of what ration_kg_grain_per_day() is checked against, "
        "never tuned to.")

CALIBRATION_LEGION_RATION_KG_GRAIN_PER_DAY_HIGH = declare(
    "CALIBRATION_LEGION_RATION_KG_GRAIN_PER_DAY_HIGH", 0.95,
    kind="calibration_target",
    unit="kg grain/soldier/day",
    source="Same as CALIBRATION_LEGION_RATION_KG_GRAIN_PER_DAY_LOW.",
    confidence="C",
    why="The high end of the same range.")

CALIBRATION_LEGION_MARCH_RATE_KM_PER_DAY_LOW = declare(
    "CALIBRATION_LEGION_MARCH_RATE_KM_PER_DAY_LOW", 20.0,
    kind="calibration_target",
    unit="km/day",
    source="Vegetius's De Re Militari: the \"ordinary march\" (iter "
           "iustum), 20 Roman miles in five summer hours, about 29.6 km "
           "for a single unencumbered day; sustained multi-day campaign "
           "marching with a baggage train is generally described as "
           "running somewhat below that pace.",
    confidence="C",
    why="The low end of what ARMY_MARCH_RATE_KM_PER_DAY is checked "
        "against.")

CALIBRATION_LEGION_MARCH_RATE_KM_PER_DAY_HIGH = declare(
    "CALIBRATION_LEGION_MARCH_RATE_KM_PER_DAY_HIGH", 32.0,
    kind="calibration_target",
    unit="km/day",
    source="Vegetius's \"full march\" (iter plenum), 24 Roman miles, "
           "about 35.5 km, taken with a small margin down as the high end "
           "of a documented range for a single day's pace rather than a "
           "sustained one.",
    confidence="C",
    why="The high end of the same range.")

CALIBRATION_MAX_SUPPLY_RANGE_DAYS_LOW = declare(
    "CALIBRATION_MAX_SUPPLY_RANGE_DAYS_LOW", 3.0,
    kind="calibration_target",
    unit="days' march from a supply base or navigable water",
    source="General historical-logistics literature on pre-mechanized "
           "armies (e.g. van Creveld, Supplying War; Engels, Alexander the "
           "Great and the Logistics of the Macedonian Army) commonly "
           "describes armies without water transport as confined to on "
           "the order of a few days' march - often cited in the range of "
           "roughly 3-5 days - from a fixed supply base or navigable river "
           "or coast, when not foraging.",
    confidence="C",
    why="The low end of what pack_animal_max_one_way_days() is checked "
        "against, never tuned to. See that function's docstring for why "
        "this module reports two different comparisons (the outer, "
        "zero-delivery bound and a delivering-half-capacity bound) rather "
        "than declaring the model 'right' or 'wrong' against a single "
        "number.")

CALIBRATION_MAX_SUPPLY_RANGE_DAYS_HIGH = declare(
    "CALIBRATION_MAX_SUPPLY_RANGE_DAYS_HIGH", 5.0,
    kind="calibration_target",
    unit="days' march from a supply base or navigable water",
    source="Same as CALIBRATION_MAX_SUPPLY_RANGE_DAYS_LOW.",
    confidence="C",
    why="The high end of the same range.")


if __name__ == "__main__":
    # A quick, human-readable readout - the same kind of thing
    # sim/world/agriculture.py's own __main__ block prints.
    print("--- ration and water ---")
    print("soldier campaign energy requirement: %.0f kcal/day"
          % soldier_campaign_energy_requirement_kcal_per_day())
    print("ration:                              %.2f kg grain/day"
          % ration_kg_grain_per_day())
    print("documented Roman ration (calibration): %.2f-%.2f kg/day"
          % (CALIBRATION_LEGION_RATION_KG_GRAIN_PER_DAY_LOW,
             CALIBRATION_LEGION_RATION_KG_GRAIN_PER_DAY_HIGH))
    print("water, temperate march:              %.1f L/day"
          % water_requirement_liters_per_day(desert=False))
    print("water, desert march:                 %.1f L/day"
          % water_requirement_liters_per_day(desert=True))

    print("\n--- baggage train ---")
    print("pack animal load capacity:  %.1f kg" % pack_animal_load_capacity_kg())
    print("pack animal daily fodder:   %.1f kg/day" % pack_animal_daily_fodder_kg())
    zero_net_days = pack_animal_max_one_way_days(delivered_fraction=0.0)
    half_net_days = pack_animal_max_one_way_days(delivered_fraction=0.5)
    print("max one-way range (zero net delivered):  %.2f days, %.0f km"
          % (zero_net_days, pack_animal_max_one_way_range_km(0.0)))
    print("max one-way range (half capacity delivered): %.2f days, %.0f km"
          % (half_net_days, pack_animal_max_one_way_range_km(0.5)))
    print("documented 'a few days' calibration:     %.0f-%.0f days"
          % (CALIBRATION_MAX_SUPPLY_RANGE_DAYS_LOW,
             CALIBRATION_MAX_SUPPLY_RANGE_DAYS_HIGH))

    print("\n--- foraging ---")
    example_surplus_kg_per_km2 = 100.0
    # Illustrative only - NOT a constant of this module and not fitted to
    # anything. Deliberately modest: agriculture.py's own net yield is
    # several hundred kg/ha (tens of thousands of kg/km^2) on FULLY
    # CULTIVATED land, but a real landscape an army crosses is a mix of
    # arable, pasture, waste and forest, and most of even the arable
    # fraction's output is claimed by local subsistence before anything is
    # "surplus" - this module has no land-per-capita or land-use mechanism
    # to compute that discount (agriculture.py names the same gap for its
    # own headline number), so a small round figure stands in for it. A
    # real figure belongs to a geography/agriculture domain and would vary
    # enormously by place - see sustainable_foraging_army_size()'s own
    # docstring for why it is a parameter here, never a constant.
    print("(illustrative surplus: %.0f kg/km^2 - see __main__ source comment)"
          % example_surplus_kg_per_km2)
    print("sustainable foraging army size: %.0f soldiers"
          % sustainable_foraging_army_size(example_surplus_kg_per_km2))
    print("(this scales LINEARLY with the surplus figure chosen above, and "
          "assumes an endless corridor of never-before-stripped land - see "
          "WHERE THIS MODEL IS WRONG (c) for the depletion mechanism that "
          "would cap it in reality)")

    print("\n--- equipment ---")
    print("iron per equipped soldier:         %.1f kg" % IRON_KG_PER_EQUIPPED_SOLDIER)
    print("annual iron replacement/soldier:   %.2f kg/year"
          % annual_iron_replacement_kg_per_soldier())

    print("\n--- firearms (same structure, different numbers) ---")
    for firearm in (FLINTLOCK_MUSKET, MODERN_SERVICE_RIFLE):
        print("%-20s ammunition/engagement: %.2f kg/soldier, "
              "maintenance items/engagement: %.2f"
              % (firearm.name,
                 ammunition_mass_kg_per_soldier_per_engagement(firearm),
                 maintenance_items_per_soldier_per_engagement(firearm)))

    print("\n--- one day, one legion (5,000 soldiers) ---")
    requirement = daily_supply_requirement_kg(
        5000.0, desert=False, firearm=FLINTLOCK_MUSKET, engagements_per_day=0.1)
    print(requirement)
