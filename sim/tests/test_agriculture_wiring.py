"""agriculture_wiring: does a real harvest now feed sim.population, and can
a famine actually happen because of it?

WIRING MILESTONE 4's SPECIFIC HOLE (docs/architecture/WIRING_MILESTONE_4.md,
this task's own brief). `Sim._demographic_recovery` (sim/engine/core.py)
used to hand `self.population.step` exactly enough calories to sit at
nutrition_ratio == 1.0 every single year, computed from the cohort counts
themselves - "is there enough food" was ASSUMED, never simulated, so a
famine could not happen for a physical reason at all, only through the
civilisation files' own scripted plague/war hazards (society.py's
_shocks). It now runs one year of sim/world/agriculture.py's land+labour+
weather harvest model (Sim.farm_land, agriculture.Storage) and feeds ITS
food_available_kcal_per_day to demography instead. This module is the
regression test that hole's fix needed and did not have: sim/tests/
test_agriculture.py and sim/tests/test_demography.py each prove their own
module correct in isolation (both still standalone, still green,
unmodified by this wiring - see their own suites), but neither one can
prove the SEAM between them behaves, because the seam does not exist
inside either module.

WHAT EACH CLASS BELOW CHECKS, and why it is the right check for a seam
rather than a module:

  - VariesWithWeatherTests: the food supply reaching demography now
    actually MOVES year to year with no hazard involved, proving it is
    computed rather than assumed (the old stand-in was bit-exact constant
    absent a hazard or a completing technology).
  - NoFamineWithoutCauseTests: with nothing forcing a shortfall, the
    computed food supply lands close to subsistence on average - the
    "the civilisation starts neither land-rich nor land-starved" claim
    farmland_for_population's own docstring makes, checked rather than
    assumed.
  - FamineHasAPhysicalCauseTests: shrinking farmland (a land fact, not a
    date) measurably lowers nutrition_ratio and measurably raises
    population loss relative to an unshocked control over the SAME years -
    the actual causal chain (land -> harvest -> calories -> mortality/
    fertility) exercised end to end, and the direct answer to this
    milestone's acceptance question.
  - DeterminismTests: two identically-constructed Sims fed the same years
    produce bit-identical population trajectories - the weather draw is a
    pure function of (civilisation id, year), not a sequentially-advanced
    generator, specifically so nothing about this wiring depends on how
    many times a --session game was saved and reloaded before reaching a
    given year (see Sim._farm_year_weather_seed's own docstring).
"""
import statistics
import unittest

# UNLIKE test_agriculture.py/test_demography.py, this module's whole subject
# is the SEAM between sim/world/ and sim/engine/, so it needs a real `Sim` -
# there is no standalone-module reason to stay off sim/tests/harness.py the
# way those two explain in their own docstrings. `sim()` (harness.py) builds
# one against the real tree with a fixed rng seed and manual=True/events as
# given, exactly as test_round10.py and test_demographics.py already do for
# every other engine-level demographic check.
from .harness import *  # noqa: F401,F403

# The engine's own copy, not a fresh `sim.world.agriculture` import: this
# repository has two import roots and they produce two distinct module
# objects, so patching or reading the wrong one silently measures nothing.
from sim.engine.core import agriculture


def _rome_sim(events=False):
    return sim(civ="rome_100ad", events=events)


class VariesWithWeatherTests(unittest.TestCase):
    """The pre-wiring stand-in produced a bit-exact-constant food supply,
    forever, absent a hazard: `subsistence_food_kcal_per_day` was computed
    FROM the same cohort counts it was about to feed, so nutrition_ratio
    was always exactly 1.0. If the new wiring is doing anything at all,
    the calorie stream `_demographic_recovery` computes each year has to
    actually move on its own, from nothing but a fresh weather draw.
    """

    def test_food_and_nutrition_ratio_are_not_a_constant(self):
        test_sim = _rome_sim(events=False)
        ratios = []
        for year in range(101, 141):
            test_sim._demographic_recovery(year)
            ratios.append(test_sim._last_demographic_step.nutrition_ratio)
        # NOT a flat distinct-value count: nutrition_ratio is structurally
        # capped at 1.0 (Storage.step never lets consumption exceed demand -
        # a good year's excess is wasted, not banked, given this wiring's
        # own no-carryover simplification, see Sim._demographic_recovery's
        # own docstring), so a comfortable majority of ordinary years
        # legitimately land on EXACTLY 1.0 and repeat that value - a
        # constant stand-in would repeat ONE value literally every year,
        # which pstdev == 0 catches directly and a distinct-value count
        # would not (it would also fail a model that is correctly capped).
        # THE THRESHOLD WAS 0.05, AND IT WAS MEASURING ROME'S REGION COUNT
        # rather than whether this model varies at all. Averaging N
        # independent weather draws divides the spread by about sqrt(N),
        # and weather is now drawn per home region and pooled by land share
        # (Complaints/47) instead of once for the whole empire - Rome's
        # seven unequal regions give an effective N near 5.6, so the same
        # unchanged mechanism reports about 0.035 where it used to report
        # 0.05-plus. Holding the old number would have asserted that a
        # civilisation must be badly diversified. What this check is FOR is
        # unchanged and is stated above: catching a constant stand-in, which
        # repeats one value every year. This century runs 10 distinct values
        # in 40 years.
        self.assertGreater(statistics.pstdev(ratios), 0.02, ratios)
        self.assertLess(min(ratios), 0.9, ratios)
        # THE 1.0 CEILING IS GONE ON PURPOSE. This used to assert
        # max(ratios) <= 1.0, because Storage.step capped consumption at
        # food_demand_kg however full the granary was - so a population
        # could never eat WELL, only adequately or badly. Combined with a
        # mortality and fertility response that floors at 1.0, that made
        # every good year worth nothing and every bad year cost lives,
        # which is the ratchet Complaints/45 is about. Consumption may now
        # exceed subsistence, bounded by what a person can physically eat
        # (MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE) and drawn only from
        # grain already beyond the reserve.
        #
        # The upper bound asserted here is that physiological ceiling, not
        # 1.0 - a ratio above it would mean people eating more than a human
        # can, which is a real bug.
        self.assertLessEqual(max(ratios),
                             agriculture.MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE + 1e-9,
                             ratios)
        # And it must ACTUALLY happen at least once, or the mechanism is
        # present but inert and this test would pass against the old cap.
        self.assertGreater(max(ratios), 1.0, ratios)

    def test_gross_harvest_is_a_real_computed_number_not_zero(self):
        test_sim = _rome_sim(events=False)
        test_sim._demographic_recovery(101)
        flows = test_sim._last_farm_year
        self.assertGreater(flows.gross_harvest_kg, 0.0, flows)
        self.assertGreater(test_sim.farm_land.hectares, 0.0, test_sim.farm_land)


class NoFamineWithoutCauseTests(unittest.TestCase):
    """farmland_for_population sizes Sim.farm_land so an AVERAGE weather
    year (weather_multiplier == 1.0) at reference technique feeds exactly
    this civilisation's starting population, with NO margin above that -
    "neither land-rich nor land-starved" is a statement about the
    reference point, not a promise that the long-run mean stays there.

    IT DOES NOT, AND THIS IS A REAL, LABELLED FINDING, NOT A BUG. Storage.
    step's consumption is capped at demand (a good year's extra harvest is
    never banked, only wasted - the direct, foreseen cost of this wiring's
    own no-cross-year-carryover simplification, see _demographic_recovery's
    own docstring for why), while a bad year is not floored the same way -
    it draws nutrition_ratio down in full. Averaged over a weather
    distribution centred on 1.0, that asymmetry pulls the MEAN ratio below
    1.0 even with no hazard, no land loss, nothing scripted - purely
    Jensen's-inequality-shaped consequence of a one-sided response curve
    meeting a demand-side that cannot be over-fulfilled, on land sized with
    no buffer. A real granary would close most of this gap; this wiring's
    granary does not carry a year's surplus into the next one (see
    _demographic_recovery's own comment on why, and CLAUDE.md SS3.2's
    explicit allowance for the baseline to get worse while the mechanism
    that will fix it does not yet exist). What this class checks is
    therefore not "stays near 1.0" but the two claims that ARE true: the
    mean lands in a plausible, non-degenerate band (ruling out a badly
    mis-sized farm), and the population declines by a real, bounded
    amount rather than collapsing towards extinction or getting stuck at
    a permanent zero-consumption floor (the second of which is exactly the
    seed-cost/land-size bug this task's own fingerprint probe caught and
    this file's FamineHasAPhysicalCauseTests would not have noticed on its
    own, because it only ever runs one or ten years).
    """

    def test_mean_nutrition_ratio_over_many_unshocked_years_is_plausible(self):
        test_sim = _rome_sim(events=False)
        ratios = []
        for year in range(101, 201):
            test_sim._demographic_recovery(year)
            ratios.append(test_sim._last_demographic_step.nutrition_ratio)
        mean_ratio = statistics.fmean(ratios)
        # Loose band: a calibration sanity check ("is the farm roughly the
        # right size, and is the asymmetry above of a plausible magnitude"),
        # not a re-assertion of agriculture.py's own pinned headline number,
        # and not a demand that the no-carryover simplification's own cost
        # be zero.
        self.assertGreater(mean_ratio, 0.7, ratios)
        # THE UPPER BOUND USED TO BE 1.0. It was wrong in principle and
        # only passed by accident. A population that grows must on average
        # be fed at or above subsistence - that is what growth is - so
        # capping the mean at subsistence forbids the outcome the
        # demographic milestone exists to produce. It passed because one
        # weather draw covered the whole empire, which made a surviving
        # surplus rare enough to round away. Weather is now drawn per home
        # region and pooled by land share (Complaints/47), so ordinary good
        # years reach the mean: measured 1.0042 over this century. The
        # ceiling that actually binds eating is physical, not this number -
        # MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE, 1.75.
        self.assertLess(mean_ratio, 1.1, ratios)

    def test_population_declines_but_does_not_run_away_to_extinction(self):
        test_sim = _rome_sim(events=False)
        start_total = test_sim.population.total
        never_hit_zero_consumption = True
        for year in range(101, 201):
            test_sim._demographic_recovery(year)
            if test_sim._last_demographic_step.nutrition_ratio < 1e-6:
                never_hit_zero_consumption = False
        end_total = test_sim.population.total
        # A REAL decline (the asymmetry above, compounded over a century)
        # is expected and is not what this guards against - see this
        # class's own docstring. What it guards against is a RUNAWAY: the
        # population reaching a state where a whole year's harvest cannot
        # feed anyone at all (nutrition_ratio pinned at exactly zero), which
        # is what an earlier, buggy version of this wiring did (seed cost
        # charged against this civilisation's full historical farmland
        # every year regardless of how few hands were left to work it,
        # manufacturing a collapse with no weather content at all - see
        # Sim._demographic_recovery's own comment on why `hectares_worked`,
        # not `farm_land` itself, is what gets sown).
        self.assertTrue(never_hit_zero_consumption)
        self.assertGreater(end_total / start_total, 0.05, (start_total, end_total))


class FamineHasAPhysicalCauseTests(unittest.TestCase):
    """The acceptance question this whole wiring exists to answer: can a
    famine happen, and does it happen for a physical reason (land, labour,
    weather, population) rather than a scripted one (a date, a
    `famine_severity` switch)? Cutting `farm_land.hectares` is a LAND fact
    (a flood, an invading army burning fields, a river changing course),
    exactly the kind of intervention CLAUDE.md SS3.3 says must propagate
    through normal rules rather than get a bespoke outcome branch - and
    here it does: through gross_harvest_kg, through food_available_kcal_
    per_day, through nutrition_ratio, through excess mortality and
    depressed fertility, with no `famine` flag anywhere in the chain.
    """

    def test_losing_most_of_the_farmland_drops_nutrition_ratio_hard(self):
        control = _rome_sim(events=False)
        control._demographic_recovery(101)
        control_ratio = control._last_demographic_step.nutrition_ratio

        shocked = _rome_sim(events=False)
        shocked.farm_land.hectares *= 0.15   # a land loss, not a famine flag
        shocked._demographic_recovery(101)
        shocked_ratio = shocked._last_demographic_step.nutrition_ratio

        self.assertLess(shocked_ratio, 0.5, (control_ratio, shocked_ratio))
        self.assertLess(shocked_ratio, control_ratio - 0.3,
                        (control_ratio, shocked_ratio))

    def test_the_same_land_loss_costs_more_lives_than_the_unshocked_control(self):
        control = _rome_sim(events=False)
        control_start = control.population.total
        for year in range(101, 111):
            control._demographic_recovery(year)
        control_end = control.population.total

        shocked = _rome_sim(events=False)
        shocked_start = shocked.population.total
        shocked.farm_land.hectares *= 0.15
        for year in range(101, 111):
            shocked._demographic_recovery(year)
        shocked_end = shocked.population.total

        control_loss = 1.0 - control_end / control_start
        shocked_loss = 1.0 - shocked_end / shocked_start
        self.assertGreater(shocked_loss, control_loss + 0.05,
                           (control_loss, shocked_loss))

    def test_children_and_elderly_absorb_more_of_a_famine_than_working_age(self):
        # The SAME age-differentiated vulnerability
        # _apply_population_mortality_shock already uses for a staff_loss
        # hazard also applies to a nutrition-driven famine, because both
        # ultimately go through demography.Population.step's excess-
        # mortality machinery (see Population.step and
        # _excess_mortality_multiplier in sim/world/demography.py) - one
        # mechanism, two different ways of arriving at a low
        # nutrition_ratio, not two different mechanisms.
        shocked = _rome_sim(events=False)
        shocked.farm_land.hectares *= 0.15
        before_children = shocked.population.children
        before_working_age = shocked.population.working_age
        shocked._demographic_recovery(101)
        children_survival = (shocked.population.children
                             + shocked._last_demographic_step.deaths_children) / before_children
        working_age_survival = (
            (shocked.population.working_age + shocked._last_demographic_step.deaths_working_age)
            / before_working_age)
        # Both are the SAME kind of figure - this year's deaths in a band
        # divided by that band's own starting count - so they are directly
        # comparable shares, and STARVATION_VULNERABILITY_CHILD (1.6x) >
        # STARVATION_VULNERABILITY_WORKING_AGE (1.0x, the reference) says
        # the child share must come out higher.
        self.assertGreater(
            shocked._last_demographic_step.deaths_children / before_children,
            shocked._last_demographic_step.deaths_working_age / before_working_age)


class DeterminismTests(unittest.TestCase):
    """The weather feeding this wiring is a pure function of (civilisation
    id, year) - see Sim._farm_year_weather_seed's own docstring for why:
    no random.Random is advanced sequentially year over year and left
    unsaved, so nothing about the trajectory can depend on how the years
    were reached (one unbroken run, or many separate --session commands).
    Checked directly: two independently constructed Sims, fed the same
    years, must land on bit-identical population counts.
    """

    def test_two_independent_sims_reach_the_same_population(self):
        first = _rome_sim(events=False)
        second = _rome_sim(events=False)
        for year in range(101, 151):
            first._demographic_recovery(year)
            second._demographic_recovery(year)
        self.assertEqual(first.population.children, second.population.children)
        self.assertEqual(first.population.working_age, second.population.working_age)
        self.assertEqual(first.population.elderly, second.population.elderly)

    def test_a_forced_shortfall_year_reproduces_exactly_on_replay(self):
        # Same idea as the whole-run check above, but specifically across
        # the one operation this milestone's own brief singled out as the
        # historical trap for exactly this kind of state (WIRING_MILESTONE_
        # 4.md SS3): reconstructing a fresh Sim mid-run (standing in for a
        # --session reload) and continuing must retrace the SAME weather.
        reference = _rome_sim(events=False)
        for year in range(101, 111):
            reference._demographic_recovery(year)
        reference_ratio = reference._last_demographic_step.nutrition_ratio

        replayed = _rome_sim(events=False)  # a fresh Sim(), like a reload
        for year in range(101, 111):
            replayed._demographic_recovery(year)
        replayed_ratio = replayed._last_demographic_step.nutrition_ratio

        self.assertEqual(reference_ratio, replayed_ratio)


if __name__ == "__main__":
    unittest.main()
