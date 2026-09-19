"""Sizing a farm worker's land, and a population's farm from it: the two
ceilings on how much one worker can crop, the headline farm-population-share
calibration, and the two functions `sim/engine/core.py` calls to turn "how
many people are there" into "how much land, worked by how many hands".

This module holds the LABOUR DEMAND subject of `sim/world/agriculture.py`'s
farming domain - see that file's own docstring, "THIS FILE IS A COMPOSITION
POINT", for the other two subject files and why the constants and tables
stay in that file instead: `hectares_per_worker_annual_hours_
ceiling` and `hectares_per_worker_harvest_window_ceiling` (the two ceilings
on a worker's cropped area, and why the harvest window is the binding one),
`hectares_cropped_per_farm_worker` (the smaller of the two), `holding_
hectares_required_per_farm_worker` (grossed up for fallow), `fraction_of_
population_that_must_farm` (the headline calibration figure this whole
package exists to compute), and `farm_workers_fte_for_population` /
`farmland_for_population` (the seam to the rest of the engine - see the
SIZING A CIVILISATION'S FARM FROM ITS POPULATION section below).

STANDALONE THE SAME WAY THE PARENT MODULE IS. Nothing here imports from
`sim/engine/`; the only imports besides the standard library are from
`sim.world.agriculture` (the declared constants and the Crop/Soil/Rotation/
Toolkit/StorageTechnique tables these functions take as optional arguments),
`sim.world.agriculture_yield` (`Land`, which `farmland_for_population`
builds), and `sim.world.agriculture_storage` (`annual_food_demand_kg_per_
person`, which `fraction_of_population_that_must_farm` divides by this
module's own output-per-worker figure). See `sim/world/agriculture.py`'s own
STANDALONE ON PURPOSE section for why that matters and to whom.
"""
from typing import Optional

from .agriculture import (
    ANNUAL_LABOUR_HOURS_PER_FARM_WORKER,
    DEFAULT_CROP,
    DEFAULT_ROTATION,
    DEFAULT_SOIL,
    DEFAULT_STORAGE_TECHNIQUE,
    DEFAULT_TOOLKIT,
    Crop,
    Rotation,
    Soil,
    StorageTechnique,
    Toolkit,
)
from .agriculture_storage import annual_food_demand_kg_per_person
from .agriculture_yield import Land


def hectares_per_worker_annual_hours_ceiling(
        crop: Optional["Crop"] = None, toolkit: Optional["Toolkit"] = None) -> float:
    """One of the two ceilings on a farm worker's cropped area: total hours
    in the farming year divided by hours needed per hectare. Treating this
    ceiling alone as the answer, ignoring the harvest-window one below,
    produces a 4.8% headline figure - wrong, because the harvest window
    binds first. See `hectares_cropped_per_farm_worker`.

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


def hectares_per_worker_harvest_window_ceiling(
        crop: Optional["Crop"] = None, toolkit: Optional["Toolkit"] = None) -> float:
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


def hectares_cropped_per_farm_worker(
        crop: Optional["Crop"] = None, toolkit: Optional["Toolkit"] = None) -> float:
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


def holding_hectares_required_per_farm_worker(
        crop: Optional["Crop"] = None, toolkit: Optional["Toolkit"] = None,
        rotation: Optional["Rotation"] = None) -> float:
    """How much land the farm must HOLD to keep one worker cropping - the
    cropped area grossed up for the fallow that is idle this year. See the
    ROTATION AND FALLOW section for why this is a land requirement and not
    a reduction in output: fraction_of_population_that_must_farm never
    reads it, deliberately.
    """
    rotation = rotation or DEFAULT_ROTATION
    return (hectares_cropped_per_farm_worker(crop, toolkit)
            / (1.0 - rotation.fallow_share_of_holding))


def fraction_of_population_that_must_farm(
        crop: Optional["Crop"] = None, soil: Optional["Soil"] = None,
        rotation: Optional["Rotation"] = None, toolkit: Optional["Toolkit"] = None,
        storage_technique: Optional["StorageTechnique"] = None) -> float:
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

def farm_workers_fte_for_population(
        adult_equivalent_population: float, crop: Optional["Crop"] = None,
        soil: Optional["Soil"] = None, rotation: Optional["Rotation"] = None,
        toolkit: Optional["Toolkit"] = None,
        storage_technique: Optional["StorageTechnique"] = None) -> float:
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


def farmland_for_population(
        adult_equivalent_population: float, crop: Optional["Crop"] = None,
        soil: Optional["Soil"] = None, rotation: Optional["Rotation"] = None,
        toolkit: Optional["Toolkit"] = None,
        storage_technique: Optional["StorageTechnique"] = None) -> "Land":
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
