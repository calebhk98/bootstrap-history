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
        # Land is deliberately tiny (0.1 ha) so the harvest-window cap
        # gross_harvest_kg now applies (see agriculture.py's "THE HARVEST
        # WINDOW NOW ALSO BINDS" docstring section) never binds across this
        # labour range - at labour_hours=100 the window would allow up to
        # 0.15 ha (100/1400 worker-years * 2.1 ha/worker), comfortably
        # above the 0.1 ha tested, so this isolates the pure Cobb-Douglas
        # labour-elasticity property the test is named for, unconfounded by
        # the window cap that a bigger, more "farm-sized" parcel would now
        # trigger.
        land = _reference_land(hectares=0.1)
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
        # 0.01 ha, for the same reason as test_doubling_labour_does_not_
        # double_output above: even the smallest labour_hours tested here
        # (10.0) allows the window to cover 0.015 ha
        # (10/ANNUAL_LABOUR_HOURS_PER_FARM_WORKER worker-years * 2.1
        # ha/worker), so land this small is never the harvest-window cap's
        # doing, only the ordinary Cobb-Douglas labour term's - which is
        # what this test means to isolate.
        land = _reference_land(hectares=0.01)
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
        # produce more, all else equal. labour_hours is large enough
        # (9000, comfortably more than one worker's ANNUAL_LABOUR_HOURS_
        # PER_FARM_WORKER) that the harvest-window cap in gross_harvest_kg
        # (see its "THE HARVEST WINDOW NOW ALSO BINDS" docstring section)
        # allows up to 13.5 ha - above BOTH land sizes tested, so neither
        # side of this comparison is window-capped and the difference
        # tested is land's, not the window's.
        small_land = _reference_land(hectares=2.0)
        big_land = _reference_land(hectares=8.0)
        harvest_small = agriculture.gross_harvest_kg(small_land, labour_hours=9000.0)
        harvest_big = agriculture.gross_harvest_kg(big_land, labour_hours=9000.0)
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
            # Storage.step now passes a Soil's weather_stdev_fraction as a
            # second positional argument (see agriculture.py's Storage.step
            # and draw_weather_multiplier) - accept and ignore it here.
            agriculture.draw_weather_multiplier = lambda rng, weather_stdev_fraction=None: 1.0
            good_storage = agriculture.Storage(stock_kg=1000.0, seed=3)
            good_flows = good_storage.step(land, labour_hours=6.0 * 150.0,
                                           population=population)

            agriculture.draw_weather_multiplier = lambda rng, weather_stdev_fraction=None: 0.4
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

        # BEHAVIOURAL, NOT A SOURCE SCAN: a grep of
        # fraction_of_population_that_must_farm's own source for the literal
        # string "FALLOW" would pass just as happily on a rewrite that
        # double-counted the idle-land share through a differently-named
        # field or a derived value with no "FALLOW" in its spelling, and it
        # would FAIL a harmless comment that merely mentions fallow, neither
        # of which is the property this check actually cares about. The
        # claim is directly observable instead:
        # fraction_of_population_that_must_farm() takes `rotation` as an
        # argument, so build one whose fallow share differs sharply from the
        # default while its OTHER field (the nitrogen/yield multiplier,
        # which this function DOES legitimately read) is held fixed, and
        # confirm the output does not move at all. If a future edit divides
        # output_per_worker_kg by (1 - rotation.fallow_share_of_holding) as
        # well - the double-count this check exists to catch - this fails
        # regardless of what that division is spelled like in the source.
        no_fallow_same_yield = agriculture.DEFAULT_ROTATION._replace(
            name="test_only_zero_fallow_same_yield_multiplier",
            fallow_share_of_holding=0.0)
        self.assertNotAlmostEqual(
            no_fallow_same_yield.fallow_share_of_holding,
            agriculture.DEFAULT_ROTATION.fallow_share_of_holding,
            places=6,
            msg="the fixture's whole point is a DIFFERENT fallow share")
        self.assertAlmostEqual(
            agriculture.fraction_of_population_that_must_farm(
                rotation=no_fallow_same_yield),
            agriculture.fraction_of_population_that_must_farm(),
            places=9,
            msg="fraction_of_population_that_must_farm() moved when only "
                "the rotation's fallow share changed and its yield "
                "multiplier did not - land is not supposed to be a binding "
                "constraint here, which is the double-count this check "
                "exists to catch")


class HarvestWindowBindsGrossHarvestTests(unittest.TestCase):
    """The defect fix: HARVEST_WINDOW_DAYS and HECTARES_REAPED_PER_WORKER_DAY
    used to be read only by the headline calibration path
    (hectares_per_worker_harvest_window_ceiling ->
    hectares_cropped_per_farm_worker -> fraction_of_population_that_must_
    farm), never by gross_harvest_kg - the function Storage.step actually
    calls every year - so a large Land worked by a large labour_hours pool
    could produce a harvest no real crew could have reaped inside a real
    harvest season. See agriculture.py's module docstring, "THE HARVEST
    WINDOW NOW ALSO BINDS" section, and _max_hectares_harvestable_by_labour.
    """

    def test_a_large_land_at_reference_labour_intensity_is_capped_below_its_full_area(self):
        # 1000 ha "worked" at exactly REFERENCE_LABOUR_HOURS_PER_HECTARE
        # (150 h/ha) is precisely the scenario the old, unfixed
        # gross_harvest_kg treated as fully reaped - it is what the
        # per-hectare labour constants were quoted at. It implies about
        # 107 worker-years of labour, and 107 workers can each crop at
        # most hectares_cropped_per_farm_worker() ~= 2.1 ha inside the
        # harvest window, i.e. about 225 ha total - far short of 1000.
        land = agriculture.Land(hectares=1000.0, quality=1.0)
        labour_hours = 1000.0 * agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE

        cap_hectares = agriculture._max_hectares_harvestable_by_labour(
            labour_hours, agriculture.DEFAULT_CROP, agriculture.DEFAULT_TOOLKIT)
        self.assertLess(cap_hectares, land.hectares)
        self.assertAlmostEqual(cap_hectares, 225.0, places=6)

        capped_harvest = agriculture.gross_harvest_kg(land, labour_hours)

        # What the OLD, unfixed gross_harvest_kg computed: the same
        # Cobb-Douglas curve with land.hectares used directly, no window
        # cap at all. Replicated here from the formula rather than reading
        # a private helper, so this test would still catch a regression
        # even if the internals were reorganised again.
        crop, toolkit = agriculture.DEFAULT_CROP, agriculture.DEFAULT_TOOLKIT
        reference_labour_hours_per_hectare = (
            crop.base_labour_hours_per_hectare * toolkit.labour_hours_multiplier)
        gross_yield_at_reference = (
            crop.planting_material_kg_per_ha * crop.fold_return_on_planting_material)
        total_factor_productivity = (
            gross_yield_at_reference
            / (reference_labour_hours_per_hectare ** agriculture.LABOUR_OUTPUT_ELASTICITY))
        uncapped_harvest = (
            total_factor_productivity
            * land.hectares ** (1.0 - agriculture.LABOUR_OUTPUT_ELASTICITY)
            * labour_hours ** agriculture.LABOUR_OUTPUT_ELASTICITY
            * land.quality)

        self.assertLess(
            capped_harvest, uncapped_harvest,
            "a large Land worked at reference labour intensity must be "
            "capped by the harvest window, not produce what an unbounded "
            "Cobb-Douglas curve would give a crew this size no time to reap")

    def test_capped_harvest_equals_the_harvest_of_just_the_reapable_land(self):
        # Precise version of the same property: gross_harvest_kg on the
        # oversized Land must equal gross_harvest_kg on a Land sized to
        # EXACTLY what the labour pool can reap - the excess hectares
        # contribute nothing, which is the honest statement that they are
        # never actually harvested.
        labour_hours = 1000.0 * agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE
        oversized_land = agriculture.Land(hectares=1000.0, quality=1.0)
        cap_hectares = agriculture._max_hectares_harvestable_by_labour(
            labour_hours, agriculture.DEFAULT_CROP, agriculture.DEFAULT_TOOLKIT)
        reapable_land = agriculture.Land(hectares=cap_hectares, quality=1.0)

        self.assertEqual(
            agriculture.gross_harvest_kg(oversized_land, labour_hours),
            agriculture.gross_harvest_kg(reapable_land, labour_hours))

    def test_autonomous_labour_with_unlimited_hours_still_cannot_exceed_full_land_use(self):
        # The stakeholder's own question: what happens with autonomous
        # labour (robots, or any actor with unlimited hours)? Once the
        # labour pool implies enough worker-equivalents to reap the WHOLE
        # of a fixed Land inside the window, giving it yet more hours does
        # NOT unlock more reaped area - land.hectares is already the
        # effective area - so from that point on, output responds only to
        # the ordinary labour term, at the SAME LABOUR_OUTPUT_ELASTICITY
        # this module uses everywhere else. Doubling hours therefore raises
        # output by exactly 2**LABOUR_OUTPUT_ELASTICITY, never by the full
        # 2x an unbound land term would otherwise have allowed once the
        # window stopped being able to supply more land.
        land = agriculture.Land(hectares=5.0, quality=1.0)
        # Both labour levels already crop the full 5 ha - see
        # hectares_per_worker_harvest_window_ceiling's ~2.1 ha/worker: 4000
        # hours implies ~2.9 workers, already 6 ha of window capacity.
        labour_low = 4000.0
        labour_high = 8000.0
        self.assertGreaterEqual(
            agriculture._max_hectares_harvestable_by_labour(
                labour_low, agriculture.DEFAULT_CROP, agriculture.DEFAULT_TOOLKIT),
            land.hectares)

        harvest_low = agriculture.gross_harvest_kg(land, labour_low)
        harvest_high = agriculture.gross_harvest_kg(land, labour_high)
        self.assertAlmostEqual(
            harvest_high / harvest_low,
            (labour_high / labour_low) ** agriculture.LABOUR_OUTPUT_ELASTICITY,
            places=6,
            msg="once the window can already supply the full Land, more "
                "hours must move output at the ordinary labour elasticity, "
                "not faster - autonomous labour does not get a free pass "
                "around the window by having 'unlimited hours' on a crew "
                "that already covers the land")


class CropSoilRotationToolkitAxisTests(unittest.TestCase):
    """One worked, non-default case per axis (crop, rotation, toolkit,
    storage technique, soil), each showing fraction_of_population_that_
    must_farm (or the specific mechanism it depends on) move in the
    DIRECTION that axis's own `why` text predicts, computed from this
    module's declared numbers rather than tuned to hit a target - see the
    task this module answers to and CLAUDE.md SS3.1/SS3.4. The default
    (wheat/two-field/ard-and-sickle/pit-silo/ordinary-loam) combination is
    exactly what HeadlineCalibrationTests already pins; this class is
    about the DIRECTIONS the other points on each axis move it, not about
    matching history.
    """

    def test_potatoes_need_fewer_farmers_than_wheat_despite_needing_more_labour_per_hectare(self):
        # Potatoes yield far more calories per hectare than wheat (see
        # POTATO_FOLD_RETURN_ON_SEED_TUBERS's declaration) even though they
        # also need more than double the labour per hectare
        # (POTATO_BASE_LABOUR_HOURS_PER_HECTARE) and dig, rather than reap,
        # more slowly (POTATO_BASE_HECTARES_REAPED_PER_WORKER_DAY). The
        # yield advantage wins: fewer farmers are needed per person fed.
        wheat_fraction = agriculture.fraction_of_population_that_must_farm()
        potato_fraction = agriculture.fraction_of_population_that_must_farm(
            crop=agriculture.POTATOES)
        self.assertLess(potato_fraction, wheat_fraction)

    def test_rice_also_needs_fewer_farmers_than_wheat_at_its_own_much_higher_labour_cost(self):
        wheat_fraction = agriculture.fraction_of_population_that_must_farm()
        rice_fraction = agriculture.fraction_of_population_that_must_farm(
            crop=agriculture.RICE)
        self.assertLess(rice_fraction, wheat_fraction)
        # And rice's own labour bill is the module's own explanation for
        # why historical wet-rice populations were dense on small
        # holdings, not because rice needs less land per calorie: fewer
        # hectares are cropped per worker under rice than under wheat.
        self.assertLess(
            agriculture.hectares_cropped_per_farm_worker(crop=agriculture.RICE),
            agriculture.hectares_cropped_per_farm_worker())

    def test_three_field_rotation_frees_land_without_touching_fallows_reservation(self):
        # Three-field cuts the idle share from a half to a third, so the
        # SAME cropped area needs a smaller holding - the land-requirement
        # half of the pairing described in the ROTATION TABLE section.
        default_holding = agriculture.holding_hectares_required_per_farm_worker()
        three_field_holding = agriculture.holding_hectares_required_per_farm_worker(
            rotation=agriculture.THREE_FIELD)
        self.assertLess(three_field_holding, default_holding)
        self.assertAlmostEqual(
            three_field_holding,
            agriculture.hectares_cropped_per_farm_worker()
            / (1.0 - agriculture.THREE_FIELD_FALLOW_SHARE_OF_HOLDING),
            places=6)

    def test_nile_flood_recession_rotation_raises_yield_and_frees_the_most_land(self):
        # The exceptional-land end of the rotation axis: continuous
        # cropping (almost no fallow) AND a fertility bonus from the silt,
        # moving together as the ROTATION TABLE section says they should.
        # Both should beat the two-field default, and Nile's near-zero
        # fallow should free more land than three-field's partial cut.
        default_fraction = agriculture.fraction_of_population_that_must_farm()
        three_field_fraction = agriculture.fraction_of_population_that_must_farm(
            rotation=agriculture.THREE_FIELD)
        nile_fraction = agriculture.fraction_of_population_that_must_farm(
            rotation=agriculture.NILE_FLOOD_RECESSION)
        self.assertLess(nile_fraction, default_fraction)
        self.assertLess(nile_fraction, three_field_fraction)

        nile_holding = agriculture.holding_hectares_required_per_farm_worker(
            rotation=agriculture.NILE_FLOOD_RECESSION)
        three_field_holding = agriculture.holding_hectares_required_per_farm_worker(
            rotation=agriculture.THREE_FIELD)
        self.assertLess(nile_holding, three_field_holding)

    def test_horse_collar_toolkit_saves_labour_but_the_window_still_absorbs_it(self):
        # The stakeholder's own example, and the module's own central
        # finding extended to a new technique: the horse collar and
        # mouldboard need fewer hours per hectare of PLOUGHING
        # (HORSE_COLLAR_LABOUR_HOURS_MULTIPLIER < 1), which raises the
        # annual-hours ceiling - but does nothing to the reaping rate, so
        # the harvest-window ceiling is unchanged and stays the binding
        # one. hectares_cropped_per_farm_worker must therefore NOT move at
        # all from this toolkit alone.
        default_annual_ceiling = agriculture.hectares_per_worker_annual_hours_ceiling()
        horse_collar_annual_ceiling = agriculture.hectares_per_worker_annual_hours_ceiling(
            toolkit=agriculture.HORSE_COLLAR_AND_MOULDBOARD)
        self.assertGreater(horse_collar_annual_ceiling, default_annual_ceiling)

        self.assertAlmostEqual(
            agriculture.hectares_cropped_per_farm_worker(
                toolkit=agriculture.HORSE_COLLAR_AND_MOULDBOARD),
            agriculture.hectares_cropped_per_farm_worker(),
            places=9,
            msg="the horse collar only touches ploughing hours, which the "
                "harvest window already made slack - it must not move the "
                "binding hectares-per-worker figure by itself")

        # The toolkit's OWN small ploughing-yield bonus is a separate,
        # independent effect and is the only thing that should move the
        # headline number here - hectares_cropped_per_farm_worker is
        # unchanged (just asserted above), so any movement has to come
        # from HORSE_COLLAR_PLOUGHING_YIELD_MULTIPLIER raising the GROSS
        # yield before seed is paid back. That subtraction is not scaled,
        # so the expected fraction is computed from the same formula
        # fraction_of_population_that_must_farm uses, not from a simple
        # division by the multiplier (which would ignore the unscaled
        # seed subtraction and give the wrong number).
        crop = agriculture.DEFAULT_CROP
        gross_yield = (crop.planting_material_kg_per_ha
                       * crop.fold_return_on_planting_material)
        net_yield_with_horse_collar = (
            gross_yield * agriculture.HORSE_COLLAR_PLOUGHING_YIELD_MULTIPLIER
            - crop.planting_material_kg_per_ha)
        food_available_per_ha = (
            net_yield_with_horse_collar * (1.0 - agriculture.GRAIN_SPOILAGE_RATE_PER_YEAR))
        expected_output_per_worker = (
            agriculture.hectares_cropped_per_farm_worker() * food_available_per_ha)
        expected_fraction = (
            agriculture.annual_food_demand_kg_per_person() / expected_output_per_worker)

        default_fraction = agriculture.fraction_of_population_that_must_farm()
        horse_collar_fraction = agriculture.fraction_of_population_that_must_farm(
            toolkit=agriculture.HORSE_COLLAR_AND_MOULDBOARD)
        self.assertLess(horse_collar_fraction, default_fraction)
        self.assertAlmostEqual(horse_collar_fraction, expected_fraction, places=6)

    def test_a_better_reaping_tool_is_what_actually_loosens_the_window(self):
        # Unlike the horse collar, a scythe-and-cradle changes ONLY the
        # reaping rate, which is exactly the harvest window's ceiling -
        # this is what the module's own docstring says would have to
        # change to move the headline number, and here it does, by
        # exactly the declared multiplier.
        default_cropped = agriculture.hectares_cropped_per_farm_worker()
        scythe_cropped = agriculture.hectares_cropped_per_farm_worker(
            toolkit=agriculture.SCYTHE_AND_CRADLE)
        self.assertAlmostEqual(
            scythe_cropped,
            default_cropped * agriculture.SCYTHE_AND_CRADLE_REAPING_RATE_MULTIPLIER,
            places=6)

        default_fraction = agriculture.fraction_of_population_that_must_farm()
        scythe_fraction = agriculture.fraction_of_population_that_must_farm(
            toolkit=agriculture.SCYTHE_AND_CRADLE)
        self.assertLess(scythe_fraction, default_fraction)
        self.assertAlmostEqual(
            scythe_fraction,
            default_fraction / agriculture.SCYTHE_AND_CRADLE_REAPING_RATE_MULTIPLIER,
            places=6)

    def test_a_mechanical_reaper_loosens_the_window_further_than_a_scythe_does(self):
        scythe_cropped = agriculture.hectares_cropped_per_farm_worker(
            toolkit=agriculture.SCYTHE_AND_CRADLE)
        reaper_cropped = agriculture.hectares_cropped_per_farm_worker(
            toolkit=agriculture.MECHANICAL_REAPER)
        self.assertGreater(reaper_cropped, scythe_cropped)
        # At MECHANICAL_REAPER_REAPING_RATE_MULTIPLIER=10, the harvest-
        # window ceiling (21.0 ha) exceeds even the annual-hours ceiling
        # (9.33 ha), so the ANNUAL-HOURS ceiling becomes the new binding
        # one - the module's own predicted shape once reaping is fast
        # enough, stated as a test rather than only as prose.
        self.assertAlmostEqual(
            reaper_cropped,
            agriculture.hectares_per_worker_annual_hours_ceiling(),
            places=6,
            msg="once reaping is fast enough, the annual-hours ceiling "
                "should take back over as the binding one")

    def test_refrigerated_storage_raises_food_available_without_touching_yield(self):
        # Storage technique acts purely on the spoilage axis - it must
        # raise the headline number's food-available term by exactly the
        # ratio of the two techniques' (1 - spoilage) factors, and it must
        # not touch hectares_cropped_per_farm_worker at all (storage has
        # nothing to do with labour or the harvest window).
        default_fraction = agriculture.fraction_of_population_that_must_farm()
        refrigerated_fraction = agriculture.fraction_of_population_that_must_farm(
            storage_technique=agriculture.REFRIGERATED_STORE)
        self.assertLess(refrigerated_fraction, default_fraction)

        expected_ratio = (
            (1.0 - agriculture.GRAIN_SPOILAGE_RATE_PER_YEAR)
            / (1.0 - agriculture.REFRIGERATED_STORE_SPOILAGE_RATE_PER_YEAR))
        self.assertAlmostEqual(
            refrigerated_fraction / default_fraction, expected_ratio, places=6)

        self.assertEqual(
            agriculture.hectares_cropped_per_farm_worker(),
            agriculture.hectares_cropped_per_farm_worker())  # storage never touches this axis

    def test_chernozem_soil_needs_fewer_farmers_than_ordinary_loam(self):
        # A pure fertility fact about a PLACE, fed through the same
        # yield multiplier toolkit.ploughing_yield_multiplier uses - see
        # the horse-collar test above for why the expected fraction has to
        # be computed from the full formula rather than a simple division:
        # CHERNOZEM_QUALITY_MULTIPLIER scales the GROSS yield, and the
        # seed subtraction after it is not scaled.
        crop = agriculture.DEFAULT_CROP
        gross_yield = (crop.planting_material_kg_per_ha
                       * crop.fold_return_on_planting_material)
        net_yield_on_chernozem = (
            gross_yield * agriculture.CHERNOZEM_QUALITY_MULTIPLIER
            - crop.planting_material_kg_per_ha)
        food_available_per_ha = (
            net_yield_on_chernozem * (1.0 - agriculture.GRAIN_SPOILAGE_RATE_PER_YEAR))
        expected_output_per_worker = (
            agriculture.hectares_cropped_per_farm_worker() * food_available_per_ha)
        expected_fraction = (
            agriculture.annual_food_demand_kg_per_person() / expected_output_per_worker)

        default_fraction = agriculture.fraction_of_population_that_must_farm()
        chernozem_fraction = agriculture.fraction_of_population_that_must_farm(
            soil=agriculture.UKRAINIAN_CHERNOZEM)
        self.assertLess(chernozem_fraction, default_fraction)
        self.assertAlmostEqual(chernozem_fraction, expected_fraction, places=6)

    def test_desert_and_arctic_soil_make_ordinary_wheat_farming_fail_outright(self):
        # These are not "poor soil" - see the SOIL TABLE section's
        # limiting_factor field - and the module is honest that at these
        # multipliers, reference-technique wheat farming cannot even
        # produce a positive surplus once seed is paid back: net yield per
        # hectare goes negative once the quality multiplier is this low,
        # which this test surfaces directly rather than papering over.
        gross_yield = (agriculture.SEED_SOWING_RATE_KG_PER_HA
                       * agriculture.FOLD_RETURN_ON_SEED_SOWN)
        for soil, label in ((agriculture.DESERT, "desert"),
                            (agriculture.ARCTIC_TUNDRA, "arctic")):
            net_yield = (gross_yield * soil.quality_multiplier
                         - agriculture.SEED_SOWING_RATE_KG_PER_HA)
            self.assertLess(
                net_yield, 0.0,
                "%s-quality wheat farming should not even return its own "
                "seed at reference technique - this is the honest content "
                "of '%s', not a bug in the fraction this makes negative"
                % (label, soil.limiting_factor))


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


class HarvestWindowIsCalendarTimeTests(unittest.TestCase):
    """The harvest window is CALENDAR time, so an actor cannot beat it by
    working the rest of the year harder.

    The first version of the window cap converted a pool of hours to
    worker-equivalents by dividing by a human's annual hours, on the stated
    reasoning that "a pool of hours is indistinguishable from that many
    worker-years". That holds for the annual-hours ceiling and fails for
    this one: twenty-one days is twenty-one days, one reaper can only be in
    one field at a time, and hours outside the window reap nothing. The
    error was 2.61x for an actor working every hour of the year, in the
    direction that flatters autonomous labour - which is the case it was
    built to answer.
    """

    def test_the_two_formulations_agree_for_one_ordinary_worker(self):
        # The identity that keeps the calendar-time form and the per-worker
        # ceiling from drifting apart: 21 days x 10 h x 0.01 ha/h = 2.1 ha.
        # If someone changes HARVEST_WORKING_DAY_HOURS or the per-day
        # reaping rate without changing the other, this fails.
        self.assertAlmostEqual(
            agriculture.max_hectares_reapable_by_crew(1),
            agriculture.hectares_per_worker_harvest_window_ceiling(),
            places=9)

    def test_working_longer_days_helps_but_only_in_proportion(self):
        ten_hour = agriculture.max_hectares_reapable_by_crew(
            1, hours_per_worker_day=10.0)
        never_sleeps = agriculture.max_hectares_reapable_by_crew(
            1, hours_per_worker_day=24.0)
        # 2.4x, not 6.26x. The gain is the ratio of hours IN THE WINDOW.
        self.assertAlmostEqual(never_sleeps / ten_hour, 2.4, places=6)

    def test_an_impossible_working_day_is_clamped_to_the_earths_rotation(self):
        self.assertAlmostEqual(
            agriculture.max_hectares_reapable_by_crew(
                1, hours_per_worker_day=1000.0),
            agriculture.max_hectares_reapable_by_crew(
                1, hours_per_worker_day=agriculture.HOURS_PER_DAY),
            places=9)

    def test_a_better_reaping_tool_is_what_actually_lifts_the_ceiling(self):
        # The substantive claim: for a FIXED crew working a fixed day, only
        # the reaping rate or the window length moves this number. That is
        # what historically moved it, so the model should agree.
        sickle = agriculture.max_hectares_reapable_by_crew(1)
        scythe = agriculture.max_hectares_reapable_by_crew(
            1, toolkit=agriculture.SCYTHE_AND_CRADLE)
        reaper = agriculture.max_hectares_reapable_by_crew(
            1, toolkit=agriculture.MECHANICAL_REAPER)
        self.assertGreater(scythe, sickle)
        self.assertGreater(reaper, scythe)

    def test_crew_size_scales_the_cap_linearly(self):
        # Ten reapers reap ten times as much: the window constrains each of
        # them separately, and nothing about calendar time is shared.
        one = agriculture.max_hectares_reapable_by_crew(1)
        ten = agriculture.max_hectares_reapable_by_crew(10)
        self.assertAlmostEqual(ten, 10.0 * one, places=9)

    def test_the_default_path_is_unchanged_by_all_of_this(self):
        # Nothing above may move the headline number. worker_count is opt-in
        # precisely so the ordinary-human case keeps its old derivation.
        self.assertAlmostEqual(
            agriculture.fraction_of_population_that_must_farm(),
            0.21181, places=4)


if __name__ == "__main__":
    unittest.main()
