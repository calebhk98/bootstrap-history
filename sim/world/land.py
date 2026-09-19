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

UPDATE (Complaints/46): THAT WAS ONLY HALF OF RICARDO, AND THIS ROUND ADDS
THE OTHER HALF. Everything above is the EXTENSIVE margin - better land
against worse. Complaints/46 measured what that leaves out: Han China holds
one region, Rome holds seven, and a civilization holding a single uniform
region has nothing WORSE of its own to earn a differential rent over, so it
priced land at exactly zero regardless of population - Han China
(58,000,000 people) and the Norse (1,500,000) came out identically priced,
which was a finding about the MAP's own filing system (how many labels a
region happened to be split into), not about either civilization's land.
The INTENSIVE margin - diminishing returns to more labour on the SAME
ground, the second and third ploughing of one field yielding less than the
first - is the other source of rent, and it does not need a worse region to
exist anywhere: crowd one region hard enough and it earns rent from itself.
See the LABOUR INTENSITY section below, sim/world/agriculture.py's own
Cobb-Douglas production function (the source this section's physics is
DUPLICATED from, per this module's STANDALONE section, never imported), and
margin_outcome_for_civilization's own docstring for where the two margins
actually combine.

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
     civilization's own list of TILE-parcels: `land_tiles["region_to_
     tiles"]` resolves each held region to the physical tiles inside it
     (dozens to over a hundred per civilization - see the UPDATE section
     below), and every tile carries its own name, arable iugera, and
     fertility. THIS IS WHERE "PER-CIVILISATION AND CHANGEABLE" LIVES. Two
     civilizations that hold the same `home_regions` list resolve to the
     same set of tiles and get the same land; a civilization that holds
     more, or better, regions gets more or better land, with no other code
     path involved - and, per the UPDATE section below, this no longer
     depends on how many region LABELS that land happens to be filed
     under, only on which physical tiles it resolves to.

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
LAND AT EXACTLY ZERO FROM THIS FUNCTION ALONE, AND THAT WAS THE WHOLE
FINDING THIS SECTION USED TO STOP AT - see Han China and the Norse in this
module's own `--why`-style report for what a purely extensive, differential
model says about why a civilization wants varied territory, not merely more
of it.

UPDATE (Complaints/46): THIS IS STILL TRUE OF `find_margin_of_cultivation`
ITSELF, AND THAT IS NOW DELIBERATE, NOT THE WHOLE ANSWER. This function
computes the EXTENSIVE margin only, on purpose, so its own tests keep
checking exactly one mechanism at a time - see the LABOUR INTENSITY section
below for the INTENSIVE margin this was missing, and
`margin_outcome_for_civilization`'s own docstring for where the two are
added together. A civilization holding one region still gets a zero
EXTENSIVE rent from this function; it no longer gets a zero PRICE from
`margin_outcome_for_civilization`, because crowding that one region is a
real, separate source of rent this function was never built to see.

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

UPDATE (stakeholder maintainability item 6, two map systems):
THE EXTENSIVE MARGIN NOW READS `land_tiles`, NOT `regions`. Everything
above this paragraph describes the mechanism as it stood when the margin's
own atomic parcel was one of the 21 hand-drawn `regions` records. That was
the SAME defect Complaints/46 found in `forest_land_ceiling`
(`sim/engine/economy_mining.py`) and Complaints/50 found in weather
pooling (`sim/engine/core.py`, since fixed - see that file's
`_compute_farm_weather_cells`): a hand-drawn region is a LABEL, sized and
named by whoever drew the map, not a unit of physical quantity, and using
it as one made a civilization's own numbers depend on how many boxes its
territory happened to be filed under rather than on how much land, of
what quality, it actually holds. `north_africa` (5,750,000 km2, one
`fertility_quality_multiplier` of 1.35, "96% Sahara, rated on the
strength of the Nile" per Complaints/46) is the concrete case: one region
record cannot show a margin between its own good land and its own bad
land, because it has only one fertility figure to its name.

`data/world/geography.json`'s `land_tiles` block (1,139 equal-area
150,000 km2 tiles, `tools/generate_geography_tiles.py`, Complaints/46's
own recommended fix, `region_to_tiles` mapping each of the 21 regions to
the tiles that fall inside it) already carries the SAME `land` fields a
region record does - `land_area_km2`, `arable_fraction`,
`fertility_quality_multiplier` - but per tile instead of per region, at
roughly a hundredth of a hand-drawn region's typical size. `load_tile_
lands` reads them the same way `load_region_lands` reads a region's own
`land` block; `cultivable_land_for_civilization` now resolves a
civilization's `home_regions` to the UNION of tiles those regions map to
(via `region_to_tiles`, deduplicated and sorted for determinism regardless
of `home_regions` order) and hands `find_margin_of_cultivation` THAT list
of parcels - dozens to over a hundred per civilization instead of one to
seven. `find_margin_of_cultivation` itself is completely unchanged: it
already took "a list of parcels" as its input and never assumed anything
about how many there are or what a parcel is called, which is exactly why
this migration touches no other function in the LABOUR INTENSITY or
MARGIN OF CULTIVATION sections below.

WHY THIS IS INVARIANT TO RE-PARTITIONING, WHICH THE OLD MECHANISM WAS NOT.
The old mechanism's answer for a civilization's territory depended on how
that territory happened to be split into region records: the SAME ground,
filed as one big region, gave a flat, blended fertility with no internal
margin; filed as several smaller, differently-fertile regions, the same
ground would show a real extensive margin between its own better and
worse parts. Nothing about the physical land changed between those two
filings - only the label count did. Reading `land_tiles` instead removes
this dependency at the source: a civilization's own land figures are now
the union of PHYSICAL TILES its `home_regions` resolve to, and that union
does not care how many region labels were used to name it or what those
labels are called - two civilizations (or the same civilization under a
hypothetical redrawing of `regions` that split or merged some of its
territory's labels without moving a single tile from one civilization to
another) holding the same set of tiles get the same territory, the same
margin, and the same price. `sim/world/land_tile_partition_invariance_
test.py` (this task's own new test, alongside this module because
`sim/tests/` is owned by other agents in the shared checkout - see that
file's own docstring) asserts exactly this property, and fails against
the pre-migration `cultivable_land_for_civilization` for exactly the
reason described above.

WHAT DID NOT MOVE: `load_region_lands` (region-keyed, one parcel per
region, straight off `geography["regions"]`) is UNCHANGED and still
present - not because anything in THIS module still calls it (nothing
does, after this update), but because `sim/tests/test_land.py`'s own
`RegionDataLoadsCleanlyTests` and part of `CivilizationTerritoryTests`
call it directly to exercise the region data on its own terms, and
because `regions` is explicitly kept working for whatever else in the
engine still reads it (`sim/world/deposits.py`'s deposit locations,
`sim/engine/geography.py`'s centroid/name lookups, `sim/engine/
economy_freight.py`'s freight distances, `sim/engine/economy_mining.py`'s
`forest_land_ceiling` - the last of these already fixed for the
COUNT-of-labels defect by Complaints/46's own per-km2 rewrite, still on
`regions` for the land AREA itself). None of those are this task's
ownership or in its scope; see this task's own final report for the
measured list of what still reads `regions` after this change.

WHAT STILL DOES NOT MOVE, EVEN NOW: a `land_tiles` tile is still one
parcel at one fertility, the same simplification a `regions` record used
to make, just at a grain roughly a hundredth the size - `tools/
generate_geography_tiles.py`'s own generation rule already documents that
a tile's own `arable_fraction`/`fertility_quality_multiplier` are not
independently surveyed either, but read off that tile's own Koppen-class
sample mix. A future finer grid (Complaints/46 and this module's earlier
sections both call out the stakeholder's stated 10,000-tile goal) would
sharpen this further with no further change here, for the same reason a
conquest mechanism needs no change here (see above): this module reads
whatever `land_tiles` the geography file hands it, at whatever grain that
file happens to be generated at.

WHAT THIS MODULE DELIBERATELY DOES NOT DO.

  - No intra-tile heterogeneity. Each of the 1,139 `land_tiles` tiles is
    still ONE parcel at ONE fertility - finer than the 21 `regions` this
    module used to read (roughly a hundredth the area at the median), but
    still a single number standing in for whatever real variation exists
    inside a 150,000 km2 cell. `sim/world/deposits.py` lists several NAMED
    deposits per metal at different grades; nothing here has that
    resolution within one tile. This is exactly why a civilization whose
    entire territory happens to be one uniform Koppen class over every
    tile it holds can still show a small or zero extensive margin - the
    tiles are finer than the old regions, not infinitely fine.
  - No transport friction between regions. A civilization's whole
    population is priced against its whole territory as one pooled land
    market, the same simplification `sim/world/deposits.py` already makes
    for a whole empire's ore demand against its whole territory's
    deposits. Real grain was expensive to move in bulk before rail, which
    this project already represents elsewhere (freight distance in
    `sim/engine/economy.py`) but not here.
  - No depletion, no capital (irrigation works, drainage, forest
    clearance) that would raise a parcel's own fertility over time. Land
    does not run out the way an ore body does - that is this module's
    entire reason for existing rather than reusing `sim/world/deposits.py`
    outright - but real land quality is not actually fixed forever either;
    treating `fertility_quality_multiplier` as a constant per region is a
    simplification, not a claim that fertility cannot be raised (or
    ruined) by what is done to it. UPDATE (Complaints/46): the INTENSIVE
    MARGIN (diminishing returns to labour on fixed land) IS now done - see
    the LABOUR INTENSITY section - and is a different thing from either of
    these: it never claims land runs out or that fertility itself changes,
    only that the SAME land yields less per additional hour of labour
    applied to it, which is what lets a civilization's own population
    density raise its own rent with no depletion and no capital
    improvement anywhere in the story.
  - The amount of land `find_margin_of_cultivation` decides is actually
    needed to meet quantity demanded is still computed at the FLAT
    reference yield, not the intensity-adjusted one the LABOUR INTENSITY
    section derives - see that section's own WHAT THIS DELIBERATELY DOES
    NOT DO for the seam this leaves and why it is left alone this round.
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
from typing import Any, Dict, List, NotRequired, Optional, TypedDict

from sim.constants import declare
from sim.world.shared_constants import (
    ANNUAL_LABOUR_HOURS_PER_FARM_WORKER as _SHARED_ANNUAL_LABOUR_HOURS_PER_FARM_WORKER,
    FALLOW_SHARE_OF_HOLDING as _SHARED_FALLOW_SHARE_OF_HOLDING,
    LABOUR_OUTPUT_ELASTICITY as _SHARED_LABOUR_OUTPUT_ELASTICITY,
    REFERENCE_LABOUR_HOURS_PER_HECTARE as _SHARED_REFERENCE_LABOUR_HOURS_PER_HECTARE,
    SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY as _SHARED_SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY,
    WHEAT_ENERGY_KCAL_PER_KG,
)
# THE FIVE NAMES ABOVE IMPORTED UNDER A LEADING-UNDERSCORE ALIAS keep this
# module's own historical public names (LAND_HUMAN_CALORIC_NEED_KCAL_PER_
# DAY, LAND_REFERENCE_LABOUR_HOURS_PER_HECTARE, LAND_LABOUR_OUTPUT_
# ELASTICITY, LAND_ANNUAL_LABOUR_HOURS_PER_FARM_WORKER) or a derived one
# (FALLOW_HOLDING_MULTIPLIER) rather than the shared module's own names -
# see each assignment below, at the exact spot each used to be its own
# independent `declare()` call, for why. This module's own STANDALONE
# property is unaffected by importing a shared value: sim/world/
# shared_constants.py imports nothing but sim.constants.declare, exactly
# like this file already did - see that module's own docstring.
# WHEAT_ENERGY_KCAL_PER_KG keeps the exact same name it always had; see its
# own assignment below for why it is imported directly rather than aliased.

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


def reference_yield_kg_per_iugerum(
        fertility_quality_multiplier: float,
        kg_per_hectare_at_quality_1: Optional[float] = None,
        iugerum_hectares: Optional[float] = None) -> float:
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

# LAND_HUMAN_CALORIC_NEED_KCAL_PER_DAY used to be its own `declare()` call
# here. It is now this module's own historical public name for
# sim/world/shared_constants's SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_
# ADULT_DAY (see this file's top-of-file import) - sim/world/agriculture.py
# needs the identical figure (formerly under its own HUMAN_ENERGY_
# REQUIREMENT_KCAL_PER_ADULT_DAY name) and now imports the same shared
# declaration. sim/world/demand.py's HUMAN_SUBSISTENCE_CALORIES_PER_
# CAPITA_DAY and sim/world/demography.py's SUBSISTENCE_CALORIES_PER_ADULT_
# EQUIVALENT_DAY still declare it independently, out of this change's
# ownership - see sim/world/shared_constants.py's own WHAT DOES NOT BELONG
# HERE section and sim/tests/test_shared_constants.py for how a future
# drift there is still caught.
LAND_HUMAN_CALORIC_NEED_KCAL_PER_DAY = (
    _SHARED_SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY)
# Sets how much grain-equivalent a population needs before this module can
# say how much land that requires - see WHEAT_ENERGY_KCAL_PER_KG for the
# other half of that conversion.

# WHEAT_ENERGY_KCAL_PER_KG used to be its own `declare()` call here too; it
# is now imported directly under this same name from sim.world.
# shared_constants (see the top-of-file import) - already safe to share the
# exact name for, since (per this module's history) the value genuinely is
# the same physical fact (wheat's own calorie density), not three modules
# independently landing on a coincidentally-equal number. Turns a caloric
# requirement into a mass of grain, the unit this module's regional yields
# are already stated in.

# FALLOW_HOLDING_MULTIPLIER used to be its own, independently-set
# `declare()` call here (2.0, holding hectares per cropped hectare). It is
# now DERIVED arithmetic from sim.world.shared_constants's
# FALLOW_SHARE_OF_HOLDING (0.5, the fraction of a holding idle in any one
# year) instead - see that module's own LAND USE section for why this pair
# is the HARD duplication case (the same physical fact under a different
# name AND a different unit, not merely a different name) and
# sim/world/agriculture.py's own comment at its FALLOW_SHARE_OF_HOLDING
# import for the other side of it. Not a `declare()` of its own: it is
# arithmetic on one already-declared number, the same convention this
# module already uses for LAND_ANNUAL_FARM_LABOUR_HOURS_PER_CAPITA below.
FALLOW_HOLDING_MULTIPLIER = 1.0 / (1.0 - _SHARED_FALLOW_SHARE_OF_HOLDING)
# 2.0, exactly reproducing this module's own historical value: a two-field
# rotation with an even 50/50 split makes a holding twice its cropped area.
# quantity_demanded_kg_grain_equivalent asks how much LAND a population's
# grain need requires, and REFERENCE_WHEAT_YIELD_KG_PER_HECTARE is a
# CROPPED-hectare figure; without this multiplier the demand side would
# understate land need by roughly half relative to the supply side this
# module also measures in whole regions, not cropped-only slivers of them.

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

LAND_CALENDAR_DAYS_PER_YEAR = declare(
    "LAND_CALENDAR_DAYS_PER_YEAR", 365.0,
    kind="physical_constant",
    unit="days/year",
    source="A plain calendar year, rounded to whole days - not the Julian "
           "365.25 average sim/world/agriculture.py's own DAYS_PER_YEAR "
           "and sim/world/demand.py's own DAYS_PER_YEAR use for the "
           "identical conversion. Declared here at the value this module "
           "already used rather than reconciled with those, because this "
           "task extracts numbers, it does not tune them - see this "
           "module's own STANDALONE section for why it does not simply "
           "import agriculture.py's DAYS_PER_YEAR instead.",
    confidence="C",
    why="Converts the daily caloric need above into the annual grain mass "
        "this function's own land-demand arithmetic runs on.")


def quantity_demanded_kg_grain_equivalent(population: float) -> float:
    """How much grain-equivalent output a population of this size needs
    from its own land in a year - the quantity find_margin_of_cultivation
    fills from the best available region-parcel down. See the module
    docstring's DEMAND IS A PARAMETER section for what each factor is and
    is not.
    """
    if population < 0:
        raise ValueError("population cannot be negative: %r" % (population,))
    grain_kg_per_person = (LAND_HUMAN_CALORIC_NEED_KCAL_PER_DAY * LAND_CALENDAR_DAYS_PER_YEAR
                           / WHEAT_ENERGY_KCAL_PER_KG)
    return (population * grain_kg_per_person
            * FALLOW_HOLDING_MULTIPLIER * DIET_DIVERSITY_LAND_MULTIPLIER)


# ============================================================================
# LABOUR INTENSITY - THE INTENSIVE MARGIN (Complaints/46)
# ============================================================================
# Everything above prices land by comparing ONE FLAT yield-per-iugerum
# (REFERENCE_WHEAT_YIELD_KG_PER_HECTARE, at whatever labour a "reference"
# farmer applies) across regions of different fertility - the EXTENSIVE
# margin, Ricardo's "worse land against better". Complaints/46 measured
# what that leaves out: a civilization holding a single uniform region has
# nothing WORSE of its own to earn a differential rent over, so it prices
# land at exactly zero regardless of how many people are drawing on that
# one region - Han China (58,000,000 people on one region) and the Norse
# (1,500,000 on one region) came out identically priced at zero, which is a
# statement about the MAP's own filing system, not about either
# civilization's land.
#
# THE FIX, FOLLOWING sim/world/agriculture.py'S OWN PHYSICS RATHER THAN
# REBUILDING IT. That module's `gross_harvest_kg` is Cobb-Douglas in land
# and labour - constant returns to the two together, but its own
# LABOUR_OUTPUT_ELASTICITY < 1 means output on a FIXED parcel grows slower
# than the labour applied to it (the second and third ploughing of one
# field yielding less than the first - exactly the intensive margin this
# module was missing). Its own `marginal_product_of_labour_kg_per_hour`
# gives the closed form for why: for harvest = TFP * hectares**(1-e) *
# hours**e, the extra kilograms the next hour of labour buys is
# e * harvest / hours, which falls as hours rises because e < 1. This
# module does NOT import agriculture.py (see the module docstring's
# STANDALONE section) - every constant below is DUPLICATED from it, with
# the same discipline REFERENCE_WHEAT_YIELD_KG_PER_HECTARE above already
# uses, and the functions below reproduce the SAME shape on a
# PER-IUGERUM basis (land fixed at exactly one iugerum, so there is no
# separate land exponent to carry) rather than calling agriculture.py's
# own code.
#
# WHAT LAND EARNS FROM THIS, AND WHY IT IS ADDITIVE WITH THE EXTENSIVE
# RENT ABOVE RATHER THAN A REPLACEMENT FOR IT. Cobb-Douglas has a standard
# property (Euler's theorem, constant returns to scale): if labour is paid
# its own marginal product for every hour actually worked, output splits
# into a labour share (the elasticity, e) and a LAND share (1 - e) with
# nothing left over - no separate market-clearing step needed.
# `intensive_rent_kg_grain_equivalent_per_iugerum` is exactly that land
# share, evaluated at however many labour-hours a civilization's own
# population actually applies to each iugerum it holds
# (`labour_hours_applied_per_iugerum`). Crowd the SAME region with more
# people and this rises - Boserup's finding, that a population pressed for
# land intensifies rather than merely spreading out - with NO dependence
# on whether any other, worse region exists anywhere: a single,
# uniformly fertile region earns this from itself alone. It is added ON
# TOP of the extensive rent computed above, not blended into it:
# `margin_outcome_for_civilization` is the one function that combines the
# two (see its own docstring), and `find_margin_of_cultivation` above is
# left completely unchanged - a civilization with varied land AND crowding
# shows BOTH effects, and one with neither (an unpopulated, single,
# uniform region) still correctly prices at zero.
#
# WHAT THIS DELIBERATELY DOES NOT DO. The amount of land
# `find_margin_of_cultivation` decides is actually needed to meet a
# civilization's quantity demanded is computed at the FLAT reference
# yield, exactly as before - it is NOT reduced to reflect that a crowded
# civilization is (by this section's own claim) squeezing MORE than the
# reference yield out of the land it already works. A fully closed model
# would feed the intensity this section derives back into how much
# iugera `find_margin_of_cultivation` allocates in the first place; this
# round prices the intensity it finds without feeding it back into that
# allocation. TAG: TEMPORARY SIMPLIFICATION (CLAUDE.md SS3.4) - see
# `margin_outcome_for_civilization`'s own docstring for exactly where this
# seam is and what closing it would require.

# LAND_REFERENCE_LABOUR_HOURS_PER_HECTARE, LAND_LABOUR_OUTPUT_ELASTICITY
# and LAND_ANNUAL_LABOUR_HOURS_PER_FARM_WORKER used to each be their own,
# independently-set `declare()` call here, duplicating sim/world/
# agriculture.py's REFERENCE_LABOUR_HOURS_PER_HECTARE, LABOUR_OUTPUT_
# ELASTICITY and ANNUAL_LABOUR_HOURS_PER_FARM_WORKER under LAND_-prefixed
# names - THE EXACT PAIR OF DUPLICATIONS THAT PROMPTED sim/world/
# shared_constants.py TO EXIST (see that module's own docstring and
# Complaints/46). All three are now this module's own historical public
# names for that single shared declaration (see this file's top-of-file
# import), so there is exactly one number behind each and no second copy
# that can silently disagree with it.
LAND_REFERENCE_LABOUR_HOURS_PER_HECTARE = (
    _SHARED_REFERENCE_LABOUR_HOURS_PER_HECTARE)
# The labour intensity REFERENCE_WHEAT_YIELD_KG_PER_HECTARE is quoted at -
# the anchor point (fertility 1.0, this many hours)
# yield_kg_per_iugerum_at_intensity's own Cobb-Douglas curve is calibrated
# to reproduce exactly.

LAND_LABOUR_OUTPUT_ELASTICITY = _SHARED_LABOUR_OUTPUT_ELASTICITY
# The curve shape that makes doubling labour on fixed land yield less than
# double the output - the whole mechanism this section exists to add.
# Without it, output would scale linearly with labour and crowding could
# never raise a region's own yield, let alone its rent.

LAND_ANNUAL_LABOUR_HOURS_PER_FARM_WORKER = (
    _SHARED_ANNUAL_LABOUR_HOURS_PER_FARM_WORKER)
# How many hours ONE farm worker can give to the land in a year - the
# first of two facts LAND_ANNUAL_FARM_LABOUR_HOURS_PER_CAPITA multiplies
# together to get how much labour a whole POPULATION (not just its farm
# workers) supplies; see LAND_AGRARIAN_POPULATION_SHARE just below for the
# second.

LAND_AGRARIAN_POPULATION_SHARE = declare(
    "LAND_AGRARIAN_POPULATION_SHARE", 0.85,
    kind="temporary_heuristic",
    unit="fraction of population engaged in farming (dimensionless)",
    source="sim/world/agriculture.py's own docstring names 'the historical "
           "80-90%' as the farm-population share of a pre-industrial "
           "society (in the course of explaining why its own computed "
           "farm-population share comes out far below that figure) - a "
           "commonly cited range in agrarian economic history, not a "
           "number this project has derived from its own data. 0.85 is "
           "the midpoint of that range, taken here because this module "
           "needs a single point figure and that docstring states only a "
           "range.",
    confidence="D",
    why="Converts LAND_ANNUAL_LABOUR_HOURS_PER_FARM_WORKER, a rate PER "
        "FARM WORKER, into a rate per PERSON OF THE WHOLE POPULATION - "
        "the same total-population convention "
        "quantity_demanded_kg_grain_equivalent already uses on the "
        "demand side (it does not split farmers from everyone else "
        "either), applied here to the supply side so both sides of this "
        "module's ledger treat 'population' the same way.")

LAND_ANNUAL_FARM_LABOUR_HOURS_PER_CAPITA = (
    LAND_ANNUAL_LABOUR_HOURS_PER_FARM_WORKER * LAND_AGRARIAN_POPULATION_SHARE)
# ~1,190 hours/person/year. Arithmetic on two already-declared numbers, not
# a fact of its own - the same non-declare() treatment
# GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA gets in sim/world/agriculture.py.
# TAG: COMPOUNDING HEURISTIC (CLAUDE.md SS3.4) - this multiplies two
# temporary_heuristic figures together, so its own uncertainty is at least
# as large as the wider of the two, not smaller; declared confidence D on
# both of its own inputs for exactly that reason, even though
# LAND_ANNUAL_LABOUR_HOURS_PER_FARM_WORKER alone is confidence C.


def labour_hours_applied_per_iugerum(
        population: float, total_arable_iugera_held: float,
        annual_farm_labour_hours_per_capita: Optional[float] = None) -> float:
    """How many labour-hours a civilization's own population applies, on
    average, to each iugerum of arable land it HOLDS - its whole endowment
    across every home region, not only the iugera `find_margin_of_
    cultivation` decides are actually needed to meet quantity demanded (see
    this section's own WHAT THIS DELIBERATELY DOES NOT DO for why the two
    are kept separate this round).

    This is a CIVILIZATION-WIDE figure, exactly like
    `quantity_demanded_kg_grain_equivalent` is civilization-wide: the same
    "one pooled land-and-labour market" simplification `find_margin_of_
    cultivation`'s own docstring already states for the extensive margin
    (no transport friction, no intra-region split), applied here to
    labour instead of land.

    Returns 0.0 for a civilization with no arable land at all (rather than
    raising), since a population with nothing to farm applies no labour to
    farming it - matches `load_region_lands`'s own "a gap here is a future
    region's problem, not this call's" handling of an unrecognised region.
    """
    if population < 0:
        raise ValueError("population cannot be negative: %r" % (population,))
    if total_arable_iugera_held < 0:
        raise ValueError("total_arable_iugera_held cannot be negative: %r"
                          % (total_arable_iugera_held,))
    annual_farm_labour_hours_per_capita = (
        LAND_ANNUAL_FARM_LABOUR_HOURS_PER_CAPITA
        if annual_farm_labour_hours_per_capita is None
        else annual_farm_labour_hours_per_capita)
    if total_arable_iugera_held <= 0.0:
        return 0.0
    return (population * annual_farm_labour_hours_per_capita
            / total_arable_iugera_held)


def yield_kg_per_iugerum_at_intensity(
        fertility_quality_multiplier: float,
        labour_hours_per_iugerum: float,
        kg_per_hectare_at_quality_1: Optional[float] = None,
        iugerum_hectares: Optional[float] = None,
        reference_labour_hours_per_hectare: Optional[float] = None,
        labour_output_elasticity: Optional[float] = None) -> float:
    """Kilograms of grain-equivalent one iugerum at this fertility produces
    in a season, at `labour_hours_per_iugerum` of labour applied to it -
    `reference_yield_kg_per_iugerum`'s own flat figure, generalised to
    depend on labour the way `sim/world/agriculture.py`'s `gross_harvest_kg`
    does.

    Cobb-Douglas in labour alone (land is fixed at exactly one iugerum, so
    there is no separate land term to raise to a power): output scales
    with `labour_hours_per_iugerum ** LAND_LABOUR_OUTPUT_ELASTICITY`,
    calibrated so that at exactly the reference intensity
    (LAND_REFERENCE_LABOUR_HOURS_PER_HECTARE, converted to one iugerum)
    this returns EXACTLY `reference_yield_kg_per_iugerum(fertility_
    quality_multiplier)` - the same anchor-at-the-known-point discipline
    `reference_yield_kg_per_iugerum` itself uses for REFERENCE_WHEAT_
    YIELD_KG_PER_HECTARE. At zero (or negative) labour hours this returns
    0.0 (no one worked it, nothing grew) rather than raising or dividing
    by zero.
    """
    if labour_hours_per_iugerum < 0:
        raise ValueError("labour_hours_per_iugerum cannot be negative: %r"
                          % (labour_hours_per_iugerum,))
    reference_labour_hours_per_hectare = (
        LAND_REFERENCE_LABOUR_HOURS_PER_HECTARE
        if reference_labour_hours_per_hectare is None
        else reference_labour_hours_per_hectare)
    labour_output_elasticity = (
        LAND_LABOUR_OUTPUT_ELASTICITY if labour_output_elasticity is None
        else labour_output_elasticity)
    iugerum_hectares_value = (
        IUGERUM_HECTARES if iugerum_hectares is None else iugerum_hectares)
    if labour_hours_per_iugerum <= 0.0:
        return 0.0
    reference_yield = reference_yield_kg_per_iugerum(
        fertility_quality_multiplier, kg_per_hectare_at_quality_1,
        iugerum_hectares)
    reference_labour_hours_per_iugerum = (
        reference_labour_hours_per_hectare * iugerum_hectares_value)
    intensity_ratio = (labour_hours_per_iugerum
                       / reference_labour_hours_per_iugerum)
    return reference_yield * (intensity_ratio ** labour_output_elasticity)


def intensive_rent_kg_grain_equivalent_per_iugerum(
        fertility_quality_multiplier: float, labour_hours_per_iugerum: float,
        kg_per_hectare_at_quality_1: Optional[float] = None,
        iugerum_hectares: Optional[float] = None,
        reference_labour_hours_per_hectare: Optional[float] = None,
        labour_output_elasticity: Optional[float] = None) -> float:
    """The INTENSIVE margin's own contribution to one iugerum's rent: the
    Cobb-Douglas LAND share of what that iugerum produces at
    `labour_hours_per_iugerum` - see this section's own WHAT LAND EARNS
    FROM THIS for the Euler's-theorem argument (labour paid its own
    marginal product leaves exactly `1 - LAND_LABOUR_OUTPUT_ELASTICITY` of
    output as land's own residual). Unlike the extensive rent `find_
    margin_of_cultivation` computes, this needs no OTHER region to compare
    against - a single, uniformly fertile region crowded by a large
    population earns this from itself alone, which is exactly what
    Complaints/46 found missing.

    Rises with `labour_hours_per_iugerum` (more crowding, more rent) and
    with `fertility_quality_multiplier` (better land still earns more,
    even from this margin alone) - both directions asserted directly in
    `sim/tests/test_land.py` rather than left to be inferred from a
    downstream price.
    """
    labour_output_elasticity = (
        LAND_LABOUR_OUTPUT_ELASTICITY if labour_output_elasticity is None
        else labour_output_elasticity)
    yield_at_intensity = yield_kg_per_iugerum_at_intensity(
        fertility_quality_multiplier, labour_hours_per_iugerum,
        kg_per_hectare_at_quality_1, iugerum_hectares,
        reference_labour_hours_per_hectare, labour_output_elasticity)
    return max(0.0, (1.0 - labour_output_elasticity) * yield_at_intensity)


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


class LandBlock(TypedDict):
    """The `land` block data/world/geography.json carries for one region -
    the known shape `_declare_land_area`, `_declare_arable_fraction` and
    `_declare_fertility` all read from, named so the dictionary schema is
    checked rather than assumed at each `land_entry["..."]` lookup."""
    land_area_km2: float
    arable_fraction: float
    fertility_quality_multiplier: float
    conf: NotRequired[str]
    source: NotRequired[Optional[str]]


def _load_json(path: str) -> Any:
    with open(path, "r") as handle:
        return json.load(handle)


_LAND_DECLARED: set[str] = set()


def _declare_land_area(region_key: str, land_entry: LandBlock) -> float:
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


def _declare_arable_fraction(region_key: str, land_entry: LandBlock) -> float:
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


def _declare_fertility(region_key: str, land_entry: LandBlock) -> float:
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


def load_region_lands(geography: Optional[Dict[str, Any]] = None) -> Dict[str, RegionLand]:
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


def load_tile_lands(geography: Optional[Dict[str, Any]] = None) -> Dict[str, RegionLand]:
    """{tile_id: RegionLand}, one entry per `data/world/geography.json`
    `land_tiles` tile - the TILE-GRAIN sibling of `load_region_lands`
    above, and what `cultivable_land_for_civilization` now reads instead
    of it. See the module docstring's UPDATE (stakeholder maintainability
    item 6...) section for why: a tile is a physical 150,000 km2 cell, not
    a hand-drawn label, so a civilization's own land figures stop
    depending on how many region records its territory was filed under.

    RegionLand's own `region` field holds the TILE's id here (e.g.
    `"north_africa_03"`), not a `regions` key - `find_margin_of_
    cultivation` never assumed anything about what that field names (it
    only sorts by fertility and breaks ties by it for determinism), so
    this is not a change to that function, only to what fills the field.

    NOT RUN THROUGH `declare()`, UNLIKE `load_region_lands` ABOVE, AND
    THAT IS A DELIBERATE DEPARTURE FROM THIS MODULE'S OWN EARLIER
    DISCIPLINE, NOT AN OVERSIGHT. `_declare_land_area`/`_declare_arable_
    fraction`/`_declare_fertility` exist so 21 HAND-SET numbers, each
    worth a human being able to find and question individually, carry
    their own provenance in `sim/constants.py`'s registry. `land_tiles`
    is 1,139 tiles - not hand-set at all, but generated in bulk by ONE
    stated rule (`tools/generate_geography_tiles.py`: equal-area grid,
    clipped to Natural Earth coastline, `arable_fraction` and `fertility_
    quality_multiplier` read off each tile's own Koppen-Geiger sample mix
    via that generator's `KOPPEN_ARABLE_AND_FERTILITY` table - confirmed
    NOT constant per climate class, since a tile's own sample mix varies
    tile to tile even within one class). Running `declare()` 1,139 times
    over per-tile duplicates of that one rule would not add provenance
    this file does not already carry (every tile's own `source` field
    already names the generator and the rule; every tile's own `conf`
    field already carries a confidence) - it would only bloat `sim/
    constants.py`'s registry with near-identical entries nobody would
    usefully browse one at a time, which is the opposite of what that
    registry is for (see its own module docstring: "One place to LOOK").
    The rule itself, and where it is declared, is `tools/generate_
    geography_tiles.py`'s own concern, out of this module's ownership.
    """
    geography = geography if geography is not None else _load_json(GEOGRAPHY_FILE)
    land_tiles = geography.get("land_tiles")
    if land_tiles is None:
        # No land_tiles block at all - real data/world/geography.json
        # always has one (see the module docstring's UPDATE section), so
        # this only happens for a hand-built `geography` dict a caller
        # passed directly (a test fixture, most likely) that predates this
        # migration. Raising rather than silently returning {} makes that
        # caller's own missing fixture data visible as a clear error
        # instead of a mysteriously-always-zero land figure downstream.
        raise KeyError(
            "geography has no 'land_tiles' block - the extensive margin "
            "now reads tile-level land (see sim/world/land.py's module "
            "docstring), not the 'regions' block alone; a hand-built "
            "geography dict passed to this function needs one too")
    out = {}
    for tile_id, tile_entry in land_tiles.get("tiles", {}).items():
        land_area_km2 = tile_entry["land_area_km2"]
        arable_fraction = tile_entry["arable_fraction"]
        fertility = tile_entry["fertility_quality_multiplier"]
        arable_km2 = land_area_km2 * arable_fraction
        arable_iugera = arable_km2 * _KM2_TO_HECTARES / IUGERUM_HECTARES
        out[tile_id] = RegionLand(
            region=tile_id, land_area_km2=land_area_km2,
            arable_fraction=arable_fraction,
            fertility_quality_multiplier=fertility,
            arable_iugera=arable_iugera)
    return out


# ============================================================================
# TERRITORY - per civilization, changeable, per the module docstring
# ============================================================================

def _load_civilization(
        civilization_id: str,
        civilizations: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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


def _tile_ids_for_home_regions(home_regions: List[str],
                               land_tiles: Dict[str, Any]) -> List[str]:
    """The deduplicated, sorted union of `land_tiles["region_to_tiles"]`
    over every region in `home_regions` - the set of physical tiles this
    territory resolves to, regardless of how many region labels
    `home_regions` names or what order they are given in. Sorted (not just
    deduplicated) so the RESULT, and therefore everything `find_margin_of_
    cultivation` computes from it, does not depend on `home_regions`'s own
    input order either - the same determinism `find_margin_of_cultivation`
    itself already guarantees by breaking ties on `region` name.

    A `home_regions` entry absent from `region_to_tiles` (should not
    happen for any of this project's 21 real regions - all 21 are mapped,
    per `docs/architecture/MAP_AND_WEATHER.md` section 1.1) contributes no
    tiles rather than raising - the same "a gap here is a future region's
    problem, not this call's" reasoning `load_region_lands` already
    applies to a region missing its `land` block.
    """
    region_to_tiles = land_tiles.get("region_to_tiles", {})
    tile_ids = set()
    for region in home_regions:
        tile_ids.update(region_to_tiles.get(region, []))
    return sorted(tile_ids)


def cultivable_land_for_civilization(
        civilization_id: str, geography: Optional[Dict[str, Any]] = None,
        civilizations: Optional[Dict[str, Any]] = None) -> List[RegionLand]:
    """This civilization's own list of RegionLand parcels - TILE-grain,
    not region-grain (see the module docstring's UPDATE (stakeholder
    maintainability item 6...) section) - resolved from the regions named
    in its `home_regions` via `land_tiles["region_to_tiles"]`, read fresh
    every call. See the module docstring's WHAT A LATER CONQUEST MECHANISM
    WOULD HAVE TO TOUCH section: this function does no caching keyed on
    civilization_id, so a caller that has updated some civilization's own
    `home_regions` (however that update eventually happens - out of this
    module's ownership) gets the new territory back on its very next
    call, with no change needed here.

    A `home_regions` entry naming a region `land_tiles["region_to_tiles"]`
    has no tiles for (should not happen for any of this project's 21 real
    regions) contributes no parcels rather than raising - see
    `_tile_ids_for_home_regions`'s own docstring.

    A civilization with an EMPTY `home_regions` (the landless case
    `margin_outcome_for_civilization`'s own tests exercise) returns an
    empty list without even looking at `geography` - checked before the
    `land_tiles` presence check below, so a civilization that holds no
    territory prices at zero without needing a `land_tiles` block to
    exist at all, the same "nothing to resolve, nothing to raise about"
    shortcut `_tile_ids_for_home_regions` would reach anyway, taken one
    call earlier so a caller building a minimal geography fixture for a
    landless civilization is not forced to give it tile data it will
    never be asked to read.
    """
    civilization = _load_civilization(civilization_id, civilizations)
    home_regions = civilization.get("home_regions") or []
    if not home_regions:
        return []
    geography = geography if geography is not None else _load_json(GEOGRAPHY_FILE)
    land_tiles = geography.get("land_tiles")
    if land_tiles is None:
        raise KeyError(
            "geography has no 'land_tiles' block - see load_tile_lands's "
            "own docstring for why cultivable_land_for_civilization no "
            "longer falls back to 'regions' alone")
    tile_lands = load_tile_lands(geography)
    tile_ids = _tile_ids_for_home_regions(home_regions, land_tiles)
    return [tile_lands[tile_id] for tile_id in tile_ids if tile_id in tile_lands]


# ============================================================================
# THE MARGIN OF CULTIVATION AND RENT
# ============================================================================

LandAllocation = collections.namedtuple("LandAllocation", [
    "region_land",
    "arable_iugera_supplied",
    "fertility_quality_multiplier",
    "rent_kg_grain_equivalent_per_iugerum",
    # The two components `rent_kg_grain_equivalent_per_iugerum` above adds
    # together - see the LABOUR INTENSITY section and margin_outcome_for_
    # civilization's own docstring. `find_margin_of_cultivation` below only
    # ever fills `extensive_...` (leaving `intensive_...` at its default of
    # 0.0, and `rent_kg_grain_equivalent_per_iugerum` equal to the
    # extensive figure alone) - it is `margin_outcome_for_civilization`
    # that fills both. Trailing, defaulted fields so every existing
    # construction site and every existing test that only names the
    # fields it cares about keeps working unchanged.
    "extensive_rent_kg_grain_equivalent_per_iugerum",
    "intensive_rent_kg_grain_equivalent_per_iugerum",
], defaults=(0.0, 0.0))

MarginOutcome = collections.namedtuple("MarginOutcome", [
    "quantity_demanded_kg",
    "margin_fertility_quality_multiplier",
    "marginal_region",
    "allocations",
    "quantity_supplied_kg",
    "unmet_demand_kg",
    "price_kg_grain_equivalent_per_iugerum",
    # The civilization-wide labour intensity (see
    # labour_hours_applied_per_iugerum) that produced this outcome's own
    # intensive-margin rent, or None when this outcome came straight from
    # find_margin_of_cultivation (extensive margin only, no intensity
    # computed) rather than from margin_outcome_for_civilization.
    "labour_hours_per_iugerum",
], defaults=(None,))


def find_margin_of_cultivation(
        region_lands: List[RegionLand], quantity_demanded_kg: float,
        kg_per_hectare_at_quality_1: Optional[float] = None,
        iugerum_hectares: Optional[float] = None) -> "MarginOutcome":
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
            rent_kg_grain_equivalent_per_iugerum=rent_per_iugerum,
            extensive_rent_kg_grain_equivalent_per_iugerum=rent_per_iugerum))
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


def margin_outcome_for_civilization(
        civilization_id: str, geography: Optional[Dict[str, Any]] = None,
        civilizations: Optional[Dict[str, Any]] = None,
        kg_per_hectare_at_quality_1: Optional[float] = None,
        iugerum_hectares: Optional[float] = None,
        annual_farm_labour_hours_per_capita: Optional[float] = None) -> "MarginOutcome":
    """find_margin_of_cultivation's own EXTENSIVE-margin outcome, for one
    civilization's own territory and population, with the INTENSIVE
    margin's own rent (see the LABOUR INTENSITY section above) added on
    top of every worked parcel - the single call sim/solve_prices.py's own
    land-rent wiring makes, and the one place in this module where the two
    margins actually combine.

    Population is read straight from the civilization's own file (an
    INITIAL CONDITION, per CLAUDE.md SS3.1), not a constant.

    THE COMBINATION, IN ORDER:

      1. Run `find_margin_of_cultivation` exactly as before - which parcel
         is marginal, and each worked parcel's EXTENSIVE rent (its own
         fertility surplus over the margin's), is computed by that
         function alone and is not touched by anything below.
      2. `labour_hours_applied_per_iugerum` turns this civilization's own
         population and its own TOTAL held arable endowment (every
         iugerum named in `home_regions`, not only the iugera step 1
         decided were actually needed) into a single, civilization-wide
         labour intensity. A civilization holding one region - the exact
         case that used to price at zero, because step 1 alone still
         returns exactly zero there - is where this number does all the
         work.
      3. Every parcel step 1 actually allocated some iugera to (an unused,
         worse-than-margin parcel stays at exactly zero from BOTH margins
         - a parcel nobody needs earns nothing, matching
         `sim/world/deposits.py`'s own convention) gets `intensive_rent_
         kg_grain_equivalent_per_iugerum` ADDED to its extensive rent, at
         THIS civilization's own intensity.
      4. The civilization's own reported price is recomputed as the same
         supply-weighted average `find_margin_of_cultivation` itself
         uses, over the COMBINED (extensive + intensive) rent instead of
         the extensive rent alone.

    WHAT THIS DOES NOT DO. The iugera step 1 allocates are computed at the
    FLAT reference yield, not the intensity-adjusted one - a fully closed
    model would let a crowded civilization's higher yield-per-iugerum
    reduce how much land `find_margin_of_cultivation` says it actually
    needs; this round prices the intensity it finds without feeding it
    back into that allocation. See the LABOUR INTENSITY section's own
    WHAT THIS DELIBERATELY DOES NOT DO.
    """
    civilization = _load_civilization(civilization_id, civilizations)
    region_lands = cultivable_land_for_civilization(
        civilization_id, geography, civilizations)
    population = civilization.get("population")
    if population is None:
        raise KeyError("%r has no population field" % (civilization_id,))
    quantity_demanded_kg = quantity_demanded_kg_grain_equivalent(population)
    extensive_outcome = find_margin_of_cultivation(
        region_lands, quantity_demanded_kg,
        kg_per_hectare_at_quality_1, iugerum_hectares)

    total_arable_iugera_held = sum(
        region_land.arable_iugera for region_land in region_lands)
    labour_hours_per_iugerum = labour_hours_applied_per_iugerum(
        population, total_arable_iugera_held,
        annual_farm_labour_hours_per_capita)

    combined_allocations = []
    weighted_rent_sum = 0.0
    supplied_iugera_total = 0.0
    for allocation in extensive_outcome.allocations:
        intensive_rent = 0.0
        if allocation.arable_iugera_supplied > 0.0:
            intensive_rent = intensive_rent_kg_grain_equivalent_per_iugerum(
                allocation.fertility_quality_multiplier,
                labour_hours_per_iugerum, kg_per_hectare_at_quality_1,
                iugerum_hectares)
        combined_rent = (allocation.rent_kg_grain_equivalent_per_iugerum
                         + intensive_rent)
        combined_allocations.append(allocation._replace(
            rent_kg_grain_equivalent_per_iugerum=combined_rent,
            intensive_rent_kg_grain_equivalent_per_iugerum=intensive_rent))
        weighted_rent_sum += combined_rent * allocation.arable_iugera_supplied
        supplied_iugera_total += allocation.arable_iugera_supplied

    combined_price = (weighted_rent_sum / supplied_iugera_total
                      if supplied_iugera_total > 0.0 else 0.0)
    return extensive_outcome._replace(
        allocations=combined_allocations,
        price_kg_grain_equivalent_per_iugerum=combined_price,
        labour_hours_per_iugerum=labour_hours_per_iugerum)


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
        print("\n%s (population %s, holds %d region(s), %d land_tiles parcel(s))"
              % (civilization_id, format(civilization["population"], ","),
                 len(civilization.get("home_regions") or []),
                 len(outcome.allocations)))
        print("  quantity demanded: %.4g kg grain-equivalent/yr"
              % outcome.quantity_demanded_kg)
        print("  labour intensity (civ-wide): %.4g hours/iugerum applied "
              "across the whole held endowment (reference is %.4g)"
              % (outcome.labour_hours_per_iugerum,
                 LAND_REFERENCE_LABOUR_HOURS_PER_HECTARE * IUGERUM_HECTARES))
        for allocation in sorted(
                outcome.allocations,
                key=lambda a: -a.fertility_quality_multiplier):
            marker = (" <- MARGINAL" if allocation.region_land.region
                      == outcome.marginal_region else "")
            print("  %-20s fertility=%5.2f  arable=%14.4g iugera  "
                  "used=%14.4g iugera  rent=%8.4f (ext=%7.4f + int=%7.4f) "
                  "kg/iugerum%s"
                  % (allocation.region_land.region,
                     allocation.fertility_quality_multiplier,
                     allocation.region_land.arable_iugera,
                     allocation.arable_iugera_supplied,
                     allocation.rent_kg_grain_equivalent_per_iugerum,
                     allocation.extensive_rent_kg_grain_equivalent_per_iugerum,
                     allocation.intensive_rent_kg_grain_equivalent_per_iugerum,
                     marker))
        print("  PRICE (supply-weighted average rent, extensive + "
              "intensive): %.4f kg grain-equivalent/iugerum"
              % outcome.price_kg_grain_equivalent_per_iugerum)
        if outcome.unmet_demand_kg > 0.0:
            print("  UNMET DEMAND: %.4g kg/yr beyond this civilization's "
                  "whole territory's combined capacity"
                  % outcome.unmet_demand_kg)
