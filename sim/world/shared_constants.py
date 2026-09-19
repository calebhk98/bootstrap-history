"""Physical and biological facts that more than one `sim/world/` domain
needs, declared exactly ONCE - so they cannot drift apart the way
`sim/world/land.py` and `sim/world/agriculture.py`'s own copies already had,
silently, before this module existed.

THE INCIDENT THIS MODULE EXISTS FOR. `land.py` needed `agriculture.py`'s
Cobb-Douglas labour-intensity physics (the labour output elasticity and the
reference labour-hours-per-hectare figure it is calibrated against) but is
STANDALONE by design (see land.py's own STANDALONE section) and may not
import `agriculture.py`. The only options were to duplicate the numbers
under new names, which is what happened, or to duplicate the whole
mechanism, which is worse. Duplicating a NUMBER with nothing keeping the two
declarations equal is exactly the failure mode CLAUDE.md's naming section
warns about in the abstract ("the same quantity under two different names")
and this repository had it for real: `LAND_LABOUR_OUTPUT_ELASTICITY` and
`LABOUR_OUTPUT_ELASTICITY` were two independent Python floats that happened
to agree, kept in sync by a code comment and an agent's diligence, not by
anything that would fail a test if either one changed.

WHY A NEW MODULE RATHER THAN PUTTING THESE IN sim/constants.py ITSELF.
sim/constants.py is the DECLARATION REGISTRY - the mechanism (`declare`,
`KINDS`, `burndown`) - and its own docstring gives a considered reason for
declaring numbers beside the formula that uses them rather than centralising
by file: a number moved away from its formula loses the paragraph that
defends it, and two domains sharing one file fight over it. Both of those
reasons argue AGAINST adding actual values to sim/constants.py, but neither
argues against a *different* file for the specific case where a number is
NOT owned by one formula - where it is, by its own nature, the same
physical or biological fact several standalone domains independently need
and none of them is entitled to own. That is what belongs here, and only
that: a constant earns a place in this file by being used (or clearly about
to be used) by more than one `sim/world/` module, not merely by being
important.

WHY sim/world/, NOT sim/. Every constant declared here is a `sim/world/`
domain fact (crop biology, human energy need, farm labour technique) with no
dependence on `sim/engine/`, exactly the boundary the rest of the package
holds - see `sim/world/__init__.py`. Keeping it inside `sim/world/` also
means `sim/tests/test_constants_burndown.py`'s own
`test_every_declaring_module_under_sim_world_is_in_the_list` sweeps this
file automatically the same way it sweeps every other domain file: nobody
has to remember to add it by hand (see that test's own docstring for how
`transport.py` and `military_logistics.py` went missing from the burndown
once already, for exactly that reason).

WHAT MAKES THIS SAFE TO IMPORT FROM A STANDALONE MODULE. This file imports
NOTHING but `sim.constants.declare` - no other `sim/world/` module, no
`sim/engine/` module, nothing from `data/` beyond what a comment cites as a
source. A module that imports only this file therefore gains no new
concurrent-edit exposure beyond what importing `sim.constants` already
carries (every domain file already accepts that): `land.py` importing this
file cannot be broken by a concurrent edit to `agriculture.py`, `demand.py`,
`demography.py` or `military_logistics.py`, because none of them is
upstream of it. This is the same "imports nothing itself" property
`sim.constants` already has for the registry mechanism, extended to actual
values.

WHAT DOES NOT BELONG HERE. A constant used by exactly one module belongs
beside the formula that uses it, in that module, exactly as
`sim/constants.py`'s own docstring argues - moving it here would be the
wrong direction for the same reason moving it to `sim/constants.py` would
be. Only genuinely shared facts belong in this file. As of this module's
creation, `sim/world/demand.py`, `sim/world/demography.py` and
`sim/world/military_logistics.py` each independently redeclare
`SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY` (as
`HUMAN_SUBSISTENCE_CALORIES_PER_CAPITA_DAY`,
`SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY` and
`SEDENTARY_ENERGY_REQUIREMENT_KCAL_PER_DAY` respectively) and/or
`WHEAT_ENERGY_KCAL_PER_KG` (as `WHEAT_ENERGY_KCAL_PER_KG` and
`GRAIN_ENERGY_KCAL_PER_KG`) under their own names, each with its own
"declared again here, deliberately, rather than imported" paragraph. Those
files are out of this task's ownership (see CLAUDE.md's own "own ONLY"
convention for a scoped task) and are NOT migrated to this module by this
change - `sim/tests/test_shared_constants.py`'s
`CrossModuleQuantityEquivalenceTests` instead asserts their declared values
still agree with this module's, so a future drift in any of them fails
loudly even before anyone gets around to pointing them at this file
directly.

HOW A CONSUMER USES ONE OF THESE. Import the value under its OWN local
name, exactly as any other declared constant is used - there is no special
API. `sim/world/land.py` and `sim/world/agriculture.py` both do this for
every constant below; see either one's own comment at the import for the
convention (a module keeps its historical public attribute name, e.g.
`agriculture.LABOUR_OUTPUT_ELASTICITY`, but that name is now an alias for
this module's single declaration rather than a second `declare()` call, so
there is exactly one place delivering the value and no way for a second
copy to exist to drift from it).
"""
from sim.constants import declare

# ============================================================================
# HUMAN FOOD ENERGY
# ============================================================================

SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY = declare(
    "SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY", 2200.0,
    kind="biological_parameter",
    unit="kcal/adult/day",
    source="FAO minimum dietary energy requirement, adult average. Formerly "
           "declared independently, under independent names, by "
           "sim/world/land.py (LAND_HUMAN_CALORIC_NEED_KCAL_PER_DAY) and "
           "sim/world/agriculture.py "
           "(HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY); both now import "
           "this declaration instead of re-declaring it. "
           "sim/world/demand.py, sim/world/demography.py and "
           "sim/world/military_logistics.py still declare the same figure "
           "under their own names (HUMAN_SUBSISTENCE_CALORIES_PER_CAPITA_"
           "DAY, SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY and "
           "SEDENTARY_ENERGY_REQUIREMENT_KCAL_PER_DAY) - out of this "
           "change's ownership, but checked against this value by "
           "sim/tests/test_shared_constants.py so a future drift there "
           "still fails loudly.",
    confidence="B",
    why="How much food energy a person needs before their labour can do "
        "anything else - the single number every food-and-population "
        "domain in this project ultimately measures land, labour and "
        "calories against. One declaration means one number to defend and "
        "one place a change in the underlying dietary-requirement estimate "
        "would need to be made.")

WHEAT_ENERGY_KCAL_PER_KG = declare(
    "WHEAT_ENERGY_KCAL_PER_KG", 3400.0,
    kind="biological_parameter",
    unit="kcal/kg of threshed whole wheat grain",
    source="Standard food-composition figures for whole wheat grain (on "
           "the order of 3,300-3,400 kcal/kg). Formerly declared "
           "independently, under the SAME name, by sim/world/land.py and "
           "sim/world/agriculture.py (and, under the name "
           "GRAIN_ENERGY_KCAL_PER_KG, by sim/world/military_logistics.py, "
           "and again under this exact name by sim/world/demand.py - "
           "neither migrated by this change; see this module's own WHAT "
           "DOES NOT BELONG HERE section).",
    confidence="B",
    why="Turns a caloric requirement into a mass of grain - the unit both "
        "land.py's regional yields and agriculture.py's harvest arithmetic "
        "are already stated in.")

# ============================================================================
# FARM LABOUR AND TECHNIQUE - the Cobb-Douglas anchor
# ============================================================================
# These three numbers are what land.py's own LABOUR INTENSITY section
# duplicated from agriculture.py to build the SAME diminishing-returns curve
# (output scales with labour_hours ** LABOUR_OUTPUT_ELASTICITY, anchored to
# reproduce the reference yield at the reference labour intensity) on a
# per-iugerum basis without importing agriculture.py itself. See land.py's
# own module docstring, LABOUR INTENSITY section, for the physics; this is
# now the one place that physics's own numbers live.

REFERENCE_LABOUR_HOURS_PER_HECTARE = declare(
    "REFERENCE_LABOUR_HOURS_PER_HECTARE", 150.0,
    kind="engineering_estimate",
    unit="labourer-hours/hectare/season, at the reference (quality-1.0, "
         "fold-return-4.5) wheat yield",
    source="data/production/40_organics.json wheat_kg entry, "
           "labour_hours.labourer: cross-ploughing, broadcast sowing, "
           "weeding, sickle reaping and threshing/winnowing aggregated to "
           "about 150 hours/ha. Formerly declared independently, under "
           "independent names, by sim/world/agriculture.py "
           "(REFERENCE_LABOUR_HOURS_PER_HECTARE) and sim/world/land.py "
           "(LAND_REFERENCE_LABOUR_HOURS_PER_HECTARE); both now import "
           "this declaration. sim/world/labour_market.py used to repeat the "
           "figure twice as a bare literal (150.0), recorded here as an "
           "outstanding finding because it was outside that change's "
           "ownership; it now imports this declaration too, so all four "
           "sites are one number.",
    confidence="B",
    why="The labour intensity the reference yield is quoted at, and the "
        "anchor every Cobb-Douglas yield curve in either consuming module "
        "is calibrated to reproduce exactly at that one point.")

LABOUR_OUTPUT_ELASTICITY = declare(
    "LABOUR_OUTPUT_ELASTICITY", 0.5,
    kind="temporary_heuristic",
    unit="dimensionless (Cobb-Douglas exponent on labour)",
    source="Agricultural-economics estimates of labour's output elasticity "
           "typically fall in the 0.3-0.6 range; 0.5 (output scales with "
           "the square root of labour hours) is the midpoint of that "
           "range, not a number derived for any crop or region this "
           "project prices specifically. Formerly declared independently, "
           "under independent names, by sim/world/agriculture.py "
           "(LABOUR_OUTPUT_ELASTICITY) and sim/world/land.py "
           "(LAND_LABOUR_OUTPUT_ELASTICITY) - the exact pair of "
           "declarations that prompted this module's creation, per "
           "Complaints/46 and the task that produced this file.",
    confidence="C",
    why="The curve shape that makes doubling labour on fixed land yield "
        "less than double the output - the whole mechanism behind "
        "diminishing returns to labour intensity in both land.py and "
        "agriculture.py. The two modules use this identical curve for two "
        "different purposes (agriculture.py's headline farm-population "
        "calibration; land.py's intensive-margin land rent) and both "
        "purposes silently assume the SAME elasticity describes the SAME "
        "physical crop - a good reason for them to share one declaration "
        "rather than two that happen to agree.")

ANNUAL_LABOUR_HOURS_PER_FARM_WORKER = declare(
    "ANNUAL_LABOUR_HOURS_PER_FARM_WORKER", 1400.0,
    kind="temporary_heuristic",
    unit="hours/worker/year",
    source="1,200-1,500 hours/year is the rough order of magnitude "
           "historical agricultural-labour estimates give for a seasonal "
           "farm calendar (bursts at ploughing, sowing and harvest, slack "
           "in between); 1,400 is a round midpoint, not a figure sourced "
           "to any one civilization this project prices. Formerly "
           "declared independently, under independent names, by "
           "sim/world/agriculture.py (ANNUAL_LABOUR_HOURS_PER_FARM_WORKER) "
           "and sim/world/land.py "
           "(LAND_ANNUAL_LABOUR_HOURS_PER_FARM_WORKER).",
    confidence="C",
    why="How many hours one adult can give to field work across a year - "
        "agriculture.py uses it (against REFERENCE_LABOUR_HOURS_PER_"
        "HECTARE) as one of two competing ceilings on hectares cropped per "
        "worker; land.py uses it (against LAND_AGRARIAN_POPULATION_SHARE, "
        "which stays local to land.py - see that constant's own "
        "declaration for why it is not also shared) to convert a whole "
        "population into a civilization-wide labour-hours supply.")

# ============================================================================
# WEATHER SPATIAL CORRELATION - Complaints/50-one-label-draws-one-coin.md
# ============================================================================
# How far apart two points on the ground have to be before one year's
# growing-season weather at one stops predicting the other's. This is the
# ONE number sim/engine/core.py's per-cell pooled harvest weather (WIRING
# THREE) turns on: it is what tells Gaul and Hispania (close, correlated)
# apart from Britannia and Mesopotamia (far, nearly independent), replacing
# the two assumptions Complaints/50 measured as both wrong in the same
# direction - a region record is one weather system, and two region records
# draw independently. Declared here, not in sim/world/agriculture.py (which
# already owns WEATHER_YIELD_STDEV_FRACTION and the clip bounds this same
# mechanism also reads), because this task's own ownership boundary is
# sim/engine/core.py and sim/world/shared_constants.py, not agriculture.py -
# see CLAUDE.md's own "own ONLY" convention. It is nonetheless a genuine
# sim/world/ climate fact, not an engine heuristic, so it belongs in this
# file's registry rather than as a bare literal in core.py.

GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM = declare(
    "GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM", 600.0,
    kind="physical_constant",
    unit="km (e-folding distance of an exponential spatial correlation "
         "kernel: correlation between two points = exp(-distance / this))",
    source="NOT a single citable figure for the exact quantity this "
           "constant stands for - the correlation length of a full GROWING "
           "SEASON's cumulative weather anomaly, at a pre-industrial "
           "regional scale. No study measuring that exact quantity was "
           "found, and this value is not presented as one; it is chained "
           "from three narrower, real figures instead. (1) DAILY "
           "precipitation fields: published global correlation-length "
           "analyses of gauge/satellite precipitation datasets put the "
           "mean e-folding distance at roughly 250-300 km over land "
           "(order 262 km land mean, order 281 km land median, 10th-90th "
           "percentile roughly 145-342 km). (2) SEASONAL-to-decadal "
           "precipitation TOTALS decorrelate over a longer distance than "
           "single days do, because summing a season averages out the "
           "day-to-day passage of individual storms and leaves the "
           "slower, larger-scale circulation regime that steered them; "
           "regional studies of monthly-to-decadal precipitation report "
           "correlation lengths on the order of 500-700 km. (3) Synoptic "
           "meteorology's own characteristic scale for the weather "
           "systems (mid-latitude frontal cyclones and their rain bands) "
           "that a growing season is built out of is of order 1,000 km "
           "(the mid-latitude Rossby radius of deformation and the "
           "synoptic wavelength are both this order of magnitude). This "
           "constant is set at figure (2), a season-scale total - the "
           "quantity a harvest actually integrates over - sitting below "
           "the full synoptic wavelength of (3) because a season's "
           "cumulative anomaly still decorrelates faster than the single "
           "largest circulation pattern that produced any one part of "
           "it. Sourced from open-web search of the spatial-statistics "
           "and precipitation-dataset literature during this task, not "
           "from a specific paper kept on file - see this task's own "
           "report for the search queries used and what they returned.",
    confidence="D",
    why="The single number that separates a compact, correlated empire "
        "(Gaul and Hispania, which growing-season weather should mostly "
        "agree between) from a spread-out, decorrelated one (Britannia "
        "and Mesopotamia, which it should not) - see sim/engine/core.py's "
        "_compute_farm_weather_cells and _pooled_farm_weather_multiplier, "
        "which this feeds, and this task's own report for a sensitivity "
        "sweep across the roughly 150-1,500 km range this docstring's own "
        "chain of reasoning spans, rather than trusting this one point "
        "estimate alone.")

# ============================================================================
# LAND USE - fallow
# ============================================================================
# THE HARD CASE THIS MODULE IS ALSO FOR. Unlike the constants above, which
# were duplicated under different NAMES but the same VALUE and the same
# UNITS, this one was duplicated under a different name, a different value
# AND a different unit that happen to describe the same physical fact from
# two directions: agriculture.py's FALLOW_SHARE_OF_HOLDING (0.5, the
# fraction of a holding idle in any one year) and land.py's own former
# FALLOW_HOLDING_MULTIPLIER (2.0, holding hectares per CROPPED hectare) are
# related by holding_multiplier = 1 / (1 - fallow_share) - algebraically
# forced to agree if the two-field rotation is exactly a 50/50 split, but
# nothing checked that before this module existed, and a change to one
# (e.g. modelling a partial fallow, or three-field rotation's 1/3 share)
# would have had to be remembered and reapplied to the other by hand. This
# is the case CLAUDE.md's naming section calls the hard one: "the same
# quantity under two different names," not merely the same name twice.

FALLOW_SHARE_OF_HOLDING = declare(
    "FALLOW_SHARE_OF_HOLDING", 0.5,
    kind="engineering_estimate",
    unit="fraction of holding idle in any one year (dimensionless)",
    source="The two-field rotation - one year cropped, one year bare "
           "fallow - is the standard Mediterranean practice of this "
           "period, named in data/production/40_organics.json's wheat_kg "
           "yield_basis. Formerly declared independently by "
           "sim/world/agriculture.py under this exact name; land.py's own "
           "FALLOW_HOLDING_MULTIPLIER (holding hectares per cropped "
           "hectare, = 1 / (1 - this)) is now DERIVED arithmetic from this "
           "single declaration instead of a second, independently-set "
           "number - see land.py's own comment at that assignment.",
    confidence="B",
    why="Converts cropped area into the land a farm must actually hold. "
        "The later three-field rotation drops the idle share to one "
        "third, which is why this is a property of the TECHNIQUE (an "
        "agricultural improvement should be able to change it) rather "
        "than a constant of nature - see agriculture.py's own "
        "THREE_FIELD_FALLOW_SHARE_OF_HOLDING for exactly that improved "
        "case, declared separately because it names a DIFFERENT "
        "technique's own share, not a duplicate of this one.")
