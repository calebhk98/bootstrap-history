"""Age-cohort population dynamics: how many people, of what age, and why.

WHAT THIS REPLACES. `Sim._demographic_recovery` (sim/engine/core.py) tracks
population as one scalar, `pop_scale`, plus a `pop_deficit` that a hazard adds
to and that decays back toward zero on a fixed exponential clock (tau derived
from how long England took to regain its pre-Black-Death population). That is
honestly labelled there as a stand-in - the docstring says as much - and it
has two real costs. First, the recovery rate is a property of the SHOCK
(which hazard, how big) rather than of the SURVIVORS: a plague that killed
mostly children and one that killed mostly adults recover on the same clock,
which is wrong in opposite directions. Second, a scalar cannot answer "how
many people can work", which is the input the labour market actually needs -
`pop_scale` scales prices and hiring caps uniformly, standing in for a labour
supply the engine has never had a way to compute.

This module answers both by tracking who is what age. Nothing here is wired
into `engine/`; it is a standalone package precisely so it can be gotten right
in isolation - see `sim/world/__init__.py` - and proven against the
accounting and long-run properties a population must satisfy before anything
is asked to trust it.

THE CENTRAL DESIGN RULE (CLAUDE.md SS3.1, and Milestone 4 of
docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md): a food shortage must raise
mortality and lower fertility THROUGH THE MODEL. There is no
`famine_severity` switch anywhere below. What exists instead is a nutrition
RATIO - calories actually available divided by what the population physically
needs - and mortality and fertility are both plain functions of that ratio,
the same functions whether the ratio is 1.3 because a good harvest came in or
0.6 because a war destroyed one. A "famine" is not a distinct code path here;
it is just what a low ratio, sustained, does to a population through the
ordinary machinery. See `_excess_mortality_multiplier` and
`_fertility_multiplier` below for the two functions that carry that rule.

SHAPE. Three age cohorts - children (0 to WORKING_AGE_LOWER_BOUND_YEARS),
working age (up to WORKING_AGE_UPPER_BOUND_YEARS), elderly (open-ended above
that) - each a plain float count, not a distribution of single-year ages.
Coarse cohorts are what docs/architecture/CURRENT_CODE_ARCHITECTURE_REVIEW.md
SS6.5 recommends starting with, and the reason is not just less code: a
single-year cohort model needs an age-specific fertility and mortality curve
for every one of 100-plus years, and this project has no source for most of
those curves that is not itself invented. Three bands need only the
boundary-defining facts (age of reproductive maturity, of menopause, of
retirement-into-frailty), which are real, sourced constants below, plus one
mortality figure and one fertility figure per band, which is a defensible
amount of invention to own explicitly rather than a hundred hidden guesses
dressed up as precision.

WHAT THIS MODULE DOES NOT DO. It does not know where food comes from - the
agriculture model (being built in parallel; see this module's caller-facing
report for exactly what is stubbed) is expected to hand `step()` a number of
calories available per day, and this module treats that as an exogenous
input, the same way it currently treats immigration and emigration. It also
does not track sex explicitly (see FEMALE_SHARE_OF_WORKING_AGE_POPULATION's
declaration for what that costs), regions, or disease as a distinct state -
disease is presently folded into the mortality-vs-nutrition relationship
exactly as docs/architecture/CURRENT_CODE_ARCHITECTURE_REVIEW.md SS6.6
describes as the "minimal first version", i.e. wrong in the specific way that
document says is acceptable for now.
"""
import collections
import math
import random

from sim.constants import declare

# ============================================================================
# AGE BAND BOUNDARIES
# ============================================================================
# These two ages are not invented for this project - they are the boundary
# ages demography as a field already uses. "Women of reproductive age,
# 15-49" is the definition the UN Demographic Yearbook and WHO fertility
# statistics are built on; this model borrows it wholesale rather than
# picking its own cutoffs, and uses the same 15/49 split for the population
# as a whole (not just women) because the model does not track sex per
# cohort - see FEMALE_SHARE_OF_WORKING_AGE_POPULATION below for what that
# simplification costs.

WORKING_AGE_LOWER_BOUND_YEARS = declare(
    "WORKING_AGE_LOWER_BOUND_YEARS", 15.0,
    kind="biological_parameter",
    unit="years",
    source="UN/WHO demographic convention: lower bound of \"women of "
           "reproductive age\", and, not coincidentally, close to median "
           "menarche age in populations without modern nutrition (menarche "
           "runs later, not earlier, under pre-industrial nutrition).",
    confidence="B",
    why="Where the child cohort ends and the working/reproductive cohort "
        "begins. Also where fertility switches on and child mortality's "
        "band ends, so this one number sets three boundaries at once.")

WORKING_AGE_UPPER_BOUND_YEARS = declare(
    "WORKING_AGE_UPPER_BOUND_YEARS", 49.0,
    kind="biological_parameter",
    unit="years",
    source="UN/WHO demographic convention: upper bound of \"women of "
           "reproductive age, 15-49\", i.e. the standard proxy for the end "
           "of the fertile years (menopause typically follows shortly "
           "after).",
    confidence="B",
    why="Where fertility switches off and the elderly band begins. Also "
        "used as the population's labour-age ceiling in the absence of any "
        "modelled distinction between fertility and labour capacity.")

CHILD_BAND_WIDTH_YEARS = WORKING_AGE_LOWER_BOUND_YEARS
WORKING_AGE_BAND_WIDTH_YEARS = (
    WORKING_AGE_UPPER_BOUND_YEARS - WORKING_AGE_LOWER_BOUND_YEARS)

# ============================================================================
# BASELINE VITAL RATES (nutrition ratio == 1.0, i.e. exactly meeting need)
# ============================================================================
# Each of these three is independently anchored to a real historical
# demography estimate - none of them is fitted to make the model behave.
# But each estimate above is a RANGE, not a point, and the specific point
# within its range used here is chosen jointly, because the three together
# imply a long-run growth rate, and a real pre-industrial population's rates
# really were close to self-replacing (net reproduction ratio near 1). That
# is a genuine, sourced fact about history - not this model's outcome -
# and picking each of the three numbers from within its own documented
# range so that the model reproduces it is calibration the same way a
# demographer fitting a historical model life table calibrates it: every
# number stays inside the range the literature supports, and the criterion
# used to choose a point inside that range is a different, independently
# documented fact (crude birth/death rates in the 30-40 per thousand range,
# life expectancy at birth in the 20s-30s - CLAUDE.md SS3.2's own anchors)
# rather than a specific dated outcome. Computed at these settings, by this
# module (see sim/tests/test_demography.py's stationarity check, which
# prints them): crude birth rate about 34/1000, crude death rate about
# 34/1000, life expectancy at birth about 30 years, net drift over 300
# years at subsistence under -0.1%. All three land inside CLAUDE.md SS3.2's
# targets without any of them being one of this model's free parameters -
# the only freedom used was where inside each already-sourced range the
# three numbers sit relative to each other.

SURVIVAL_TO_WORKING_AGE = declare(
    "SURVIVAL_TO_WORKING_AGE", 0.50,
    kind="biological_parameter",
    unit="fraction of live births",
    source="Historical demography of pre-transition populations (e.g. "
           "Livi-Bacci, A Concise History of World Population; Wrigley & "
           "Schofield, The Population History of England 1541-1871) puts "
           "survival from birth to age 15 anywhere from roughly 45% to 70% "
           "depending on period, place and whether plague years are "
           "included - i.e. something between a third and just over half "
           "of children die before reaching working age, the great "
           "majority of them in infancy and early childhood. 0.50 is "
           "within this range, toward its harsher end; see the paragraph "
           "above this declaration for why this specific point in the "
           "range was used rather than, say, its midpoint.",
    confidence="C",
    why="Converted below into the child band's average annual mortality "
        "rate: a single hazard that, applied for the whole 15-year band, "
        "reproduces this survival fraction. The real curve is front-loaded "
        "(infant mortality dwarfs mortality at age 10) rather than flat; "
        "flattening it across the band is the coarse-cohort trade-off "
        "described in this module's docstring.")

# exp(mean_hazard * -width) == SURVIVAL_TO_WORKING_AGE, per band width, i.e.
# a constant annual hazard that compounds to the sourced survival fraction
# over CHILD_BAND_WIDTH_YEARS years - the standard way to turn a life-table
# survivorship figure into a single-band exponential hazard.
BASELINE_ANNUAL_MORTALITY_RATE_CHILD = (
    -math.log(SURVIVAL_TO_WORKING_AGE) / CHILD_BAND_WIDTH_YEARS)

BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE = declare(
    "BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE", 0.014,
    kind="biological_parameter",
    unit="fraction of cohort per year",
    source="Wrigley & Schofield's reconstructed English mortality rates "
           "for ages 15-49 in the early-modern period run roughly "
           "1.0-1.5% per year outside epidemic years; 1.4% sits near the "
           "upper end of that range - see the paragraph above SURVIVAL_TO_"
           "WORKING_AGE for why this range's upper end was used.",
    confidence="C",
    why="Adults are the survivors of the child band's much higher hazard, "
        "so their own baseline rate is far lower; this is what makes "
        "'kill 30% of the population' and 'more mouths than usual' hit the "
        "child and elderly bands harder than the working-age one, matching "
        "the real age pattern of famine and plague mortality (see "
        "STARVATION_VULNERABILITY_CHILD / _ELDERLY below).")

REMAINING_LIFE_EXPECTANCY_AT_WORKING_AGE_CEILING_YEARS = declare(
    "REMAINING_LIFE_EXPECTANCY_AT_WORKING_AGE_CEILING_YEARS", 17.0,
    kind="biological_parameter",
    unit="years",
    source="Model life tables calibrated to a life expectancy at birth in "
           "the mid-20s to low-30s (Coale-Demeny \"West\", low levels; "
           "consistent with Wrigley & Schofield's English series) show "
           "roughly 15-19 further years of life, on average, for someone "
           "who has already reached their late 40s.",
    confidence="C",
    why="The elderly band has no upper edge, so it cannot be given a "
        "band-width hazard the way the other two bands are; treating it as "
        "a single pool with an exponential survival curve whose mean "
        "matches this remaining-life figure is the least additional "
        "invention available. It is still a real structural approximation "
        "(true elderly mortality rises with age within the band, this "
        "gives it one flat rate) - flagged here rather than smuggled in as "
        "an unlabelled number, and the first thing to fix if the elderly "
        "band's dynamics ever need to be more than a stand-in for a real "
        "old-age mortality curve.")

BASELINE_ANNUAL_MORTALITY_RATE_ELDERLY = (
    1.0 / REMAINING_LIFE_EXPECTANCY_AT_WORKING_AGE_CEILING_YEARS)

TOTAL_FERTILITY_RATE = declare(
    "TOTAL_FERTILITY_RATE", 5.0,
    kind="biological_parameter",
    unit="births per woman, lifetime",
    source="Natural-fertility (no deliberate birth control) populations "
           "studied by Coale & Trussell and surveyed in Livi-Bacci run "
           "total fertility rates of roughly 4 to 7 depending on marriage "
           "age and breastfeeding customs; 5.0 sits at the lower-middle of "
           "that range - see the paragraph above SURVIVAL_TO_WORKING_AGE "
           "for why this specific point was used.",
    confidence="C",
    why="Spread evenly over the reproductive band below to get an annual "
        "per-woman rate. This is the single most load-bearing number in "
        "the model: paired with SURVIVAL_TO_WORKING_AGE and the two adult "
        "mortality rates above, it is what makes the 'roughly stationary "
        "at subsistence' test pass - three independently sourced ranges "
        "landing on a self-replacing population, at a plausible crude "
        "birth/death rate and life expectancy, is a consistency check on "
        "the sourcing, not a tuning of one number against an outcome this "
        "model is meant to produce on its own.")

ANNUAL_FERTILITY_RATE_PER_WOMAN = TOTAL_FERTILITY_RATE / WORKING_AGE_BAND_WIDTH_YEARS

FEMALE_SHARE_OF_WORKING_AGE_POPULATION = declare(
    "FEMALE_SHARE_OF_WORKING_AGE_POPULATION", 0.5,
    kind="temporary_heuristic",
    unit="fraction",
    source=None,
    confidence="D",
    why="This model has no sex dimension at all - one working-age count, "
        "not a male and a female one - so an even split stands in for "
        "tracking women separately, which is what the fertility side "
        "actually needs (only women bear children; sex-differential "
        "mortality, sex-selective migration and marriage-market effects on "
        "fertility are all invisible to a single pooled cohort). Real "
        "historical sex ratios are close to but not exactly even, and "
        "diverge further after sex-selective mortality events. Replace "
        "when sex becomes a tracked dimension of the cohort state.")

# ============================================================================
# NUTRITION: the one input that moves both fertility and mortality
# ============================================================================
# The subsistence and starvation-floor calorie figures below are the two
# real anchors of the model's response to food. Everything downstream of
# them is stated PURELY in terms of where a population's actual calories per
# adult-equivalent sits between these two figures - there is no separate
# "famine" state or multiplier; see the module docstring.

SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY = declare(
    "SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY", 2200.0,
    kind="biological_parameter",
    unit="kcal/adult-equivalent/day",
    source="FAO minimum dietary energy requirement, adult average - the "
           "same figure the project's economy side uses for how much grain "
           "a person eats before their labour can do anything else.",
    confidence="B",
    why="The denominator of the nutrition ratio: calories available divided "
        "by (population, in adult-equivalents) times this figure gives the "
        "single number - 1.0 means exactly meeting need - that mortality "
        "and fertility below are both plain functions of. Declared "
        "separately from any figure engine/ or a future agriculture module "
        "might declare under a similar name, deliberately, since this "
        "module has no dependency on either and should not silently start "
        "requiring one just because a name happens to collide.")

CHILD_CALORIE_EQUIVALENT = declare(
    "CHILD_CALORIE_EQUIVALENT", 0.5,
    kind="biological_parameter",
    unit="fraction of an adult's daily requirement",
    source="FAO/WHO/UNU age-specific energy requirement tables: averaged "
           "over ages 0-14 (a newborn needs a small fraction of an adult's "
           "intake, a 14-year-old close to all of it), the band average "
           "comes out close to half.",
    confidence="C",
    why="Feeds the adult-equivalent population used to compute the "
        "nutrition ratio - a society is not fed in head-count, it is fed in "
        "calories, and children eat less of them.")

ELDERLY_CALORIE_EQUIVALENT = declare(
    "ELDERLY_CALORIE_EQUIVALENT", 0.85,
    kind="biological_parameter",
    unit="fraction of an adult's daily requirement",
    source="FAO/WHO/UNU tables show roughly 10-20% lower energy "
           "requirements past 60, from lower basal metabolic rate and "
           "reduced physical activity.",
    confidence="C",
    why="Same role as CHILD_CALORIE_EQUIVALENT, for the other cohort whose "
        "requirement is not a full adult's.")

STARVATION_FLOOR_CALORIES_PER_ADULT_EQUIVALENT_DAY = declare(
    "STARVATION_FLOOR_CALORIES_PER_ADULT_EQUIVALENT_DAY", 800.0,
    kind="biological_parameter",
    unit="kcal/adult-equivalent/day",
    source="Famine mortality literature (e.g. O Grada, Famine: A Short "
           "History) and documented 20th-century starvation records "
           "(wartime siege rations, famine relief thresholds) place "
           "sustained intake below roughly 500-1000 kcal/day as the range "
           "where starvation itself, not merely elevated disease "
           "susceptibility, becomes the dominant cause of death within a "
           "year.",
    confidence="C",
    why="The other anchor of the nutrition-to-mortality relationship: "
        "calories at or below this level are treated as the ceiling of the "
        "model's mortality response (see "
        "STARVATION_MORTALITY_CEILING_MULTIPLIER), calories at or above "
        "SUBSISTENCE... are treated as imposing no excess mortality at "
        "all, and everything between is a straight line connecting the two "
        "- the two endpoints are sourced, the straight line between them "
        "is not (see that constant's own docstring).")

STARVATION_MORTALITY_CEILING_MULTIPLIER = declare(
    "STARVATION_MORTALITY_CEILING_MULTIPLIER", 4.0,
    kind="temporary_heuristic",
    unit="multiple of baseline mortality",
    source=None,
    confidence="D",
    why="How much a band's baseline mortality is multiplied by once "
        "calories per head fall to the starvation floor. The real "
        "relationship between sustained caloric deficit and excess "
        "mortality is a proper starvation/disease hazard curve that this "
        "project does not have; a straight line from 1x at subsistence to "
        "this ceiling at the floor is the invented stand-in for it. Sized, "
        "together with the two vulnerability multipliers below, so that a "
        "population held at half its subsistence requirement for a full "
        "year (computed: ~22%/year child mortality, ~5%/year working-age, "
        "~25%/year elderly) sits in the range of documented worst-year "
        "crude death rates during real severe famines and sieges, rather "
        "than either a rounding error or a wipeout of an entire age band "
        "in one season - both of which an equally plausible-looking but "
        "wrong multiplier produced during calibration (12x came first and "
        "put child mortality at half rations over 100%, which is not "
        "'severe famine', it is a claim that famine cannot be survived; "
        "kept here as a worked example of the kind of check this number "
        "needs, not as a citation). Replace once a real starvation-hazard "
        "function exists.")

STARVATION_VULNERABILITY_CHILD = declare(
    "STARVATION_VULNERABILITY_CHILD", 1.6,
    kind="temporary_heuristic",
    unit="ratio to working-age vulnerability",
    source=None,
    confidence="D",
    why="Famine demography (e.g. Watkins & Menken 1985 on age patterns of "
        "famine mortality) documents that a given caloric shortfall kills a "
        "larger share of children than of working-age adults - lower "
        "physiological reserves, higher baseline vulnerability to the "
        "infections that a shortfall's immune suppression lets through. "
        "The DIRECTION is documented; the specific multiple used to scale "
        "the model's excess-mortality term is invented and needs a real "
        "dose-response curve to replace it.")

STARVATION_VULNERABILITY_WORKING_AGE = 1.0  # the reference the other two
# bands' vulnerability is stated relative to; not independently invented, so
# not separately declared.

STARVATION_VULNERABILITY_ELDERLY = declare(
    "STARVATION_VULNERABILITY_ELDERLY", 1.4,
    kind="temporary_heuristic",
    unit="ratio to working-age vulnerability",
    source=None,
    confidence="D",
    why="Same reasoning and same status as STARVATION_VULNERABILITY_CHILD, "
        "for the elderly band instead.")

FERTILITY_SURPLUS_CEILING_MULTIPLIER = declare(
    "FERTILITY_SURPLUS_CEILING_MULTIPLIER", 1.8,
    kind="temporary_heuristic",
    unit="multiple of baseline fertility",
    source="Eaton & Mayer 1953's study of Hutterite colonies is the "
           "standard demographic reference for the highest total fertility "
           "rate documented for any human population with no deliberate "
           "birth control: roughly 9 to 11 births per woman, lifetime, "
           "against this module's own TOTAL_FERTILITY_RATE baseline of "
           "5.0. 1.8x sits at the low end of that ratio (9/5.0 = 1.8; "
           "11/5.0 = 2.2) rather than its middle or high end - chosen "
           "conservatively, the same direction every other point-within-"
           "range choice in this module leans (see the paragraph above "
           "SURVIVAL_TO_WORKING_AGE).",
    confidence="D",
    why="The ceiling _fertility_multiplier ramps up to as nutrition rises "
        "above subsistence, mirroring _excess_mortality_multiplier's "
        "ramp down to STARVATION_MORTALITY_CEILING_MULTIPLIER below it. "
        "Checked against the stakeholder's own biological growth-rate "
        "ceiling (Complaints/45-no-granary-so-the-baseline-collapses.md): "
        "at this model's stationary age structure (roughly 46% "
        "working-age) and ANNUAL_FERTILITY_RATE_PER_WOMAN, a population "
        "fed at this ceiling throughout contributes on the order of 2-3% "
        "growth a year from births alone, comfortably under the ~9.06%/"
        "year ceiling that assumes no deaths at all and a birth every "
        "year from every woman aged 18-40 - so 1.8x is not chosen to hit "
        "any particular growth number, it is bounded independently by the "
        "Hutterite comparison and then CHECKED (not tuned) against the "
        "growth ceiling, which it does not come close to binding.")

NUTRITION_YEAR_TO_YEAR_NOISE_STD = declare(
    "NUTRITION_YEAR_TO_YEAR_NOISE_STD", 0.03,
    kind="temporary_heuristic",
    unit="fraction of the nutrition ratio, standard deviation",
    source=None,
    confidence="D",
    why="Real harvests vary year to year for reasons (weather, pests, "
        "local disruption) that a single 'food available' number handed in "
        "by whatever supplies it does not capture, and `step(jitter=True)` "
        "exists so a caller can explore that. It defaults OFF (see "
        "step()'s `jitter` parameter) rather than being applied "
        "unconditionally, for a reason worth recording rather than "
        "quietly working around: THE MORTALITY RESPONSE STILL HAS A FLOOR "
        "at nutrition_ratio == 1.0 (a good year does not reduce mortality "
        "below baseline - see _excess_mortality_multiplier's own "
        "docstring for why no sourced biological limit was found to lift "
        "that floor). Fertility no longer floors the same way - "
        "_fertility_multiplier now ramps UP above subsistence, applied "
        "for Complaints/45-no-granary-so-the-baseline-collapses.md - so "
        "symmetric noise around 1.0 partially cancels on the fertility "
        "side but still pushes AVERAGE excess mortality up whenever "
        "average food supply is exactly at subsistence (Jensen's "
        "inequality applied to what is now a one-sided response curve on "
        "ONE side of the ledger instead of both). Real agrarian societies "
        "also damp the INPUT side of this with grain storage, carrying a "
        "good year's surplus into a bad year; that storage now exists one "
        "layer up, at the point food actually reaches this module (sim/"
        "engine/core.py's `Sim.farm_stock_kg`). Between the two changes, "
        "less of the original problem remains, but the mortality floor is "
        "real and sourced (see _excess_mortality_multiplier), not a gap "
        "left for convenience, so turning noise on here without a real "
        "harvest-variance figure would still manufacture a downward drift "
        "that is an artefact of an unsourced noise MAGNITUDE, not a claim "
        "about real variability - precisely the kind of invented outcome "
        "CLAUDE.md SS3.1 rules out - so it stays off until a real "
        "harvest-variance figure replaces the guess. Still declared, and "
        "the machinery (`step`'s `jitter` argument, each Population's own "
        "seeded `random.Random`) still exists, so a scenario that DOES "
        "want to explore harvest variance has a real, deterministic, "
        "seeded random source to use rather than needing to invent its "
        "own.")


# ============================================================================
# THE FOOD-TO-VITAL-RATES MECHANISM
# ============================================================================

def _excess_mortality_multiplier(nutrition_ratio, vulnerability):
    """How much a band's baseline mortality is scaled by, given nutrition.

    This is the one function in the module where "a food shortage raises
    mortality through the model, not through a famine modifier" actually
    happens, so it is worth being explicit about what it is and is not.

    At or above nutrition_ratio == 1.0 (need fully met) this returns exactly
    1.0: baseline mortality, sourced above, is ALREADY the observed
    mortality of real historical populations who were, on average, close to
    subsistence - it is not a floor being modelled downward, it already IS
    the answer for adequate nutrition. Extra calories beyond subsistence do
    not mechanically lower mortality further here; that is a genuine
    simplification (real nutrition has diminishing but non-zero further
    benefit above bare subsistence) rather than an oversight, and it means
    this function cannot depress mortality to zero by overfeeding, which a
    naive multiplicative model easily could.

    CHECKED FOR A SOURCED LOWER LIMIT, FOR Complaints/45-no-granary-so-the-
    baseline-collapses.md, AND NONE WAS FOUND (unlike the fertility side -
    see _fertility_multiplier and FERTILITY_SURPLUS_CEILING_MULTIPLIER for
    the ceiling that WAS sourced and applied). The literature on whether
    better-nourished pre-industrial sub-populations had materially lower
    mortality than the general population does not give a clean multiplier
    to mirror the fertility ramp with: Antonovsky's review of historical
    social-class mortality differentials found them smallest or absent
    exactly where baseline mortality was highest (i.e. exactly the regime
    this model's baseline rates describe), and the best-studied elite
    cohort - the British peerage - shows mortality no better, and before
    the eighteenth century sometimes WORSE, than the general English
    population studied by Wrigley & Schofield, because any nutritional
    advantage was offset by other exposures (the peerage's own excess risks)
    that a pure nutrition-to-mortality channel does not capture. Whatever
    real biological floor exists below an already-near-subsistence baseline
    is confounded, in every source found, with disease environment, hygiene
    and medical care rather than isolated as a calorie effect - so there is
    no sourced number here to apply, and inventing one to mirror the
    fertility side just because it would be symmetric is exactly the kind
    of unlabelled heuristic CLAUDE.md SS3.4 forbids. This floor therefore
    stays exactly as it was. If a future source isolates a nutrition-only
    mortality elasticity below this baseline, it belongs here.

    Below 1.0, this is linear in the calories the population actually has,
    from 1.0 (at the subsistence line) to STARVATION_MORTALITY_CEILING_
    MULTIPLIER (at the starvation floor). The two endpoints are sourced; the
    straight line between them is the specific thing that is invented (see
    STARVATION_MORTALITY_CEILING_MULTIPLIER's own declaration) - deliberately
    the SAME straight line for every band, with the age-specific difference
    applied afterwards as `vulnerability`, so there is exactly one invented
    curve shape in the whole model rather than three uncoordinated ones.
    """
    if nutrition_ratio >= 1.0:
        return 1.0
    calories = nutrition_ratio * SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY
    span = (SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY
            - STARVATION_FLOOR_CALORIES_PER_ADULT_EQUIVALENT_DAY)
    if calories <= STARVATION_FLOOR_CALORIES_PER_ADULT_EQUIVALENT_DAY:
        fraction_of_span = 1.0
    else:
        fraction_of_span = (
            (SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY - calories) / span)
    excess = (STARVATION_MORTALITY_CEILING_MULTIPLIER - 1.0) * fraction_of_span
    return 1.0 + excess * vulnerability


def _fertility_multiplier(nutrition_ratio):
    """How much baseline fertility is scaled by, given nutrition.

    Below subsistence: linear in the ratio itself, down to 0 at zero food.
    This is a deliberately simplified stand-in for the qualitative
    relationship documented in reproductive endocrinology (energy
    availability and LH pulsatility - see e.g. Loucks & Thuma 2003):
    caloric restriction suppresses ovulation roughly in proportion to the
    energy deficit as intake falls below maintenance. That literature is
    about the DIRECTION and rough shape, not this exact line, so the linear
    form is an invented simplification of a real, more complex relationship
    - it is not separately `declare()`d only because it introduces no
    additional numeric constant beyond the nutrition ratio itself and the
    definitional bounds 0 and 1.

    AT OR ABOVE SUBSISTENCE: a bounded upward ramp, mirroring
    `_excess_mortality_multiplier`'s below-1.0 ramp exactly - linear from
    1.0 at subsistence to FERTILITY_SURPLUS_CEILING_MULTIPLIER at the same
    calorie distance above subsistence that the starvation floor sits below
    it (so span == SUBSISTENCE... - STARVATION_FLOOR..., reused on both
    sides rather than invented twice), flat at the ceiling beyond that. A
    population that eats well really does raise more surviving children;
    the two sourced endpoints (1.0 at subsistence, the Hutterite-anchored
    ceiling at FERTILITY_SURPLUS_CEILING_MULTIPLIER - see that constant's
    own declaration) are real, the straight line between them is invented,
    same status as the mortality side's own straight line.

    RESOLVES Complaints/45-no-granary-so-the-baseline-collapses.md's THIRD
    QUESTION ("should the floor at nutrition_ratio == 1.0 become a real,
    bounded benefit above it"). This exact shape was designed, implemented,
    checked against the stakeholder's own growth-rate ceiling, and then
    REVERTED once already because sim/tests/test_demography.py's pinned
    `test_fertility_does_not_rise_above_baseline_on_surplus` asserted the
    opposite and that file was outside the reverting task's ownership (see
    that complaint's own account, and FERTILITY_SURPLUS_CEILING_MULTIPLIER's
    declaration for the arithmetic that check used). This change applies it
    and updates that test in the same commit, which is what the earlier
    attempt could not do.

    Measured (sim/tests/test_demography.py's GrowthCeilingTests): fed with
    unlimited food (nutrition ratio pinned above the ceiling every year, no
    shortfall ever), this model now grows at a small positive annual rate,
    not the ~-0.03%/year it produced with fertility flat at 1.0 above
    subsistence - see that test class's own docstring for the exact figure
    and its comparison to the stakeholder's ~9.06%/year biological ceiling
    (Complaints/45), which it stays far under.

    `_excess_mortality_multiplier` (the floor, not the ceiling side) is
    DELIBERATELY LEFT UNCHANGED - see its own docstring for why: lowering
    it needs a biological ceiling on how far mortality can fall below an
    already-historically-observed baseline, and nothing sourced was found
    for that (see this module's caller-facing report / this task's own
    report for what was checked and why it came up empty). Baseline
    mortality here already IS the observed rate of a population at
    subsistence, not a floor modelled downward from something higher, so
    there is no equivalent "how far above the historical figure can we go"
    room to check the way there was on the fertility side.
    """
    if nutrition_ratio < 1.0:
        return max(0.0, nutrition_ratio)
    calories = nutrition_ratio * SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY
    span = (SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY
            - STARVATION_FLOOR_CALORIES_PER_ADULT_EQUIVALENT_DAY)
    abundance_ceiling_calories = (
        SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY + span)
    if calories >= abundance_ceiling_calories:
        return FERTILITY_SURPLUS_CEILING_MULTIPLIER
    fraction_of_span = (
        (calories - SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY) / span)
    surplus = (FERTILITY_SURPLUS_CEILING_MULTIPLIER - 1.0) * fraction_of_span
    return 1.0 + surplus


StepFlows = collections.namedtuple(
    "StepFlows",
    ["start_total", "births", "immigration", "deaths", "emigration",
     "end_total", "nutrition_ratio", "deaths_children", "deaths_working_age",
     "deaths_elderly"])


class Population(object):
    """Three age cohorts and the machinery that ages them by one year.

    `children`, `working_age` and `elderly` are plain floats, not integer
    head-counts. That is deliberate, not sloppy: at the scale this model
    runs at (a civilisation's population, not a village's), a fractional
    person is the ordinary floating-point residue of "37.2% annual
    mortality applied to 4,102,993 people", not a claim that a third of a
    person died. Treating counts as continuous is also what keeps the
    accounting identity in `step()` exact to floating-point tolerance rather
    than exact modulo an ad hoc integer-rounding rule.

    SEED AND DETERMINISM. Each Population owns one `random.Random` instance,
    seeded once at construction and never reseeded or replaced. `step()`
    draws from it (see NUTRITION_YEAR_TO_YEAR_NOISE_STD) and nothing else in
    this module touches the shared `random` module state or any global
    generator, so two Populations built with the same seed and driven with
    the same sequence of `step()` calls produce bit-identical trajectories
    regardless of what else is going on in the process - see
    sim/tests/test_demography.py's determinism check. This also means the
    project's `id()`-reuse hazard (Complaints/27) cannot recur here: nothing
    is ever cached by an object's `id()`; the only per-instance state is the
    `random.Random` object itself, held by direct reference, never by
    address.
    """

    __slots__ = ("children", "working_age", "elderly", "_random")

    def __init__(self, children, working_age, elderly, seed=0):
        self.children = float(children)
        self.working_age = float(working_age)
        self.elderly = float(elderly)
        self._random = random.Random(seed)

    @property
    def total(self):
        return self.children + self.working_age + self.elderly

    @property
    def working_age_population(self):
        """The number this whole module exists to be able to answer."""
        return self.working_age

    def copy(self):
        """An independent Population with its own, separately-advancing
        random stream (re-seeded from a draw of this one's), for branching a
        scenario (e.g. 'what if food had NOT been cut') without either copy's
        later draws depending on how many steps the other one takes.
        """
        clone = Population(self.children, self.working_age, self.elderly,
                            seed=self._random.getrandbits(64))
        return clone

    def __repr__(self):
        return ("Population(children=%.3f, working_age=%.3f, elderly=%.3f, "
                "total=%.3f)" % (self.children, self.working_age,
                                  self.elderly, self.total))

    def nutrition_ratio(self, food_available_calories_per_day, jitter=False):
        """Calories actually available, divided by what this population
        needs, in adult-equivalents. 1.0 means exactly meeting need. This is
        the single number mortality and fertility both respond to - see the
        module docstring for why there is nothing else in that path.

        `jitter=True` adds the year-to-year noise described at
        NUTRITION_YEAR_TO_YEAR_NOISE_STD's declaration, drawn from THIS
        population's own `_random` (never a shared or module-level
        generator, so two Populations' draws never interfere with each
        other regardless of call order). It defaults to False for the
        reason given there and at `step()`.
        """
        adult_equivalent_population = (
            self.children * CHILD_CALORIE_EQUIVALENT
            + self.working_age * 1.0
            + self.elderly * ELDERLY_CALORIE_EQUIVALENT)
        if adult_equivalent_population <= 0.0:
            return 1.0
        ratio = (food_available_calories_per_day
                 / (adult_equivalent_population
                    * SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY))
        if jitter:
            ratio *= (1.0 + self._random.gauss(0.0, NUTRITION_YEAR_TO_YEAR_NOISE_STD))
        return max(0.0, ratio)

    def step(self, food_available_calories_per_day, immigration=0.0,
             emigration=0.0, jitter=False):
        """Advance by one year. Mutates this Population in place and returns
        the flows that moved it, for the caller (a test, or eventually an
        engine) to check the accounting against.

        ORDER OF OPERATIONS, fixed so the same inputs always give the same
        outputs regardless of what order someone might otherwise be tempted
        to compute things in:

          1. Nutrition ratio from THIS YEAR'S STARTING counts - the
             population that has to be fed this year is the one that exists
             at the start of it, not one already thinned by this year's own
             deaths.
          2. Deaths per band, from starting counts and that ratio.
          3. Births, from the starting working-age count and that ratio -
             also computed against the start-of-year count, for the same
             reason as (1).
          4. Survivors age (children into working-age, working-age into
             elderly) at a rate of 1/(band width), the standard way to turn
             a coarse band into an annual transition without tracking
             single-year ages.
          5. Immigration and emigration are applied to the working-age band
             only (migrants are disproportionately working-age in every
             historical migration stream this project is aware of), after
             aging.

        `jitter` defaults to False: see NUTRITION_YEAR_TO_YEAR_NOISE_STD's
        declaration for why unconditional noise is not on by default (it
        biases the long-run population down for a reason that has nothing
        to do with real harvest variability and everything to do with this
        model not yet having grain storage to damp it). Pass `jitter=True`
        to opt into it for a scenario that specifically wants to explore
        that variability; `stationary()` below always uses the default
        (False), since it is looking for the model's noise-free fixed
        point.

        The identity `start_total + births + immigration - deaths -
        emigration == end_total` holds exactly (see
        test_demography.py's accounting-closure check) because every term
        that moves people BETWEEN bands (aging) is added to one band and
        subtracted from another in the same step and so cancels out of the
        total; only births, deaths, immigration and emigration touch the
        total itself.
        """
        start_total = self.total
        ratio = self.nutrition_ratio(food_available_calories_per_day, jitter=jitter)

        deaths_children = self.children * min(1.0, BASELINE_ANNUAL_MORTALITY_RATE_CHILD
                                              * _excess_mortality_multiplier(
                                                  ratio, STARVATION_VULNERABILITY_CHILD))
        deaths_working_age = self.working_age * min(
            1.0, BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
            * _excess_mortality_multiplier(ratio, STARVATION_VULNERABILITY_WORKING_AGE))
        deaths_elderly = self.elderly * min(
            1.0, BASELINE_ANNUAL_MORTALITY_RATE_ELDERLY
            * _excess_mortality_multiplier(ratio, STARVATION_VULNERABILITY_ELDERLY))

        births = (self.working_age * FEMALE_SHARE_OF_WORKING_AGE_POPULATION
                  * ANNUAL_FERTILITY_RATE_PER_WOMAN * _fertility_multiplier(ratio))

        survivors_children = self.children - deaths_children
        survivors_working_age = self.working_age - deaths_working_age
        survivors_elderly = self.elderly - deaths_elderly

        children_aging_out = survivors_children / CHILD_BAND_WIDTH_YEARS
        working_age_aging_out = survivors_working_age / WORKING_AGE_BAND_WIDTH_YEARS

        self.children = survivors_children - children_aging_out + births
        self.working_age = (survivors_working_age - working_age_aging_out
                             + children_aging_out + immigration - emigration)
        self.elderly = survivors_elderly + working_age_aging_out

        end_total = self.total
        return StepFlows(
            start_total=start_total, births=births, immigration=immigration,
            deaths=deaths_children + deaths_working_age + deaths_elderly,
            emigration=emigration, end_total=end_total, nutrition_ratio=ratio,
            deaths_children=deaths_children,
            deaths_working_age=deaths_working_age,
            deaths_elderly=deaths_elderly)

    @classmethod
    def stationary(cls, total_population, seed=0, years=400):
        """A Population of the given total, with an age structure that is
        the model's OWN stable answer to "what age structure does a
        population fed at exactly subsistence, forever, settle into" -
        rather than a split invented separately from the mortality and
        fertility rates that will then be applied to it.

        This exists because a civilisation file (data/civilizations/*.json)
        records a total population and nothing about its age structure, and
        an age structure invented independently of BASELINE_ANNUAL_MORTALITY_
        RATE_* and TOTAL_FERTILITY_RATE would not actually be this model's
        stationary state - starting from one would produce a sharp, fake
        transient in the first few decades of any run as the model
        corrected the mismatch. Iterating the model itself at the noise-free
        subsistence ratio until the PROPORTIONS (not the absolute size,
        which will drift a little at each step) stop moving finds the
        structure this model actually implies, and rescaling that structure
        to the requested total is then the natural way to seed one.

        `years=400` is roughly ten times CHILD_BAND_WIDTH_YEARS +
        WORKING_AGE_BAND_WIDTH_YEARS, comfortably enough for age-structure
        transients (which move on the timescale of one to two generations)
        to have died out; it is a convergence budget, not a modelling claim,
        so it is not `declare()`d.
        """
        probe = cls(total_population / 3.0, total_population / 3.0,
                    total_population / 3.0, seed=seed)
        for _ in range(years):
            probe.step(probe._subsistence_food(), jitter=False)
        scale = total_population / probe.total
        return cls(probe.children * scale, probe.working_age * scale,
                    probe.elderly * scale, seed=seed)

    def _subsistence_food(self):
        """Exactly enough calories to put this population's nutrition ratio
        at 1.0 right now, with no noise - the noise-free food level
        `stationary()` iterates against to find a genuine fixed point."""
        adult_equivalent_population = (
            self.children * CHILD_CALORIE_EQUIVALENT
            + self.working_age * 1.0
            + self.elderly * ELDERLY_CALORIE_EQUIVALENT)
        return adult_equivalent_population * SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY
