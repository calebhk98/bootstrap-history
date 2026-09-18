"""Ricardian rent on ARABLE LAND: why a field is not priced like a mine.

WHAT THIS IS FOR. Complaints/43 measured `iugerum_land` solving to exactly
0.0 in `sim/solve_prices.py`: land has no cost of production (its own
`data/production/40_organics.json` entry says so directly - "essentially no
labour... a rent set by the worst iugerum still worth taking"), and rent on
every extracted material used to be fixed at zero, so land came out free.
`sim/world/deposits.py` fixed this for six ORES this same round, but a mine
and a field are not the same physical object and do not want the same
mechanism: a mine's marginal unit is set by GRADE, which falls as a deposit
is worked out (the intensive margin) or exhausted outright (the extensive
margin, moving to the next deposit). A field does not deplete - the same
iugerum grows wheat next year exactly as well as this year - so there is no
grade to fall and nothing to exhaust. What varies between one iugerum and
another is LOCATION and FERTILITY, fixed at the start and not consumed by
use, and the margin that sets land's price is the worst LAND actually
needed to feed however many people are drawing on it, not the worst DEPOSIT
actually needed to meet a metal quota. This module is that mechanism.

THE STAKEHOLDER'S FRAMING, which this module is built to fit rather than
adapt afterwards: land belongs under geography (not floating free the way
`iugerum_land` used to), it must be PER-CIVILISATION and CHANGEABLE (China
has more of it than Europe, Rome's is better growing ground than the
Norse's, and a civilisation that wins a war holds more of it), and mines
should ride on the same territory (you can hold a lot of land and still
have no coal - `sim/world/deposits.py`'s own regional shares already do
this for ore; this module does the equivalent for the ground itself).

WHERE THE PHYSICAL FACTS COME FROM, AND WHAT THEY ARE NOT. Every region in
`data/world/geography.json` now carries a `land` block: `land_area_km2`
(the region's real, coarse land area), `arable_fraction` (the share of that
area physically capable of supporting pre-industrial rain-fed or simple-
irrigation farming - a terrain and climate fact, not a fact about who
farms it today) and `fertility_quality_multiplier` (a yield multiplier on
the arable share, 1.0 being `data/production/40_organics.json`'s own
Roman-Italian wheat_kg baseline - see REFERENCE_WHEAT_YIELD_KG_PER_HECTARE
below). These are COUNTRY-SCALE APPROXIMATIONS from general, well-attested
geography (how big the region roughly is; whether the ground is desert,
rainforest, steppe, floodplain or ordinary temperate farmland) — a stand-in
for a real per-region soil and land-cover survey this project does not
have, exactly the kind of heuristic CLAUDE.md SS3.4 asks to be labelled
rather than hidden. Every one of the 21 real regions is declared confidence
D except `italia`, confidence C, because Italia's own fertility figure is
not an estimate at all: it is DEFINED as 1.0, because that is the ground
`wheat_kg`'s own 577.5 kg/ha net figure already describes. Nothing here is
tuned so a computed price matches `data/prices.json`'s 250-denarii book
figure for `iugerum_land` - see this module's own `_declare_land_area`,
`_declare_arable_fraction` and `_declare_fertility` for the discipline
`sim/world/deposits.py`'s own `_declare_grade` already applies to ore.

THE SAME UNIT `sim/world/agriculture.py` ALREADY USES, ON PURPOSE.
`sim/world/agriculture.py`'s own `Land(hectares, quality=...)` already
carries "a plain multiplier on yield, 1.0 being the 'decent land' baseline
data/production/40_organics.json's own wheat entry describes" - see that
class's own docstring, which also names the EXTENSIVE MARGIN (bringing
worse land under the plough as demand grows) as the reason `quality` lives
on the land rather than being folded into one society-wide yield number.
`fertility_quality_multiplier` here is exactly that same multiplier, in
the same units, anchored at the same place (Italia = 1.0). This is
deliberate, not a coincidence of two authors picking the same round number:
a later module that wants to hand agriculture.py's demography/food loop a
real, geography-driven `Land(hectares, quality=region.fertility_quality_
multiplier)` instead of a flat 1.0 needs no unit conversion and no rename
to do it - see WHAT A LATER CONQUEST MECHANISM WOULD TOUCH below for
exactly where that wiring would go. THIS MODULE DOES NOT DO THAT WIRING
ITSELF: nothing here imports `sim.world.agriculture` (see STANDALONE below),
and no caller in this round hands agriculture.py this number.

THE MECHANISM, IN ORDER.

  1. TERRITORY. `cultivable_land_for_civilization` reads one civilization's
     `home_regions` (already a plain list of `data/world/geography.json`
     region keys, in every `data/civilizations/*.json` file - Rome holds
     seven, Han China and the Norse each hold exactly one) and returns that
     civilization's own list of region-parcels: name, arable iugera, and
     fertility. THIS IS WHERE "PER-CIVILISATION AND CHANGEABLE" LIVES. Two
     civilizations that hold the same `home_regions` list get the same
     land; a civilization that holds more, or better, regions gets more or
     better land, with no other code path involved.

  2. QUANTITY DEMANDED. Exactly like `sim/world/deposits.py`'s own metal
     quantity, this project has no closed food-demand system yet, so this
     is a parameter, not something this module invents from a price -
     see DEMAND IS A PARAMETER below for what stands in for it this round
     and why it is population, not a constant, this time (a civilization's
     own population is a real INITIAL CONDITION already sitting in its own
     file, per CLAUDE.md SS3.1 - not a fixed empire-wide figure the way
     `sim/world/deposits.py` currently has to use for every civilization
     alike, which is a limitation of THAT module this one does not need to
     repeat).

  3. THE MARGIN OF CULTIVATION. `find_margin_of_cultivation` sorts a
     civilization's region-parcels BEST FERTILITY FIRST (the opposite
     order from `sim/world/deposits.py`'s cheapest-cost-first, because
     fertility and cost run in opposite directions: the best land is the
     CHEAPEST source of a kilogram of grain, not the dearest) and fills
     quantity demanded from the best parcel down. The parcel where that
     fill completes is marginal; every parcel strictly better than it is
     fully worked and earns rent; every parcel worse is not worked at all
     this round (uncultivated frontier, not a bug - see
     `sim/world/deposits.py`'s own `unmet_demand` reasoning for the sibling
     case, "demand exceeds every given source's combined capacity", which
     this module reports the same way if a civilization's own territory
     cannot feed its own stated population).

  4. RENT, per iugerum: a parcel's fertility surplus over the margin's own
     fertility, multiplied by the reference yield a decent (quality-1.0)
     iugerum produces - the SAME "yield of the best land minus yield of the
     marginal land, valued at the market price of the crop" Ricardo's own
     argument makes, just read off a coarse 21-region ranking instead of
     an English parish's own field-by-field one. `rent_hours_per_iugerum`
     (in `sim/solve_prices.py`, not here - see WHY THE HOURS CONVERSION
     LIVES IN solve_prices.py, NOT HERE below) turns the physical surplus
     this module returns (kilograms of grain-equivalent per iugerum) into
     the solver's own labour-hour price unit, using wheat_kg's own
     zero-rent price - exactly the ratio `sim/world/deposits.py`'s own
     `rent_hours_per_kg_by_ore_material` uses an ore's zero-rent recipe
     price for.

WHY A CIVILIZATION'S PRICE IS THE SUPPLY-WEIGHTED AVERAGE ACROSS ITS OWN
REGIONS, NOT THE MARGIN'S OWN RENT (WHICH IS ZERO BY DEFINITION). Ore's
single reported price ends up EXACTLY the marginal deposit's own cost (see
`sim/world/deposits.py`'s `find_marginal_deposit` and `sim/solve_prices.py`'s
`rent_hours_per_kg_by_ore_material` docstring for the algebra) because
extracting ore genuinely costs labour even at the margin, so "price equals
marginal cost" is a real, nonzero number. Land's cost of "production" is
genuinely near zero EVEN AT THE MARGIN (marking a boundary costs a scribe
minutes, per `iugerum_land`'s own `yield_basis`), so copying ore's algebra
literally would reproduce Complaints/43's own zero. What land actually has
that a kilogram of homogeneous ore does not is a MARKET made of parcels of
DIFFERENT quality trading at DIFFERENT rents simultaneously - a chernozem
field and a stony hillside are not the same price even though both are
called "land" - so the one number this module hands back for a whole
civilization is deliberately an AVERAGE over the parcels actually being
worked (weighted by how much of each is actually needed to meet quantity
demanded - the SAME `quantity_supplied` bookkeeping
`sim/world/deposits.py`'s own `Allocation` already keeps, so a parcel
priced in but not reached contributes zero weight, not zero price to a
nonzero weight). A CIVILIZATION HOLDING ONLY ONE REGION THEREFORE PRICES
LAND AT EXACTLY ZERO THIS ROUND, AND THAT IS A FINDING, NOT A BUG - see
Han China and the Norse in this module's own `--why`-style report and the
task's own write-up for what it says about why a civilization wants
varied territory, not merely more of it.

DEMAND IS A PARAMETER, EXACTLY LIKE sim/world/deposits.py'S OWN, BUT A
DIFFERENT ONE. `quantity_demanded_kg_grain_equivalent` needs three
independent, physically-grounded numbers, none of them tuned to make any
particular civilization's price come out anywhere in particular:

  - a caloric requirement per person per year (a biological fact),
  - wheat's own calorie density (a biological fact, used only to turn the
    first number into a mass of grain - the same single-staple
    simplification `sim/world/agriculture.py`'s own `annual_food_demand_
    kg_per_person` already documents and, per that function's own
    docstring, UNDERSTATES real land need because grain is the highest-
    yield-per-hectare calorie source a real diet is not exclusively made
    of),
  - and two multipliers that correct for exactly that understatement and
    for the fact a cropped hectare is not a held one: FALLOW_HOLDING_
    MULTIPLIER (a two-field-rotation holding is about twice its cropped
    area every year, per `data/production/40_organics.json`'s own
    wheat_kg `basis` note) and DIET_DIVERSITY_LAND_MULTIPLIER (a
    TEMPORARY HEURISTIC standing in for the land a non-grain diet - oil,
    wine, legumes, pasture for draught and dairy animals - needs beyond
    grain calories alone, which this single-crop module cannot derive
    without a real multi-crop diet model).

Multiply these together against a civilization's own population and the
result is a kilogram figure this module's margin-finder can compare
directly against each region's own grain-equivalent output capacity. TAG:
TEMPORARY HEURISTIC (CLAUDE.md SS3.4) on the whole quantity - the day a
real, closed food-demand system exists (this project's own architecture
notes name `sim/world/agriculture.py` and `sim/world/demography.py` as
where it would live), THIS is the one function that changes, and every
region's own rent computation downstream of it is already wired to take
whatever number it produces, exactly the promise `sim/world/deposits.py`'s
own docstring makes for its sibling parameter.

WHY THE HOURS CONVERSION LIVES IN sim/solve_prices.py, NOT HERE.
`sim/world/deposits.py` never imports `data/production/`'s own recipe data
and never computes a labour-hours price - `sim/solve_prices.py`'s own
`rent_hours_per_kg_by_ore_material` does that conversion, reading
`production_entries` and `wage_by_trade` this module has never heard of.
This module follows the identical split for the identical reason (see
`sim/world/deposits.py`'s own STANDALONE section: nothing here imports
`sim.engine`, `sim.solve_prices` or any other `sim.world` module, so a
concurrent edit to `data/production/`, `sim/world/agriculture.py` or
`sim/world/demography.py` - all owned by other agents as this module is
written - cannot break this one or be broken by it). Every function below
that needs a reference yield takes it as an explicit argument, defaulting
to REFERENCE_WHEAT_YIELD_KG_PER_HECTARE (duplicated from `data/production/
40_organics.json`'s own wheat_kg entry rather than imported, for the same
concurrency reason - see that constant's own declaration for what happens
if the two numbers drift, which is a visible finding for a future
reconciliation pass, not a bug in either file).

WHAT A LATER CONQUEST MECHANISM WOULD HAVE TO TOUCH. Nothing in this
module treats `home_regions` as fixed - `cultivable_land_for_civilization`
re-reads it fresh every call, straight off the civilization dict handed
in or loaded from disk, and does no caching keyed on a civilization id
across calls. A conquest mechanism therefore needs to do exactly one
thing this module does not already do: PERSIST a change to some
civilization's own list of held regions somewhere a save can round-trip
(this project's `SAVE_FIELDS` mechanism, per CLAUDE.md SS3.5 - a plain
list of region-key strings is about as simple a field as that mechanism
ever has to carry). It does NOT need to touch this module, `sim/solve_
prices.py`'s land-rent wiring, or `data/world/geography.json` at all:
call `cultivable_land_for_civilization` (or `land_rent_hours_per_iugerum`
in `sim/solve_prices.py`) again with the updated list and every number
downstream - endowment, margin, rent, price - updates with no further
change, because "the regions a civilization holds" was never anything
more than a plain list this module reads, never a constant it assumes.
The one thing this round deliberately does NOT do is give `Sim` (or
whatever engine object eventually represents a civilization mid-game) a
live, mutable `home_regions` of its own - `data/civilizations/*.json`
today is a fixed STARTING file, read once at solve time via `--civ`, not
state the engine carries and changes turn to turn. Wiring a real conquest
EVENT (an army wins a war, a region changes hands) therefore also needs
somewhere in `sim/engine/` to hold and mutate that per-civilization region
list at runtime - out of this module's ownership and this round's scope,
and exactly the boundary CLAUDE.md's own "own ONLY" instruction for this
task draws.

WHAT THIS MODULE DELIBERATELY DOES NOT DO.

  - No intra-region heterogeneity. `sim/world/deposits.py` lists several
    NAMED deposits per metal at different grades; this module treats each
    of the 21 regions as ONE parcel at ONE fertility, per the task's own
    "22 regions is the right grain" instruction. This is exactly why a
    civilization holding only one region prices land at zero this round
    (see above) - the finer grain a real within-region soil survey would
    need is future work, not a defect in the mechanism.
  - No transport friction between regions. A civilization's whole
    population is priced against its whole territory as one pooled land
    market, the same simplification `sim/world/deposits.py` already makes
    for a whole empire's ore demand against its whole territory's
    deposits. Real grain was expensive to move in bulk before rail, which
    this project already represents elsewhere (freight distance in
    `sim/engine/economy.py`) but not here.
  - No depletion, no intensive margin, no capital (irrigation works,
    drainage, forest clearance) that would raise a parcel's own fertility
    over time. Land does not run out the way an ore body does - that is
    this module's entire reason for existing rather than reusing
    `sim/world/deposits.py` outright - but real land quality is not
    actually fixed forever either; treating `fertility_quality_multiplier`
    as a constant per region is a simplification, not a claim that
    fertility cannot be raised (or ruined) by what is done to it.
  - No feedback from land rent into wheat_kg's own price, or into any
    other `extracted_from: "arable land"` material's price (wheat, wool,
    linen, olive oil - see `data/production/40_organics.json`'s own
    `_note`). `iugerum_land` is not consumed as an `inputs` entry by any
    of them today, so there is no structural link for rent to travel
    along even if this module wanted to send it - see `sim/solve_prices.py`
    for where that wiring, if it existed, would need to attach.
"""
import collections
import json
import os

from sim.constants import declare

# ============================================================================
# DATA FILE LOCATIONS - same pattern as sim/world/deposits.py's own, for the
# same STANDALONE reason (see the module docstring).
# ============================================================================

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
GEOGRAPHY_FILE = os.path.join(_ROOT, "data", "world", "geography.json")
CIVILIZATIONS_DIR = os.path.join(_ROOT, "data", "civilizations")


# ============================================================================
# THE REFERENCE YIELD - what a decent (quality 1.0) iugerum produces
# ============================================================================

IUGERUM_HECTARES = declare(
    "IUGERUM_HECTARES", 0.2523,
    kind="physical_constant",
    unit="hectares/iugerum",
    source="The Roman iugerum (240 x 120 Roman feet) - the same conversion "
           "data/production/40_organics.json's own iugerum_land entry "
           "already states; duplicated here rather than imported, per this "
           "module's own STANDALONE section.",
    confidence="B",
    why="Every area this module works in is stated per iugerum, to match "
        "`iugerum_land` itself; every physical yield fact available to it "
        "(wheat_kg's own 577.5 kg/ha) is stated per hectare, so this "
        "conversion is load-bearing on every call.")

REFERENCE_WHEAT_YIELD_KG_PER_HECTARE = declare(
    "REFERENCE_WHEAT_YIELD_KG_PER_HECTARE", 577.5,
    kind="engineering_estimate",
    unit="kg threshed grain/hectare/season, net of seed corn, at fertility_"
         "quality_multiplier 1.0",
    source="data/production/40_organics.json's own wheat_kg entry - "
           "Columella's ~4.5-fold return on a 165 kg/ha seeding rate for "
           "ancient Mediterranean dry farming. Duplicated here rather than "
           "imported, per this module's own STANDALONE section - if the "
           "two numbers ever drift apart that is a visible finding for a "
           "future reconciliation pass, not a bug in either file.",
    confidence="B",
    why="This is the yield fertility_quality_multiplier is a multiplier ON, "
        "and the anchor that makes Italia's own multiplier exactly 1.0 by "
        "construction rather than by estimate - see the module docstring.")


def reference_yield_kg_per_iugerum(fertility_quality_multiplier,
                                   kg_per_hectare_at_quality_1=None,
                                   iugerum_hectares=None):
    """Kilograms of grain-equivalent one iugerum at this fertility produces
    in a season, net of seed - the physical quantity every rent
    calculation in this module bottoms out in. Takes both reference
    figures as optional explicit arguments (defaulting to this module's own
    declared constants) so a caller with the LIVE `wheat_kg` yield in hand
    - `sim/solve_prices.py`, which already loaded `data/production/` for
    other reasons - can pass it instead of relying on this module's own
    duplicate staying in sync; see the module docstring's WHY THE HOURS
    CONVERSION LIVES IN sim/solve_prices.py section.
    """
    kg_per_hectare_at_quality_1 = (
        REFERENCE_WHEAT_YIELD_KG_PER_HECTARE if kg_per_hectare_at_quality_1 is None
        else kg_per_hectare_at_quality_1)
    iugerum_hectares = IUGERUM_HECTARES if iugerum_hectares is None else iugerum_hectares
    return kg_per_hectare_at_quality_1 * iugerum_hectares * fertility_quality_multiplier


# ============================================================================
# QUANTITY DEMANDED - see the module docstring's own DEMAND IS A PARAMETER
# section for what each of these stands for and why none of them is tuned
# to any civilization's outcome.
# ============================================================================

LAND_HUMAN_CALORIC_NEED_KCAL_PER_DAY = declare(
    "LAND_HUMAN_CALORIC_NEED_KCAL_PER_DAY", 2200.0,
    kind="biological_parameter",
    unit="kcal/person/day",
    source="FAO minimum dietary energy requirement, adult average - the "
           "same figure sim/world/demand.py's own HUMAN_SUBSISTENCE_"
           "CALORIES_PER_CAPITA_DAY, sim/world/agriculture.py's own HUMAN_"
           "ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY and sim/world/"
           "demography.py's SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY "
           "all already use. Declared again here under its own, LAND_-"
           "prefixed name rather than imported, per this module's own "
           "STANDALONE section (see sim/world/demand.py's own HUMAN_"
           "SUBSISTENCE_CALORIES_PER_CAPITA_DAY declaration for the exact "
           "same reasoning applied there first) - `declare()` shares one "
           "registry keyed by name, so re-using the SAME name across "
           "independent modules with a DIFFERENT value fails loudly at "
           "import time, and re-using it with the SAME value would still "
           "leave the two modules coupled to a name neither owns.",
    confidence="B",
    why="Sets how much grain-equivalent a population needs before this "
        "module can say how much land that requires - see WHEAT_ENERGY_"
        "KCAL_PER_KG for the other half of that conversion.")

WHEAT_ENERGY_KCAL_PER_KG = declare(
    "WHEAT_ENERGY_KCAL_PER_KG", 3400.0,
    kind="biological_parameter",
    unit="kcal/kg of threshed whole wheat grain",
    source="Same figure and same name as sim/world/agriculture.py's own "
           "WHEAT_ENERGY_KCAL_PER_KG and sim/world/demand.py's own "
           "(re-)declaration of it - unlike the caloric-need figure above, "
           "this one is safe to share the EXACT name for because the value "
           "genuinely is the same physical fact (wheat's own calorie "
           "density) rather than three modules independently landing on a "
           "coincidentally-equal number.",
    confidence="B",
    why="Turns a caloric requirement into a mass of grain, the unit this "
        "module's regional yields are already stated in.")

FALLOW_HOLDING_MULTIPLIER = declare(
    "FALLOW_HOLDING_MULTIPLIER", 2.0,
    kind="engineering_estimate",
    unit="multiplier, holding hectares per cropped hectare (dimensionless)",
    source="data/production/40_organics.json's own wheat_kg entry states "
           "this directly: 'under the two-field rotation of this period an "
           "equal area lies fallow, so a holding is about twice this area'. "
           "Duplicated here rather than imported, per this module's own "
           "STANDALONE section.",
    confidence="C",
    why="quantity_demanded_kg_grain_equivalent asks how much LAND a "
        "population's grain need requires, and REFERENCE_WHEAT_YIELD_KG_"
        "PER_HECTARE is a CROPPED-hectare figure; without this multiplier "
        "the demand side would understate land need by roughly half "
        "relative to the supply side this module also measures in whole "
        "regions, not cropped-only slivers of them.")

DIET_DIVERSITY_LAND_MULTIPLIER = declare(
    "DIET_DIVERSITY_LAND_MULTIPLIER", 1.3,
    kind="temporary_heuristic",
    unit="multiplier on grain-equivalent land need (dimensionless)",
    source=None,
    confidence="D",
    why="sim/world/agriculture.py's own annual_food_demand_kg_per_person "
        "documents this exact gap: 'real pre-industrial diets were not "
        "100% grain calories... that simplification runs in the direction "
        "of UNDERSTATING how much land a real diet needs'. This module "
        "independently re-derives, rather than imports, a correction for "
        "the same gap (oil, wine, legumes, pasture for draught and dairy "
        "animals) - the DIRECTION is not in doubt, the SIZE is a "
        "placeholder pending a real multi-crop diet model, which is "
        "agriculture.py's job, not this module's.")


def quantity_demanded_kg_grain_equivalent(population):
    """How much grain-equivalent output a population of this size needs
    from its own land in a year - the quantity find_margin_of_cultivation
    fills from the best available region-parcel down. See the module
    docstring's DEMAND IS A PARAMETER section for what each factor is and
    is not.
    """
    if population < 0:
        raise ValueError("population cannot be negative: %r" % (population,))
    grain_kg_per_person = (LAND_HUMAN_CALORIC_NEED_KCAL_PER_DAY * 365.0
                           / WHEAT_ENERGY_KCAL_PER_KG)
    return (population * grain_kg_per_person
            * FALLOW_HOLDING_MULTIPLIER * DIET_DIVERSITY_LAND_MULTIPLIER)


# ============================================================================
# REGION LAND - the physical facts, read from data/world/geography.json
# ============================================================================

RegionLand = collections.namedtuple("RegionLand", [
    "region",                        # geography.json region key
    "land_area_km2",
    "arable_fraction",
    "fertility_quality_multiplier",  # 1.0 = data/production/40_organics.json's
                                      # own wheat_kg baseline (Italia)
    "arable_iugera",                 # derived: land_area_km2 * arable_fraction
                                      # / IUGERUM_HECTARES * 100 (km2->ha)
])

_KM2_TO_HECTARES = 100.0


def _load_json(path):
    with open(path, "r") as handle:
        return json.load(handle)


_LAND_DECLARED = set()


def _declare_land_area(region_key, land_entry):
    """data/world/geography.json's own land_area_km2 for one region, run
    through declare() with that entry's own conf/source - the same
    discipline sim/world/deposits.py's own _declare_grade applies to an
    ore body's grade.
    """
    name = "REGION_LAND_AREA_KM2_%s" % region_key.upper()
    if name in _LAND_DECLARED:
        return land_entry["land_area_km2"]
    _LAND_DECLARED.add(name)
    confidence = land_entry.get("conf", "D")
    kind = "engineering_estimate" if confidence in ("A", "B", "C") else "temporary_heuristic"
    return declare(
        name, land_entry["land_area_km2"], kind=kind,
        unit="km2, coarse country-scale approximation",
        source=land_entry.get("source"), confidence=confidence,
        why="This region's real land area - a geography fact, never tuned "
            "to any downstream price - read from data/world/geography.json's "
            "%r region." % region_key)


def _declare_arable_fraction(region_key, land_entry):
    name = "REGION_ARABLE_FRACTION_%s" % region_key.upper()
    if name in _LAND_DECLARED:
        return land_entry["arable_fraction"]
    _LAND_DECLARED.add(name)
    confidence = land_entry.get("conf", "D")
    kind = "engineering_estimate" if confidence in ("A", "B", "C") else "temporary_heuristic"
    return declare(
        name, land_entry["arable_fraction"], kind=kind,
        unit="fraction of land_area_km2 physically workable by pre-"
             "industrial rain-fed or simple-irrigation farming (dimensionless)",
        source=land_entry.get("source"), confidence=confidence,
        why="A terrain/climate fact about this region (how much of it is "
            "desert, mountain, rainforest or ice versus ordinary plough "
            "land), never a fact about who farms it today - read from "
            "data/world/geography.json's %r region." % region_key)


def _declare_fertility(region_key, land_entry):
    name = "REGION_FERTILITY_QUALITY_MULTIPLIER_%s" % region_key.upper()
    if name in _LAND_DECLARED:
        return land_entry["fertility_quality_multiplier"]
    _LAND_DECLARED.add(name)
    confidence = land_entry.get("conf", "D")
    kind = "engineering_estimate" if confidence in ("A", "B", "C") else "temporary_heuristic"
    return declare(
        name, land_entry["fertility_quality_multiplier"], kind=kind,
        unit="multiplier on REFERENCE_WHEAT_YIELD_KG_PER_HECTARE, 1.0 = "
             "Italia's own dry-farmed Mediterranean baseline (dimensionless)",
        source=land_entry.get("source"), confidence=confidence,
        why="A soil/climate quality fact about this region's arable "
            "share, in the SAME units sim/world/agriculture.py's own "
            "Land(hectares, quality=...) already uses - see the module "
            "docstring's THE SAME UNIT section. Read from data/world/"
            "geography.json's %r region." % region_key)


def load_region_lands(geography=None):
    """{region_key: RegionLand}, for every region data/world/geography.json
    carries a `land` block for. `geography` defaults to loading the file
    fresh, accepted as an argument purely so a caller that already has it
    in hand (or a test) is not made to re-read it.
    """
    geography = geography if geography is not None else _load_json(GEOGRAPHY_FILE)
    out = {}
    for region_key, region_entry in geography["regions"].items():
        if region_key.startswith("_"):
            continue
        land_entry = region_entry.get("land")
        if land_entry is None:
            # A region with no land block yet - should not happen once this
            # task lands (every real region gets one), but a future region
            # added without one should not crash the whole module.
            continue
        land_area_km2 = _declare_land_area(region_key, land_entry)
        arable_fraction = _declare_arable_fraction(region_key, land_entry)
        fertility = _declare_fertility(region_key, land_entry)
        arable_km2 = land_area_km2 * arable_fraction
        arable_iugera = arable_km2 * _KM2_TO_HECTARES / IUGERUM_HECTARES
        out[region_key] = RegionLand(
            region=region_key, land_area_km2=land_area_km2,
            arable_fraction=arable_fraction,
            fertility_quality_multiplier=fertility,
            arable_iugera=arable_iugera)
    return out


# ============================================================================
# TERRITORY - per civilization, changeable, per the module docstring
# ============================================================================

def _load_civilization(civilization_id, civilizations=None):
    if civilizations is not None and civilization_id in civilizations:
        return civilizations[civilization_id]
    path = os.path.join(CIVILIZATIONS_DIR, "%s.json" % civilization_id)
    if not os.path.exists(path):
        available = sorted(name[:-len(".json")]
                           for name in os.listdir(CIVILIZATIONS_DIR)
                           if name.endswith(".json") and not name.startswith("_"))
        raise FileNotFoundError(
            "no civilization %r - have: %s" % (civilization_id, ", ".join(available)))
    return _load_json(path)


def cultivable_land_for_civilization(civilization_id, geography=None,
                                     civilizations=None):
    """This civilization's own list of RegionLand parcels - the sum over
    the regions named in its `home_regions`, read fresh every call. See
    the module docstring's WHAT A LATER CONQUEST MECHANISM WOULD HAVE TO
    TOUCH section: this function does no caching keyed on civilization_id,
    so a caller that has updated some civilization's own `home_regions`
    (however that update eventually happens - out of this module's
    ownership) gets the new territory back on its very next call, with no
    change needed here.

    A `home_regions` entry naming a region data/world/geography.json does
    not carry a `land` block for (should not happen for any of this
    project's real regions, all 21 of which get one this round) is
    silently skipped rather than raising - the same "a gap here is a
    future region's problem, not this call's" reasoning `load_region_lands`
    already applies.
    """
    civilization = _load_civilization(civilization_id, civilizations)
    region_lands = load_region_lands(geography)
    home_regions = civilization.get("home_regions") or []
    return [region_lands[region] for region in home_regions if region in region_lands]


# ============================================================================
# THE MARGIN OF CULTIVATION AND RENT
# ============================================================================

LandAllocation = collections.namedtuple("LandAllocation", [
    "region_land",
    "arable_iugera_supplied",
    "fertility_quality_multiplier",
    "rent_kg_grain_equivalent_per_iugerum",
])

MarginOutcome = collections.namedtuple("MarginOutcome", [
    "quantity_demanded_kg",
    "margin_fertility_quality_multiplier",
    "marginal_region",
    "allocations",
    "quantity_supplied_kg",
    "unmet_demand_kg",
    "price_kg_grain_equivalent_per_iugerum",
])


def find_margin_of_cultivation(region_lands, quantity_demanded_kg,
                               kg_per_hectare_at_quality_1=None,
                               iugerum_hectares=None):
    """The Ricardian margin of cultivation over `region_lands`: which
    parcel is the worst one actually needed to meet `quantity_demanded_kg`
    of grain-equivalent output, and what each parcel earns above it.

    Sorts BEST FERTILITY FIRST (see the module docstring's item 3 for why
    this is the opposite order from sim/world/deposits.py's cheapest-cost-
    first - fertility and cost of a kilogram of grain run opposite ways),
    ties broken by region name for determinism regardless of input order,
    exactly matching sim/world/deposits.py's own supply_curve discipline.
    """
    if quantity_demanded_kg < 0:
        raise ValueError("quantity demanded cannot be negative: %r"
                          % (quantity_demanded_kg,))

    ordered = sorted(
        region_lands,
        key=lambda land: (-land.fertility_quality_multiplier, land.region))

    remaining = quantity_demanded_kg
    margin_fertility = None
    marginal_region = None
    raw_allocations = []  # (region_land, iugera_supplied, capacity_kg)
    for land in ordered:
        capacity_kg = (land.arable_iugera
                       * reference_yield_kg_per_iugerum(
                           land.fertility_quality_multiplier,
                           kg_per_hectare_at_quality_1, iugerum_hectares))
        supplied_kg = min(capacity_kg, max(0.0, remaining))
        supplied_iugera = (supplied_kg / capacity_kg * land.arable_iugera
                           if capacity_kg > 0.0 else 0.0)
        if supplied_kg > 0.0:
            margin_fertility = land.fertility_quality_multiplier
            marginal_region = land.region
        raw_allocations.append((land, supplied_iugera))
        remaining -= supplied_kg

    unmet = max(0.0, remaining)
    if unmet > 0.0 and ordered:
        # Demand exceeds this civilization's whole territory's combined
        # capacity - every region is fully worked, the worst one held is
        # marginal by convention, and the shortfall is reported rather than
        # silently absorbed. See sim/world/deposits.py's own
        # find_marginal_deposit for the sibling case.
        margin_fertility = ordered[-1].fertility_quality_multiplier
        marginal_region = ordered[-1].region

    reference_yield_at_1 = reference_yield_kg_per_iugerum(
        1.0, kg_per_hectare_at_quality_1, iugerum_hectares)

    allocations = []
    weighted_rent_sum = 0.0
    supplied_iugera_total = 0.0
    for land, supplied_iugera in raw_allocations:
        rent_per_iugerum = 0.0
        if margin_fertility is not None:
            rent_per_iugerum = (max(0.0, land.fertility_quality_multiplier
                                    - margin_fertility)
                                * reference_yield_at_1)
        allocations.append(LandAllocation(
            region_land=land,
            arable_iugera_supplied=supplied_iugera,
            fertility_quality_multiplier=land.fertility_quality_multiplier,
            rent_kg_grain_equivalent_per_iugerum=rent_per_iugerum))
        weighted_rent_sum += rent_per_iugerum * supplied_iugera
        supplied_iugera_total += supplied_iugera

    price_per_iugerum = (weighted_rent_sum / supplied_iugera_total
                         if supplied_iugera_total > 0.0 else 0.0)

    return MarginOutcome(
        quantity_demanded_kg=quantity_demanded_kg,
        margin_fertility_quality_multiplier=margin_fertility,
        marginal_region=marginal_region,
        allocations=allocations,
        quantity_supplied_kg=quantity_demanded_kg - unmet,
        unmet_demand_kg=unmet,
        price_kg_grain_equivalent_per_iugerum=price_per_iugerum)


def margin_outcome_for_civilization(civilization_id, geography=None,
                                    civilizations=None,
                                    kg_per_hectare_at_quality_1=None,
                                    iugerum_hectares=None):
    """find_margin_of_cultivation, for one civilization's own territory and
    population - the single call sim/solve_prices.py's own land-rent
    wiring makes. Population is read straight from the civilization's own
    file (an INITIAL CONDITION, per CLAUDE.md SS3.1), not a constant.
    """
    civilization = _load_civilization(civilization_id, civilizations)
    region_lands = cultivable_land_for_civilization(
        civilization_id, geography, civilizations)
    population = civilization.get("population")
    if population is None:
        raise KeyError("%r has no population field" % (civilization_id,))
    quantity_demanded_kg = quantity_demanded_kg_grain_equivalent(population)
    return find_margin_of_cultivation(
        region_lands, quantity_demanded_kg,
        kg_per_hectare_at_quality_1, iugerum_hectares)


if __name__ == "__main__":
    # A quick, human-readable readout - the same kind of thing
    # sim/world/deposits.py's own __main__ block prints.
    print("LAND - Ricardian rent from regional fertility and territory")
    print("=" * 72)
    civilization_ids = sorted(
        name[:-len(".json")] for name in os.listdir(CIVILIZATIONS_DIR)
        if name.endswith(".json") and not name.startswith("_"))
    for civilization_id in civilization_ids:
        outcome = margin_outcome_for_civilization(civilization_id)
        civilization = _load_civilization(civilization_id)
        print("\n%s (population %s, holds %d region(s))"
              % (civilization_id, format(civilization["population"], ","),
                 len(civilization.get("home_regions") or [])))
        print("  quantity demanded: %.4g kg grain-equivalent/yr"
              % outcome.quantity_demanded_kg)
        for allocation in sorted(
                outcome.allocations,
                key=lambda a: -a.fertility_quality_multiplier):
            marker = (" <- MARGINAL" if allocation.region_land.region
                      == outcome.marginal_region else "")
            print("  %-20s fertility=%5.2f  arable=%14.4g iugera  "
                  "used=%14.4g iugera  rent=%8.4f kg/iugerum%s"
                  % (allocation.region_land.region,
                     allocation.fertility_quality_multiplier,
                     allocation.region_land.arable_iugera,
                     allocation.arable_iugera_supplied,
                     allocation.rent_kg_grain_equivalent_per_iugerum,
                     marker))
        print("  PRICE (supply-weighted average rent): %.4f kg grain-"
              "equivalent/iugerum"
              % outcome.price_kg_grain_equivalent_per_iugerum)
        if outcome.unmet_demand_kg > 0.0:
            print("  UNMET DEMAND: %.4g kg/yr beyond this civilization's "
                  "whole territory's combined capacity"
                  % outcome.unmet_demand_kg)
