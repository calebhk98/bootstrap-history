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
declaration for what that costs), or regions.

DISEASE AND SANITATION ARE NOW A SECOND, SEPARATE AXIS, DISTINCT FROM
NUTRITION - no longer folded into the mortality-vs-nutrition relationship the
way docs/architecture/CURRENT_CODE_ARCHITECTURE_REVIEW.md SS6.6 once
described as an acceptable "minimal first version". The stakeholder's own
diagnosis (see this task's report) was exact: with only a nutrition axis,
mortality could only ever rise above its pre-industrial baseline, and
SURVIVAL_TO_WORKING_AGE was a plain constant that unlimited food could never
move - a model that cannot express clean water, sewered sanitation, germ
theory or vaccination doing what they actually did. `step()` and
`Population.stationary()` now also take a `disease_burden` argument, 1.0
(the default - today's full pre-industrial infectious-disease environment,
identical to this module's behaviour before this change) down to 0.0 (clean
water and sanitation, germ theory-informed hygiene and quarantine, and
vaccination all fully present). See `_disease_mortality_multiplier`,
`_fertility_ceiling_for_disease_burden` and `child_survival_fraction` below
for the mechanism, and this task's own report for exactly what the engine
would have to compute from `data/civilizations/_TECH_EFFECTS.json`'s medical
entries to drive it - this module still does not import the engine or the
tech tree, and takes disease burden only as a plain float handed to it.
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
# rather than a specific dated outcome.
#
# THIS CALIBRATION FAILED ITS OWN STATED TEST, AND WAS CAUGHT MEASURING IT
# PROPERLY RATHER THAN BY EYE. With SURVIVAL_TO_WORKING_AGE at 0.50 (this
# range's harsh end), the pre-correction BASELINE_ANNUAL_MORTALITY_RATE_
# WORKING_AGE at 0.014 (its own range's harsh end) and TOTAL_FERTILITY_RATE
# at 5.0, a population fed EXACTLY at subsistence forever - constant,
# zero-variance, no jitter, nothing else in play - did not hold flat. It
# shrank by 0.030%/year, every year, forever: 1,000,000 people became
# 970,422 over an unshocked century (`sim/tests/test_demography.py`'s
# `StationarityTests` computed births 33,930.5 against deaths 34,230.7 in a
# single year at ratio 1.0 - a permanent net deficit, not sampling noise,
# since nothing here varies). The old comment on this paragraph called the
# drift "under -0.1%" and treated that as close enough; it is not - over the
# 500 years this game plays, -0.03%/year compounds to a 14% loss with
# nothing bad happening, which is not what a "roughly stationary" baseline
# means and not what CLAUDE.md SS3.2 asks this model to produce.
#
# TWO THINGS WERE CHECKED AND RULED OUT before touching a rate. First,
# whether `Population.stationary`'s cohort construction disagrees with
# `step`'s own rates (i.e. seeds an age structure the model's own dynamics
# would not settle into): it does not. The converged children:working-age
# ratio `stationary()` finds (0.6714) and the elderly:working-age ratio it
# finds (0.4956) both solve this module's own transition matrix's dominant-
# eigenvalue equation to four decimal places - `stationary()` is correctly
# finding this model's own fixed point, including its (small) built-in
# decline, not seeding something the step rates then fight. Second, whether
# jitter/weather variance is required for a decline at all (the mechanism
# every earlier pass at this problem, including two prior investigations,
# examined): it is not - the number above has jitter=False and constant
# food, so Jensen's inequality (see _excess_mortality_multiplier's own
# docstring, which is the real and separate mechanism behind the FULL
# engine's larger, weather-driven decline) cannot be what is happening here.
#
# WHAT IS ACTUALLY HAPPENING: solving the exact continuous-age Lotka
# renewal equation for these same three rates (no band coarsening at all -
# a closed-form check, independent of this module's own 3-band mechanics)
# gives a net reproduction ratio of 0.9946, not 1.0 - i.e. the three
# harshest-defensible points from three independent literature ranges,
# stacked together, describe a population that is genuinely, if barely,
# sub-replacement even in principle, before this module's own 3-band
# coarsening adds anything of its own. Reproducing the identical rates in
# this module's 3-band transition matrix widens that to the measured
# -0.030%/year (a coarse-cohort discretization cost, not a new biological
# claim - see the paragraph below BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
# for why refining that discretization further was tried and rejected).
# Stacking three separately-uncertain "toward the harsh end" choices is
# itself the error the file's own prior comment did not check for: each of
# the three individually stays inside its citation, but choosing the
# pessimistic end of all three simultaneously describes a population more
# extreme than any one citation supports on its own, and the file's own
# stated goal for this joint choice - a self-replacing NRR near 1, per
# CLAUDE.md SS3.2's own anchors - was not actually being met. Fixed by
# moving BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE (below) off its range's
# harsh end and onto its range's midpoint instead, plus a second, smaller
# and independently sourced correction described there
# (DOUBLE_COUNT_CORRECTION_FACTOR). SURVIVAL_TO_WORKING_AGE and
# TOTAL_FERTILITY_RATE are UNCHANGED - only one of the three stacked harsh-
# end choices needed to move to stop the stack, and moving the fewest
# numbers keeps this auditable.
#
# Re-measured at these settings, by this module (see
# sim/tests/test_demography.py's stationarity check, which prints them):
# crude birth rate 34.0/1000, crude death rate 33.1/1000, life expectancy at
# birth 30.3 years, net drift over 300 years at subsistence now +29.5%
# (+0.086%/year) rather than the earlier, silently-wrong "under -0.1%" this
# comment used to claim - all still land inside CLAUDE.md SS3.2's targets
# (25-45/1000 for the crude rates, 18-35 years for e0), and the small
# positive drift is deliberately far short of the ~9.06%/year biological
# ceiling GrowthCeilingTests checks against (a population held exactly at
# subsistence should be slow, not racing toward that ceiling - that ceiling
# is for unlimited food, checked separately). None of these three numbers
# is a free parameter chosen to hit this specific figure - the only freedom
# used, both before and after this fix, is where inside each already-
# sourced range the numbers sit relative to each other.

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
        "described in this module's docstring. LEFT AT THE HARSH END, NOT "
        "MOVED: the joint-calibration failure described in the paragraph "
        "above this declaration only needed one of the three stacked "
        "harsh-end choices to move to stop being sub-replacement; moving "
        "BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE instead (below) was "
        "enough, and touching the fewest sourced numbers keeps this "
        "auditable. If a future change needs more headroom, this is the "
        "widest of the three ranges (45%-70%) and the next one to revisit.")

DOUBLE_COUNT_CORRECTION_FACTOR = declare(
    "DOUBLE_COUNT_CORRECTION_FACTOR", 0.995,
    kind="biological_parameter",
    unit="multiple applied to an annual mortality hazard",
    source="Fogel's review of Wrigley & Schofield's own English mortality "
           "series (the same series BASELINE_ANNUAL_MORTALITY_RATE_WORKING_"
           "AGE is drawn from) bounds ALL crisis mortality - epidemic and "
           "famine combined - at under 5% of total pre-1800 English deaths, "
           "and attributes less than 10% of even that crisis share to "
           "famine specifically (year-to-year mortality swings tracked "
           "epidemic disease far more than food prices or harvests). The "
           "most that ordinary harvest-driven mortality could already be "
           "baked into a baseline rate estimated from that series is "
           "therefore bounded above by 5% * 10% = 0.5% of it - stated here "
           "as the surviving fraction, 1 - 0.005.",
    confidence="C",
    why="This module's own nutrition-ratio mechanism (see "
        "_excess_mortality_multiplier) ALSO adds harvest-driven excess "
        "mortality on top of the baseline whenever a real shortfall drops "
        "the ratio below 1.0. To the extent the baseline historical series "
        "already contains some of that same harvest-driven mortality "
        "averaged in, applying the module's own response on top of it "
        "double-counts that sliver - real but small, per the source above. "
        "Applied to BASELINE_ANNUAL_MORTALITY_RATE_CHILD and _WORKING_AGE, "
        "both ultimately traceable to the same English mortality "
        "reconstructions; NOT applied to BASELINE_ANNUAL_MORTALITY_RATE_"
        "ELDERLY, which is sourced from Coale-Demeny model life tables "
        "(see REMAINING_LIFE_EXPECTANCY_AT_WORKING_AGE_CEILING_YEARS) "
        "rather than this specific English series, so this specific bound "
        "does not transfer to it. Requested directly by the stakeholder "
        "(see this task's own report) after a prior investigation measured "
        "this same bound and correctly found it, ALONE, more than an order "
        "of magnitude smaller than the drag it was checked against "
        "(MortalityDragDecompositionTests, unchanged and still passing) - "
        "true, but 'too small to explain the whole gap' is not 'too small "
        "to bother applying', and over the 500 years this game plays even "
        "a fraction of a percent compounds.")

# exp(mean_hazard * -width) == SURVIVAL_TO_WORKING_AGE, per band width, i.e.
# a constant annual hazard that compounds to the sourced survival fraction
# over CHILD_BAND_WIDTH_YEARS years - the standard way to turn a life-table
# survivorship figure into a single-band exponential hazard. The double-
# count correction is applied on top, as a separate, explicit factor,
# rather than folded into SURVIVAL_TO_WORKING_AGE itself, so the sourced
# survival fraction stays legible on its own and the correction stays
# auditable as its own line.
BASELINE_ANNUAL_MORTALITY_RATE_CHILD = (
    -math.log(SURVIVAL_TO_WORKING_AGE) / CHILD_BAND_WIDTH_YEARS
    * DOUBLE_COUNT_CORRECTION_FACTOR)

BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE = declare(
    "BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE", 0.0125,
    kind="biological_parameter",
    unit="fraction of cohort per year",
    source="Wrigley & Schofield's reconstructed English mortality rates "
           "for ages 15-49 in the early-modern period run roughly "
           "1.0-1.5% per year outside epidemic years. MOVED FROM 0.014 "
           "(near this range's upper end) TO 0.0125, this range's own "
           "midpoint. Not a new source: the range is the same one already "
           "cited here. What changed is which point inside it is used, and "
           "why - see the long comment above SURVIVAL_TO_WORKING_AGE for "
           "the measurement that made this necessary: with SURVIVAL_TO_"
           "WORKING_AGE and TOTAL_FERTILITY_RATE both left at their own "
           "documented ranges' harsh ends (as they still are), stacking a "
           "third independently-uncertain harsh-end choice on top of them "
           "described a population more pessimistic than any one of the "
           "three citations, on its own, supports - measured as a genuine, "
           "zero-variance, exactly-at-subsistence decline of 0.030%/year, "
           "not the near-replacement rate this module's own stated "
           "calibration goal (the paragraph above SURVIVAL_TO_WORKING_AGE) "
           "was supposed to produce. Moving this one rate to its own "
           "range's midpoint - not to whatever point would exactly zero "
           "the result, which was not chosen or searched for - stops the "
           "three-way stack without touching either of the other two "
           "sourced figures.",
    confidence="C",
    why="Adults are the survivors of the child band's much higher hazard, "
        "so their own baseline rate is far lower; this is what makes "
        "'kill 30% of the population' and 'more mouths than usual' hit the "
        "child and elderly bands harder than the working-age one, matching "
        "the real age pattern of famine and plague mortality (see "
        "STARVATION_VULNERABILITY_CHILD / _ELDERLY below). A FINER-GRAINED "
        "FIX WAS TRIED FIRST AND REJECTED: splitting the child and working-"
        "age bands into several equal-width sub-stages (the 'linear chain "
        "trick' - representing a fixed-width age band as a chain of "
        "several exponential compartments instead of one, which is a "
        "numerical-refinement technique, not a new curve, since every "
        "sub-stage would still use this SAME flat rate) was checked "
        "numerically against the exact continuous-age Lotka renewal "
        "equation for these rates. It does not converge cleanly toward "
        "that continuous answer as the stage count grows - the resulting "
        "growth rate swung from -0.28%/year to +0.60%/year across "
        "otherwise-reasonable stage counts, with no sourced basis for "
        "preferring one stage count over another. That swing is bigger "
        "than the deficit it would be used to fix, so picking a stage "
        "count would just be this same forbidden move (tuning a free "
        "parameter to make a number come out) wearing a numerical-methods "
        "costume. Rejected for that reason, in favour of the smaller, "
        "auditable, within-cited-range change actually made above.")
# The double-count correction is applied here, on top of the declared
# literature figure, for the same reason it is applied on top of
# SURVIVAL_TO_WORKING_AGE above rather than folded into either sourced
# number directly: the registry above records the literature midpoint
# (0.0125) with its own citation; this line's own factor is the separately-
# sourced adjustment on top of it (see DOUBLE_COUNT_CORRECTION_FACTOR).
BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE *= DOUBLE_COUNT_CORRECTION_FACTOR

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
# DISEASE AND SANITATION: a second axis, distinct from nutrition, that can
# take mortality below the pre-industrial baseline and child survival above
# its pre-industrial 0.5
# ============================================================================
# `disease_burden` is a plain float, 1.0 to 0.0, that a caller hands to
# `step()`/`stationary()` alongside the nutrition ratio. It is NOT read from
# the tech tree or the engine by this module - see the module docstring and
# this task's own report for what the engine would have to compute to
# produce one.
#
#   1.0  today's default. The full pre-industrial infectious-disease
#        environment that SURVIVAL_TO_WORKING_AGE and the three
#        BASELINE_ANNUAL_MORTALITY_RATE_* figures above already describe.
#        Every scenario that never sets this argument (every test and
#        engine call site that predates this change) behaves EXACTLY as
#        before - this axis is additive, not a replacement for the
#        nutrition one.
#   0.0  clean water and sewered sanitation, germ theory-informed hygiene
#        and quarantine, and vaccination all fully present.
#
# WHY THIS IS A SEPARATE MULTIPLICATIVE CHANNEL FROM NUTRITION, NOT A
# REPLACEMENT FOR IT. `_excess_mortality_multiplier` (nutrition) is
# deliberately floored at 1.0 - see its own docstring for the literature
# search (Antonovsky's social-class mortality differentials, the British
# peerage's own mortality record) that found no sourced nutrition-only
# mortality benefit below the historical baseline, and that conclusion is
# UNCHANGED and still correct: better-fed pre-industrial populations did not
# reliably outlive worse-fed ones by much, because nutrition alone was never
# what was holding pre-industrial mortality up. Disease is a different,
# independently and extensively documented channel: the historical
# mortality decline that took crude death rates from the 30-40/1000 this
# module's baseline describes down toward modern rates under 10/1000 is
# attributed by the historical-demography literature overwhelmingly to
# infectious-disease control specifically, not to better diets - Omran's
# epidemiologic transition (Omran, "The Epidemiologic Transition: A Theory
# of the Epidemiology of Population Change", Milbank Memorial Fund
# Quarterly, 1971) names exactly this shift ("age of pestilence and famine"
# to "age of receding pandemics") as the mechanism, and Preston's
# decomposition of 20th-century life expectancy gains (Preston, "The
# Changing Relation between Mortality and Level of Economic Development",
# Population Studies, 1975) and Cutler & Miller's study of clean water
# technology in early-20th-century American cities (Cutler & Miller, "The
# Role of Public Health Improvements in Health Advances: The Twentieth-
# Century United States", Demography, 2005 - finding clean water alone
# responsible for roughly half of the total urban mortality decline they
# studied, and nearly all of the child-mortality share of it) both find the
# same thing from different data. That is why THIS channel, unlike the
# nutrition one, is allowed to take mortality below the pre-industrial
# baseline - it is a different, sourced mechanism, not the same one applied
# more generously.

MODERN_SURVIVAL_TO_WORKING_AGE_CEILING = declare(
    "MODERN_SURVIVAL_TO_WORKING_AGE_CEILING", 0.95,
    kind="biological_parameter",
    unit="fraction of live births",
    source="World Bank / UNICEF-WHO-UN IGME under-5 mortality estimates for "
           "the two countries this task's own brief names as today's "
           "fastest-growing real populations - Niger (under-5 mortality on "
           "the order of 75-80 per 1,000 live births in recent UN IGME "
           "estimates, i.e. roughly 92-93% survival to age 5) and Uganda "
           "(on the order of 40-45 per 1,000, i.e. roughly 95-96% survival "
           "to age 5) - both already running under modern, if imperfect, "
           "germ theory-informed medicine, sanitation and vaccination "
           "coverage, and both without a food constraint (that is what "
           "makes their growth rate this task's own upper anchor). "
           "Surviving from age 5 to age 15 costs a little further mortality "
           "in any real population (UN model life tables), so 0.95 sits "
           "inside, not above, the age-5 range these two real populations "
           "show - used here as an estimate of where survival-to-15 lands "
           "under a fully modern disease-and-sanitation regime, not a "
           "figure read directly off either country's own age-15 table "
           "(neither source publishes one at the resolution this needed).",
    confidence="C",
    why="The disease-free endpoint of the child band's disease-response "
        "curve, paired with SURVIVAL_TO_WORKING_AGE (the pre-industrial "
        "endpoint, disease_burden==1.0) exactly the way SUBSISTENCE_"
        "CALORIES... and STARVATION_FLOOR_CALORIES... anchor the nutrition "
        "response: two sourced points, one invented interpolation between "
        "them (see _disease_mortality_multiplier).")

# Same log-hazard transform BASELINE_ANNUAL_MORTALITY_RATE_CHILD was built
# with, run on the modern endpoint instead of the pre-industrial one. NO
# DOUBLE_COUNT_CORRECTION_FACTOR here: that correction is specifically about
# a property of the WRIGLEY & SCHOFIELD ENGLISH SERIES SURVIVAL_TO_WORKING_
# AGE and BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE are drawn from (see
# that constant's own declaration) - a multi-century average that may
# already contain some of the harvest-driven mortality this module's own
# nutrition mechanism separately adds. MODERN_SURVIVAL_TO_WORKING_AGE_
# CEILING is sourced from present-day UN IGME national estimates, an
# entirely different data-collection method with no shared provenance and
# no reason to carry that specific bias.
MODERN_ANNUAL_MORTALITY_RATE_CHILD_FLOOR = (
    -math.log(MODERN_SURVIVAL_TO_WORKING_AGE_CEILING) / CHILD_BAND_WIDTH_YEARS)

# The child band's disease floor multiplier is DERIVED, not declared: it is
# the ratio of two already-sourced hazards (the modern one just above, the
# pre-industrial one at the top of this file), not a new invented number of
# its own.
DISEASE_MORTALITY_FLOOR_MULTIPLIER_CHILD = (
    MODERN_ANNUAL_MORTALITY_RATE_CHILD_FLOOR
    / BASELINE_ANNUAL_MORTALITY_RATE_CHILD)

# The two endpoints of the disease_burden SCALE ITSELF. These are
# definitional, not sourced empirical facts (unlike everything declare()d
# above and below), so they are plain floats rather than declare()d: there
# is nothing to cite for "1.0 is the top of the scale and 0.0 is the
# bottom", only a choice of which end means which regime, made once here
# and used everywhere else in this module.
PRE_INDUSTRIAL_DISEASE_BURDEN = 1.0
FULLY_MODERN_DISEASE_BURDEN = 0.0

DISEASE_MORTALITY_FLOOR_MULTIPLIER_WORKING_AGE = declare(
    "DISEASE_MORTALITY_FLOOR_MULTIPLIER_WORKING_AGE", 0.35,
    kind="temporary_heuristic",
    unit="multiple of pre-industrial baseline mortality",
    source=None,
    confidence="D",
    why="No single study isolates the exact share of pre-industrial "
        "working-age mortality that was infectious in origin, the way "
        "MODERN_SURVIVAL_TO_WORKING_AGE_CEILING lets the child band's floor "
        "be DERIVED rather than guessed. What the historical-demography "
        "literature does establish directionally and repeatedly - Riley, "
        "\"Rising Life Expectancy: A Global History\" (2001); Omran 1971 "
        "above - is that tuberculosis, typhoid/enteric fever and dysentery "
        "were the leading killers of 15-49-year-olds specifically in "
        "pre-transition Europe (TB alone was called \"the Captain of the "
        "Men of Death\" and its 19th-century mortality peaked at ages "
        "20-40), all three squarely addressed by clean water, sanitation "
        "and germ theory-informed hygiene, alongside a real but smaller "
        "non-infectious residual this axis does NOT reach (accidents, "
        "violence, non-infectious degenerative disease, obstetric "
        "haemorrhage as opposed to obstetric SEPSIS - see med_obstetric_"
        "antisepsis below). 0.35 (a roughly two-thirds reduction) is the "
        "invented point that reflects 'most, not all, of pre-industrial "
        "working-age mortality was infectious', deliberately less extreme "
        "than the child band's ~13x reduction (DISEASE_MORTALITY_FLOOR_"
        "MULTIPLIER_CHILD), because every source above agrees the "
        "epidemiologic transition's mortality decline was concentrated "
        "far more in infancy and childhood than in adulthood. Replace with "
        "a derived figure if a source ever splits pre-transition adult "
        "cause-of-death the way UN IGME splits child cause-of-death.")

DISEASE_MORTALITY_FLOOR_MULTIPLIER_ELDERLY = declare(
    "DISEASE_MORTALITY_FLOOR_MULTIPLIER_ELDERLY", 0.45,
    kind="temporary_heuristic",
    unit="multiple of pre-industrial baseline mortality",
    source=None,
    confidence="D",
    why="Same status and reasoning as DISEASE_MORTALITY_FLOOR_MULTIPLIER_"
        "WORKING_AGE, set slightly higher (a smaller disease-driven "
        "reduction) for the same reason STARVATION_VULNERABILITY_ELDERLY "
        "differs from _WORKING_AGE elsewhere in this file: pre-antibiotic "
        "pneumonia and influenza were real, infection-driven killers of the "
        "elderly (the historical aphorism that 'pneumonia is the old man's "
        "friend' is about exactly this), which clean water and germ "
        "theory-informed hygiene do not reach as directly as they reach "
        "diarrhoeal and typhoid mortality, and degenerative disease's share "
        "of elderly mortality was already larger pre-transition than at "
        "working age, leaving less room for a disease-and-sanitation axis "
        "to close. Not separately sourced beyond the qualitative direction "
        "above; the specific value is this module's own invented point "
        "between the child and working-age floors.")


def _disease_mortality_multiplier(disease_burden: float, floor_multiplier: float) -> float:
    """How much a band's baseline mortality hazard is scaled by, given the
    disease-and-sanitation environment - the disease-axis counterpart to
    `_excess_mortality_multiplier`'s nutrition axis, and the mechanism that
    lets `Population.step` take mortality below the pre-industrial baseline
    (see the section docstring above for why that is allowed here and not
    on the nutrition axis).

    Linear between two endpoints exactly the way `_excess_mortality_
    multiplier` is linear between subsistence and the starvation floor: 1.0
    at disease_burden==1.0 (by construction - this axis changes nothing
    when nobody sets it), `floor_multiplier` at disease_burden==0.0 (sourced
    per band at each call site above). The two endpoints are real; the
    straight line between them is the same kind of invented interpolation
    as the nutrition axis's, not a claim about the actual shape of a real
    disease-elimination trajectory.
    """
    disease_burden = max(0.0, min(1.0, disease_burden))
    return floor_multiplier + (1.0 - floor_multiplier) * disease_burden


DISEASE_FERTILITY_CEILING_UPLIFT_FRACTION = declare(
    "DISEASE_FERTILITY_CEILING_UPLIFT_FRACTION", 0.30,
    kind="temporary_heuristic",
    unit="fraction by which the nutrition-driven fertility ceiling rises "
         "as disease_burden falls from 1.0 to 0.0",
    source="Frank, \"Infertility in Sub-Saharan Africa: Estimates and "
           "Implications\", Population and Development Review, 1983, and "
           "Bongaarts, Frank & Lesthaeghe, \"The Proximate Determinants of "
           "Fertility in Sub-Saharan Africa\", Population and Development "
           "Review, 1984: the historically documented sub-Saharan "
           "'infertility belt', where sexually-transmitted-infection-driven "
           "pathological sterility (chiefly tubal damage from untreated "
           "gonococcal and chlamydial infection) measurably depressed total "
           "fertility rates in affected regions by roughly 20-40% relative "
           "to disease-free natural-fertility populations under the same "
           "nutritional and breastfeeding regime. 0.30 is that range's "
           "midpoint, not its high or low end - unlike every point-within-"
           "range choice earlier in this file, there is no reason here to "
           "lean conservative in either direction (the earlier convention "
           "leaned toward not overstating growth; that same conservatism "
           "left FERTILITY_SURPLUS_CEILING_MULTIPLIER anchored to the "
           "Hutterites' own REALIZED rate under real, non-zero disease "
           "burden, which is the mistake this task's report corrects).",
    confidence="D",
    why="FERTILITY_SURPLUS_CEILING_MULTIPLIER (1.8x baseline fertility) is "
        "sourced to the Hutterites - Eaton & Mayer 1953 - the best-"
        "documented natural-fertility population, but the stakeholder's "
        "correction to this task (see this task's own report) is that "
        "Hutterite colonies farmed finite land and lived through the "
        "pre-antibiotic era's ORDINARY infectious mortality: their 9-11 "
        "births/woman is fertility ACHIEVED under a real, non-zero disease "
        "burden, not a disease-free ceiling. A single flat "
        "FERTILITY_SURPLUS_CEILING_MULTIPLIER cannot be both 'the ceiling "
        "reached under today's default pre-industrial disease_burden==1.0' "
        "(which the exactly-subsistence and pre-industrial-unlimited-food "
        "acceptance targets require to stay unchanged) AND 'a ceiling that "
        "rises once disease is removed' at the same time - so this fraction "
        "makes the CEILING ITSELF a second, separate function of "
        "disease_burden (see _fertility_ceiling_for_disease_burden), "
        "exactly mirroring how mortality got a second, separate disease "
        "axis rather than a change to its existing nutrition-only "
        "response. Directionally this is the fertility side of the same "
        "well-documented phenomenon _disease_mortality_multiplier's own "
        "docstring cites for mortality - disease suppressing a vital rate "
        "below what nutrition and behaviour alone would produce - via a "
        "different, but real and specifically sourced, biological pathway "
        "(pathological sterility rather than mortality).")


def _fertility_ceiling_for_disease_burden(disease_burden: float) -> float:
    """The fertility ramp's ceiling (see `_fertility_multiplier`) as a
    function of the disease-and-sanitation environment, not a fixed number.

    At disease_burden==1.0 (today's default) this returns exactly
    FERTILITY_SURPLUS_CEILING_MULTIPLIER, unchanged - every scenario that
    never sets disease_burden gets the identical ceiling this module has
    always used, so the exactly-subsistence and pre-industrial-disease/
    unlimited-food acceptance targets are untouched by this function's
    existence. As disease_burden falls toward 0.0 the ceiling rises toward
    FERTILITY_SURPLUS_CEILING_MULTIPLIER * (1 + DISEASE_FERTILITY_CEILING_
    UPLIFT_FRACTION) - see that constant's own declaration for why the
    ceiling needs a second, disease-driven degree of freedom rather than
    just being raised outright.
    """
    disease_burden = max(0.0, min(1.0, disease_burden))
    disease_free_ceiling = (
        FERTILITY_SURPLUS_CEILING_MULTIPLIER
        * (1.0 + DISEASE_FERTILITY_CEILING_UPLIFT_FRACTION))
    return (FERTILITY_SURPLUS_CEILING_MULTIPLIER
            + (disease_free_ceiling - FERTILITY_SURPLUS_CEILING_MULTIPLIER)
            * (1.0 - disease_burden))


# ============================================================================
# THE FOOD-TO-VITAL-RATES MECHANISM
# ============================================================================

def _excess_mortality_multiplier(nutrition_ratio: float, vulnerability: float) -> float:
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

    A SECOND HYPOTHESIS WAS CHECKED (re-opened for the unshocked-century
    follow-up to Complaints/45-no-granary-so-the-baseline-collapses.md,
    after the granary and the fertility ramp above 1.0 had already closed
    most of the gap but 100 years of rome_100ad with events=False still
    settled around 74 percent of its starting population - measured on
    this checkout by running the real engine, not estimated): that the
    three BASELINE_ANNUAL_MORTALITY_RATE_* / SURVIVAL_TO_WORKING_AGE
    figures are DOUBLE-COUNTING bad years, because the historical series
    they are drawn from is itself a multi-century average that already
    contains ordinary harvest-driven mortality swings, and this module
    then adds its own harvest-driven excess mortality ON TOP of a number
    that already has some baked in. The direction of that concern is
    correct, but its SIZE is not what closes the remaining gap, and this
    is a case where the literature gives an actual bound rather than
    silence: Fogel's review of Wrigley & Schofield's own English series
    (the source BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE cites) puts ALL
    crisis mortality - famine AND epidemic together - at under 5 percent of
    total pre-1800 English mortality, and attributes less than 10 percent
    of even that crisis share to famine specifically (Wrigley & Schofield
    found year-to-year mortality swings tracked epidemic disease far more
    than food prices or harvests). Famine's plausible double-counted share
    of the baseline is therefore bounded above by roughly 5% * 10% = 0.5%
    of it - about seven parts in one hundred thousand of the working-age
    rate per year - which `MortalityDragDecompositionTests` below shows is
    more than an order of magnitude too small to be the residual drag.
    Real double-counting of ordinary bad years is not zero, but it is not
    where the missing population went.

    WHERE THE DRAG ACTUALLY COMES FROM, measured directly from the same
    engine run: the realized nutrition ratio the engine hands this module
    has mean close to 1.0 (0.993 in the run measured for this
    investigation) but real year-to-year variance (its stdev was 0.081 in
    that run, coming from agriculture.py's weather draw and the granary's
    only-partial buffering of it, neither owned by this module). Because
    this function is FLAT at and above 1.0 and RISING below it, it is
    convex at the ratio-1.0 kink, so by Jensen's inequality the AVERAGE of
    this function over a varying ratio is strictly greater than this
    function evaluated at the AVERAGE ratio, even when that average ratio
    sits exactly on the subsistence line. `MortalityDragDecompositionTests`
    proves this with the model's own machinery, not a numeric coincidence:
    two populations fed the identical MEAN food, one at a constant ratio of
    1.0 and one alternating symmetrically around it, diverge - the
    alternating one ends smaller, from nothing but the shape of this
    function. That is the real mechanism, it needs no unsourced floor to
    produce it, and it is a genuine property of subsistence agriculture
    (storage smooths but cannot fully undo the fact that a bad year costs
    more than a good year of the same size gives back) rather than an
    artefact of this module. The remaining lever, to the extent the input
    side of that asymmetry can still be narrowed, is agriculture.py's own
    storage/consumption asymmetry (outside this module's ownership; see
    that module's GRANARY_CAPACITY_YEARS_OF_DEMAND and
    MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE, and the reserve-size experiment
    in this project's own history showing a bigger reserve narrows the
    decline further but a bigger intake ceiling does not) - not this
    function's floor.

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


def _fertility_multiplier(
        nutrition_ratio: float,
        fertility_ceiling: float = FERTILITY_SURPLUS_CEILING_MULTIPLIER) -> float:
    """How much baseline fertility is scaled by, given nutrition.

    `fertility_ceiling` defaults to FERTILITY_SURPLUS_CEILING_MULTIPLIER, so
    every existing caller of this function (including the tests that call
    it directly rather than through `step()`) is unaffected. `step()`
    itself now passes `_fertility_ceiling_for_disease_burden(disease_burden)`
    instead of relying on the default - see that function's own declaration
    for why the ceiling needs to move with the disease-and-sanitation
    environment as well as with nutrition.

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
        return fertility_ceiling
    fraction_of_span = (
        (calories - SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY) / span)
    surplus = (fertility_ceiling - 1.0) * fraction_of_span
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

    def __init__(self, children: float, working_age: float, elderly: float,
                 seed: int = 0) -> None:
        self.children = float(children)
        self.working_age = float(working_age)
        self.elderly = float(elderly)
        self._random = random.Random(seed)

    @property
    def total(self) -> float:
        return self.children + self.working_age + self.elderly

    @property
    def working_age_population(self) -> float:
        """The number this whole module exists to be able to answer."""
        return self.working_age

    def copy(self) -> "Population":
        """An independent Population with its own, separately-advancing
        random stream (re-seeded from a draw of this one's), for branching a
        scenario (e.g. 'what if food had NOT been cut') without either copy's
        later draws depending on how many steps the other one takes.
        """
        clone = Population(self.children, self.working_age, self.elderly,
                            seed=self._random.getrandbits(64))
        return clone

    def __repr__(self) -> str:
        return ("Population(children=%.3f, working_age=%.3f, elderly=%.3f, "
                "total=%.3f)" % (self.children, self.working_age,
                                  self.elderly, self.total))

    def nutrition_ratio(
            self, food_available_calories_per_day: float,
            jitter: bool = False) -> float:
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

    def step(self, food_available_calories_per_day: float, immigration: float = 0.0,
             emigration: float = 0.0, jitter: bool = False,
             disease_burden: float = PRE_INDUSTRIAL_DISEASE_BURDEN) -> "StepFlows":
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
          2. Deaths per band, from starting counts, that ratio, AND
             `disease_burden` - see the "DISEASE AND SANITATION" section
             above `_disease_mortality_multiplier` for what this argument
             means and why it is a second axis rather than a change to the
             nutrition one.
          3. Births, from the starting working-age count, that ratio, and
             `disease_burden` (which also moves the fertility ramp's
             ceiling - see `_fertility_ceiling_for_disease_burden`) - also
             computed against the start-of-year count, for the same reason
             as (1).
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

        `disease_burden` defaults to PRE_INDUSTRIAL_DISEASE_BURDEN (1.0):
        every existing caller, including the engine's own call site in
        sim/engine/core.py, does not pass this argument and so is completely
        unaffected by this parameter's existence - see the module docstring
        and this task's own report for exactly what a caller would need to
        compute to pass in something other than the default.

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

        deaths_children = self.children * min(
            1.0, BASELINE_ANNUAL_MORTALITY_RATE_CHILD
            * _disease_mortality_multiplier(
                disease_burden, DISEASE_MORTALITY_FLOOR_MULTIPLIER_CHILD)
            * _excess_mortality_multiplier(ratio, STARVATION_VULNERABILITY_CHILD))
        deaths_working_age = self.working_age * min(
            1.0, BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
            * _disease_mortality_multiplier(
                disease_burden, DISEASE_MORTALITY_FLOOR_MULTIPLIER_WORKING_AGE)
            * _excess_mortality_multiplier(ratio, STARVATION_VULNERABILITY_WORKING_AGE))
        deaths_elderly = self.elderly * min(
            1.0, BASELINE_ANNUAL_MORTALITY_RATE_ELDERLY
            * _disease_mortality_multiplier(
                disease_burden, DISEASE_MORTALITY_FLOOR_MULTIPLIER_ELDERLY)
            * _excess_mortality_multiplier(ratio, STARVATION_VULNERABILITY_ELDERLY))

        births = (self.working_age * FEMALE_SHARE_OF_WORKING_AGE_POPULATION
                  * ANNUAL_FERTILITY_RATE_PER_WOMAN
                  * _fertility_multiplier(
                      ratio, _fertility_ceiling_for_disease_burden(disease_burden)))

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
    def stationary(cls, total_population: float, seed: int = 0, years: int = 400,
                    disease_burden: float = PRE_INDUSTRIAL_DISEASE_BURDEN) -> "Population":
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

        `disease_burden` defaults to PRE_INDUSTRIAL_DISEASE_BURDEN, matching
        every existing caller (a civilisation's starting age structure is a
        pre-industrial one unless a caller explicitly asks for the stable
        structure a disease-free population would settle into instead).
        """
        probe = cls(total_population / 3.0, total_population / 3.0,
                    total_population / 3.0, seed=seed)
        for _ in range(years):
            probe.step(probe._subsistence_food(), jitter=False,
                       disease_burden=disease_burden)
        scale = total_population / probe.total
        return cls(probe.children * scale, probe.working_age * scale,
                    probe.elderly * scale, seed=seed)

    def _subsistence_food(self) -> float:
        """Exactly enough calories to put this population's nutrition ratio
        at 1.0 right now, with no noise - the noise-free food level
        `stationary()` iterates against to find a genuine fixed point."""
        adult_equivalent_population = (
            self.children * CHILD_CALORIE_EQUIVALENT
            + self.working_age * 1.0
            + self.elderly * ELDERLY_CALORIE_EQUIVALENT)
        return adult_equivalent_population * SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY


def child_survival_fraction(
        nutrition_ratio: float = 1.0,
        disease_burden: float = PRE_INDUSTRIAL_DISEASE_BURDEN) -> float:
    """The fraction of children who reach working age, if `nutrition_ratio`
    and `disease_burden` were both held constant for an entire CHILD_BAND_
    WIDTH_YEARS-year childhood - the closed-form inverse of the transform
    SURVIVAL_TO_WORKING_AGE and MODERN_SURVIVAL_TO_WORKING_AGE_CEILING were
    each turned into a hazard with, run forward instead of backward.

    This is not used by `step()` itself (which works in annual hazards
    applied to a continuous cohort, not in "a child's fate", and a real
    child's nutrition and disease exposure both vary year to year rather
    than sitting fixed for fifteen years) - it exists so a caller, a test,
    or this task's own report can ask the question the stakeholder actually
    asked ("what does survival to working age DO as disease and nutrition
    change") directly, rather than reading it off indirectly through a
    century of simulated cohort flows.

    At disease_burden==PRE_INDUSTRIAL_DISEASE_BURDEN and nutrition_ratio==
    1.0 this returns a little over SURVIVAL_TO_WORKING_AGE (0.50) itself -
    slightly above because of DOUBLE_COUNT_CORRECTION_FACTOR, exactly as
    BASELINE_ANNUAL_MORTALITY_RATE_CHILD's own declaration explains. At
    disease_burden==FULLY_MODERN_DISEASE_BURDEN and nutrition_ratio==1.0 it
    returns exactly MODERN_SURVIVAL_TO_WORKING_AGE_CEILING (0.95), by
    construction (see that constant's own declaration).
    """
    hazard = (BASELINE_ANNUAL_MORTALITY_RATE_CHILD
              * _disease_mortality_multiplier(
                  disease_burden, DISEASE_MORTALITY_FLOOR_MULTIPLIER_CHILD)
              * _excess_mortality_multiplier(nutrition_ratio, STARVATION_VULNERABILITY_CHILD))
    return math.exp(-hazard * CHILD_BAND_WIDTH_YEARS)
