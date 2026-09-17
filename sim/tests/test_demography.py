"""Regression tests for sim/world/demography.py.

Written as unittest.TestCase classes, like sim/tests/test_tierless_schema.py
and sim/tests/test_agriculture.py, rather than the flat check()-at-import
style most topics use: this module has no dependency on sim/engine/ (see
demography.py's own docstring for why), and importing sim/tests/harness.py
would pull in the whole engine for no reason. sim/tests/__main__.py's
_run_topic already runs both styles identically - see its own docstring.

The task this module answers to says the tests matter more than the model,
because a demographic model that LOOKS plausible and is WRONG is the easiest
thing in the world to write. So every class below checks a property, not a
number: exact accounting, boundedness at subsistence, a directional response
to less food, and - the one the old scalar `pop_deficit` mechanism in
sim/engine/core.py could never have passed - that recovery from a mortality
shock depends on WHICH cohorts survived it, not merely on how many people
did.
"""
import math
import unittest

from sim.world import demography


def _stationary(total=1_000_000.0, seed=1):
    return demography.Population.stationary(total, seed=seed)


class AccountingClosureTests(unittest.TestCase):
    """start + births + immigration - deaths - emigration == end, exactly,
    every single step - this is pure bookkeeping (see Population.step's own
    docstring for why the aging terms cancel out of the total algebraically)
    and should hold no matter how extreme the food input is, since it is
    stock-flow bookkeeping, not a claim about how PLAUSIBLE the flows are.
    """

    def test_closes_at_subsistence(self):
        population = _stationary()
        for _year in range(50):
            flows = population.step(population._subsistence_food())
            self._assert_closes(flows)

    def test_closes_under_famine(self):
        population = _stationary()
        food = population._subsistence_food()
        for _year in range(50):
            flows = population.step(food * 0.4)
            self._assert_closes(flows)

    def test_closes_under_surplus(self):
        population = _stationary()
        food = population._subsistence_food()
        for _year in range(50):
            flows = population.step(food * 2.0)
            self._assert_closes(flows)

    def test_closes_with_migration(self):
        population = _stationary()
        food = population._subsistence_food()
        for year in range(50):
            flows = population.step(food, immigration=500.0 + year,
                                     emigration=200.0)
            self._assert_closes(flows)

    def test_closes_with_jitter_and_extinction_edge_cases(self):
        # jitter=True and a population driven toward zero are the two
        # conditions most likely to break an identity that only "usually"
        # holds - a clamp on a per-band mortality rate (see step()'s use of
        # min(1.0, ...)) is exactly the kind of thing that can silently
        # break conservation if it is applied to the rate but the flows
        # are not recomputed consistently with it.
        population = demography.Population(100.0, 100.0, 100.0, seed=7)
        for _year in range(80):
            flows = population.step(0.0, jitter=True)
            self._assert_closes(flows)
        self.assertGreaterEqual(population.children, 0.0)
        self.assertGreaterEqual(population.working_age, 0.0)
        self.assertGreaterEqual(population.elderly, 0.0)

    def _assert_closes(self, flows):
        implied_end = (flows.start_total + flows.births + flows.immigration
                       - flows.deaths - flows.emigration)
        self.assertAlmostEqual(implied_end, flows.end_total, places=6,
                                msg=str(flows))
        self.assertAlmostEqual(
            flows.deaths,
            flows.deaths_children + flows.deaths_working_age
            + flows.deaths_elderly, places=6)


class StationarityTests(unittest.TestCase):
    """At subsistence, forever, a population should neither explode nor die
    out - CLAUDE.md SS3.2's own validation target, and the property that
    replaces "does this match 100 AD" with "is this the right SHAPE of
    history". The bar is deliberately loose (population inside a 2x band
    either way over three centuries) because pre-industrial demography
    really was punctuated by crises even without this module's own harvest
    noise (which defaults off - see NUTRITION_YEAR_TO_YEAR_NOISE_STD) - the
    test is for "does not run away or collapse", not "is exactly flat".
    """

    def test_roughly_stationary_over_three_centuries(self):
        population = _stationary()
        start = population.total
        low = high = start
        for _year in range(300):
            population.step(population._subsistence_food())
            low = min(low, population.total)
            high = max(high, population.total)
        self.assertGreater(population.total, start * 0.5, "population collapsed")
        self.assertLess(population.total, start * 2.0, "population exploded")
        self.assertGreater(low, start * 0.5)
        self.assertLess(high, start * 2.0)

    def test_crude_rates_and_life_expectancy_land_in_the_documented_ranges(self):
        # CLAUDE.md SS3.2's own anchors: crude birth/death rates in the
        # 30-40 per thousand range, life expectancy at birth in the 20s to
        # low 30s. These numbers are an OUTPUT of the three baseline vital
        # rates declared in demography.py, not inputs chosen to hit this
        # range directly - see the comment above SURVIVAL_TO_WORKING_AGE's
        # declaration for how the two were reconciled.
        population = _stationary()
        start = population.total
        total_births = total_deaths = 0.0
        years = 300
        for _year in range(years):
            flows = population.step(population._subsistence_food())
            total_births += flows.births
            total_deaths += flows.deaths
        average_population = (start + population.total) / 2.0
        crude_birth_rate = total_births / years / average_population * 1000.0
        crude_death_rate = total_deaths / years / average_population * 1000.0
        self.assertTrue(25.0 <= crude_birth_rate <= 45.0,
                         "CBR %.1f/1000 outside the documented range" % crude_birth_rate)
        self.assertTrue(25.0 <= crude_death_rate <= 45.0,
                         "CDR %.1f/1000 outside the documented range" % crude_death_rate)

        life_expectancy = self._life_expectancy_at_birth()
        self.assertTrue(18.0 <= life_expectancy <= 35.0,
                         "e0 %.1f outside the documented range" % life_expectancy)

    def _life_expectancy_at_birth(self):
        """Integrates the three piecewise-constant baseline hazards
        directly - a closed-form check on the DECLARED constants, entirely
        independent of Population/step(), so this test cannot be fooled by
        a bug in step() that happens to leave crude rates looking right."""
        child_hazard = demography.BASELINE_ANNUAL_MORTALITY_RATE_CHILD
        working_hazard = demography.BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
        elderly_hazard = demography.BASELINE_ANNUAL_MORTALITY_RATE_ELDERLY
        lower_bound = demography.WORKING_AGE_LOWER_BOUND_YEARS
        upper_bound = demography.WORKING_AGE_UPPER_BOUND_YEARS
        working_width = demography.WORKING_AGE_BAND_WIDTH_YEARS

        def survival(age):
            if age <= lower_bound:
                return math.exp(-child_hazard * age)
            survival_to_working_age = math.exp(-child_hazard * lower_bound)
            if age <= upper_bound:
                return survival_to_working_age * math.exp(
                    -working_hazard * (age - lower_bound))
            survival_to_elderly = survival_to_working_age * math.exp(
                -working_hazard * working_width)
            return survival_to_elderly * math.exp(
                -elderly_hazard * (age - upper_bound))

        age_step = 0.05
        age = 0.0
        expectancy = 0.0
        while age < 150.0:
            expectancy += survival(age) * age_step
            age += age_step
        return expectancy


class NutritionResponseTests(unittest.TestCase):
    """The central design rule: food moves mortality and fertility THROUGH
    the model, with no distinct 'famine' code path. These tests exercise
    the response functions directly (not through step()) so a failure here
    points straight at _excess_mortality_multiplier or _fertility_multiplier
    rather than at some interaction in the cohort bookkeeping.
    """

    def test_fertility_falls_monotonically_below_subsistence(self):
        ratios = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        values = [demography._fertility_multiplier(ratio) for ratio in ratios]
        self.assertEqual(values, sorted(values))
        self.assertEqual(values[0], 0.0)
        self.assertEqual(values[-1], 1.0)

    def test_fertility_does_not_rise_above_baseline_on_surplus(self):
        self.assertEqual(demography._fertility_multiplier(1.0), 1.0)
        self.assertEqual(demography._fertility_multiplier(1.5), 1.0)
        self.assertEqual(demography._fertility_multiplier(3.0), 1.0)

    def test_mortality_multiplier_is_one_at_and_above_subsistence(self):
        for vulnerability in (1.0, demography.STARVATION_VULNERABILITY_CHILD,
                              demography.STARVATION_VULNERABILITY_ELDERLY):
            self.assertEqual(
                demography._excess_mortality_multiplier(1.0, vulnerability), 1.0)
            self.assertEqual(
                demography._excess_mortality_multiplier(2.0, vulnerability), 1.0)

    def test_mortality_multiplier_rises_monotonically_as_food_falls(self):
        ratios_from_full_to_none = [1.0, 0.8, 0.6, 0.4, 0.2, 0.0]
        values = [demography._excess_mortality_multiplier(ratio, 1.0)
                  for ratio in ratios_from_full_to_none]
        self.assertEqual(values, sorted(values))

    def test_mortality_multiplier_never_exceeds_the_declared_ceiling(self):
        for ratio in (0.5, 0.3, 0.1, 0.0, -1.0):
            multiplier = demography._excess_mortality_multiplier(
                ratio, demography.STARVATION_VULNERABILITY_CHILD)
            self.assertLessEqual(
                multiplier,
                1.0 + (demography.STARVATION_MORTALITY_CEILING_MULTIPLIER - 1.0)
                * demography.STARVATION_VULNERABILITY_CHILD + 1e-9)

    def test_children_and_elderly_are_more_vulnerable_than_working_age(self):
        # The direction (children and the elderly die faster than
        # working-age adults from the SAME shortfall) is the documented,
        # not-invented part of STARVATION_VULNERABILITY_CHILD/_ELDERLY -
        # see those constants' own declarations.
        ratio = 0.5
        working_age_excess = (
            demography._excess_mortality_multiplier(ratio, 1.0) - 1.0)
        child_excess = demography._excess_mortality_multiplier(
            ratio, demography.STARVATION_VULNERABILITY_CHILD) - 1.0
        elderly_excess = demography._excess_mortality_multiplier(
            ratio, demography.STARVATION_VULNERABILITY_ELDERLY) - 1.0
        self.assertGreater(child_excess, working_age_excess)
        self.assertGreater(elderly_excess, working_age_excess)


class FoodShockAndRecoveryTests(unittest.TestCase):
    """Halve the food, watch mortality rise and fertility fall and the
    population fall; restore the food, watch the population recover over a
    generational timescale. No term anywhere in demography.py references a
    remembered trend or a fixed recovery horizon (the whole thing
    sim/engine/core.py's _demographic_recovery uses) - what recovery there
    is has to come from births and deaths computed off the actual surviving
    cohorts, which is exactly what these tests are set up to distinguish
    from a decay constant.
    """

    def test_halving_food_raises_mortality_lowers_fertility_and_population_falls(self):
        population = _stationary()
        base_food = population._subsistence_food()
        full_food_flows = population.copy().step(base_food)

        shocked = demography.Population(
            population.children, population.working_age, population.elderly,
            seed=3)
        shocked_flows = shocked.step(base_food * 0.5)

        self.assertGreater(shocked_flows.deaths, full_food_flows.deaths)
        self.assertLess(shocked_flows.births, full_food_flows.births)
        self.assertLess(shocked_flows.end_total, population.total)

        # Sustained, not just a one-year wobble: several years at half food
        # should leave the population meaningfully smaller than where it
        # started, not merely down by one year's noise.
        trajectory = [shocked.total]
        for _year in range(10):
            shocked.step(base_food * 0.5)
            trajectory.append(shocked.total)
        self.assertLess(trajectory[-1], trajectory[0] * 0.8)
        # And monotonically worse while the shortfall continues - this is a
        # population in genuine, mechanism-driven decline, not oscillating
        # noise around a level.
        self.assertEqual(trajectory, sorted(trajectory, reverse=True))

    def test_population_recovers_once_food_is_restored(self):
        # A FIXED absolute food supply (this population's own pre-shock
        # subsistence requirement, held constant rather than recomputed off
        # whatever the population happens to be each year) stands in for
        # "the land did not go anywhere, only some of the people who worked
        # it did" - the ordinary Malthusian mechanism (fewer mouths, the
        # same harvest) by which real post-famine and post-plague
        # populations actually recovered, without this test hand-writing a
        # recovery rate anywhere.
        population = _stationary()
        base_food = population._subsistence_food()

        shocked = demography.Population(
            population.children, population.working_age, population.elderly,
            seed=4)
        for _year in range(10):
            shocked.step(base_food * 0.5)
        trough = shocked.total
        self.assertLess(trough, population.total * 0.7)

        recovery_trajectory = [trough]
        for _year in range(100):
            shocked.step(base_food)
            recovery_trajectory.append(shocked.total)

        # It grows back from the trough - genuine recovery, not merely "the
        # decline stops".
        self.assertGreater(max(recovery_trajectory), trough * 1.05)
        # It takes a while to get there: recovery on a GENERATIONAL
        # timescale means the ten-year mark should still be well short of
        # wherever this trajectory eventually peaks, not there already.
        self.assertLess(recovery_trajectory[10],
                         max(recovery_trajectory) * 0.98)

    def test_recovery_is_not_a_decay_constant_it_depends_on_who_survived(self):
        """The decisive test. sim/engine/core.py's `_demographic_recovery`
        would treat any two population losses of the SAME SIZE identically
        - `pop_deficit` is a fraction of baseline, with no notion of which
        people that fraction refers to, and decays back down on a clock set
        by how big the loss was. This model cannot behave that way even in
        principle, because it has no `pop_deficit` and no clock: births and
        deaths are computed from the actual children/working_age/elderly
        counts every single step. This test proves that difference rather
        than asserting it: two populations lose the SAME 30% of their total
        in the SAME single year, but the loss falls on different cohorts in
        each - one spares working-age adults (a famine/plague age pattern,
        the direction STARVATION_VULNERABILITY_CHILD/_ELDERLY already
        documents), the other falls on working-age adults specifically and
        spares children and the elderly. A model driven by aggregate
        deficit alone could not tell these two 30%-losses apart; this one
        produces two visibly different futures from them.
        """
        base_population = _stationary()
        total_loss_fraction = 0.30

        spares_working_age = demography.Population(
            base_population.children, base_population.working_age,
            base_population.elderly, seed=101)
        child_and_elderly_share = ((spares_working_age.children
                                    + spares_working_age.elderly)
                                   / spares_working_age.total)
        cut = total_loss_fraction / child_and_elderly_share
        spares_working_age.children *= (1.0 - cut)
        spares_working_age.elderly *= (1.0 - cut)

        hits_working_age = demography.Population(
            base_population.children, base_population.working_age,
            base_population.elderly, seed=102)
        working_age_share = (
            hits_working_age.working_age / hits_working_age.total)
        cut = total_loss_fraction / working_age_share
        hits_working_age.working_age *= (1.0 - cut)

        # Both scenarios start from IDENTICAL total population loss.
        self.assertAlmostEqual(spares_working_age.total, hits_working_age.total,
                                delta=1.0)
        self.assertAlmostEqual(
            spares_working_age.total,
            base_population.total * (1.0 - total_loss_fraction), delta=1.0)

        spares_trajectory = [spares_working_age.total]
        hits_trajectory = [hits_working_age.total]
        for _year in range(100):
            spares_working_age.step(spares_working_age._subsistence_food())
            hits_working_age.step(hits_working_age._subsistence_food())
            spares_trajectory.append(spares_working_age.total)
            hits_trajectory.append(hits_working_age.total)

        # The one that kept its reproductive-age adults grows back;
        # the one whose reproductive-age adults were destroyed does not -
        # despite an IDENTICAL immediate loss in the founding year.
        self.assertGreater(spares_trajectory[-1], spares_trajectory[0],
                            "population with surviving working-age adults "
                            "should recover, not merely fail to shrink")
        self.assertLessEqual(hits_trajectory[-1], hits_trajectory[0] * 1.02,
                              "population whose working-age adults were "
                              "destroyed should not meaningfully recover")
        self.assertGreater(spares_trajectory[-1], hits_trajectory[-1] * 1.2,
                            "the two 30%-loss scenarios should diverge "
                            "sharply, which a scalar-deficit model could "
                            "never produce from an equal-sized loss")
        # And the recovery that does happen is gradual - generations, not a
        # jump. It is not instantaneous (finding half of the eventual gain
        # takes more than a single year) and getting NEARLY all the way
        # there takes longer than one whole child-to-working-age maturation
        # (WORKING_AGE_LOWER_BOUND_YEARS) - consistent with the gain coming
        # from children born after the shock growing up into the
        # working-age band, not from any single-step correction.
        peak = max(spares_trajectory)
        year_of_half_recovery = next(
            year for year, total in enumerate(spares_trajectory)
            if total >= spares_trajectory[0] + 0.5 * (peak - spares_trajectory[0]))
        year_of_90pct_recovery = next(
            year for year, total in enumerate(spares_trajectory)
            if total >= spares_trajectory[0] + 0.9 * (peak - spares_trajectory[0]))
        self.assertGreater(year_of_half_recovery, 1)
        self.assertGreater(year_of_90pct_recovery,
                            demography.WORKING_AGE_LOWER_BOUND_YEARS)


class WorkingAgePopulationTests(unittest.TestCase):
    """The question this whole module exists to answer: how many people of
    working age are there, and how does that respond to food. If this
    module cannot answer this cheaply and directly, it has not done its
    job regardless of how the rest of it behaves.
    """

    def test_working_age_population_is_directly_readable(self):
        population = demography.Population(300.0, 450.0, 180.0, seed=1)
        self.assertEqual(population.working_age_population, 450.0)
        population.step(population._subsistence_food())
        self.assertEqual(population.working_age_population,
                          population.working_age)

    def test_working_age_share_falls_under_sustained_famine(self):
        # Children die fastest and are born least under famine, so a
        # population sustained at low food for a generation should show a
        # LOWER child share and, since the working-age band is not
        # immediately replenished by the (now scarce) children behind it,
        # eventually a lower absolute working-age count than an
        # otherwise-identical population fed at subsistence throughout -
        # i.e. the labour supply a wage would be computed from is smaller
        # after a famine, and this module can say so directly.
        fed = _stationary()
        fed_twin = demography.Population(
            fed.children, fed.working_age, fed.elderly, seed=5)
        starved_twin = demography.Population(
            fed.children, fed.working_age, fed.elderly, seed=6)
        base_food = fed._subsistence_food()
        for _year in range(40):
            fed_twin.step(base_food)
            starved_twin.step(base_food * 0.6)
        self.assertLess(starved_twin.working_age_population,
                         fed_twin.working_age_population)


class DeterminismTests(unittest.TestCase):
    """Same seed, same answer, run repeatedly in one process - see
    Complaints/27-nondeterministic-simulation.md and sim/tests/
    test_determinism.py for why this project checks this explicitly rather
    than assuming it. Population holds its own random.Random by direct
    reference (never by id()), so this also serves as a demonstration that
    the module cannot reproduce that bug's shape: nothing here is ever
    cached or compared by an object's address.
    """

    def test_same_seed_same_trajectory_with_jitter(self):
        def run_trajectory(seed):
            population = demography.Population(
                500_000.0, 700_000.0, 300_000.0, seed=seed)
            totals = []
            for _year in range(60):
                food = population._subsistence_food() * 0.9
                population.step(food, jitter=True)
                totals.append(population.total)
            return totals

        first_run = run_trajectory(seed=2024)
        for _repeat in range(5):
            self.assertEqual(run_trajectory(seed=2024), first_run)

    def test_different_seeds_can_diverge_under_jitter(self):
        # Not a strict requirement of correctness, but a sanity check that
        # the seed is actually doing something: if every seed produced the
        # same trajectory under jitter=True, the determinism test above
        # would be vacuous.
        def run_final_total(seed):
            population = demography.Population(
                500_000.0, 700_000.0, 300_000.0, seed=seed)
            for _year in range(60):
                population.step(population._subsistence_food(), jitter=True)
            return population.total

        results = {run_final_total(seed) for seed in range(5)}
        self.assertGreater(len(results), 1)

    def test_stationary_construction_is_deterministic(self):
        first = demography.Population.stationary(2_000_000.0, seed=17)
        second = demography.Population.stationary(2_000_000.0, seed=17)
        self.assertEqual(first.children, second.children)
        self.assertEqual(first.working_age, second.working_age)
        self.assertEqual(first.elderly, second.elderly)


if __name__ == "__main__":
    unittest.main()
