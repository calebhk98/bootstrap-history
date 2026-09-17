"""Ricardian rent: why a scarce deposit is not priced at its own digging cost.

WHAT THIS IS FOR. Complaints/32 measured the actual defect in this project's
price solver: `sim/solve_prices.py` fixes rent on every extracted material at
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
built this way survives other agents editing sim/engine/economy.py,
sim/solve_prices.py and sim/prove_rename_safe.py concurrently with this
file's construction. It reads two data files that already exist
(data/world/geography.json, data/world/resources.json) and one new one this
task adds (data/world/deposits.json), as plain JSON - that is data, not an
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
                             data/world/deposits.json's own _doc for the same
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
data/world/deposits.json's two gold entries are the sharpest illustration
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
"""
import collections
import json
import os

from sim.constants import declare

# ============================================================================
# DATA FILE LOCATIONS
# ============================================================================
# Same ROOT-relative pattern sim/engine/data.py already uses for these two
# existing files (RESFILE, GEOFILE there); repeated here rather than
# imported, for the same reason every sim/world/ module gives for not
# importing sim/engine/ - see the module docstring's STANDALONE section.

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
GEOGRAPHY_FILE = os.path.join(_ROOT, "data", "world", "geography.json")
RESOURCES_FILE = os.path.join(_ROOT, "data", "world", "resources.json")
DEPOSITS_FILE = os.path.join(_ROOT, "data", "world", "deposits.json")

# The seven metals this module and data/world/deposits.json cover -
# exactly the metals data/world/resources.json's empire_output_100ad table
# gives a Roman-era annual output for. Declared as a plain tuple, not
# through declare(): it is a list of names, not a fact with a value that
# could be wrong.
METALS = ("iron", "copper", "tin", "lead", "silver", "gold", "mercury")

# geography.json's own regional mineral shares are calibrated so that ONLY
# these seven "home" regions (reach_from_italia 0 or 1) sum to about 1.0 per
# metal - see that file's regions._note. A farther region with a nonzero
# share (China's iron, India's copper) is ADDITIONAL production outside the
# empire's own output, not a slice of it (geography.json says so explicitly
# for Malayan tin), so including it here would double-count against
# resources.json's empire-wide total rather than partition it.
HOME_REACH_MAXIMUM = 1


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
        "data/world/deposits.json actually use - most pre-modern ore was "
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

HAULAGE_MULTIPLIER_SHALLOW_VEIN = declare(
    "HAULAGE_MULTIPLIER_SHALLOW_VEIN", 1.5,
    kind="engineering_estimate",
    unit="multiplier on breaking hours (dimensionless)",
    source=None,
    confidence="D",
    why="A modest extra labour charge for hoisting broken ore up a ladder "
        "or basket-and-windlass from a shaft too deep to simply carry ore "
        "out on foot, but shallow enough that standing water is not yet a "
        "problem needing continuous pumping. No specific ancient hoisting-"
        "rate figure is behind this number; it is a placeholder pending a "
        "real derivation from shaft depth and basket-hoist rate, which is "
        "why it is a temporary_heuristic-confidence figure declared at "
        "engineering_estimate kind only because the DIRECTION (deeper "
        "costs more) is not in doubt even though the SIZE is.")

HAULAGE_MULTIPLIER_DEEP_VEIN = declare(
    "HAULAGE_MULTIPLIER_DEEP_VEIN", 3.5,
    kind="engineering_estimate",
    unit="multiplier on breaking hours (dimensionless)",
    source="Roman deep mines - Rio Tinto above all - are the standard "
           "textbook example of ancient continuous dewatering: recovered "
           "drainage-wheel batteries (compartmentalised Archimedes-screw "
           "and reverse-overshot-wheel trains) lifted water from shafts "
           "on the order of a hundred metres deep, run continuously, which "
           "on top of the long ore-hoist itself is a substantial standing "
           "labour charge quite separate from breaking the rock.",
    confidence="D",
    why="Same reasoning as HAULAGE_MULTIPLIER_SHALLOW_VEIN's own "
        "declaration - the DIRECTION (deep, wet workings cost much more "
        "than shallow dry ones) is well attested by the archaeology; the "
        "specific multiplier is this file's own placeholder pending a real "
        "derivation from shaft depth, water inflow rate and a drainage "
        "wheel's lift-rate, none of which this project has yet.")

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
        "and the tin entries in data/world/deposits.json, none of which "
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
           "data/world/deposits.json (Rio Tinto, Almaden, Las Medulas) "
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


_HARDNESS_BREAKING_HOURS = {
    "soft": BREAKING_HOURS_PER_TONNE_SOFT,
    "medium": BREAKING_HOURS_PER_TONNE_MEDIUM,
    "hard": BREAKING_HOURS_PER_TONNE_HARD,
}

_DEPTH_HAULAGE_MULTIPLIER = {
    "surface": 1.0,
    "shallow_vein": HAULAGE_MULTIPLIER_SHALLOW_VEIN,
    "deep_vein": HAULAGE_MULTIPLIER_DEEP_VEIN,
}

DEPTH_CLASSES = ("surface", "shallow_vein", "deep_vein", "alluvial",
                  "alluvial_hydraulic")
HARDNESS_CLASSES = ("soft", "medium", "hard")


# ============================================================================
# DEPOSIT
# ============================================================================

Deposit = collections.namedtuple("Deposit", [
    "name",
    "metal",
    "region",                     # geography.json key, or a free-text label
                                   # (e.g. "dacia") when no such region exists
    "material_moved",             # "ore" or "gravel"
    "ore_grade_kg_per_tonne",     # kg of CONTAINED METAL per tonne raised
    "depth_class",
    "hardness_class",             # None for alluvial deposits
    "quantity_tonnes_per_year",   # this deposit's derived annual output
    "note",
])


def extraction_cost_labour_hours_per_kg(deposit):
    """Labour-hours to raise one kilogram of CONTAINED METAL from `deposit`,
    from physical properties alone. Never reads a price anywhere - see the
    module docstring's EXTRACTION COST MECHANICS section for what each of
    the three inputs means and sim/tests/test_deposits.py's
    NoPriceDataTests for the check that this stays true.
    """
    if deposit.depth_class == "alluvial_hydraulic":
        hours_per_tonne_material = ALLUVIAL_HYDRAULIC_PROCESSING_HOURS_PER_TONNE
    elif deposit.depth_class == "alluvial":
        hours_per_tonne_material = ALLUVIAL_HAND_PROCESSING_HOURS_PER_TONNE
    else:
        hours_per_tonne_material = (
            _HARDNESS_BREAKING_HOURS[deposit.hardness_class]
            * _DEPTH_HAULAGE_MULTIPLIER[deposit.depth_class])
    return hours_per_tonne_material / deposit.ore_grade_kg_per_tonne


# ============================================================================
# LOADING DEPOSITS
# ============================================================================

def _load_json(path):
    with open(path, "r") as handle:
        return json.load(handle)


def _region_share(geography, region, metal):
    """geography.json's own regional mineral share for `metal` at `region`,
    or None if that region carries no entry for it at all (as opposed to an
    explicit zero) - used only to tell a genuine gap in geography.json apart
    from a region that simply produces none of this metal.
    """
    entry = geography["regions"].get(region)
    if entry is None:
        return None
    return entry.get("minerals", {}).get(metal)


_GRADE_DECLARED = set()


def _declare_grade(deposit_entry, metal):
    """Run every deposit's ore_grade_kg_per_tonne through declare(), with
    the provenance data/world/deposits.json already carries per entry -
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
            "fact about the rock, read from data/world/deposits.json's "
            "%r entry and never derived from what %s sells for."
            % (deposit_entry["name"], metal))


_SHARE_DECLARED = set()


def _declare_explicit_share(deposit_entry, metal):
    """share_of_empire_output, for the two metals (gold, mercury)
    geography.json carries no regional breakdown for at all - see
    data/world/deposits.json's own _doc. Declared for the same reason the
    grade is: it is a number this file asserts, not arithmetic on an
    already-declared one.
    """
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
        why="Stands in for the regional breakdown data/world/geography.json "
            "carries for iron, copper, tin, lead and silver but not for %s "
            "- see data/world/deposits.json's own _doc for why gold and "
            "mercury need their own explicit share instead of a "
            "geography.json lookup." % metal)


def load_deposits(metal, geography=None, resources=None, deposits_data=None):
    """Every named deposit for `metal`, with its extraction-cost inputs and
    its derived `quantity_tonnes_per_year`, built from data/world/
    deposits.json plus (for iron, copper, tin, lead, silver)
    data/world/geography.json's own regional mineral shares times
    data/world/resources.json's empire_output_100ad, or (for gold, mercury,
    which geography.json carries no regional breakdown for) the deposit's
    own declared share_of_empire_output.

    The three data arguments default to loading the files fresh, and are
    accepted as arguments purely so a caller (or a test) that already has
    them in hand is not made to re-read three files it just read.
    """
    if metal not in METALS:
        raise ValueError("unknown metal %r; must be one of %s" % (metal, METALS))
    geography = geography if geography is not None else _load_json(GEOGRAPHY_FILE)
    resources = resources if resources is not None else _load_json(RESOURCES_FILE)
    deposits_data = (deposits_data if deposits_data is not None
                      else _load_json(DEPOSITS_FILE))

    empire_total_tonnes = resources["empire_output_100ad"][metal]["t_per_yr"]

    out = []
    for entry in deposits_data["deposits"].get(metal, []):
        grade = _declare_grade(entry, metal)
        if "share_of_empire_output" in entry:
            share = _declare_explicit_share(entry, metal)
        else:
            region_entry = geography["regions"].get(entry["region"])
            if region_entry is None:
                raise KeyError(
                    "%s: region %r not found in data/world/geography.json, "
                    "and this entry carries no share_of_empire_output of "
                    "its own" % (entry["name"], entry["region"]))
            if region_entry.get("reach_from_italia", 99) > HOME_REACH_MAXIMUM:
                # geography.json's own shares are normalised so only the
                # "home" regions sum to ~1.0 per metal (see this module's
                # HOME_REACH_MAXIMUM); a farther region's share is EXTRA
                # production, not part of empire_output_100ad's total, so it
                # is deliberately excluded here rather than double-counted.
                continue
            share = _region_share(geography, entry["region"], metal)
            if share is None:
                raise KeyError(
                    "%s: region %r has no %r entry in geography.json's "
                    "minerals table" % (entry["name"], entry["region"], metal))
        quantity_tonnes_per_year = share * empire_total_tonnes
        out.append(Deposit(
            name=entry["name"],
            metal=metal,
            region=entry["region"],
            material_moved=entry["material_moved"],
            ore_grade_kg_per_tonne=grade,
            depth_class=entry["depth_class"],
            hardness_class=entry.get("hardness_class"),
            quantity_tonnes_per_year=quantity_tonnes_per_year,
            note=entry.get("source", "")))
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


def supply_curve(deposits):
    """`deposits`, sorted cheapest-first, each annotated with its own
    extraction cost and the running total of quantity available at or
    below that cost - the object Complaints/32 says this project is
    missing entirely. Ties broken by name, so the curve is deterministic
    regardless of the order `deposits` arrives in.
    """
    ordered = sorted(
        deposits,
        key=lambda d: (extraction_cost_labour_hours_per_kg(d), d.name))
    points = []
    cumulative = 0.0
    for deposit in ordered:
        cumulative += deposit.quantity_tonnes_per_year
        points.append(SupplyCurvePoint(
            deposit=deposit,
            own_cost_labour_hours_per_kg=extraction_cost_labour_hours_per_kg(deposit),
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


def find_marginal_deposit(deposits, quantity_demanded_tonnes_per_year):
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
        rent_total = rent_per_kg * allocation.quantity_supplied_tonnes_per_year * 1000.0
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
    """

    __slots__ = ("deposit", "remaining_reserve_tonnes_metal")

    def __init__(self, deposit, remaining_reserve_tonnes_metal):
        if remaining_reserve_tonnes_metal < 0:
            raise ValueError("reserve cannot be negative: %r"
                              % (remaining_reserve_tonnes_metal,))
        self.deposit = deposit
        self.remaining_reserve_tonnes_metal = float(remaining_reserve_tonnes_metal)

    @property
    def exhausted(self):
        return self.remaining_reserve_tonnes_metal <= 0.0

    def annual_capacity_tonnes(self):
        """This deposit's usual annual output, capped by whatever is left
        in the ground - the number find_marginal_deposit actually sees for
        a deposit that is running low.
        """
        return min(self.deposit.quantity_tonnes_per_year,
                    self.remaining_reserve_tonnes_metal)

    def extract(self, tonnes):
        if tonnes < 0:
            raise ValueError("cannot extract a negative quantity: %r" % (tonnes,))
        tonnes = min(tonnes, self.remaining_reserve_tonnes_metal)
        self.remaining_reserve_tonnes_metal -= tonnes
        return tonnes

    def __repr__(self):
        return "DepositState(%s, remaining=%.4g t)" % (
            self.deposit.name, self.remaining_reserve_tonnes_metal)


def init_deposit_states(deposits, working_life_years=None):
    """One DepositState per deposit, with an initial reserve of
    `quantity_tonnes_per_year * working_life_years` - see
    DEPOSIT_ASSUMED_WORKING_LIFE_YEARS's own declaration for exactly what
    this stands in for and does not claim to be.
    """
    working_life_years = (DEPOSIT_ASSUMED_WORKING_LIFE_YEARS
                           if working_life_years is None else working_life_years)
    return [DepositState(d, d.quantity_tonnes_per_year * working_life_years)
            for d in deposits]


YearOutcome = collections.namedtuple("YearOutcome", [
    "year",
    "price_at_margin_labour_hours_per_kg",
    "marginal_deposit_name",
    "exhausted_this_year",
    "unmet_demand_tonnes_per_year",
])


def simulate_depletion(deposits, quantity_demanded_tonnes_per_year, years,
                        working_life_years=None):
    """`years` of constant demand, working the cheapest available deposits
    first each year and retiring a deposit once its reserve runs out - the
    demonstration DEPLETION in the module docstring's item 4 promises.
    Nothing here simulates prices feeding back into anything else, or the
    demand quantity itself changing - only the mechanism this module owns:
    a deposit that runs out forces the margin to a costlier one, which is
    exactly the property sim/tests/test_deposits.py's DepletionTests checks
    (the reported price is non-decreasing year over year, and strictly
    rises the year a deposit is exhausted).
    """
    states = init_deposit_states(deposits, working_life_years)
    outcomes = []
    for year in range(1, int(years) + 1):
        available = [s for s in states if not s.exhausted]
        # Each state's CURRENT capacity (its usual annual output, capped by
        # whatever remains) stands in for the deposit itself this year -
        # find_marginal_deposit only ever sees Deposit namedtuples, so a
        # throwaway copy with quantity_tonnes_per_year overridden is built
        # here rather than teaching that function about DepositState at
        # all.
        this_year_deposits = [
            s.deposit._replace(quantity_tonnes_per_year=s.annual_capacity_tonnes())
            for s in available]
        outcome = find_marginal_deposit(this_year_deposits, quantity_demanded_tonnes_per_year)

        # find_marginal_deposit sorts internally (supply_curve), so
        # outcome.allocations is NOT in `available`'s order - matching by
        # position here previously credited each state with a DIFFERENT
        # deposit's allocation whenever the sort reordered them, which
        # silently mis-depletes every deposit but the cheapest. Match by
        # name instead.
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


if __name__ == "__main__":
    # A quick, human-readable readout - the same kind of thing
    # sim/world/agriculture.py's own __main__ block prints, for whoever
    # next wants to see this module's headline numbers without opening a
    # test file. Uses data/world/resources.json's own empire_output_100ad
    # as an illustrative quantity demanded - see the module docstring's
    # DEMAND IS A PARAMETER section for why that is a real historical
    # output level being used as a stand-in, not a claim that this module
    # invented a demand figure.
    resources = _load_json(RESOURCES_FILE)
    print("DEPOSITS - Ricardian rent from physical ore-body properties")
    print("=" * 72)
    for metal in METALS:
        deposits = load_deposits(metal)
        demand = resources["empire_output_100ad"][metal]["t_per_yr"]
        outcome = find_marginal_deposit(deposits, demand)
        print("\n%s (stated Roman output: %.4g t/yr)" % (metal.upper(), demand))
        for allocation in sorted(outcome.allocations,
                                  key=lambda a: a.own_cost_labour_hours_per_kg):
            marker = " <- MARGINAL" if allocation.deposit is outcome.marginal_deposit else ""
            print("  %-26s cost=%10.5f h/kg  supplies=%9.2f t/yr  "
                  "rent=%10.5f h/kg%s"
                  % (allocation.deposit.name,
                     allocation.own_cost_labour_hours_per_kg,
                     allocation.quantity_supplied_tonnes_per_year,
                     allocation.rent_labour_hours_per_kg,
                     marker))
        print("  price at margin: %.5f labour-hours/kg" % outcome.price_at_margin_labour_hours_per_kg)
        if outcome.unmet_demand_tonnes_per_year > 0.0:
            print("  UNMET DEMAND: %.2f t/yr beyond every named deposit's "
                  "combined capacity" % outcome.unmet_demand_tonnes_per_year)

    print("\n" + "=" * 72)
    print("Depletion demo: silver at its stated output, over %d years"
          % int(DEPOSIT_ASSUMED_WORKING_LIFE_YEARS * 1.2))
    silver_deposits = load_deposits("silver")
    silver_demand = resources["empire_output_100ad"]["silver"]["t_per_yr"]
    for year_outcome in simulate_depletion(
            silver_deposits, silver_demand,
            years=int(DEPOSIT_ASSUMED_WORKING_LIFE_YEARS * 1.2)):
        if year_outcome.exhausted_this_year or year_outcome.year in (1,):
            print("  year %3d: price at margin %.4f h/kg (%s)%s%s"
                  % (year_outcome.year,
                     year_outcome.price_at_margin_labour_hours_per_kg,
                     year_outcome.marginal_deposit_name,
                     ("  EXHAUSTED: %s" % ", ".join(year_outcome.exhausted_this_year)
                      if year_outcome.exhausted_this_year else ""),
                     ("  UNMET %.2f t/yr" % year_outcome.unmet_demand_tonnes_per_year
                      if year_outcome.unmet_demand_tonnes_per_year > 0 else "")))
