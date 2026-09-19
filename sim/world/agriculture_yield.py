"""The production function: how much land, labour, weather and technique
turn into a harvest, and the marginal value of one more hour on it.

Split out of `sim/world/agriculture.py`, which had grown to 2,238 lines and
was the single file every agent touching farming had to collide in. See that
file's own docstring, "THIS FILE AND ITS SIBLINGS, AND WHY THIS SPLIT LOOKS
DIFFERENT", for why the split lands here rather than by line count. This
module holds the YIELD subject: `Land` (a parcel, its size and its quality),
one year's weather as a single multiplicative draw, the harvest-window
helpers that turn a labour pool into the area a crew can actually reap in a
season, `gross_harvest_kg` (the Cobb-Douglas production function itself,
capped at what the harvest window lets the labour pool bring in), and
`marginal_product_of_labour_kg_per_hour` (the closed-form derivative of that
same function, which is what a labour market needs to price the last hour of
farm work against everything else).

STANDALONE THE SAME WAY THE PARENT MODULE IS. Nothing here imports from
`sim/engine/`; the only imports besides the standard library are from
`sim.world.agriculture` itself, for the declared constants and the
Crop/Toolkit/Rotation tables this module's functions take as optional
arguments - see `sim/world/agriculture.py`'s own STANDALONE ON PURPOSE
section for why that matters and to whom.

Behaviour is unchanged and verified byte-identical by `sim/perf_fingerprint.
py`; every docstring below moved verbatim from where it used to live in
`sim/world/agriculture.py`.
"""
import random
from typing import Optional

from .agriculture import (
    ANNUAL_LABOUR_HOURS_PER_FARM_WORKER,
    DEFAULT_CROP,
    DEFAULT_ROTATION,
    DEFAULT_TOOLKIT,
    HARVEST_WORKING_DAY_HOURS,
    HOURS_PER_DAY,
    LABOUR_OUTPUT_ELASTICITY,
    WEATHER_CEILING_MULTIPLIER,
    WEATHER_FLOOR_MULTIPLIER,
    WEATHER_YIELD_STDEV_FRACTION,
    Crop,
    Rotation,
    Toolkit,
)
# `hectares_cropped_per_farm_worker` is NOT imported up here at module level.
# It lives in sim/world/agriculture_labour.py, which itself imports `Land`
# from THIS module at ITS own top level - a top-level import in both
# directions would be a genuine circular import between two sibling modules,
# unlike sim/world/agriculture.py's own composition-point imports, which are
# safe only because they run against a PARENT module that is merely
# mid-execution, not two siblings each waiting on the other to finish.
# `_max_hectares_harvestable_by_labour` below imports it locally, at call
# time, once - see that function's own comment at the one line that needs it.


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

    def __init__(self, hectares: float, quality: float = 1.0) -> None:
        if hectares < 0:
            raise ValueError("hectares cannot be negative: %r" % (hectares,))
        if quality <= 0:
            raise ValueError("quality must be positive: %r" % (quality,))
        self.hectares = float(hectares)
        self.quality = float(quality)

    def __repr__(self) -> str:
        return "Land(hectares=%.4f, quality=%.4f)" % (self.hectares, self.quality)


def draw_weather_multiplier(
        rng: random.Random,
        weather_stdev_fraction: float = WEATHER_YIELD_STDEV_FRACTION) -> float:
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


def _max_hectares_harvestable_by_labour(
        labour_hours: float, crop: "Crop", toolkit: "Toolkit",
        worker_count: Optional[float] = None,
        hours_per_worker_day: Optional[float] = None) -> float:
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
    # LOCAL IMPORT, ON PURPOSE - see this file's own top-of-file comment on
    # why: sim/world/agriculture_labour.py (where hectares_cropped_per_farm_
    # worker lives) imports Land from this module at ITS top level, so a
    # top-level import here in the other direction would be a real circular
    # import between two sibling files. Deferred to call time instead, by
    # which point sim/world/agriculture.py's own composition-point imports
    # have already finished loading both modules in full, so this is an
    # ordinary, already-cached module lookup, not a fresh import.
    from .agriculture_labour import hectares_cropped_per_farm_worker
    worker_equivalents = labour_hours / ANNUAL_LABOUR_HOURS_PER_FARM_WORKER
    return worker_equivalents * hectares_cropped_per_farm_worker(crop, toolkit)


def hectares_reaped_per_worker_hour(
        crop: Optional["Crop"] = None, toolkit: Optional["Toolkit"] = None) -> float:
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


def max_hectares_reapable_by_crew(
        worker_count: float, hours_per_worker_day: Optional[float] = None,
        crop: Optional["Crop"] = None, toolkit: Optional["Toolkit"] = None) -> float:
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


def gross_harvest_kg(
        land: "Land", labour_hours: float, technique_multiplier: float = 1.0,
        weather_multiplier: float = 1.0, crop: Optional["Crop"] = None,
        toolkit: Optional["Toolkit"] = None, rotation: Optional["Rotation"] = None,
        worker_count: Optional[float] = None,
        hours_per_worker_day: Optional[float] = None) -> float:
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


def marginal_product_of_labour_kg_per_hour(
        land: "Land", labour_hours: float, technique_multiplier: float = 1.0,
        weather_multiplier: float = 1.0, crop: Optional["Crop"] = None,
        toolkit: Optional["Toolkit"] = None, rotation: Optional["Rotation"] = None,
        worker_count: Optional[float] = None,
        hours_per_worker_day: Optional[float] = None) -> float:
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
