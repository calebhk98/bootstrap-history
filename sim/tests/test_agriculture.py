"""Regression tests for sim/world/agriculture.py.

Written as unittest.TestCase classes, like sim/tests/test_tierless_schema.py,
rather than the flat check()-at-import style most topics use: this module
has no dependency on sim/engine/ (see agriculture.py's own docstring for
why), and importing sim/tests/harness.py would pull in the whole engine for
no reason. sim/tests/__main__.py's _run_topic already runs both styles
identically - see its own docstring.

The task this module answers to is explicit that the model's PLAUSIBILITY
is not the point, its PROPERTIES are: conservation, diminishing returns,
determinism, and a bad year actually costing food rather than being a
modifier bolted on after the fact. That is what each class below checks.
The one exception is HeadlineCalibrationTests, which computes the fraction
of a population that must farm and compares it to the historical 80-90%
range WITHOUT retuning anything to close the gap if it does not land there -
see that class and agriculture.py's own "ON THE HEADLINE NUMBER" docstring
section for the reading of why it does not.
"""
import inspect
import random
import unittest

from sim.world import agriculture


def _reference_land(hectares=10.0):
    return agriculture.Land(hectares=hectares, quality=1.0)


class ConservationTests(unittest.TestCase):
    """seed sown + harvest - consumption - spoilage - seed retained must
    balance exactly against the change in stock, every year - see
    Storage.step's own docstring for the precise identity and why it holds
    by construction rather than by coincidence.
    """

    def test_single_year_balances_exactly(self):
        land = _reference_land(hectares=8.0)
        storage = agriculture.Storage(stock_kg=5000.0, seed=1)
        flows = storage.step(land, labour_hours=8.0 * 150.0, population=20.0)

        implied_stock_after = (
            flows.stock_before_kg + flows.gross_harvest_kg - flows.seed_sown_kg
            - flows.consumption_kg - flows.spoilage_kg - flows.seed_retained_kg)
        self.assertAlmostEqual(implied_stock_after, flows.stock_after_kg, places=6)
        self.assertAlmostEqual(storage.stock_kg, flows.stock_after_kg, places=6)

    def test_balances_exactly_across_many_years_and_many_seeds(self):
        # Different seeds draw different weather, different population
        # sizes push consumption and shortfall around, and the balance
        # should hold regardless - this is a property of the bookkeeping,
        # not of any one lucky combination of inputs.
        for seed in range(12):
            land = _reference_land(hectares=6.0)
            storage = agriculture.Storage(stock_kg=2000.0, seed=seed)
            population = 10.0 + seed
            for _year in range(15):
                flows = storage.step(land, labour_hours=6.0 * 150.0,
                                     population=population)
                implied_stock_after = (
                    flows.stock_before_kg + flows.gross_harvest_kg
                    - flows.seed_sown_kg - flows.consumption_kg
                    - flows.spoilage_kg - flows.seed_retained_kg)
                self.assertAlmostEqual(
                    implied_stock_after, flows.stock_after_kg, places=6,
                    msg="conservation broke at seed=%d" % seed)

    def test_balances_even_when_the_seed_corn_itself_gets_eaten(self):
        # A starved household still sows what it can and still owes next
        # year's seed - the balance has to hold even when stock goes
        # negative, which is exactly how this model represents one bad
        # harvest turning into two rather than needing a separate crisis
        # code path (CLAUDE.md SS3.1/SS3.3: no bespoke outcome branches).
        land = _reference_land(hectares=20.0)
        storage = agriculture.Storage(stock_kg=10.0, seed=7)
        flows = storage.step(land, labour_hours=1.0, population=500.0)
        self.assertLess(flows.stock_after_kg, 0.0)
        implied_stock_after = (
            flows.stock_before_kg + flows.gross_harvest_kg - flows.seed_sown_kg
            - flows.consumption_kg - flows.spoilage_kg - flows.seed_retained_kg)
        self.assertAlmostEqual(implied_stock_after, flows.stock_after_kg, places=6)
        self.assertGreater(flows.food_shortfall_kg, 0.0)


class DiminishingReturnsTests(unittest.TestCase):
    """The single most important property this module has: doubling labour
    on FIXED land must not double output, and the marginal product of the
    next hour of labour must fall as more hours are already applied. A
    linear model gets every downstream answer (population ceiling, who is
    free to leave farming) wrong - see agriculture.py's own docstring on
    gross_harvest_kg.
    """

    def test_doubling_labour_does_not_double_output(self):
        land = _reference_land(hectares=5.0)
        harvest_at_100 = agriculture.gross_harvest_kg(land, labour_hours=100.0)
        harvest_at_200 = agriculture.gross_harvest_kg(land, labour_hours=200.0)
        self.assertGreater(harvest_at_200, harvest_at_100)
        self.assertLess(harvest_at_200, 2.0 * harvest_at_100)
        # Exact, given the Cobb-Douglas exponent: output should scale by
        # exactly 2**LABOUR_OUTPUT_ELASTICITY, not merely "less than double".
        self.assertAlmostEqual(
            harvest_at_200 / harvest_at_100,
            2.0 ** agriculture.LABOUR_OUTPUT_ELASTICITY, places=6)

    def test_marginal_product_of_labour_falls_monotonically(self):
        land = _reference_land(hectares=5.0)
        hours_series = [10.0, 50.0, 150.0, 500.0, 2000.0, 10000.0]
        marginal_products = [
            agriculture.marginal_product_of_labour_kg_per_hour(land, hours)
            for hours in hours_series]
        for earlier, later in zip(marginal_products, marginal_products[1:]):
            self.assertGreater(
                earlier, later,
                "marginal product must fall as more labour is already "
                "applied to the same fixed land: %r" % (marginal_products,))

    def test_more_land_at_the_same_labour_raises_output(self):
        # Not the headline property, but a basic sanity check that land is
        # actually doing something: the same labour on more hectares should
        # produce more, all else equal.
        small_land = _reference_land(hectares=2.0)
        big_land = _reference_land(hectares=8.0)
        harvest_small = agriculture.gross_harvest_kg(small_land, labour_hours=300.0)
        harvest_big = agriculture.gross_harvest_kg(big_land, labour_hours=300.0)
        self.assertGreater(harvest_big, harvest_small)

    def test_better_land_quality_raises_output_at_the_same_labour_and_area(self):
        poor_land = agriculture.Land(hectares=5.0, quality=0.6)
        good_land = agriculture.Land(hectares=5.0, quality=1.2)
        harvest_poor = agriculture.gross_harvest_kg(poor_land, labour_hours=750.0)
        harvest_good = agriculture.gross_harvest_kg(good_land, labour_hours=750.0)
        self.assertGreater(harvest_good, harvest_poor)
        self.assertAlmostEqual(harvest_good / harvest_poor, 1.2 / 0.6, places=6)


class WeatherTests(unittest.TestCase):
    """A bad weather year has to cut output and show up as less food per
    person through the ordinary accounting - not as a modifier slapped on
    top of an otherwise-unaffected result.
    """

    def test_a_low_weather_draw_cuts_gross_harvest(self):
        land = _reference_land(hectares=5.0)
        normal = agriculture.gross_harvest_kg(land, labour_hours=750.0,
                                              weather_multiplier=1.0)
        bad_year = agriculture.gross_harvest_kg(land, labour_hours=750.0,
                                                weather_multiplier=0.5)
        self.assertLess(bad_year, normal)
        self.assertAlmostEqual(bad_year / normal, 0.5, places=6)

    def test_bad_year_reduces_consumption_and_food_per_person_through_storage(self):
        # Same land, same labour, same population, same starting stock -
        # the only difference is which weather multiplier gets drawn. The
        # test forces the draw directly (rather than hunting for a seed
        # that happens to produce a bad year) by monkeypatching the
        # module-level draw function Storage.step calls.
        land = _reference_land(hectares=6.0)
        population = 15.0

        original_draw = agriculture.draw_weather_multiplier
        try:
            agriculture.draw_weather_multiplier = lambda rng: 1.0
            good_storage = agriculture.Storage(stock_kg=1000.0, seed=3)
            good_flows = good_storage.step(land, labour_hours=6.0 * 150.0,
                                           population=population)

            agriculture.draw_weather_multiplier = lambda rng: 0.4
            bad_storage = agriculture.Storage(stock_kg=1000.0, seed=3)
            bad_flows = bad_storage.step(land, labour_hours=6.0 * 150.0,
                                         population=population)
        finally:
            agriculture.draw_weather_multiplier = original_draw

        self.assertLess(bad_flows.gross_harvest_kg, good_flows.gross_harvest_kg)
        self.assertLess(bad_flows.food_available_kcal_per_day,
                        good_flows.food_available_kcal_per_day)
        # The shortfall shows up on the population's plate, not as some
        # side channel: either less was eaten, or a shortfall was recorded
        # (or both cannot happen simultaneously with full consumption).
        self.assertGreaterEqual(bad_flows.food_shortfall_kg,
                                good_flows.food_shortfall_kg)

    def test_weather_multiplier_is_clipped_to_its_declared_bounds(self):
        rng = random.Random(0)
        draws = [agriculture.draw_weather_multiplier(rng) for _ in range(2000)]
        self.assertGreaterEqual(min(draws), agriculture.WEATHER_FLOOR_MULTIPLIER)
        self.assertLessEqual(max(draws), agriculture.WEATHER_CEILING_MULTIPLIER)
        # And the upper clip actually gets exercised at
        # WEATHER_YIELD_STDEV_FRACTION's declared width (1.3 sits only 1.5
        # standard deviations above the mean, so 2000 draws hits it
        # comfortably) - if this ever stops being true the stdev or the
        # bound drifted out of step. The floor sits much further out
        # (4.25 standard deviations) and is not expected to be hit by a
        # sample this size; its own correctness is covered by the min()
        # bound above, not by requiring it be exercised here.
        self.assertTrue(any(d >= agriculture.WEATHER_CEILING_MULTIPLIER - 1e-9
                            for d in draws))


class DeterminismTests(unittest.TestCase):
    """Same seed, same answer, repeatedly, in one process - the property
    CLAUDE.md SS6 calls out by name after the id()-reuse incident. This
    module carries no id()-keyed cache of its own, but the discipline of
    proving determinism directly, rather than assuming a plain
    random.Random seed is enough, is cheap and worth keeping.
    """

    def _run_five_years(self, seed):
        land = _reference_land(hectares=7.0)
        storage = agriculture.Storage(stock_kg=3000.0, seed=seed)
        results = []
        for _year in range(5):
            results.append(storage.step(land, labour_hours=7.0 * 150.0,
                                        population=18.0))
        return results, storage.stock_kg

    def test_same_seed_reproduces_the_same_five_years_exactly(self):
        first_flows, first_final_stock = self._run_five_years(seed=12345)
        second_flows, second_final_stock = self._run_five_years(seed=12345)
        self.assertEqual(first_flows, second_flows)
        self.assertEqual(first_final_stock, second_final_stock)

    def test_different_seeds_do_not_reproduce_the_same_weather(self):
        # Not strictly required by "determinism", but guards against a
        # trivial way this could be faked: a draw function that ignores its
        # rng argument would pass the identical-seed test above too.
        flows_a, _ = self._run_five_years(seed=1)
        flows_b, _ = self._run_five_years(seed=2)
        self.assertNotEqual([f.weather_multiplier for f in flows_a],
                            [f.weather_multiplier for f in flows_b])

    def test_repeated_calls_in_one_process_do_not_drift(self):
        # Runs the same scenario many times in a row in this one process,
        # the way Complaints/27 describes the original id()-reuse hazard
        # only showing up after enough allocations happened - a determinism
        # bug that depends on process history will not show up on the
        # first call.
        baseline_flows, baseline_stock = self._run_five_years(seed=999)
        for _repeat in range(20):
            flows, stock = self._run_five_years(seed=999)
            self.assertEqual(flows, baseline_flows)
            self.assertEqual(stock, baseline_stock)


class HeadlineCalibrationTests(unittest.TestCase):
    """The calibration target from CLAUDE.md SS3.2: with this module's own
    parameters, what fraction of a population must farm to feed itself?
    Should land somewhere near 80-90%. This suite does NOT retune anything
    to force that - see agriculture.py's "ON THE HEADLINE NUMBER" docstring
    section for the reading of why it currently does not, and the module's
    caller-facing report for the same reading in full.

    The second test below pins the CURRENT computed value as a plain
    regression check: if a future change to a declared constant moves this
    number, the diff should be visible and explained, not silently
    absorbed. It is deliberately NOT an assertion that the number is
    correct - only that it is the number this module currently, honestly,
    computes.
    """

    def test_is_a_well_defined_probability(self):
        fraction = agriculture.fraction_of_population_that_must_farm()
        self.assertGreater(fraction, 0.0)
        self.assertLess(fraction, 1.0)

    def test_current_computed_value_and_its_relation_to_the_historical_target(self):
        fraction = agriculture.fraction_of_population_that_must_farm()
        # Pinned regression value - see this module's own module docstring
        # for the derivation (seed rate x fold return, minus seed, minus
        # spoilage, divided across the hectares one worker can cover in a
        # year, against one person's annual caloric need).
        self.assertAlmostEqual(fraction, 0.21181, places=4)
        self.assertLess(
            fraction, agriculture.HISTORICAL_FARM_POPULATION_SHARE_LOW,
            "the computed farm-population share now falls inside or above "
            "the historical range - if a real change caused this, update "
            "this pin and agriculture.py's headline-number docstring "
            "together; do not just delete the assertion.")

    def test_one_farm_worker_feeds_more_people_than_history_implies_is_possible(self):
        # Restated the other way round, because "one worker feeds N people"
        # is the more legible form of the same discrepancy. Beware the
        # arithmetic here, which an earlier version of this comment got
        # wrong: a society with 85% of its POPULATION on farms means each
        # farm resident feeds 1/0.85 ~= 1.2 people, not 1/(1 - 0.85) ~= 6.7.
        # But farm residents are not full-time-equivalent field workers,
        # which is what this module counts, and that conversion is exactly
        # the unit mismatch recorded as reason (a) in agriculture.py's
        # headline docstring - so the honest comparison is a range, not a
        # number, and it is wide.
        #
        # This module computes about 4.7 people fed per FTE farm worker.
        # The assertion below is loose on purpose: it records that the
        # figure is still on the wrong side of anything history allows,
        # without pretending to a precision the FTE conversion does not
        # have. The pinned value in the test above is what catches a drift.
        people_fed = 1.0 / agriculture.fraction_of_population_that_must_farm()
        self.assertGreater(people_fed, 3.0)

    def test_the_harvest_window_is_what_binds_not_the_farming_year(self):
        # The substantive finding of the seasonality work, asserted rather
        # than only written down: at the declared constants the annual-hours
        # ceiling is slack by a wide margin, so changing it does not move
        # the headline number at all. If a future edit makes annual hours
        # bind again, this fails and whoever made it has to say why.
        self.assertLess(
            agriculture.hectares_per_worker_harvest_window_ceiling(),
            agriculture.hectares_per_worker_annual_hours_ceiling(),
            "the harvest window no longer binds - the headline number is "
            "now sensitive to REFERENCE_LABOUR_HOURS_PER_HECTARE and "
            "ANNUAL_LABOUR_HOURS_PER_FARM_WORKER again, which changes what "
            "agriculture.py's docstring claims about them.")
        self.assertAlmostEqual(
            agriculture.hectares_cropped_per_farm_worker(),
            agriculture.hectares_per_worker_harvest_window_ceiling(),
            places=9)

    def test_fallow_changes_the_land_requirement_and_not_the_output(self):
        # Guards the other half of the finding: fallow is a land fact here,
        # not a labour one, so it must show up in the holding and NOWHERE
        # in the food figure. If someone later multiplies the headline
        # number by the fallow share as well, this catches the
        # double-count.
        holding = agriculture.holding_hectares_required_per_farm_worker()
        cropped = agriculture.hectares_cropped_per_farm_worker()
        self.assertAlmostEqual(
            holding,
            cropped / (1.0 - agriculture.FALLOW_SHARE_OF_HOLDING),
            places=9)
        self.assertGreater(holding, cropped)

        source = inspect.getsource(agriculture.fraction_of_population_that_must_farm)
        self.assertNotIn(
            "FALLOW", source,
            "fraction_of_population_that_must_farm() must not read the "
            "fallow share: land is not the binding constraint in this "
            "module, so applying it there double-counts. See the ROTATION "
            "AND FALLOW section in agriculture.py.")


class DataConsistencyTests(unittest.TestCase):
    """This module is required to be consistent with
    data/production/40_organics.json's wheat_kg entry rather than inventing
    a second set of numbers - these checks fail loudly if a future edit
    quietly drifts the two apart, and record the one place they are already
    known to disagree (see agriculture.py's own DISAGREEMENT docstring
    section) as an explicit, tested statement rather than a silent gap.
    """

    def test_seed_rate_and_labour_hours_match_the_production_file(self):
        import json
        import os
        production_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))),
            "data", "production", "40_organics.json")
        with open(production_path) as handle:
            wheat = json.load(handle)["materials"]["wheat_kg"]

        self.assertEqual(wheat["labour_hours"]["labourer"],
                         agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE)
        # Seed rate is a midpoint this module read out of that entry's prose
        # ("around 150-180 kg/ha"), not a machine-readable field, so this
        # checks it falls inside the stated range rather than matching a
        # field exactly.
        self.assertGreaterEqual(agriculture.SEED_SOWING_RATE_KG_PER_HA, 150.0)
        self.assertLessEqual(agriculture.SEED_SOWING_RATE_KG_PER_HA, 180.0)

    def test_gross_reference_yield_falls_inside_the_files_own_derived_range(self):
        # The production file derives "roughly 700-900 kg/ha" gross from
        # the same fold-return arithmetic this module uses (see both
        # modules' docstrings) - this module's GROSS figure must land
        # inside that range even though it disagrees with the file's own
        # NET-of-seed label on 800 kg/ha.
        self.assertGreaterEqual(
            agriculture.GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA, 700.0)
        self.assertLessEqual(
            agriculture.GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA, 900.0)

    def test_the_file_and_this_module_agree_on_the_net_yield(self):
        # These two used to disagree: the file said 800 kg/ha net while
        # deriving it by fold-return times seed rate, which is gross. The
        # file was corrected (see agriculture.py's ARITHMETIC CORRECTION
        # docstring section); this reads the file rather than restating its
        # number, so the two cannot drift apart again without failing here.
        import json
        import os
        production_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))),
            "data", "production", "40_organics.json")
        with open(production_path) as handle:
            wheat = json.load(handle)["materials"]["wheat_kg"]

        this_module_net_kg_per_ha = (
            agriculture.GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA
            - agriculture.SEED_SOWING_RATE_KG_PER_HA)
        self.assertAlmostEqual(
            wheat["outputs"]["wheat_kg"], this_module_net_kg_per_ha, places=6)

    def test_the_file_states_its_yield_net_of_seed_not_gross(self):
        # The distinction the correction turned on, pinned so a future edit
        # cannot quietly put the gross figure back under the same label: the
        # file's stated output must be BELOW the gross harvest by exactly the
        # seed rate, not equal to it.
        import json
        import os
        production_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))),
            "data", "production", "40_organics.json")
        with open(production_path) as handle:
            wheat = json.load(handle)["materials"]["wheat_kg"]

        stated = wheat["outputs"]["wheat_kg"]
        self.assertLess(
            stated, agriculture.GROSS_YIELD_AT_REFERENCE_LABOUR_KG_PER_HA,
            "40_organics.json's wheat yield is no longer below the gross "
            "harvest - if someone restated it as gross, wheat_kg must also "
            "gain wheat_kg among its inputs, and Complaints/31 says why that "
            "does not work yet.")
        self.assertEqual(wheat["inputs"], {})


if __name__ == "__main__":
    unittest.main()
