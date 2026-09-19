"""The granary: one person's annual food need, how much a granary can
physically hold, and `Storage.step`'s full sow-grow-harvest-eat-spoil-retain
cycle for one year.

This module holds the STORAGE subject of `sim/world/agriculture.py`'s
farming domain - see that file's own docstring, "THIS FILE IS A COMPOSITION
POINT", for the other two subject files and why the constants and tables
stay in that file instead: `annual_food_demand_kg_per_person` and
`granary_capacity_kg` (what a population needs and what its granary can
hold), `YearFlows` (the exact accounting of one year's grain), `Storage`
itself (the running stock and the one-year cycle that moves it - sow, grow,
harvest, eat, spoil, retain next year's seed, bank the rest), and
`stock_to_carry_forward_kg` (the one-line fix a caller that persists
`Storage` across years needs, or it double-charges seed every year - see
that function's own docstring for the incident this exists because of).

STANDALONE THE SAME WAY THE PARENT MODULE IS. Nothing here imports from
`sim/engine/`; the only imports besides the standard library are from
`sim.world.agriculture` (the declared constants and the Crop/Soil/Rotation/
Toolkit/StorageTechnique tables `Storage.step` takes as optional arguments)
and `sim.world.agriculture_yield` (the harvest itself: `gross_harvest_kg`
and `marginal_product_of_labour_kg_per_hour`, which `Storage.step` calls to
turn this year's sowing into this year's harvest and this year's marginal
product). See `sim/world/agriculture.py`'s own STANDALONE ON PURPOSE section
for why that matters and to whom.

`draw_weather_multiplier` ITSELF IS CALLED THROUGH THE `agriculture` MODULE
OBJECT, NOT IMPORTED BY NAME LIKE THE OTHER TWO, BECAUSE A NAME IMPORT WOULD
BREAK MONKEYPATCHING. `sim/tests/test_agriculture.py`'s bad-year test
monkeypatches `agriculture.draw_weather_multiplier` directly (there is no
seed that reliably produces a bad enough year on demand, so the test
replaces the draw instead of hunting for one) and expects `Storage.step` to
draw through the patched function. A `from .agriculture_yield import
draw_weather_multiplier` here would copy the ORIGINAL function object into
this module's own globals at import time, permanently, so patching
`agriculture.draw_weather_multiplier` afterward would not reach
`Storage.step` at all - the "green tests do not mean unchanged behaviour"
trap CLAUDE.md SS6 warns about, which is exactly what the one test built to
catch it exists to catch. Looking the name up on the module at call time,
below, keeps monkeypatching `agriculture.draw_weather_multiplier` working.
"""
import collections
import random
from typing import Optional

from . import agriculture
from .agriculture import (
    DAYS_PER_YEAR,
    DEFAULT_CROP,
    DEFAULT_ROTATION,
    DEFAULT_SOIL,
    DEFAULT_STORAGE_TECHNIQUE,
    DEFAULT_TOOLKIT,
    GRANARY_CAPACITY_YEARS_OF_DEMAND,
    HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY,
    MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE,
    Crop,
    Rotation,
    Soil,
    StorageTechnique,
    Toolkit,
)
from .agriculture_yield import (
    Land,
    gross_harvest_kg,
    marginal_product_of_labour_kg_per_hour,
)


def annual_food_demand_kg_per_person(crop: Optional["Crop"] = None) -> float:
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


def granary_capacity_kg(
        food_demand_kg: float, capacity_years: Optional[float] = None) -> float:
    """How much grain a population's storage infrastructure can physically
    hold, given `food_demand_kg` (that population's OWN annual food need -
    see `annual_food_demand_kg_per_person`, usually multiplied up by however
    many people there are).

    This is a ceiling on the STOCK a granary can carry into next year, not a
    term inside `Storage.step`'s own one-year accounting - see
    GRANARY_CAPACITY_YEARS_OF_DEMAND's own declaration for why the cap lives
    here, as a plain function callers apply to whatever they carry forward,
    rather than inside `Storage` itself. A caller (sim/engine/core.py) that
    ignores this entirely just gets an uncapped granary - nothing in
    `Storage.step` enforces it - so applying it is the caller's choice, the
    same way applying `storage_technique` at all is.

    `capacity_years` defaults to GRANARY_CAPACITY_YEARS_OF_DEMAND; a caller
    exploring a different storage infrastructure (a state granary system
    built for multi-year reserves, or a village with no real granary at all)
    passes its own figure.
    """
    if capacity_years is None:
        capacity_years = GRANARY_CAPACITY_YEARS_OF_DEMAND
    return food_demand_kg * capacity_years


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

    def __init__(self, stock_kg: float = 0.0, seed: Optional[int] = None) -> None:
        self.stock_kg = float(stock_kg)
        self._random = random.Random(seed)

    def __repr__(self) -> str:
        return "Storage(stock_kg=%.4f)" % (self.stock_kg,)

    def step(
            self, land: "Land", labour_hours: float, population: float,
            technique_multiplier: float = 1.0,
            hectares_next_year: Optional[float] = None, crop: Optional["Crop"] = None,
            soil: Optional["Soil"] = None, rotation: Optional["Rotation"] = None,
            toolkit: Optional["Toolkit"] = None,
            storage_technique: Optional["StorageTechnique"] = None,
            worker_count: Optional[float] = None,
            hours_per_worker_day: Optional[float] = None,
            reserve_target_kg: Optional[float] = None,
            weather_multiplier: Optional[float] = None) -> "YearFlows":
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

        `weather_multiplier` defaults to `None`, meaning "draw one from
        `self._random` the way this method always has" (step 2 below). A
        caller that passes a number instead (sim/engine/core.py's
        `_pooled_farm_weather_multiplier`, Complaints/47-one-weather-draw-
        for-a-continent.md) gets that number used AS this year's weather
        multiplier verbatim, and `self._random`/`draw_weather_multiplier`
        are not touched at all - this is what lets a caller that already
        knows how to pool several independent regional draws into one
        civilisation-wide multiplier (a land-share-weighted average, not a
        single region's draw) hand the RESULT of that pooling to this
        method instead of this method drawing its own single, un-pooled
        multiplier internally. Every existing caller that does not pass
        this argument is unaffected - this is an additional way IN, not a
        change to the default path.

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

        A CALLER THAT CARRIES `stock_after_kg` ACROSS YEARS MUST ALSO CARRY
        `seed_retained_kg` BACK IN, OR IT WILL DOUBLE-CHARGE SEED EVERY
        SINGLE YEAR. This was invisible for as long as every caller (see
        Complaints/45-no-granary-so-the-baseline-collapses.md) constructed
        a fresh `Storage` at stock_kg=0.0 every year and threw `stock_after_
        kg` away unused - a bug in a number nothing ever reads cannot bite.
        The instant a caller starts persisting `stock_kg`, it does: step 5
        above SUBTRACTS `seed_retained_kg` from `self.stock_kg` (the class
        docstring's own "set aside" language means exactly that - it is
        REMOVED from the ledger, not merely labelled), which is correct
        ONLY if that removed amount is handed back at the top of NEXT
        year's `step` call as part of `stock_before_kg`, where it is
        immediately spent again as THAT year's `seed_sown_kg`. Persist
        `stock_after_kg` alone (without adding `seed_retained_kg` back in)
        and every single year permanently loses one full season's seed
        requirement from the ledger - not a weather effect, not a real
        famine, a bookkeeping amount that vanishes into the void and never
        returns, compounding without bound over a multi-year run. This is
        exactly the failure this task's own probe caught empirically (a
        near-total-extinction result on ordinary weather, once persistence
        was first tried without this correction) - `stock_to_carry_forward_
        kg`, just below this class, is the one-line fix: it returns
        `stock_after_kg + seed_retained_kg`, and a caller that wants to
        persist a granary across years should carry THAT value forward as
        next year's `stock_kg`, never `stock_after_kg` alone. The
        conservation identity above is unaffected either way - this is
        about what a MULTI-YEAR caller does with `stock_after_kg` after
        `step` returns it, not about anything `step` itself computes
        wrongly.
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

        if weather_multiplier is None:
            # Through the `agriculture` module object, not a bare name - see
            # this file's own top-of-file comment on why: a monkeypatched
            # `agriculture.draw_weather_multiplier` has to reach this call.
            weather_multiplier = agriculture.draw_weather_multiplier(
                self._random, soil.weather_stdev_fraction)
        harvest_kg = gross_harvest_kg(land, labour_hours, technique_multiplier,
                                      weather_multiplier, crop, toolkit, rotation,
                                      worker_count=worker_count,
                                      hours_per_worker_day=hours_per_worker_day)
        self.stock_kg += harvest_kg

        food_demand_kg = population * annual_food_demand_kg_per_person(crop)
        # CONSUMPTION IS NOT CAPPED AT min(demand, stock), BECAUSE THAT WOULD
        # MAKE EVERY GOOD YEAR WORTH NOTHING. Capping intake at subsistence
        # regardless of how full the granary is means the nutrition ratio
        # handed to demography could never exceed 1.0, however full the
        # granary was; combined with a mortality and fertility response that
        # floors at 1.0, that turns every bad year into a real population
        # cost with no good year ever offsetting it - the ratchet
        # Complaints/45 records. The granary alone does not fix this:
        # banking grain and then forbidding anyone to eat the surplus solves
        # nothing.
        #
        # THE RESERVE IS FILLED FIRST, which is the whole point of having
        # one. Extra eating comes only out of what is already beyond the
        # reserve a prudent household is holding against next year, so this
        # cannot empty the granary to feast - it eats the grain that would
        # otherwise have sat there and spoiled.
        #
        # `reserve_target_kg` defaults to None, meaning "no reserve named",
        # and then no extra is eaten at all and this reduces to exactly the
        # old line. A caller that persists stock across years should pass
        # the same figure it caps the granary at.
        subsistence_consumption_kg = max(0.0, min(food_demand_kg, self.stock_kg))
        extra_consumption_kg = 0.0
        if reserve_target_kg is not None:
            stock_beyond_reserve_kg = max(
                0.0, self.stock_kg - subsistence_consumption_kg - reserve_target_kg)
            most_a_person_can_eat_kg = food_demand_kg * (
                MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE - 1.0)
            extra_consumption_kg = min(stock_beyond_reserve_kg,
                                       most_a_person_can_eat_kg)
        consumption_kg = subsistence_consumption_kg + extra_consumption_kg
        # Shortfall is measured against SUBSISTENCE demand, never against the
        # larger amount a well-fed year allows - eating well is not a way to
        # run a deficit.
        food_shortfall_kg = max(0.0, food_demand_kg - subsistence_consumption_kg)
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


def stock_to_carry_forward_kg(flows: "YearFlows") -> float:
    """What a caller that persists `Storage` across years should use as
    NEXT year's opening `stock_kg` - `flows.stock_after_kg`, the free
    surplus `Storage.step` computed, PLUS `flows.seed_retained_kg`, the
    amount that same call earmarked for next year's sowing and then
    removed from the ledger.

    See `Storage.step`'s own docstring, the paragraph on carrying
    `stock_after_kg` across years, for why omitting `seed_retained_kg`
    here double-charges one whole season's seed requirement every single
    year (once as this call's own `seed_retained_kg` deduction, again as
    NEXT call's `seed_sown_kg` deduction, with nothing in between ever
    replacing what the first deduction removed) - a bug invisible for as
    long as nothing persisted `stock_kg` at all, and the specific,
    measured cause of a near-total-extinction result the first attempt at
    Complaints/45's granary fix produced on perfectly ordinary weather,
    with no famine, no hazard and no land loss of any kind.

    A caller that does NOT intend to persist `Storage` across years (one
    that still rebuilds it fresh at stock_kg=0.0 every step, as this
    module's whole test suite still does for calls that are not
    specifically testing multi-year carry) has no reason to call this at
    all - it exists for exactly one job, the one Sim._demographic_recovery
    (sim/engine/core.py) now does.
    """
    return flows.stock_after_kg + flows.seed_retained_kg
