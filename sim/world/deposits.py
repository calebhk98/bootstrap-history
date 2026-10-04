"""Ricardian rent: why a scarce deposit is not priced at its own digging cost.

WHAT THIS IS FOR. Complaints/32 measured the actual defect in this project's
price solver: `sim/engine/solve_prices.py` fixes rent on every extracted material at
zero (`RENT_IS_ZERO`), so a computed price is exactly the labour embodied in
the good, valued at relative wages, with no claim on it from scarcity at all.
Cinnabar comes out at 0.035 labour-hours/kg - two minutes of digging -
because nothing in the model knows there were only about three cinnabar
deposits worth working in the Roman world. This module is what a deposit's
rent actually is and where it comes from: the difference between what a
deposit costs to work and what the MARGINAL deposit - the worst one that has
to be worked to meet the quantity demanded - costs. The marginal deposit
earns zero rent by definition; every deposit cheaper than it earns the
difference, for as long as it keeps being worked. That is also what CLAUDE.md
SS3.1's own example needs to actually work: a gold deposit appearing in Rome
cannot change any price while every deposit's rent is fixed at zero, because
there is nothing for a NEW deposit to compare its cost against.

DEMAND IS A PARAMETER, NOT SOMETHING THIS MODULE INVENTS. Ricardian rent
depends on how much is demanded - the marginal deposit is only "marginal"
relative to some quantity that has to be supplied - and this project does
not have a demand system yet. So every function below that needs a quantity
takes it as an explicit argument (`quantity_demanded_tonnes_per_year`),
exactly as sim/world/agriculture.py takes weather as a parameter and
sim/world/demography.py takes food as one. The day a real demand system
exists, it plugs into that parameter and nothing in this module changes.
Until then, the demonstrations here and in sim/tests/test_deposits.py use
data/world/resources.json's own `empire_output_100ad` figures as an
illustrative quantity - a real historical output level, not a demand curve -
because it is the only quantity this project already has for these metals.

STANDALONE ON PURPOSE, LIKE ITS SIBLINGS. Nothing here imports sim/engine/
or any other sim/world/ module - see sim/world/__init__.py for why a module
built this way survives other agents editing sim/engine/economy.py and
sim/engine/solve_prices.py concurrently with this
file's construction. It reads two data files that already exist
(data/world/geography.json, data/world/resources.json) and one new one this
task adds (the geography deposit catalogue), as plain JSON - that is data, not an
import of another module's code, and cannot be broken by or break any of
those agents' work.

WHAT THIS MODULE COMPUTES, IN ORDER.

  1. EXTRACTION COST, from physical deposit properties alone (never from
     what the metal sells for): `extraction_cost_labour_hours_per_kg`. A
     deposit's ore grade (kilograms of contained metal per tonne of rock or
     gravel raised - the dominant term, because halving the grade doubles
     the rock moved for the same metal) divides down a labour-hours-per-
     tonne figure that itself depends on how hard the rock is to break
     (`hardness_class`) and how deep it sits (`depth_class` - surface, a
     shallow vein worked with basket and ladder, a deep vein needing
     continuous dewatering, or alluvial gravel that need not be broken at
     all, only moved and washed). See EXTRACTION COST MECHANICS below for
     the constants and the arithmetic.

  2. THE SUPPLY CURVE, from a list of deposits for one metal:
     `supply_curve` sorts them by that cost and gives each one a cumulative
     quantity - the curve Complaints/32 says is the whole missing
     mechanism. The marginal cost of meeting a given quantity demanded
     RISES as more is demanded, because meeting it means reaching further
     down (up, in cost) the sorted list.

  3. THE MARGINAL DEPOSIT AND RENT, given a quantity demanded:
     `find_marginal_deposit` walks the supply curve, cheapest first, until
     cumulative supply meets demand. The deposit where that happens is
     marginal; its own cost IS the price every unit of that metal sells at
     (Ricardian rent theory does not price cheap and dear deposits
     separately - one metal, one price, set at the margin). Every deposit
     cheaper than the margin earns rent: (price_at_margin - its own cost)
     times the quantity it actually supplies. A deposit not needed at all
     to meet demand supplies nothing and earns nothing, however cheap it
     is - it simply is not being worked yet.

  4. DEPLETION, because a deposit is not a tap: `DepositState` gives each
     deposit a finite remaining reserve, and `simulate_depletion` walks
     several years of constant demand, working the cheapest available
     deposits first each year and retiring one once its reserve is used
     up. The reserve figure is a labelled heuristic (see
     DEPOSIT_ASSUMED_WORKING_LIFE_YEARS's own declaration) standing in for
     real ore-body volume data this project does not have; the MECHANISM -
     a deposit that runs out forces the margin to a costlier one, raising
     the price with no change in demand at all - is the real point, and it
     needs no year-by-year economic simulation to demonstrate: each
     simulated year is just find_marginal_deposit() run again against
     whatever reserves are left.

EXTRACTION COST MECHANICS. Every deposit below is built from three
independent physical facts:

  ore_grade_kg_per_tonne     kilograms of CONTAINED METAL per tonne of rock
                             (or, for gravel, per tonne of gravel) actually
                             raised. A geological fact about the rock, never
                             derived from what the metal sells for - see
                             the geography deposit catalogue's own _doc for the same
                             discipline applied to every entry there.
  hardness_class             "soft" (friable, weathered, earthy ore - bog
                             iron, oxidised copper), "medium" (ordinary
                             consolidated vein ore, broken with hammer,
                             wedge and fire-setting) or "hard" (massive
                             sulfide or quartz vein rock) - how many
                             labour-hours it takes to break one tonne of
                             ROCK, before grade ever enters the arithmetic.
                             Never set for a gravel deposit: gravel is
                             moved and washed, not broken.
  depth_class                "surface" (no extra haulage cost), "shallow_
                             vein" (basket-and-ladder hoist from modest
                             depth), "deep_vein" (a long hoist AND
                             continuous dewatering - Rio Tinto's Roman-era
                             drainage-wheel batteries are the textbook
                             example of what this multiplier stands for),
                             "alluvial" (loose gravel, panned or sluiced by
                             hand, no rock-breaking labour at all) or
                             "alluvial_hydraulic" (the SAME loose gravel,
                             but the excavation itself is done by diverted
                             water rather than by hand - Pliny's account of
                             the "ruina montium" method at Las Medulas is
                             the reason this is its own class rather than
                             folded into plain "alluvial": it is what let
                             Rome work gold gravel at a grade an order of
                             magnitude leaner than hand panning ever could,
                             for a fraction of the labour per tonne moved).

ALLUVIAL GOLD AND DEEP VEIN GOLD ARE NOT THE SAME COST, AND THIS IS WHY.
the geography deposit catalogue's two gold entries are the sharpest illustration
this module has: Las Medulas (Hispania, alluvial_hydraulic, grade 0.0003
kg/t) costs a little over 166 labour-hours per kilogram of gold by this
module's own arithmetic; Dacia (deep_vein, hard rock, grade 0.008 kg/t)
costs about 8,750 - fifty-two times more, even though its ore is nearly
thirty times RICHER by grade, because breaking hard rock at depth costs
roughly 470 times more labour per tonne of material moved than water doing
the same job at Las Medulas. Grade is the dominant term the module
docstring above promises it would be, but it is not the ONLY term - see
sim/tests/test_deposits.py's AlluvialVersusVeinTests.

WHAT THIS MODULE DELIBERATELY DOES NOT DO. It stops at ore (or, for gold and
tin, gravel) raised to the surface, in kilograms of CONTAINED metal - it does
not model smelting, roasting, retorting or refining, which is a separate,
metal-specific process with its own fuel and labour (data/world/
resources.json's own `constraints` section already carries some of that,
e.g. `charcoal_kg_per_kg_metal` for copper and lead smelting). This matters
most for mercury: cinnabar ore can be sold AS ITSELF (the pigment minium,
data/prices.json's cinnabar_kg), needing no metallurgy at all, but metallic
mercury needs roasting the ore and condensing the vapour, a real added cost
this module does not carry. See the module's own CALIBRATION TARGETS section
and sim/tests/test_deposits.py's BookPriceComparisonTests for exactly how
large that gap turns out to be and why it is the leading suspect for
mercury's own price still coming out far below book even after rent is
added - read that test's printed report rather than trusting this
docstring's numbers, which are illustrative and not re-verified here.

SINKING COST IS FIXED, NOT PER-TONNE - THE STAKEHOLDER'S FIRST OBSERVATION.
Everything above (`extraction_cost_labour_hours_per_kg`) is a RECURRING cost:
so many hours per tonne of rock or gravel raised, forever, for as long as the
deposit is worked, and that figure already never depended on the deposit's
richness (breaking a tonne of hard rock costs the same whether the vein
behind it is rich or poor - only how MANY tonnes must be broken to get one
kilogram of metal depends on grade). What this module did NOT have before
this task is the other half of the stakeholder's observation: "you have the
same cost to make a mine regardless of if there is 1 ton of gold in there, or
500 B tons of gold". That is a ONE-TIME, FIXED cost - sinking the shaft,
timbering it, building the hoist, or (for Las Medulas) building the aqueduct
- paid once regardless of what is eventually brought up through it.
`shaft_cost_labour_hours` gives that figure for ONE shaft from depth and rock
hardness alone, and `shafts_needed` counts how many a district's output
requires from what one shaft's hoist can raise (surface and hand-worked
alluvial ground need no shaft, so their fixed cost is zero); `amortized_sinking_cost_labour_hours_per_kg`
spreads it over the metal raised during one shaft service life
(`SHAFT_SERVICE_LIFE_YEARS`: timbering and headworks are rebuilt on that
timescale, so the horizon belongs to the works and not to the ore body; it is
deliberately a different knob from `DEPOSIT_ASSUMED_WORKING_LIFE_YEARS`, which
only sizes the demonstration reserve); `total_cost_labour_hours_per_kg`
is the two added together, and is what `supply_curve` and
`find_marginal_deposit` now sort and price by. Whether the sinking share is
large enough to reorder a supply curve is measured, not asserted: run the
script in Complaints/54. A deposit with a tiny output can be pushed out of
the market by its shaft cost alone even if its ore is rich, which a pure
per-tonne cost cannot produce.

DECLINING GRADE WITHIN A DEPOSIT - THE INTENSIVE MARGIN, AND THE STAKEHOLDER'S
SECOND OBSERVATION. Everything above `find_marginal_deposit` already models
the EXTENSIVE margin: a fixed list of named deposits, each at its own fixed
grade, exhausted one at a time as `DepositState`'s reserve runs out, forcing
the market to a costlier deposit next. That leaves out the mechanism inside
ONE deposit the stakeholder described directly: "it takes the same amount of
effort to mine the same amount ... but you would slowly go out of good
materials and have more waste materials". Real ore bodies are worked
best-ore-first, so the grade of what is actually being raised falls as the
deposit is worked, well before it runs out - which is why real extraction
costs rise secularly even without exhausting anything, a fact the old
all-or-nothing exhaustion model could not produce (its price was flat, then
jumped once, at zero warning, the instant a deposit's reserve hit zero).

`current_ore_grade_kg_per_tonne(deposit, fraction_extracted)` is the fix:
given how much of the deposit's assumed total reserve has already been
raised (0 = untouched, 1 = fully worked out), it returns a grade that has
fallen from the deposit's stated (richest, worked-first) grade toward zero.
`current_extraction_cost_labour_hours_per_kg` is
`extraction_cost_labour_hours_per_kg` run against that fallen grade instead
of the deposit's nominal one - and nothing else changes: the effort per
tonne of ROCK (`hardness_class`, `depth_class`) is exactly what it always
was, precisely the stakeholder's own intuition ("effort per tonne of rock is
roughly constant; what changes is the metal per tonne of rock"). `DepositState`
now tracks its own `fraction_extracted` (from how much of its ORIGINAL
reserve remains) and `simulate_depletion` builds each year's working deposit
at that year's fallen grade, so the EXTENSIVE margin (a deposit exhausts,
forcing a jump to the next one) and the INTENSIVE margin (a deposit's own
cost creeps up all through its working life) now sit on the same curve,
meeting exactly at fraction_extracted=1 where the fallen grade reaches zero
and the deposit's own cost goes to infinity - which is also, not
coincidentally, the point `DepositState.exhausted` already called it done.
The SHAPE of the decline (linear in fraction_extracted, `GRADE_DECLINE_
SHAPE_EXPONENT`'s own declaration explains why) is a placeholder for a real
surveyed grade-tonnage curve this project has for no deposit; the DIRECTION
(richer ore first, grade falls monotonically, effort per tonne of rock
unchanged) is the stakeholder's own claim and is not in doubt.

WASTE ROCK AND GRAVEL - MADE EXPLICIT, NOT LEFT IMPLICIT, BUT NOT DISPOSED OF
ANYWHERE YET. The stakeholder's third observation - "when you make a mine,
you have waste rock, gravel" - is already arithmetically PRESENT in
`extraction_cost_labour_hours_per_kg` (dividing hours-per-tonne-of-MATERIAL
by a grade of kilograms-per-tonne already charges for every tonne of
material moved, metal or not), but nothing named the quantity or let anyone
see that a 0.3 g/t placer deposit lifts roughly three million tonnes of
gravel for every tonne of gold. `material_moved_tonnes_per_kg_metal` and
`waste_tonnes_per_kg_metal` make that number a first-class, queryable fact,
and the module's own __main__ block prints it for a sample of deposits.
Computing the QUANTITY of waste is worth doing, because it is arithmetic
this module already implicitly does. Modelling WHERE that waste GOES -
burying farmland, silting a river the way Pliny's "ruina montium" did to
whatever lay downstream
of Las Medulas - is deliberately NOT done here: it needs a place for the
waste to go (a location, a downstream user of that land or river) that lives
in data/world/geography.json and whatever eventually represents farmland and
water quality, neither of which this module reads (see its own STANDALONE
section) and neither of which exists yet as a modelled stock. This is a
labelled hook, not a silent omission: the quantity is now computed and ready
for whichever future module gives waste rock somewhere to go.

POLYMETALLIC DEPOSITS - THE STAKEHOLDER'S FOURTH OBSERVATION. "A mine for
gold can also mine iron, copper, diamonds, as well as the gold." A `Deposit`
can now carry a `byproducts` tuple: other metals present in the SAME rock,
at their OWN grade, alongside the primary metal `load_deposits` already
builds it for. `byproduct_quantities_tonnes_per_year` computes how much of
each by-product necessarily comes up if the deposit is worked for its
primary metal at its stated rate - fixed by the ratio of the two grades,
never a quantity anyone chooses, exactly the geological fact Complaints/29
already established for germanium and indium riding along with zinc.
`joint_output_quantities_kg` packages primary-plus-byproducts as a plain
{material_key: kilograms/year} dict - the same shape sim.world.demand's
joint_output_mass_shares and joint_output_value_shares both take as their
own first argument (see that module's own functions, not imported here -
see this module's STANDALONE section) - so a caller with real prices in
hand can run this deposit's joint output straight through Complaints/29's
own demand-cleared value-share answer instead of a mass split.

A BYPRODUCT IS COUNTED ONCE: `load_deposits` of the byproduct's metal splits
only what the empire total leaves after the byproduct
(`empire_output_net_of_byproducts_tonnes_per_year`), so silver raised with
lead is not also asked of the silver-only deposits. A byproduct is stated as
an assay per tonne of the primary metal contained (`kg_per_tonne_of_primary_
metal` in the geography deposit catalogue), one figure per deposit.
"""
import collections
import json
import math
import os
from typing import Any, Dict, List, Optional

from sim.constants import declare
from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world import mine_fire_setting, mine_works
from sim.geography.api import deposit_records, tile_lookup

# ============================================================================
# DATA FILE LOCATIONS
# ============================================================================
# Same ROOT-relative pattern sim/engine/data.py already uses for these two
# existing files (RESFILE, GEOFILE there); repeated here rather than
# imported, for the same reason every sim/world/ module gives for not
# importing sim/engine/ - see the module docstring's STANDALONE section.

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
RESOURCES_FILE = os.path.join(_ROOT, "data", "world", "resources.json")

# The seven metals this module and the geography deposit catalogue cover -
# exactly the metals data/world/resources.json's empire_output_100ad table
# gives a Roman-era annual output for. Declared as a plain tuple, not
# through declare(): it is a list of names, not a fact with a value that
# could be wrong.
METALS = ("iron", "copper", "tin", "lead", "silver", "gold", "mercury")


# ============================================================================
# EXTRACTION COST CONSTANTS
# ============================================================================
# Every one of these is a labour-hours-per-tonne-of-material figure, not a
# price, and not read from anything this metal sells for. They are pre-
# blasting hand-tool figures throughout (hammer, wedge, fire-setting, spade,
# basket, ladder, windlass) since nothing in this project's timeframe has
# gunpowder blasting in general civilian use yet - see data/world/
# resources.json's own gunpowder_composition entry for how scarce saltpetre
# still is in 100 AD.

BREAKING_HOURS_PER_TONNE_SOFT = declare(
    "BREAKING_HOURS_PER_TONNE_SOFT", 3.0,
    kind="engineering_estimate",
    unit="labourer-hours/tonne of rock broken and raised",
    source="Friable, weathered or earthy ore - bog iron nodules raked from a "
           "lakebed, oxidised gossan, clay ironstone - needs no more than "
           "spade, mattock and basket to break and lift; pre-mechanical "
           "digging of loose or weakly consolidated ground is commonly "
           "cited at several tonnes per worker-day, i.e. a few hours per "
           "tonne.",
    confidence="C",
    why="The cheapest of the three hardness classes, and the reason bog "
        "iron and surface hematite were worked before anyone owned a shaft: "
        "no rock-breaking labour to speak of, only digging and hauling.")

BREAKING_HOURS_PER_TONNE_MEDIUM = declare(
    "BREAKING_HOURS_PER_TONNE_MEDIUM", 8.0,
    kind="engineering_estimate",
    unit="labourer-hours/tonne of rock broken and raised",
    source="Ordinary consolidated vein ore - galena, siderite, oxidised "
           "copper ore in a hard matrix - broken by hammer and wedge, "
           "assisted by fire-setting (heating the rock face, then "
           "quenching it to crack it) where the rock allows it. "
           "Pre-blasting hard-rock mining productivity is commonly cited "
           "on the order of half a tonne to a tonne per worker-day for "
           "moderately hard rock, i.e. roughly 8-16 hours/tonne; taken at "
           "the easier end.",
    confidence="C",
    why="The middle hardness class, and the one most named deposits in "
        "the geography deposit catalogue actually use - most pre-modern ore was "
        "neither loose earth nor the hardest vein quartz.")

BREAKING_HOURS_PER_TONNE_HARD = declare(
    "BREAKING_HOURS_PER_TONNE_HARD", 20.0,
    kind="engineering_estimate",
    unit="labourer-hours/tonne of rock broken and raised",
    source="Massive sulfide (Rio Tinto's copper-silver-lead ore) or hard "
           "quartz vein (Dacian gold-quartz) rock, worked without "
           "gunpowder. Fire-setting hard rock is notoriously slow - "
           "accounts of pre-blasting hard-rock mining productivity for the "
           "toughest rock commonly fall below half a tonne per worker-day, "
           "i.e. well over 16 hours/tonne; taken as a round 20.",
    confidence="C",
    why="The most expensive hardness class, and, paired with depth, the "
        "reason Rio Tinto's copper and Dacia's gold come out as this "
        "module's costliest deposits - see the module docstring's ALLUVIAL "
        "GOLD AND DEEP VEIN GOLD section.")

ALLUVIAL_HAND_PROCESSING_HOURS_PER_TONNE = declare(
    "ALLUVIAL_HAND_PROCESSING_HOURS_PER_TONNE", 1.5,
    kind="engineering_estimate",
    unit="labourer-hours/tonne of gravel dug and washed",
    source="Hand panning or simple ground-sluicing of loose river gravel "
           "(Cornish tin 'streaming') needs no rock-breaking labour at "
           "all, only digging the gravel and washing it across a riffle "
           "or in a pan; cheaper per tonne of MATERIAL than even soft-ore "
           "breaking, though the grade of what is being processed is "
           "usually far leaner than a worked vein.",
    confidence="C",
    why="What makes alluvial deposits worth working at much lower grades "
        "than hard-rock ones - see hardness_class in the module docstring "
        "and the tin entries in the geography deposit catalogue, none of which "
        "needed a vein-mining alternative in the Roman period at all.")

ALLUVIAL_HYDRAULIC_PROCESSING_HOURS_PER_TONNE = declare(
    "ALLUVIAL_HYDRAULIC_PROCESSING_HOURS_PER_TONNE", 0.05,
    kind="engineering_estimate",
    unit="labourer-hours/tonne of gravel moved and washed",
    source="Pliny, Natural History 33.66-78, describes the 'ruina montium' "
           "method at Las Medulas: aqueducts carrying water many "
           "kilometres collapsed whole hillsides and washed the resulting "
           "gravel through sluice channels, so the excavation itself costs "
           "almost no HUMAN labour per tonne moved - the labour is in "
           "building and maintaining the aqueduct once, not in moving each "
           "further tonne of gravel. Taken at thirtyfold below hand "
           "panning's rate as a round figure for what substituting water "
           "power for muscle power for the bulk-excavation step buys.",
    confidence="D",
    why="The entire reason Las Medulas could work gold gravel at a grade "
        "(0.0003 kg/t) that would be uneconomic to pan by hand at any "
        "price - see the module docstring's ALLUVIAL GOLD AND DEEP VEIN "
        "GOLD section for the number this produces. The multiple below "
        "hand-panning is this file's own placeholder, not a measured "
        "water-power figure; the mechanism (water substituting for "
        "muscle in the excavation step) is well attested, the SIZE of "
        "the saving is not.")

DEPOSIT_ASSUMED_WORKING_LIFE_YEARS = declare(
    "DEPOSIT_ASSUMED_WORKING_LIFE_YEARS", 150.0,
    kind="temporary_heuristic",
    unit="years",
    source="Several of the major Roman mining districts named in "
           "the geography deposit catalogue (Rio Tinto, Almaden, Las Medulas) "
           "were worked for centuries; 150 years is a round order-of-"
           "magnitude figure for how long a deposit sustains its derived "
           "annual quantity before running out, used only to give "
           "DepositState a finite reserve to demonstrate depletion "
           "against.",
    confidence="D",
    why="This is NOT a geological reserve estimate - the physically "
        "correct number would come from a surveyed ore-body volume times "
        "its grade, which this project has for none of these deposits. "
        "It exists purely so simulate_depletion() has a stock that "
        "actually runs out in a demonstrable number of years, showing the "
        "MECHANISM (a deposit's exhaustion forces the margin to a costlier "
        "one) without claiming to know any real mine's true remaining "
        "life.")

# ----------------------------------------------------------------------
# BUILD COST - what it takes to sink and equip a shaft, and what one shaft
# can raise. Nothing here reads ore grade or quantity: a shaft costs what
# its depth and rock cost, wherever it is dug.
# ----------------------------------------------------------------------

GRAVITY_METRES_PER_SECOND_SQUARED = declare(
    "GRAVITY_METRES_PER_SECOND_SQUARED", 9.81, kind="physical_constant",
    unit="m/s^2", source="Standard gravity.", confidence="A",
    why="Converts a lifted mass and height into work.")

ROCK_DENSITY_TONNES_PER_CUBIC_METRE = declare(
    "ROCK_DENSITY_TONNES_PER_CUBIC_METRE", 2.6, kind="physical_constant",
    unit="tonnes/m^3",
    source="Typical in-place density of crystalline and sedimentary host rock.",
    confidence="B",
    why="Turns a shaft's volume into tonnes of rock to break and hoist.")

HUMAN_SUSTAINED_POWER_WATTS = declare(
    "HUMAN_SUSTAINED_POWER_WATTS", 75.0, kind="biological_parameter",
    unit="watts of useful mechanical power per labourer, sustained over a shift",
    source="Sustained human work output is commonly put at 50-100 W.",
    confidence="B",
    why="Sets how fast a hand windlass crew can lift rock from depth.")

HOIST_MECHANICAL_EFFICIENCY = declare(
    "HOIST_MECHANICAL_EFFICIENCY", 0.5, kind="engineering_estimate",
    unit="fraction of labourer power that becomes lift",
    source=None, confidence="D",
    why="Rope, axle and basket friction and idle return strokes in a hand "
        "windlass; an order-of-magnitude figure.")

HOIST_CREW_SIZE = declare(
    "HOIST_CREW_SIZE", 8.0, kind="temporary_heuristic",
    unit="labourers on one shaft's hoist", source=None, confidence="D",
    why="How many people turn one shaft's windlass; a shaft's raising "
        "capacity scales with it. Replace with a hoist-design derivation.")

HOIST_HOURS_PER_YEAR = declare(
    "HOIST_HOURS_PER_YEAR", 2000.0, kind="temporary_heuristic",
    unit="hours/year a hoist crew works", source=None, confidence="D",
    why="A working year for the hoist crew.")

SHAFT_CROSS_SECTION_SQUARE_METRES = declare(
    "SHAFT_CROSS_SECTION_SQUARE_METRES", 2.0, kind="engineering_estimate",
    unit="m^2",
    source="Ancient shafts at Laurion and Rio Tinto were narrow rectangular "
           "or square drives a metre or two a side.",
    confidence="C",
    why="With depth and rock density, sets the tonnes of rock a shaft removes.")

SHAFT_DEPTH_METRES_SHALLOW_VEIN = declare(
    "SHAFT_DEPTH_METRES_SHALLOW_VEIN", 30.0, kind="temporary_heuristic",
    unit="metres", source=None, confidence="D",
    why="the deposit catalogue gives a depth class, not a depth; this is the depth "
        "assumed for the shallow class until the data carries metres.")

SHAFT_DEPTH_METRES_DEEP_VEIN = declare(
    "SHAFT_DEPTH_METRES_DEEP_VEIN", 100.0, kind="temporary_heuristic",
    unit="metres",
    source="Rio Tinto's drained shafts reached about a hundred metres.",
    confidence="D",
    why="Depth assumed for the deep class until the data carries metres.")

SHAFT_SUPPORT_HOURS_PER_METRE = declare(
    "SHAFT_SUPPORT_HOURS_PER_METRE", 60.0, kind="temporary_heuristic",
    unit="labourer-hours per metre of shaft at the surface, for timbering "
         "and lining", source=None, confidence="D",
    why="Cutting, dressing and fitting timber to hold a shaft's walls.")

SHAFT_SUPPORT_DEPTH_SCALE_METRES = declare(
    "SHAFT_SUPPORT_DEPTH_SCALE_METRES", 100.0, kind="temporary_heuristic",
    unit="metres of depth over which support per metre doubles",
    source=None, confidence="D",
    why="Rock pressure grows with depth, so each further metre needs "
        "more support.")

SHAFT_DRAINAGE_HOURS_PER_METRE_OF_HEAD = declare(
    "SHAFT_DRAINAGE_HOURS_PER_METRE_OF_HEAD", 100.0, kind="temporary_heuristic",
    unit="labourer-hours per metre of depth, to build the water-lifting works",
    source=None, confidence="D",
    why="The water a shaft meets must be lifted out; the works to do it "
        "grow with the height to lift.")

SHAFT_SERVICE_LIFE_YEARS = declare(
    "SHAFT_SERVICE_LIFE_YEARS", 30.0, kind="engineering_estimate",
    unit="years a sunk shaft and its headworks serve before being rebuilt",
    source="Timber shaft lining, windlass frame and drainage works rot and "
           "are replaced on a timescale of decades in the documented "
           "ancient and medieval mining districts.",
    confidence="D",
    why="The horizon over which one shaft's build cost is spread. It is a "
        "property of the works, not of the ore body, so it is separate "
        "from DEPOSIT_ASSUMED_WORKING_LIFE_YEARS (a stock for the depletion "
        "demonstration); a shaft that outlasts neither is rebuilt, and each "
        "rebuild costs the same again.")

HOIST_FRAME_HOURS = declare(
    "HOIST_FRAME_HOURS", 500.0, kind="temporary_heuristic",
    unit="labourer-hours per shaft", source=None, confidence="D",
    why="Building the windlass frame and headworks over a shaft.")

AQUEDUCT_CONSTRUCTION_HOURS_ALLUVIAL_HYDRAULIC = declare(
    "AQUEDUCT_CONSTRUCTION_HOURS_ALLUVIAL_HYDRAULIC", 500000.0,
    kind="temporary_heuristic",
    unit="labourer-hours to build ONE aqueduct and sluice system",
    source="Pliny, Natural History 33.66-78 describes aqueducts carrying "
           "water many kilometres to Las Medulas.",
    confidence="D",
    why="No ancient source gives labour-hours; an order-of-magnitude "
        "placeholder for canal length times digging rate. One system "
        "supplies the flow set by AQUEDUCT_WATER_FLOW_CUBIC_METRES_PER_SECOND.")

AQUEDUCT_WATER_FLOW_CUBIC_METRES_PER_SECOND = declare(
    "AQUEDUCT_WATER_FLOW_CUBIC_METRES_PER_SECOND", 0.5, kind="temporary_heuristic",
    unit="m^3/s delivered by one aqueduct system", source=None, confidence="D",
    why="Sets how much gravel one aqueduct system can wash per year.")

SLUICING_WATER_CUBIC_METRES_PER_TONNE_GRAVEL = declare(
    "SLUICING_WATER_CUBIC_METRES_PER_TONNE_GRAVEL", 10.0,
    kind="engineering_estimate",
    unit="m^3 of water per tonne of gravel washed", source=None,
    confidence="D",
    why="Water needed to break down and carry a tonne of gravel through "
        "the sluices.")

SECONDS_PER_YEAR = declare(
    "SECONDS_PER_YEAR", 31557600.0, kind="physical_constant",
    unit="seconds/year", source="Julian year.", confidence="A",
    why="Converts a flow rate into a yearly volume.")

SECONDS_PER_HOUR = declare(
    "SECONDS_PER_HOUR", 3600.0, kind="physical_constant",
    unit="seconds/hour", source="Definition.", confidence="A",
    why="Converts labour-hours to seconds of work.")

GRADE_DECLINE_SHAPE_EXPONENT = declare(
    "GRADE_DECLINE_SHAPE_EXPONENT", 1.0,
    kind="temporary_heuristic",
    unit="dimensionless exponent p in "
         "grade(fraction_extracted) = initial_grade * (1 - fraction_extracted)**p",
    source=None,
    confidence="D",
    why="Real ore bodies have their own surveyed grade-tonnage curve - how "
        "the grade of the ore actually being mined falls as cumulative "
        "tonnage rises - and this project has none surveyed for any named "
        "deposit. p=1 (a straight-line decline from the deposit's stated, "
        "richest grade at fraction_extracted=0 to exactly zero at "
        "fraction_extracted=1) is the simplest monotonic placeholder "
        "consistent with the stakeholder's own observation that the best "
        "ore is worked first and grade falls as a deposit is worked out; "
        "it is NOT a claim that any real deposit's curve is actually "
        "linear (many are closer to lognormal, with a long low-grade "
        "tail), only that grade falls monotonically and reaches zero "
        "exactly where DepositState already calls the deposit exhausted - "
        "see the module docstring's DECLINING GRADE WITHIN A DEPOSIT "
        "section for why that meeting point matters.")


_HARDNESS_BREAKING_HOURS = {
    "soft": BREAKING_HOURS_PER_TONNE_SOFT,
    "medium": BREAKING_HOURS_PER_TONNE_MEDIUM,
    "hard": BREAKING_HOURS_PER_TONNE_HARD,
}

# Shaft depth per depth class; classes with no shaft are absent.
_SHAFT_DEPTH_METRES = {
    "shallow_vein": SHAFT_DEPTH_METRES_SHALLOW_VEIN,
    "deep_vein": SHAFT_DEPTH_METRES_DEEP_VEIN,
}

DEPTH_CLASSES = ("surface", "shallow_vein", "deep_vein", "alluvial",
                  "alluvial_hydraulic")
HARDNESS_CLASSES = ("soft", "medium", "hard")


# ============================================================================
# DEPOSIT
# ============================================================================

ByproductSpec = collections.namedtuple("ByproductSpec", [
    "metal",                       # e.g. "silver" - one of METALS, or any
                                    # other metal name this file does not
                                    # itself carry a full deposit list for
    "material_key",                # sim.world.demand's own spelling, e.g.
                                    # "silver_kg" - see POLYMETALLIC
                                    # DEPOSITS in the module docstring
    "ore_grade_kg_per_tonne",      # kg of this BYPRODUCT per tonne of the
                                    # SAME rock the primary metal is graded
                                    # against - a second, independent
                                    # geological fact about one rock, not a
                                    # fraction of the primary grade
])

Deposit = collections.namedtuple("Deposit", [
    "name",
    "metal",
    "tile",                       # key of geography.json's land_tiles that
                                  # holds the deposit's lat/lon
    "material_moved",             # "ore" or "gravel"
    "ore_grade_kg_per_tonne",     # kg of CONTAINED METAL per tonne raised
    "depth_class",
    "hardness_class",             # None for alluvial deposits
    "quantity_tonnes_per_year",   # this deposit's derived annual output
    "note",
    "byproducts",                 # tuple of ByproductSpec, empty for most
                                   # deposits - see POLYMETALLIC DEPOSITS
    "ore_type",                   # "primary" for ore smelted or amalgamated
                                   # as such; "jarosite" for gossan that
                                   # needs added lead as a collector
], defaults=((), "primary"))


def extraction_cost_labour_hours_per_kg(deposit: "Deposit") -> float:
    """Labour-hours to raise one kilogram of CONTAINED METAL from `deposit`,
    from physical properties alone. Never reads a price anywhere - see the
    module docstring's EXTRACTION COST MECHANICS section for what each of
    the three inputs means and sim/tests/test_deposits.py's
    NoPriceDataTests for the check that this stays true.

    This is the RECURRING cost only - so many hours per tonne, forever - and
    always uses the deposit's own stated (virgin, richest) grade. A caller
    that wants the grade actually being worked at some point in the
    deposit's life should go through current_extraction_cost_labour_hours_
    per_kg instead (see the module docstring's DECLINING GRADE WITHIN A
    DEPOSIT section); a caller that wants the FULL unit cost including the
    fixed, one-time cost of opening the deposit should use
    total_cost_labour_hours_per_kg (see SINKING COST).
    """
    if deposit.depth_class == "alluvial_hydraulic":
        hours_per_tonne_material = ALLUVIAL_HYDRAULIC_PROCESSING_HOURS_PER_TONNE
    elif deposit.depth_class == "alluvial":
        hours_per_tonne_material = ALLUVIAL_HAND_PROCESSING_HOURS_PER_TONNE
    else:
        hours_per_tonne_material = vein_hours_per_tonne_ore(deposit)
    return hours_per_tonne_material / deposit.ore_grade_kg_per_tonne


def vein_hours_per_tonne_ore(deposit: "Deposit") -> float:
    """Labourer-hours per tonne of ore presented from a vein or surface
    working: breaking and fire-setting every tonne of rock broken (ore plus
    the barren rock that comes with it), then hoisting, carrying, draining
    and timbering (sim/world/mine_works.py)."""
    rock_per_ore = mine_works.rock_broken_tonnes_per_tonne_ore(deposit.depth_class)
    on_rock = (_HARDNESS_BREAKING_HOURS[deposit.hardness_class]
               + mine_fire_setting.fire_setting_labour_hours_per_tonne_rock(
                   deposit.hardness_class))
    on_ore = sum(mine_works.works_hours_per_tonne_ore(
        deposit.depth_class, deposit.hardness_class,
        _lift_hours_per_tonne_metre(), shaft_depth_metres(deposit),
        mine_fire_setting.MINING_SHIFT_HOURS).values())
    return on_rock * rock_per_ore + on_ore


# ============================================================================
# BUILD COST - shafts to sink, what each costs, what each can raise
# ============================================================================
# A shaft costs what its depth and rock make it cost. The number of shafts a
# district needs follows from the rock it must raise per year against what
# one shaft's hoist can lift from that depth. Hydraulic ground counts one
# aqueduct system as the unit instead of a shaft.

def shaft_depth_metres(deposit: "Deposit") -> float:
    """Depth of one shaft into `deposit`; zero where no shaft is dug."""
    return _SHAFT_DEPTH_METRES.get(deposit.depth_class, 0.0)


def _lift_hours_per_tonne_metre() -> float:
    """Labourer-hours to lift one tonne one metre by hand windlass."""
    joules_per_tonne_metre = (GRAVITY_METRES_PER_SECOND_SQUARED
                              * KILOGRAMS_PER_TONNE)
    return joules_per_tonne_metre / (
        HUMAN_SUSTAINED_POWER_WATTS * HOIST_MECHANICAL_EFFICIENCY
        * SECONDS_PER_HOUR)


def shaft_cost_labour_hours(deposit: "Deposit") -> float:
    """Labour-hours to sink and equip ONE shaft (or build one aqueduct
    system for hydraulic ground): breaking the rock, lifting the spoil,
    timbering, draining, and the hoist frame. Reads depth and hardness
    only, never grade or quantity. Zero for surface and hand-worked
    alluvial ground.
    """
    if deposit.depth_class == "alluvial_hydraulic":
        return AQUEDUCT_CONSTRUCTION_HOURS_ALLUVIAL_HYDRAULIC
    depth = shaft_depth_metres(deposit)
    if depth <= 0.0:
        return 0.0
    tonnes_per_metre = (SHAFT_CROSS_SECTION_SQUARE_METRES
                        * ROCK_DENSITY_TONNES_PER_CUBIC_METRE)
    breaking = (tonnes_per_metre * depth
                * _HARDNESS_BREAKING_HOURS[deposit.hardness_class])
    # Spoil from depth z is lifted z metres; summed over the shaft that is depth^2 / 2.
    spoil_lift = tonnes_per_metre * _lift_hours_per_tonne_metre() * depth ** 2 / 2.0
    # Support per metre grows linearly with depth.
    support = SHAFT_SUPPORT_HOURS_PER_METRE * (
        depth + depth ** 2 / (2.0 * SHAFT_SUPPORT_DEPTH_SCALE_METRES))
    drainage = SHAFT_DRAINAGE_HOURS_PER_METRE_OF_HEAD * depth
    # A ventilation shaft is sunk and lined like the working shaft but has
    # no hoist frame and no sump.
    ventilation = (mine_works.VENTILATION_OPENINGS_PER_WORKING_SHAFT
                   * (breaking + spoil_lift + support))
    return (breaking + spoil_lift + support + drainage + HOIST_FRAME_HOURS
            + ventilation)


def shaft_rock_capacity_tonnes_per_year(deposit: "Deposit") -> float:
    """Tonnes of rock (or gravel) one shaft's hoist, or one aqueduct
    system's flow, can raise or wash per year. Hoisting is work-limited:
    crew power times efficiency times hours, over the weight lifted
    through the shaft's depth. Infinite where no works are needed.
    """
    if deposit.depth_class == "alluvial_hydraulic":
        return (AQUEDUCT_WATER_FLOW_CUBIC_METRES_PER_SECOND * SECONDS_PER_YEAR
                / SLUICING_WATER_CUBIC_METRES_PER_TONNE_GRAVEL)
    depth = shaft_depth_metres(deposit)
    if depth <= 0.0:
        return float("inf")
    crew_work_joules = (HOIST_CREW_SIZE * HUMAN_SUSTAINED_POWER_WATTS
                        * HOIST_MECHANICAL_EFFICIENCY * HOIST_HOURS_PER_YEAR
                        * SECONDS_PER_HOUR)
    joules_per_tonne = (GRAVITY_METRES_PER_SECOND_SQUARED * KILOGRAMS_PER_TONNE
                        * depth)
    return crew_work_joules / joules_per_tonne


def shafts_needed_fractional(deposit: "Deposit", tonnes_metal_per_year: float) -> float:
    """Shafts (or aqueduct systems) `tonnes_metal_per_year` of contained
    metal needs, before rounding up: rock to raise per year over what one
    shaft raises."""
    if tonnes_metal_per_year <= 0.0:
        return 0.0
    rock_tonnes_per_year = (tonnes_metal_per_year * KILOGRAMS_PER_TONNE
                            * material_moved_tonnes_per_kg_metal(deposit))
    return rock_tonnes_per_year / shaft_rock_capacity_tonnes_per_year(deposit)


def shafts_needed(deposit: "Deposit", tonnes_metal_per_year: float) -> int:
    """Whole shafts needed to raise `tonnes_metal_per_year` of metal."""
    fractional = shafts_needed_fractional(deposit, tonnes_metal_per_year)
    if fractional <= 0.0:
        return 0
    # The tolerance absorbs floating-point noise on an exact multiple.
    return math.ceil(fractional - 1e-9)


def build_cost_labour_hours(deposit: "Deposit", tonnes_metal_per_year: float) -> float:
    """Labour-hours to open capacity for `tonnes_metal_per_year`: whole
    shafts times the per-shaft cost."""
    return shafts_needed(deposit, tonnes_metal_per_year) * shaft_cost_labour_hours(deposit)


def build_cost_labour_hours_per_tonne_year(deposit: "Deposit") -> float:
    """Build cost per tonne/year of capacity, shafts counted fractionally,
    for pricing a fleet large enough that rounding is immaterial."""
    return shafts_needed_fractional(deposit, 1.0) * shaft_cost_labour_hours(deposit)


def amortized_sinking_cost_labour_hours_per_kg(
        deposit: "Deposit", shaft_service_life_years: Optional[float] = None) -> float:
    """The whole district's build cost (shafts for its own annual output
    times the per-shaft cost), spread over the metal raised during one
    shaft service life (SHAFT_SERVICE_LIFE_YEARS), not over the assumed
    reserve. Zero where no works are needed.
    """
    fixed_hours = build_cost_labour_hours(deposit, deposit.quantity_tonnes_per_year)
    if fixed_hours <= 0.0:
        return 0.0
    shaft_service_life_years = (SHAFT_SERVICE_LIFE_YEARS
                                if shaft_service_life_years is None
                                else shaft_service_life_years)
    output_over_service_life_kg = (deposit.quantity_tonnes_per_year
                                   * shaft_service_life_years * KILOGRAMS_PER_TONNE)
    if output_over_service_life_kg <= 0.0:
        return float("inf")
    return fixed_hours / output_over_service_life_kg


def total_cost_labour_hours_per_kg(deposit: "Deposit") -> float:
    """The deposit's full unit cost: the recurring extraction cost plus its
    fixed sinking cost amortised over one shaft service life. This is
    what supply_curve and find_marginal_deposit actually sort and price by
    - see the module docstring's SINKING COST section for why a pure
    per-tonne cost cannot, on its own, make a poor deposit uneconomic at
    low demand and economic at high demand.
    """
    return (extraction_cost_labour_hours_per_kg(deposit)
            + amortized_sinking_cost_labour_hours_per_kg(deposit))


# ============================================================================
# DECLINING GRADE WITHIN A DEPOSIT - the intensive margin
# ============================================================================
# See the module docstring's own DECLINING GRADE WITHIN A DEPOSIT section.

def current_ore_grade_kg_per_tonne(deposit: "Deposit", fraction_extracted: float) -> float:
    """The grade of the ore actually being raised NOW, given that
    `fraction_extracted` (0.0 = untouched, 1.0 = the deposit's whole
    assumed reserve already raised) of `deposit` has already been worked.
    Declared as a straight-line decline from the deposit's own stated
    grade at fraction_extracted=0 to zero at fraction_extracted=1 - see
    GRADE_DECLINE_SHAPE_EXPONENT's own declaration for what this shape
    does and does not claim.
    """
    if not 0.0 <= fraction_extracted <= 1.0:
        raise ValueError("fraction_extracted must be within [0, 1]: %r"
                          % (fraction_extracted,))
    remaining_share = (1.0 - fraction_extracted) ** GRADE_DECLINE_SHAPE_EXPONENT
    return deposit.ore_grade_kg_per_tonne * remaining_share


def current_extraction_cost_labour_hours_per_kg(
        deposit: "Deposit", fraction_extracted: float) -> float:
    """extraction_cost_labour_hours_per_kg, but at the grade actually being
    worked at this point in the deposit's life rather than its virgin
    grade. The effort per tonne of ROCK (hardness_class, depth_class) is
    untouched - only the grade that divides it falls, exactly the
    stakeholder's own "effort per tonne of rock is roughly constant; what
    changes is the metal per tonne of rock". At fraction_extracted=1.0 the
    grade is zero and this is float('inf') - the deposit is worked out.
    """
    grade_now = current_ore_grade_kg_per_tonne(deposit, fraction_extracted)
    if grade_now <= 0.0:
        return float("inf")
    return extraction_cost_labour_hours_per_kg(
        deposit._replace(ore_grade_kg_per_tonne=grade_now))


# ============================================================================
# WASTE ROCK AND GRAVEL - made explicit
# ============================================================================
# See the module docstring's own WASTE ROCK AND GRAVEL section for why this
# is computed (it was already implicit in the cost arithmetic above) and
# why disposing of it is deliberately NOT modelled here.

def material_moved_tonnes_per_kg_metal(deposit: "Deposit") -> float:
    """Tonnes of rock (or gravel) that must be raised to recover one
    kilogram of CONTAINED METAL from `deposit`'s own stated grade - the
    plain inverse of ore_grade_kg_per_tonne, expressed in the units the
    stakeholder's own question was asked in.
    """
    return 1.0 / deposit.ore_grade_kg_per_tonne


def waste_tonnes_per_kg_metal(deposit: "Deposit") -> float:
    """material_moved_tonnes_per_kg_metal minus the (usually negligible)
    tonnage the recovered metal itself accounts for - everything that
    comes up that is NOT the metal: at Las Medulas's 0.0003 kg/t this is
    all but one part in about three million of what is lifted.
    """
    return material_moved_tonnes_per_kg_metal(deposit) - 1.0 / KILOGRAMS_PER_TONNE


def annual_waste_rock_tonnes(deposit: "Deposit") -> float:
    """Tonnes/year of waste rock or gravel `deposit` produces at its own
    quantity_tonnes_per_year (tonnes of METAL/year) - the number that
    would have to go somewhere (spoil heap, tailings pond, a river, in Las
    Medulas's own case) if this project modelled where waste rock goes,
    which it does not yet - see the module docstring's own judgement.
    """
    return deposit.quantity_tonnes_per_year * KILOGRAMS_PER_TONNE * waste_tonnes_per_kg_metal(deposit)


# ============================================================================
# POLYMETALLIC DEPOSITS - byproducts fixed by geology
# ============================================================================
# See the module docstring's own POLYMETALLIC DEPOSITS section.

def byproduct_quantities_tonnes_per_year(deposit: "Deposit") -> Dict[str, float]:
    """{byproduct metal name: tonnes/year}, for every ByproductSpec
    `deposit` carries - the quantity of each byproduct that necessarily
    comes up if `deposit` is worked for its PRIMARY metal at its own
    quantity_tonnes_per_year, fixed by the ratio of the byproduct's own
    grade to the primary metal's grade. Nothing here is a choice: this is
    what the rock contains, not what anyone wants out of it. Empty dict
    for a deposit with no byproducts at all.
    """
    if not deposit.byproducts:
        return {}
    rock_or_gravel_tonnes_per_year = (
        deposit.quantity_tonnes_per_year * KILOGRAMS_PER_TONNE / deposit.ore_grade_kg_per_tonne)
    return {
        spec.metal: rock_or_gravel_tonnes_per_year * spec.ore_grade_kg_per_tonne / KILOGRAMS_PER_TONNE
        for spec in deposit.byproducts
    }


def joint_output_quantities_kg(deposit: "Deposit") -> Dict[str, float]:
    """{material_key: kilograms/year} for `deposit`'s primary metal plus
    every byproduct it carries - the SAME {material_key: quantity} shape
    sim.world.demand's joint_output_mass_shares and joint_output_value_
    shares both take as their own first argument (see that module's own
    functions - not imported here, see this module's STANDALONE section),
    so a caller holding real prices can feed a polymetallic deposit's
    output straight into Complaints/29's demand-cleared value split
    instead of a mass split.
    """
    primary_key = "%s_kg" % deposit.metal
    out = {primary_key: deposit.quantity_tonnes_per_year * KILOGRAMS_PER_TONNE}
    byproduct_tonnes = byproduct_quantities_tonnes_per_year(deposit)
    for spec in deposit.byproducts:
        out[spec.material_key] = byproduct_tonnes[spec.metal] * KILOGRAMS_PER_TONNE
    return out


# ============================================================================
# LOADING DEPOSITS
# ============================================================================

def _load_json(path: str) -> Any:
    with open(path, "r") as handle:
        return json.load(handle)


_GRADE_DECLARED: set = set()


def _declare_grade(deposit_entry: Dict[str, Any], metal: str) -> float:
    """Run every deposit's ore_grade_kg_per_tonne through declare(), with
    the provenance the geography deposit catalogue already carries per entry -
    see that file's own _doc for why the grade itself lives in JSON (a
    table of ~20 deposits) while still going through the same provenance
    registry every other physical fact in this project does.
    """
    name = "DEPOSIT_GRADE_%s_%s" % (metal.upper(), deposit_entry["name"].upper())
    if name in _GRADE_DECLARED:
        return deposit_entry["ore_grade_kg_per_tonne"]
    _GRADE_DECLARED.add(name)
    unit = ("kg contained metal / tonne gravel"
            if deposit_entry["material_moved"] == "gravel"
            else "kg contained metal / tonne ore")
    confidence = deposit_entry.get("conf", "D")
    kind = "engineering_estimate" if confidence in ("A", "B", "C") else "temporary_heuristic"
    return declare(
        name, deposit_entry["ore_grade_kg_per_tonne"],
        kind=kind, unit=unit, source=deposit_entry.get("source"),
        confidence=confidence,
        why="This deposit's ore grade, the dominant term in its extraction "
            "cost (see extraction_cost_labour_hours_per_kg) - a physical "
            "fact about the rock, read from the geography deposit catalogue's "
            "%r entry and never derived from what %s sells for."
            % (deposit_entry["name"], metal))


def _declare_byproduct_grade(
        deposit_entry: Dict[str, Any], byproduct_entry: Dict[str, Any],
        primary_metal: str) -> float:
    """The byproduct's grade in the rock, from its assay per tonne of the
    primary metal contained (`kg_per_tonne_of_primary_metal`, the figure
    sources quote) times the deposit's own primary grade. The assay goes
    through declare() as a physical fact about this deposit's rock, never
    derived from what either metal sells for; it shares the "DEPOSIT_GRADE_"
    prefix so sim/tests/test_deposits.py's kind check covers it."""
    grade = (deposit_entry["ore_grade_kg_per_tonne"]
             * byproduct_entry["kg_per_tonne_of_primary_metal"] / KILOGRAMS_PER_TONNE)
    name = "DEPOSIT_GRADE_%s_BYPRODUCT_%s_%s" % (
        byproduct_entry["metal"].upper(), primary_metal.upper(),
        deposit_entry["name"].upper())
    if name in _GRADE_DECLARED:
        return grade
    _GRADE_DECLARED.add(name)
    confidence = byproduct_entry.get("conf", "D")
    kind = "engineering_estimate" if confidence in ("A", "B", "C") else "temporary_heuristic"
    declare(
        name, byproduct_entry["kg_per_tonne_of_primary_metal"],
        kind=kind,
        unit="kg of %s per tonne of %s contained in %s's rock"
             % (byproduct_entry["metal"], primary_metal, deposit_entry["name"]),
        source=byproduct_entry.get("source"), confidence=confidence,
        why="A polymetallic by-product assay - %s's %s ore also carries "
            "%s, fixed by geology (see the module docstring's POLYMETALLIC "
            "DEPOSITS section): opening the deposit for %s necessarily "
            "raises this much %s too, and it is never derived from what "
            "either metal sells for."
            % (deposit_entry["name"], primary_metal, byproduct_entry["metal"],
               primary_metal, byproduct_entry["metal"]))
    return grade


_SHARE_DECLARED: set = set()


def _declare_explicit_share(deposit_entry: Dict[str, Any], metal: str) -> float:
    """share_of_empire_output: this deposit's slice of the metal's output,
    the figure the quantity is derived from. Declared because it is a number
    this file asserts, not arithmetic on an already-declared one."""
    name = "DEPOSIT_SHARE_%s_%s" % (metal.upper(), deposit_entry["name"].upper())
    if name in _SHARE_DECLARED:
        return deposit_entry["share_of_empire_output"]
    _SHARE_DECLARED.add(name)
    confidence = deposit_entry.get("conf", "D")
    return declare(
        name, deposit_entry["share_of_empire_output"],
        kind="temporary_heuristic",
        unit="fraction of empire_output_100ad for this metal (dimensionless)",
        source=deposit_entry.get("source"),
        confidence=confidence,
        why="Stands in for a located production figure per deposit: the "
            "share of the %s output of the Roman world worked at this "
            "site, normalised so the deposits of one metal sum to about "
            "1.0 (see the geography deposit catalogue's own _doc)." % metal)


def load_deposit_data() -> Dict[str, Any]:
    """{"deposits": {metal: [entry]}}: the geography catalogue's named deposits that carry a share of the
    empire's output, in the catalogue's order (metals by first appearance), each entry's `name` the catalogue id."""
    data: Dict[str, Any] = {"deposits": {}}
    for row in deposit_records():
        if row.get("resource") in METALS and "share_of_empire_output" in row:
            data["deposits"].setdefault(row["resource"], []).append(dict(row, name=row["id"]))
    for metal in METALS:
        data["deposits"].setdefault(metal, [])
    return data


def empire_output_net_of_byproducts_tonnes_per_year(
        metal: str, resources: Optional[Dict[str, Any]] = None,
        deposits_data: Optional[Dict[str, Any]] = None) -> float:
    """The empire total of `metal` less what other metals' deposits raise of
    it as a byproduct (silver riding with lead), so one ounce is counted once:
    this is what the metal's own deposits must supply and the quantity its
    own shares split (Complaints/291). Byproduct tonnes are the other
    deposit's share times its own empire total times the assay, which needs
    no grade."""
    resources = resources if resources is not None else _load_json(RESOURCES_FILE)
    deposits_data = (deposits_data if deposits_data is not None
                     else load_deposit_data())
    total = resources["empire_output_100ad"][metal]["t_per_yr"]
    for other_metal, entries in deposits_data["deposits"].items():
        if other_metal == metal:
            continue
        other_total = resources["empire_output_100ad"][other_metal]["t_per_yr"]
        for entry in entries:
            for byproduct_entry in entry.get("byproducts", []):
                if byproduct_entry["metal"] == metal:
                    total -= (entry["share_of_empire_output"] * other_total
                              * byproduct_entry["kg_per_tonne_of_primary_metal"]
                              / KILOGRAMS_PER_TONNE)
    return max(0.0, total)


def load_deposits(
        metal: str, resources: Optional[Dict[str, Any]] = None,
        deposits_data: Optional[Dict[str, Any]] = None) -> List["Deposit"]:
    """Every named deposit for `metal`, with its extraction-cost inputs and
    its derived `quantity_tonnes_per_year`: the deposit's own
    share_of_empire_output times data/world/resources.json's
    empire_output_100ad. Each deposit sits on the land tile holding its lat/lon
    (a key of geography.json's land_tiles); nothing here reads the region
    records.

    The data arguments default to loading the files fresh, and are accepted
    purely so a caller (or a test) that already has them in hand is not made
    to re-read them.
    """
    if metal not in METALS:
        raise ValueError("unknown metal %r; must be one of %s" % (metal, METALS))
    resources = resources if resources is not None else _load_json(RESOURCES_FILE)
    deposits_data = (deposits_data if deposits_data is not None
                     else load_deposit_data())

    empire_total_tonnes = empire_output_net_of_byproducts_tonnes_per_year(
        metal, resources, deposits_data)

    out = []
    for entry in deposits_data["deposits"].get(metal, []):
        grade = _declare_grade(entry, metal)
        share = _declare_explicit_share(entry, metal)
        quantity_tonnes_per_year = share * empire_total_tonnes
        byproducts = tuple(
            ByproductSpec(
                metal=byproduct_entry["metal"],
                material_key=byproduct_entry.get(
                    "material_key", "%s_kg" % byproduct_entry["metal"]),
                ore_grade_kg_per_tonne=_declare_byproduct_grade(
                    entry, byproduct_entry, metal))
            for byproduct_entry in entry.get("byproducts", []))
        out.append(Deposit(
            name=entry["name"],
            metal=metal,
            tile=tile_lookup.tile_holding(entry["lat"], entry["lon"]),
            material_moved=entry["material_moved"],
            ore_grade_kg_per_tonne=grade,
            depth_class=entry["depth_class"],
            hardness_class=entry.get("hardness_class"),
            quantity_tonnes_per_year=quantity_tonnes_per_year,
            note=entry.get("source", ""),
            byproducts=byproducts,
            ore_type=entry.get("ore_type", "primary")))
    return out


# ============================================================================
# THE SUPPLY CURVE
# ============================================================================

SupplyCurvePoint = collections.namedtuple("SupplyCurvePoint", [
    "deposit",
    "own_cost_labour_hours_per_kg",
    "quantity_tonnes_per_year",
    "cumulative_quantity_tonnes_per_year",
])


def supply_curve(deposits: List["Deposit"]) -> List["SupplyCurvePoint"]:
    """`deposits`, sorted cheapest-first, each annotated with its own FULL
    unit cost (total_cost_labour_hours_per_kg: recurring extraction plus
    amortised sinking - see the module docstring's SINKING COST section)
    and the running total of quantity available at or below that cost -
    the object Complaints/32 says this project is missing entirely. Ties
    broken by name, so the curve is deterministic regardless of the order
    `deposits` arrives in.
    """
    ordered = sorted(
        deposits,
        key=lambda d: (total_cost_labour_hours_per_kg(d), d.name))
    points = []
    cumulative = 0.0
    for deposit in ordered:
        cumulative += deposit.quantity_tonnes_per_year
        points.append(SupplyCurvePoint(
            deposit=deposit,
            own_cost_labour_hours_per_kg=total_cost_labour_hours_per_kg(deposit),
            quantity_tonnes_per_year=deposit.quantity_tonnes_per_year,
            cumulative_quantity_tonnes_per_year=cumulative))
    return points


# ============================================================================
# THE MARGINAL DEPOSIT AND RENT
# ============================================================================

Allocation = collections.namedtuple("Allocation", [
    "deposit",
    "quantity_supplied_tonnes_per_year",
    "own_cost_labour_hours_per_kg",
    "rent_labour_hours_per_kg",
    "rent_total_labour_hours_per_year",
])

MarginalOutcome = collections.namedtuple("MarginalOutcome", [
    "quantity_demanded_tonnes_per_year",
    "price_at_margin_labour_hours_per_kg",
    "marginal_deposit",
    "allocations",
    "quantity_supplied_tonnes_per_year",
    "unmet_demand_tonnes_per_year",
])


def find_marginal_deposit(
        deposits: List["Deposit"],
        quantity_demanded_tonnes_per_year: float) -> "MarginalOutcome":
    """The Ricardian rent calculation this module exists for.

    Walks `deposits` cheapest-first, filling `quantity_demanded_tonnes_per_
    year` from the cheapest available deposit first, then the next, and so
    on. The deposit whose quantity fills the LAST unit of demand is
    marginal, and its own cost is `price_at_margin_labour_hours_per_kg` -
    the single price every unit of this metal sells at, regardless of which
    deposit it actually came from (see the module docstring's item 3 for
    why one price, not many, is the correct reading of "marginal cost
    pricing"). Every deposit strictly cheaper than the margin earns rent on
    everything it supplies; a deposit not reached at all before demand is
    met supplies nothing and appears in `allocations` with zero quantity
    and zero rent - it exists, but at this quantity demanded it is not
    worth working. If total capacity across every given deposit still
    falls short of demand, the costliest deposit is marginal by default and
    `unmet_demand_tonnes_per_year` is positive - a flag that the deposit
    list handed in does not cover the whole of the modelled world at this
    quantity, not a bug.

    "Cost" throughout is supply_curve's own total_cost_labour_hours_per_kg
    (recurring extraction plus amortised sinking cost - see the module
    docstring's SINKING COST section), not the older extraction-only
    figure.
    """
    if quantity_demanded_tonnes_per_year < 0:
        raise ValueError("quantity demanded cannot be negative: %r"
                          % (quantity_demanded_tonnes_per_year,))

    points = supply_curve(deposits)
    remaining = quantity_demanded_tonnes_per_year
    allocations = []
    marginal_deposit = None
    price_at_margin = 0.0

    for point in points:
        supplied = min(point.quantity_tonnes_per_year, max(0.0, remaining))
        if supplied > 0.0:
            marginal_deposit = point.deposit
            price_at_margin = point.own_cost_labour_hours_per_kg
        allocations.append(Allocation(
            deposit=point.deposit,
            quantity_supplied_tonnes_per_year=supplied,
            own_cost_labour_hours_per_kg=point.own_cost_labour_hours_per_kg,
            rent_labour_hours_per_kg=0.0,   # filled in below, once the
                                             # margin for the WHOLE curve is
                                             # known - a deposit's rent
                                             # depends on the marginal cost,
                                             # not on its own position alone.
            rent_total_labour_hours_per_year=0.0))
        remaining -= supplied

    unmet = max(0.0, remaining)
    if unmet > 0.0 and points:
        # Demand exceeds every given deposit's combined capacity. The
        # costliest deposit is marginal by convention (it is the last one
        # actually worked, at full capacity), and the shortfall is reported
        # rather than silently absorbed - see this function's own docstring.
        marginal_deposit = points[-1].deposit
        price_at_margin = points[-1].own_cost_labour_hours_per_kg

    finished = []
    for allocation in allocations:
        rent_per_kg = max(0.0, price_at_margin - allocation.own_cost_labour_hours_per_kg)
        rent_total = rent_per_kg * allocation.quantity_supplied_tonnes_per_year * KILOGRAMS_PER_TONNE
        finished.append(allocation._replace(
            rent_labour_hours_per_kg=rent_per_kg,
            rent_total_labour_hours_per_year=rent_total))

    supplied_total = quantity_demanded_tonnes_per_year - unmet
    return MarginalOutcome(
        quantity_demanded_tonnes_per_year=quantity_demanded_tonnes_per_year,
        price_at_margin_labour_hours_per_kg=price_at_margin,
        marginal_deposit=marginal_deposit,
        allocations=finished,
        quantity_supplied_tonnes_per_year=supplied_total,
        unmet_demand_tonnes_per_year=unmet)


# ============================================================================
# DEPLETION
# ============================================================================

class DepositState(object):
    """A deposit plus how much of it is left - the mutable running stock
    Complaints/32's "depletion" requirement needs, in the same spirit as
    sim/world/agriculture.py's `Storage`: the physical facts (`deposit`)
    stay fixed, only the stock moves.

    Also tracks `initial_reserve_tonnes_metal` (the reserve this state
    STARTED with, never mutated) alongside the remaining one, so
    `fraction_extracted` can answer "how far through this deposit's life
    are we" for the declining-grade (intensive margin) mechanism - see the
    module docstring's DECLINING GRADE WITHIN A DEPOSIT section.
    """

    __slots__ = ("deposit", "remaining_reserve_tonnes_metal",
                 "initial_reserve_tonnes_metal")

    def __init__(self, deposit: "Deposit", remaining_reserve_tonnes_metal: float) -> None:
        if remaining_reserve_tonnes_metal < 0:
            raise ValueError("reserve cannot be negative: %r"
                              % (remaining_reserve_tonnes_metal,))
        self.deposit = deposit
        self.remaining_reserve_tonnes_metal = float(remaining_reserve_tonnes_metal)
        self.initial_reserve_tonnes_metal = float(remaining_reserve_tonnes_metal)

    @property
    def exhausted(self) -> bool:
        return self.remaining_reserve_tonnes_metal <= 0.0

    @property
    def fraction_extracted(self) -> float:
        """0.0 for an untouched deposit, rising toward 1.0 as its reserve
        is worked down - the input current_ore_grade_kg_per_tonne needs. A
        deposit given zero initial reserve is treated as already fully
        worked (1.0) rather than dividing by zero.
        """
        if self.initial_reserve_tonnes_metal <= 0.0:
            return 1.0
        return 1.0 - (self.remaining_reserve_tonnes_metal
                       / self.initial_reserve_tonnes_metal)

    def current_grade_kg_per_tonne(self) -> float:
        """The grade actually being worked right now, given how much of
        this state's reserve has already been extracted - see module-level
        current_ore_grade_kg_per_tonne.
        """
        return current_ore_grade_kg_per_tonne(
            self.deposit, min(1.0, max(0.0, self.fraction_extracted)))

    def deposit_as_worked(self) -> "Deposit":
        """This state's own Deposit, with ore_grade_kg_per_tonne replaced
        by the grade actually being worked at this point in its life (the
        INTENSIVE margin) rather than its virgin, richest grade - the
        object a caller pricing "this deposit, right now" should use
        instead of `self.deposit` directly. quantity_tonnes_per_year is
        left untouched here; annual_capacity_tonnes handles the EXTENSIVE
        (reserve-running-out) side separately.
        """
        return self.deposit._replace(
            ore_grade_kg_per_tonne=self.current_grade_kg_per_tonne())

    def annual_capacity_tonnes(self) -> float:
        """This deposit's usual annual output, capped by whatever is left
        in the ground - the number find_marginal_deposit actually sees for
        a deposit that is running low.
        """
        return min(self.deposit.quantity_tonnes_per_year,
                    self.remaining_reserve_tonnes_metal)

    def extract(self, tonnes: float) -> float:
        if tonnes < 0:
            raise ValueError("cannot extract a negative quantity: %r" % (tonnes,))
        tonnes = min(tonnes, self.remaining_reserve_tonnes_metal)
        self.remaining_reserve_tonnes_metal -= tonnes
        return tonnes

    def __repr__(self) -> str:
        return "DepositState(%s, remaining=%.4g t, fraction_extracted=%.3f)" % (
            self.deposit.name, self.remaining_reserve_tonnes_metal,
            self.fraction_extracted)


def init_deposit_states(
        deposits: List["Deposit"],
        working_life_years: Optional[float] = None) -> List["DepositState"]:
    """One DepositState per deposit, with an initial reserve of
    `quantity_tonnes_per_year * working_life_years` - see
    DEPOSIT_ASSUMED_WORKING_LIFE_YEARS's own declaration for exactly what
    this stands in for and does not claim to be.
    """
    working_life_years = (DEPOSIT_ASSUMED_WORKING_LIFE_YEARS
                           if working_life_years is None else working_life_years)
    return [DepositState(deposit, deposit.quantity_tonnes_per_year * working_life_years)
            for deposit in deposits]


YearOutcome = collections.namedtuple("YearOutcome", [
    "year",
    "price_at_margin_labour_hours_per_kg",
    "marginal_deposit_name",
    "exhausted_this_year",
    "unmet_demand_tonnes_per_year",
])


def simulate_depletion(
        deposits: List["Deposit"], quantity_demanded_tonnes_per_year: float, years: float,
        working_life_years: Optional[float] = None) -> List["YearOutcome"]:
    """`years` of constant demand, working the cheapest available deposits
    first each year and retiring a deposit once its reserve runs out - the
    demonstration DEPLETION in the module docstring's item 4 promises. Each
    year's deposit is also built at that deposit's CURRENT grade (`state.
    deposit_as_worked`), which falls as the deposit's own reserve is worked
    down - the intensive margin (module docstring's DECLINING GRADE WITHIN
    A DEPOSIT section) is now live inside this loop too, not only the
    extensive one. Nothing here simulates prices feeding back into
    anything else, or the demand quantity itself changing - only the
    mechanisms this module owns: a deposit's own cost creeps up as it is
    worked, and a deposit that runs out forces the margin to a costlier
    one, which together are exactly the property sim/tests/test_deposits.
    py's DepletionMechanismTests checks (the reported price is non-
    decreasing year over year).
    """
    states = init_deposit_states(deposits, working_life_years)
    outcomes = []
    for year in range(1, int(years) + 1):
        available = [state for state in states if not state.exhausted]
        # Each state's CURRENT grade (declining as its reserve is worked
        # down - the intensive margin) and CURRENT capacity (its usual
        # annual output, capped by whatever remains - the extensive one)
        # both stand in for the deposit itself this year -
        # find_marginal_deposit only ever sees Deposit namedtuples, so a
        # throwaway copy with both fields overridden is built here rather
        # than teaching that function about DepositState at all.
        this_year_deposits = [
            state.deposit_as_worked()._replace(
                quantity_tonnes_per_year=state.annual_capacity_tonnes())
            for state in available]
        outcome = find_marginal_deposit(
            this_year_deposits, quantity_demanded_tonnes_per_year)

        # find_marginal_deposit sorts internally (supply_curve), so
        # outcome.allocations is NOT in `available`'s order - matching by
        # position would credit each state with a DIFFERENT deposit's
        # allocation whenever the sort reorders them, silently
        # mis-depleting every deposit but the cheapest. Match by name
        # instead.
        supplied_by_name = {
            allocation.deposit.name: allocation.quantity_supplied_tonnes_per_year
            for allocation in outcome.allocations}
        exhausted_this_year = []
        for state in available:
            extracted = state.extract(supplied_by_name.get(state.deposit.name, 0.0))
            if state.exhausted and extracted > 0.0:
                exhausted_this_year.append(state.deposit.name)

        outcomes.append(YearOutcome(
            year=year,
            price_at_margin_labour_hours_per_kg=outcome.price_at_margin_labour_hours_per_kg,
            marginal_deposit_name=(outcome.marginal_deposit.name
                                    if outcome.marginal_deposit else None),
            exhausted_this_year=exhausted_this_year,
            unmet_demand_tonnes_per_year=outcome.unmet_demand_tonnes_per_year))
    return outcomes


# Force every deposit's grade (and gold/mercury's share_of_empire_output)
# through declare() at IMPORT time, not only the first time some caller
# happens to invoke load_deposits() for that metal. Without this,
# `python3 sim/constants.py --burndown` - which only IMPORTS this module,
# exactly like every other module in _import_declaring_modules() - would
# silently miss every one of the ~30 per-deposit grades and count only the
# handful of shared breaking-hours/haulage constants above, understating
# this module's own burndown the same way _import_declaring_modules()
# missing a module entirely did (see sim/tests/test_constants_burndown.py's
# docstring for that earlier bug) - a lazily-declared constant is invisible
# to a tool that only imports, for exactly the same reason.
for _metal in METALS:
    load_deposits(_metal)
del _metal
