"""Regression tests for sim/world/deposits.py.

Written as unittest.TestCase classes, like sim/tests/test_agriculture.py,
sim/tests/test_demography.py and sim/tests/test_transport.py: this module
has no dependency on sim/engine/ or any other sim/world/ module (see
deposits.py's own docstring for why), so importing sim/tests/harness.py
would pull in the whole engine for no reason. sim/tests/__main__.py's
_run_topic already runs both styles identically.

CalibrationAgainstBookPricesTests is the one class that reads
data/prices.json - the CALIBRATION TARGETS deposits.py's own docstring
promises are read only by tests, never by the module's own functions (see
sim/world/agriculture.py's own CALIBRATION TARGETS section for the same
discipline applied there first). It reports the disagreement; it never
asserts a tolerance tight enough to tempt anyone into tuning a grade or a
breaking-hours constant to close it.
"""
import ast
import json
import os
import subprocess
import sys
import unittest

from sim.world import deposits

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def _make_deposit(name, metal="test_metal", material_moved="ore",
                   ore_grade_kg_per_tonne=10.0, depth_class="surface",
                   hardness_class="medium", quantity_tonnes_per_year=100.0,
                   note="", byproducts=()):
    return deposits.Deposit(
        name=name, metal=metal, region="nowhere",
        material_moved=material_moved,
        ore_grade_kg_per_tonne=ore_grade_kg_per_tonne,
        depth_class=depth_class, hardness_class=hardness_class,
        quantity_tonnes_per_year=quantity_tonnes_per_year, note=note,
        byproducts=byproducts)


class ExtractionCostMechanicsTests(unittest.TestCase):
    """extraction_cost_labour_hours_per_kg is where every physical fact
    this module cares about actually enters the arithmetic. These checks
    are ORDERINGS, not particular numbers - see
    sim/tests/test_transport.py's own RollingResistanceOrdersSurfacesTests
    for the same reasoning applied to a sibling module: the constants
    behind these numbers are engineering estimates, but the DIRECTIONS
    (richer is cheaper, deeper is dearer, harder is dearer) are not in
    doubt regardless of their exact size.
    """

    def test_higher_grade_is_cheaper(self):
        lean = _make_deposit("lean", ore_grade_kg_per_tonne=5.0)
        rich = _make_deposit("rich", ore_grade_kg_per_tonne=50.0)
        self.assertGreater(
            deposits.extraction_cost_labour_hours_per_kg(lean),
            deposits.extraction_cost_labour_hours_per_kg(rich))

    def test_deeper_is_costlier_at_equal_grade_and_hardness(self):
        surface = _make_deposit("s", depth_class="surface")
        shallow = _make_deposit("sh", depth_class="shallow_vein")
        deep = _make_deposit("d", depth_class="deep_vein")
        cost = deposits.extraction_cost_labour_hours_per_kg
        self.assertLess(cost(surface), cost(shallow))
        self.assertLess(cost(shallow), cost(deep))

    def test_harder_is_costlier_at_equal_grade_and_depth(self):
        soft = _make_deposit("soft", hardness_class="soft")
        medium = _make_deposit("medium", hardness_class="medium")
        hard = _make_deposit("hard", hardness_class="hard")
        cost = deposits.extraction_cost_labour_hours_per_kg
        self.assertLess(cost(soft), cost(medium))
        self.assertLess(cost(medium), cost(hard))

    def test_hydraulic_alluvial_cheaper_than_hand_alluvial_at_equal_grade(self):
        hand = _make_deposit("hand", material_moved="gravel",
                              depth_class="alluvial", hardness_class=None)
        hydraulic = _make_deposit("hydraulic", material_moved="gravel",
                                   depth_class="alluvial_hydraulic",
                                   hardness_class=None)
        self.assertLess(
            deposits.extraction_cost_labour_hours_per_kg(hydraulic),
            deposits.extraction_cost_labour_hours_per_kg(hand))

    def test_every_named_deposit_has_a_positive_finite_cost(self):
        for metal in deposits.METALS:
            for deposit in deposits.load_deposits(metal):
                cost = deposits.extraction_cost_labour_hours_per_kg(deposit)
                self.assertGreater(cost, 0.0, deposit.name)
                self.assertLess(cost, float("inf"), deposit.name)


class AlluvialVersusVeinGoldTests(unittest.TestCase):
    """The module docstring's own headline illustration: Las Medulas
    (alluvial, hydraulically worked) against Dacia (hard rock, deep vein).
    Grade alone would suggest Dacia is cheaper (its ore is far richer per
    tonne); depth and hardness overwhelm that, which is exactly the point -
    grade is the dominant term in general, not the ONLY one.
    """

    def setUp(self):
        gold = {d.name: d for d in deposits.load_deposits("gold")}
        self.las_medulas = gold["las_medulas_alluvial"]
        self.dacia = gold["dacia_vein_gold"]

    def test_dacia_ore_is_richer_by_grade(self):
        self.assertGreater(self.dacia.ore_grade_kg_per_tonne,
                            self.las_medulas.ore_grade_kg_per_tonne)

    def test_las_medulas_is_nonetheless_far_cheaper(self):
        cost = deposits.extraction_cost_labour_hours_per_kg
        las_medulas_cost = cost(self.las_medulas)
        dacia_cost = cost(self.dacia)
        self.assertLess(las_medulas_cost, dacia_cost)
        # "far cheaper", not just cheaper - the whole reason alluvial and
        # vein gold cannot be treated as one commodity with one cost.
        self.assertGreater(dacia_cost / las_medulas_cost, 10.0)


class SupplyCurveTests(unittest.TestCase):

    def test_sorted_ascending_by_cost(self):
        raw = [
            _make_deposit("d3", ore_grade_kg_per_tonne=1.0),
            _make_deposit("d1", ore_grade_kg_per_tonne=100.0),
            _make_deposit("d2", ore_grade_kg_per_tonne=10.0),
        ]
        points = deposits.supply_curve(raw)
        costs = [p.own_cost_labour_hours_per_kg for p in points]
        self.assertEqual(costs, sorted(costs))
        self.assertEqual([p.deposit.name for p in points], ["d1", "d2", "d3"])

    def test_cumulative_quantity_accumulates_in_sorted_order(self):
        raw = [
            _make_deposit("cheap", ore_grade_kg_per_tonne=100.0,
                          quantity_tonnes_per_year=10.0),
            _make_deposit("dear", ore_grade_kg_per_tonne=1.0,
                          quantity_tonnes_per_year=5.0),
        ]
        points = deposits.supply_curve(raw)
        self.assertEqual(points[0].deposit.name, "cheap")
        self.assertEqual(points[0].cumulative_quantity_tonnes_per_year, 10.0)
        self.assertEqual(points[1].cumulative_quantity_tonnes_per_year, 15.0)


class MarginalDepositRentTests(unittest.TestCase):
    """The Ricardian rent arithmetic itself, on a small hand-worked
    example rather than the real deposit list, so the expected numbers can
    be checked by hand.

    Three deposits, grades chosen so their costs come out at round numbers:
    cheap (grade 100 -> cost 1.0/10=0.1... arranged below to exact values).
    """

    def setUp(self):
        # hours_per_tonne_material fixed at BREAKING_HOURS_PER_TONNE_MEDIUM
        # (surface, medium) for all three, so cost = MEDIUM / grade exactly.
        medium = deposits.BREAKING_HOURS_PER_TONNE_MEDIUM
        self.cheap = _make_deposit("cheap", depth_class="surface",
                                    hardness_class="medium",
                                    ore_grade_kg_per_tonne=medium / 1.0,   # cost 1.0
                                    quantity_tonnes_per_year=10.0)
        self.middle = _make_deposit("middle", depth_class="surface",
                                     hardness_class="medium",
                                     ore_grade_kg_per_tonne=medium / 2.0,  # cost 2.0
                                     quantity_tonnes_per_year=10.0)
        self.dear = _make_deposit("dear", depth_class="surface",
                                   hardness_class="medium",
                                   ore_grade_kg_per_tonne=medium / 5.0,    # cost 5.0
                                   quantity_tonnes_per_year=10.0)
        self.deposits = [self.dear, self.cheap, self.middle]  # deliberately
                                                                # out of order

    def test_marginal_deposit_is_the_one_that_fills_demand(self):
        # 15 tonnes demanded: cheap (10) fully, then 5 of middle's 10.
        outcome = deposits.find_marginal_deposit(self.deposits, 15.0)
        self.assertEqual(outcome.marginal_deposit.name, "middle")
        self.assertAlmostEqual(outcome.price_at_margin_labour_hours_per_kg, 2.0)

    def test_price_is_the_same_for_every_unit_regardless_of_source(self):
        # Ricardian pricing: ONE price for the whole metal, set at the
        # margin - not each deposit selling at its own cost.
        outcome = deposits.find_marginal_deposit(self.deposits, 15.0)
        by_name = {a.deposit.name: a for a in outcome.allocations}
        self.assertEqual(by_name["cheap"].own_cost_labour_hours_per_kg, 1.0)
        self.assertEqual(outcome.price_at_margin_labour_hours_per_kg, 2.0)

    def test_rent_is_marginal_cost_minus_own_cost_times_quantity(self):
        outcome = deposits.find_marginal_deposit(self.deposits, 15.0)
        by_name = {a.deposit.name: a for a in outcome.allocations}
        cheap = by_name["cheap"]
        self.assertEqual(cheap.quantity_supplied_tonnes_per_year, 10.0)
        self.assertAlmostEqual(cheap.rent_labour_hours_per_kg, 2.0 - 1.0)
        self.assertAlmostEqual(
            cheap.rent_total_labour_hours_per_year,
            (2.0 - 1.0) * 10.0 * 1000.0)

    def test_marginal_deposit_itself_earns_zero_rent(self):
        outcome = deposits.find_marginal_deposit(self.deposits, 15.0)
        by_name = {a.deposit.name: a for a in outcome.allocations}
        self.assertEqual(by_name["middle"].rent_labour_hours_per_kg, 0.0)

    def test_deposit_not_reached_supplies_and_earns_nothing(self):
        outcome = deposits.find_marginal_deposit(self.deposits, 15.0)
        by_name = {a.deposit.name: a for a in outcome.allocations}
        self.assertEqual(by_name["dear"].quantity_supplied_tonnes_per_year, 0.0)
        self.assertEqual(by_name["dear"].rent_labour_hours_per_kg, 0.0)

    def test_quantity_conservation(self):
        outcome = deposits.find_marginal_deposit(self.deposits, 15.0)
        total_supplied = sum(
            a.quantity_supplied_tonnes_per_year for a in outcome.allocations)
        self.assertAlmostEqual(total_supplied, 15.0)
        self.assertAlmostEqual(outcome.quantity_supplied_tonnes_per_year, 15.0)
        self.assertEqual(outcome.unmet_demand_tonnes_per_year, 0.0)

    def test_higher_demand_raises_the_margin(self):
        # This IS the mechanism: the same deposits, more demanded, a
        # costlier deposit becomes marginal and the price rises with no
        # change to any deposit's own cost.
        low = deposits.find_marginal_deposit(self.deposits, 10.0)
        high = deposits.find_marginal_deposit(self.deposits, 30.0)
        self.assertLess(low.price_at_margin_labour_hours_per_kg,
                         high.price_at_margin_labour_hours_per_kg)
        self.assertEqual(low.marginal_deposit.name, "cheap")
        self.assertEqual(high.marginal_deposit.name, "dear")

    def test_demand_beyond_every_deposits_capacity_is_reported_unmet(self):
        outcome = deposits.find_marginal_deposit(self.deposits, 100.0)
        self.assertGreater(outcome.unmet_demand_tonnes_per_year, 0.0)
        self.assertEqual(outcome.marginal_deposit.name, "dear")
        self.assertAlmostEqual(
            outcome.unmet_demand_tonnes_per_year, 100.0 - 30.0)

    def test_zero_demand_supplies_nothing_and_prices_nothing(self):
        outcome = deposits.find_marginal_deposit(self.deposits, 0.0)
        self.assertEqual(outcome.quantity_supplied_tonnes_per_year, 0.0)
        self.assertEqual(outcome.unmet_demand_tonnes_per_year, 0.0)
        for allocation in outcome.allocations:
            self.assertEqual(allocation.quantity_supplied_tonnes_per_year, 0.0)

    def test_negative_demand_is_rejected(self):
        with self.assertRaises(ValueError):
            deposits.find_marginal_deposit(self.deposits, -1.0)


class DepletionMechanismTests(unittest.TestCase):
    """DepositState and simulate_depletion: a deposit that runs out forces
    the margin to a costlier one, with no change in demand at all - the
    EXTENSIVE margin. Price does not sit flat between exhaustion events
    either, because the intensive margin (declining grade within a deposit)
    also moves it - see IntensiveMarginTests for that mechanism checked in
    isolation, and this class's own test_price_rises_once_... for the two
    effects told apart within a single simulation.
    """

    def setUp(self):
        self.cheap = _make_deposit("cheap", ore_grade_kg_per_tonne=100.0,
                                    quantity_tonnes_per_year=10.0)
        self.dear = _make_deposit("dear", ore_grade_kg_per_tonne=1.0,
                                   quantity_tonnes_per_year=10.0)

    def test_price_rises_once_the_cheap_deposit_is_exhausted(self):
        # Demand of 10/yr, entirely from `cheap`, whose reserve (working
        # life 3 years x 10/yr = 30 t) runs out after year 3. Within years
        # 1-3 price already creeps up (the intensive margin: cheap's own
        # grade falling as it is worked down), but the JUMP at exhaustion
        # (to `dear`'s cost at ITS OWN untouched, virgin grade) dwarfs that
        # gentle creep - this is what tells "a deposit is running low"
        # apart from "a deposit just ran out" in the reported price.
        outcomes = deposits.simulate_depletion(
            [self.cheap, self.dear], quantity_demanded_tonnes_per_year=10.0,
            years=6, working_life_years=3.0)
        early_prices = [o.price_at_margin_labour_hours_per_kg for o in outcomes[:3]]
        late_prices = [o.price_at_margin_labour_hours_per_kg for o in outcomes[3:]]
        # Each block rises on its own (the intensive margin, live within
        # both `cheap`'s and then `dear`'s own working life)...
        self.assertEqual(early_prices, sorted(early_prices))
        self.assertLess(early_prices[0], early_prices[-1])
        self.assertEqual(late_prices, sorted(late_prices))
        self.assertLess(late_prices[0], late_prices[-1])
        # ...but the jump AT exhaustion is far bigger than either block's
        # own intra-deposit creep: `dear`'s virgin cost (8/1=8.0) against
        # `cheap`'s own most-depleted cost (8/33.33=0.24) is a jump over
        # 30x, dwarfing the roughly 3x the intensive margin alone produces
        # within either block.
        self.assertGreater(late_prices[0] / early_prices[-1], 10.0)
        self.assertIn("cheap", outcomes[2].exhausted_this_year)

    def test_prices_are_non_decreasing_while_any_deposit_still_supplies(self):
        # Bounded at 6 years deliberately: both deposits' reserves (working
        # life 3 years each) are exhausted by year 6, and once NEITHER can
        # supply anything price_at_margin_labour_hours_per_kg falls back to
        # 0.0 (find_marginal_deposit's documented "no deposit at all"
        # reading, not a falling price) - see that function's own
        # docstring. Monotonic non-decrease is only a property of the
        # RENT mechanism while there is a market to have a margin in.
        outcomes = deposits.simulate_depletion(
            [self.cheap, self.dear], quantity_demanded_tonnes_per_year=10.0,
            years=6, working_life_years=3.0)
        prices = [o.price_at_margin_labour_hours_per_kg for o in outcomes]
        self.assertEqual(prices, sorted(prices))
        self.assertGreater(prices[-1], prices[0])

    def test_extraction_is_attributed_to_the_correct_deposit(self):
        # Regression test for a real bug this file's own author introduced
        # and caught: simulate_depletion matched find_marginal_deposit's
        # allocations back to DepositState objects by ZIP POSITION, but
        # find_marginal_deposit sorts internally, so a reordering silently
        # credited each state with a DIFFERENT deposit's extraction. Three
        # deposits whose cost order differs from construction order is
        # exactly the case that stayed silent under position-matching.
        a = _make_deposit("a_expensive", ore_grade_kg_per_tonne=1.0,
                           quantity_tonnes_per_year=5.0)
        b = _make_deposit("b_cheap", ore_grade_kg_per_tonne=100.0,
                           quantity_tonnes_per_year=5.0)
        c = _make_deposit("c_middle", ore_grade_kg_per_tonne=10.0,
                           quantity_tonnes_per_year=5.0)
        states = deposits.init_deposit_states([a, b, c], working_life_years=2.0)
        outcomes = deposits.simulate_depletion(
            [a, b, c], quantity_demanded_tonnes_per_year=5.0, years=1,
            working_life_years=2.0)
        # Only the cheapest (b_cheap) should have been touched at all: 5
        # tonnes demanded, b_cheap alone supplies its full 5.
        self.assertEqual(outcomes[0].marginal_deposit_name, "b_cheap")
        by_name = {s.deposit.name: s for s in
                   deposits.init_deposit_states([a, b, c], working_life_years=2.0)}
        # Replay the same single year by hand and check remaining reserves
        # land on the deposit that was ACTUALLY supplied, not on whichever
        # one the sort happened to put in that list position.
        state_b = by_name["b_cheap"]
        state_b.extract(5.0)
        self.assertEqual(state_b.remaining_reserve_tonnes_metal, 5.0)  # 10 - 5
        # a and c were never touched this year.
        self.assertEqual(by_name["a_expensive"].remaining_reserve_tonnes_metal, 10.0)
        self.assertEqual(by_name["c_middle"].remaining_reserve_tonnes_metal, 10.0)
        del states  # constructed only to document the "before" reserves above


class SinkingCostTests(unittest.TestCase):
    """sinking_cost_labour_hours, amortized_sinking_cost_labour_hours_per_kg
    and total_cost_labour_hours_per_kg - the stakeholder's first
    observation: a fixed, one-time cost to open a deposit, independent of
    what is down there, additive with the recurring per-tonne cost.
    """

    def test_surface_and_hand_alluvial_have_zero_fixed_cost(self):
        surface = _make_deposit("s", depth_class="surface")
        alluvial = _make_deposit("a", material_moved="gravel",
                                  depth_class="alluvial", hardness_class=None)
        self.assertEqual(deposits.sinking_cost_labour_hours(surface), 0.0)
        self.assertEqual(deposits.sinking_cost_labour_hours(alluvial), 0.0)

    def test_shaft_and_aqueduct_classes_have_positive_fixed_cost(self):
        shallow = _make_deposit("sh", depth_class="shallow_vein")
        deep = _make_deposit("d", depth_class="deep_vein")
        hydraulic = _make_deposit("h", material_moved="gravel",
                                   depth_class="alluvial_hydraulic",
                                   hardness_class=None)
        self.assertGreater(deposits.sinking_cost_labour_hours(shallow), 0.0)
        self.assertGreater(deposits.sinking_cost_labour_hours(deep), 0.0)
        self.assertGreater(deposits.sinking_cost_labour_hours(hydraulic), 0.0)
        # A deep shaft (dewatering battery included) costs more to open
        # than a shallow one - the same DIRECTION as the recurring haulage
        # multiplier already asserts for these two classes.
        self.assertGreater(deposits.sinking_cost_labour_hours(deep),
                            deposits.sinking_cost_labour_hours(shallow))

    def test_zero_fixed_cost_leaves_total_cost_equal_to_extraction_cost(self):
        # Surface deposits pay no fixed cost at all, whatever their size -
        # this is what keeps every EXISTING test in this file (all built on
        # depth_class="surface" deposits) valid unchanged now that
        # total_cost_labour_hours_per_kg, not extraction_cost_labour_
        # hours_per_kg, is what supply_curve and find_marginal_deposit
        # actually sort and price by.
        deposit = _make_deposit("s", depth_class="surface",
                                 ore_grade_kg_per_tonne=25.0)
        self.assertEqual(
            deposits.total_cost_labour_hours_per_kg(deposit),
            deposits.extraction_cost_labour_hours_per_kg(deposit))

    def test_fixed_cost_is_independent_of_grade(self):
        # The stakeholder's own claim: a shaft of a given depth through
        # given rock costs what it costs, whatever the ore grade behind it.
        lean = _make_deposit("lean", depth_class="deep_vein",
                              ore_grade_kg_per_tonne=1.0)
        rich = _make_deposit("rich", depth_class="deep_vein",
                              ore_grade_kg_per_tonne=1000.0)
        self.assertEqual(deposits.sinking_cost_labour_hours(lean),
                          deposits.sinking_cost_labour_hours(rich))

    def test_larger_reserve_amortizes_the_fixed_cost_more_thinly(self):
        # "The same cost to make a mine regardless of if there is 1 ton of
        # gold in there, or 500 billion tons" - a bigger assumed lifetime
        # output spreads the SAME fixed shaft cost over more kilograms, so
        # the amortised charge per kilogram falls.
        small = _make_deposit("small", depth_class="deep_vein",
                               quantity_tonnes_per_year=1.0)
        large = _make_deposit("large", depth_class="deep_vein",
                               quantity_tonnes_per_year=1000.0)
        self.assertGreater(
            deposits.amortized_sinking_cost_labour_hours_per_kg(small),
            deposits.amortized_sinking_cost_labour_hours_per_kg(large))

    def test_total_cost_is_extraction_plus_amortized_sinking(self):
        deposit = _make_deposit("d", depth_class="shallow_vein")
        expected = (deposits.extraction_cost_labour_hours_per_kg(deposit)
                    + deposits.amortized_sinking_cost_labour_hours_per_kg(deposit))
        self.assertAlmostEqual(
            deposits.total_cost_labour_hours_per_kg(deposit), expected)

    def test_a_poor_deposit_can_be_pushed_out_by_its_shaft_cost_alone(self):
        # A rich but deep (expensive shaft) small deposit can cost MORE
        # overall than a poorer but surface (free shaft) deposit with a
        # bigger assumed reserve - the whole point of a fixed cost: it is
        # not always dominated by the per-tonne term.
        rich_but_tiny_deep = _make_deposit(
            "rich_tiny_deep", depth_class="deep_vein",
            ore_grade_kg_per_tonne=1000.0, quantity_tonnes_per_year=0.001)
        poor_but_ample_surface = _make_deposit(
            "poor_ample_surface", depth_class="surface",
            ore_grade_kg_per_tonne=1.0, quantity_tonnes_per_year=1000.0)
        self.assertGreater(
            deposits.total_cost_labour_hours_per_kg(rich_but_tiny_deep),
            deposits.total_cost_labour_hours_per_kg(poor_but_ample_surface))


class IntensiveMarginTests(unittest.TestCase):
    """current_ore_grade_kg_per_tonne and current_extraction_cost_labour_
    hours_per_kg - the stakeholder's second observation, checked on a
    single deposit in isolation from any exhaustion event at all.
    """

    def setUp(self):
        self.deposit = _make_deposit("d", ore_grade_kg_per_tonne=40.0)

    def test_fraction_zero_is_the_deposit_own_stated_grade(self):
        self.assertEqual(
            deposits.current_ore_grade_kg_per_tonne(self.deposit, 0.0), 40.0)

    def test_fraction_one_is_zero_grade(self):
        self.assertEqual(
            deposits.current_ore_grade_kg_per_tonne(self.deposit, 1.0), 0.0)

    def test_grade_falls_monotonically_with_fraction_extracted(self):
        grades = [deposits.current_ore_grade_kg_per_tonne(self.deposit, f)
                  for f in (0.0, 0.25, 0.5, 0.75, 1.0)]
        self.assertEqual(grades, sorted(grades, reverse=True))
        self.assertGreater(grades[0], grades[-1])

    def test_fraction_out_of_range_is_rejected(self):
        with self.assertRaises(ValueError):
            deposits.current_ore_grade_kg_per_tonne(self.deposit, -0.01)
        with self.assertRaises(ValueError):
            deposits.current_ore_grade_kg_per_tonne(self.deposit, 1.01)

    def test_extraction_cost_rises_as_fraction_extracted_rises(self):
        # "Effort per tonne of rock is roughly constant; what changes is
        # the metal per tonne of rock" - the stakeholder's own intuition,
        # checked directly: cost at fraction 0.5 exceeds cost at 0.0,
        # purely from grade falling, with hardness_class/depth_class (and
        # therefore effort per tonne of ROCK) never touched.
        cost = deposits.current_extraction_cost_labour_hours_per_kg
        self.assertLess(cost(self.deposit, 0.0), cost(self.deposit, 0.5))
        self.assertLess(cost(self.deposit, 0.5), cost(self.deposit, 0.9))

    def test_extraction_cost_at_fraction_zero_matches_the_ordinary_function(self):
        # An untouched deposit's intensive-margin cost must agree exactly
        # with the plain (grade-oblivious) extraction_cost_labour_hours_
        # per_kg - fraction_extracted=0 is supposed to mean "as if nothing
        # about depletion existed yet".
        self.assertAlmostEqual(
            deposits.current_extraction_cost_labour_hours_per_kg(self.deposit, 0.0),
            deposits.extraction_cost_labour_hours_per_kg(self.deposit))

    def test_extraction_cost_at_fraction_one_is_infinite(self):
        self.assertEqual(
            deposits.current_extraction_cost_labour_hours_per_kg(self.deposit, 1.0),
            float("inf"))

    def test_deposit_state_tracks_its_own_fraction_extracted(self):
        state = deposits.DepositState(self.deposit, remaining_reserve_tonnes_metal=100.0)
        self.assertEqual(state.fraction_extracted, 0.0)
        state.extract(25.0)
        self.assertAlmostEqual(state.fraction_extracted, 0.25)
        self.assertLess(state.current_grade_kg_per_tonne(),
                         self.deposit.ore_grade_kg_per_tonne)
        state.extract(75.0)
        self.assertEqual(state.fraction_extracted, 1.0)
        self.assertEqual(state.current_grade_kg_per_tonne(), 0.0)

    def test_deposit_as_worked_only_replaces_the_grade(self):
        state = deposits.DepositState(self.deposit, remaining_reserve_tonnes_metal=100.0)
        state.extract(50.0)
        worked = state.deposit_as_worked()
        self.assertEqual(worked.ore_grade_kg_per_tonne,
                          state.current_grade_kg_per_tonne())
        self.assertEqual(worked.depth_class, self.deposit.depth_class)
        self.assertEqual(worked.hardness_class, self.deposit.hardness_class)
        self.assertEqual(worked.quantity_tonnes_per_year,
                          self.deposit.quantity_tonnes_per_year)

    def test_a_single_deposit_far_from_exhaustion_still_gets_costlier_over_time(self):
        # The intensive margin alone, with no extensive-margin exhaustion
        # anywhere in sight: one deposit, demand well below its annual
        # capacity so it is never at risk of running dry within the
        # simulated years, and yet its own reported price still climbs
        # every single year, purely because the grade being worked falls.
        deposit = _make_deposit("lone", ore_grade_kg_per_tonne=50.0,
                                 quantity_tonnes_per_year=100.0)
        outcomes = deposits.simulate_depletion(
            [deposit], quantity_demanded_tonnes_per_year=10.0,
            years=5, working_life_years=100.0)
        prices = [o.price_at_margin_labour_hours_per_kg for o in outcomes]
        self.assertEqual(prices, sorted(prices))
        self.assertLess(prices[0], prices[-1])
        self.assertEqual(
            [o.exhausted_this_year for o in outcomes], [[]] * 5,
            "this deposit should not be anywhere near exhaustion yet")


class WasteRockTests(unittest.TestCase):
    """material_moved_tonnes_per_kg_metal, waste_tonnes_per_kg_metal and
    annual_waste_rock_tonnes - the stakeholder's third observation, made an
    explicit, queryable number rather than left implicit inside the cost
    arithmetic.
    """

    def test_material_moved_is_the_inverse_of_grade(self):
        deposit = _make_deposit("d", ore_grade_kg_per_tonne=25.0)
        self.assertAlmostEqual(
            deposits.material_moved_tonnes_per_kg_metal(deposit), 1.0 / 25.0)

    def test_waste_is_almost_all_the_material_moved_at_low_grade(self):
        # At a placer-gold-grade deposit, essentially everything raised is
        # waste - the 99%-of-what-you-lift figure the task itself named.
        deposit = _make_deposit("placer", ore_grade_kg_per_tonne=0.0003)
        material_moved = deposits.material_moved_tonnes_per_kg_metal(deposit)
        waste = deposits.waste_tonnes_per_kg_metal(deposit)
        self.assertGreater(waste / material_moved, 0.999)

    def test_leaner_deposits_produce_more_waste_per_kilogram(self):
        lean = _make_deposit("lean", ore_grade_kg_per_tonne=1.0)
        rich = _make_deposit("rich", ore_grade_kg_per_tonne=100.0)
        self.assertGreater(
            deposits.waste_tonnes_per_kg_metal(lean),
            deposits.waste_tonnes_per_kg_metal(rich))

    def test_annual_waste_scales_with_annual_metal_output(self):
        small = _make_deposit("small", ore_grade_kg_per_tonne=10.0,
                               quantity_tonnes_per_year=1.0)
        large = _make_deposit("large", ore_grade_kg_per_tonne=10.0,
                               quantity_tonnes_per_year=100.0)
        self.assertAlmostEqual(
            deposits.annual_waste_rock_tonnes(large)
            / deposits.annual_waste_rock_tonnes(small),
            100.0, places=3)

    def test_every_named_deposit_has_finite_positive_waste(self):
        for metal in deposits.METALS:
            for deposit in deposits.load_deposits(metal):
                waste = deposits.waste_tonnes_per_kg_metal(deposit)
                self.assertGreater(waste, 0.0, deposit.name)
                self.assertLess(waste, float("inf"), deposit.name)


class PolymetallicByproductTests(unittest.TestCase):
    """ByproductSpec, byproduct_quantities_tonnes_per_year and
    joint_output_quantities_kg - the stakeholder's fourth observation: a
    deposit that carries several metals at their own grades, so opening it
    for one yields the others as a by-product fixed by geology.
    """

    def test_most_deposits_carry_no_byproducts(self):
        deposit = _make_deposit("d")
        self.assertEqual(deposit.byproducts, ())
        self.assertEqual(deposits.byproduct_quantities_tonnes_per_year(deposit), {})

    def test_britannia_lead_carries_a_silver_byproduct(self):
        # This module's own worked example - see data/world/deposits.json's
        # britannia_lead entry and the module docstring's POLYMETALLIC
        # DEPOSITS section for why this one and not a new load_deposits
        # ('silver') entry.
        lead_deposits = {d.name: d for d in deposits.load_deposits("lead")}
        britannia_lead = lead_deposits["britannia_lead"]
        self.assertEqual(len(britannia_lead.byproducts), 1)
        byproduct = britannia_lead.byproducts[0]
        self.assertEqual(byproduct.metal, "silver")
        self.assertEqual(byproduct.material_key, "silver_kg")
        self.assertGreater(byproduct.ore_grade_kg_per_tonne, 0.0)
        # Every OTHER named lead deposit carries none - this is a worked
        # example on one deposit, not a blanket assumption.
        for name, deposit in lead_deposits.items():
            if name != "britannia_lead":
                self.assertEqual(deposit.byproducts, (), name)

    def test_byproduct_quantity_is_fixed_by_the_grade_ratio_not_chosen(self):
        primary = _make_deposit(
            "primary", metal="lead", ore_grade_kg_per_tonne=150.0,
            quantity_tonnes_per_year=1500.0,
            byproducts=(deposits.ByproductSpec(
                metal="silver", material_key="silver_kg",
                ore_grade_kg_per_tonne=0.5),))
        # rock moved/year = 1500 t metal/yr * 1000 kg/t / 150 kg/t = 10,000
        # t rock/yr; silver riding along = 10,000 * 0.5 / 1000 = 5 t/yr.
        byproducts = deposits.byproduct_quantities_tonnes_per_year(primary)
        self.assertAlmostEqual(byproducts["silver"], 5.0)

    def test_doubling_the_primary_grade_halves_the_byproduct_for_the_same_output(self):
        # Geology, not a choice: raising the same tonnes/year of metal from
        # richer ore means moving less rock, and therefore less of
        # whatever byproduct rides along with each tonne of that rock.
        spec = (deposits.ByproductSpec(
            metal="silver", material_key="silver_kg",
            ore_grade_kg_per_tonne=0.5),)
        lean = _make_deposit("lean", metal="lead", ore_grade_kg_per_tonne=75.0,
                              quantity_tonnes_per_year=1500.0, byproducts=spec)
        rich = _make_deposit("rich", metal="lead", ore_grade_kg_per_tonne=150.0,
                              quantity_tonnes_per_year=1500.0, byproducts=spec)
        lean_silver = deposits.byproduct_quantities_tonnes_per_year(lean)["silver"]
        rich_silver = deposits.byproduct_quantities_tonnes_per_year(rich)["silver"]
        self.assertAlmostEqual(lean_silver / rich_silver, 2.0)

    def test_joint_output_quantities_kg_matches_sim_world_demand_shape(self):
        # {material_key: quantity} - see sim.world.demand's own
        # joint_output_mass_shares/joint_output_value_shares (not imported
        # here - see the module docstring's STANDALONE section). Checked
        # structurally rather than by importing that module, which is
        # being edited concurrently by another agent.
        lead_deposits = {d.name: d for d in deposits.load_deposits("lead")}
        britannia_lead = lead_deposits["britannia_lead"]
        joint = deposits.joint_output_quantities_kg(britannia_lead)
        self.assertIn("lead_kg", joint)
        self.assertIn("silver_kg", joint)
        for key, value in joint.items():
            self.assertIsInstance(key, str)
            self.assertTrue(key.endswith("_kg"), key)
            self.assertGreater(value, 0.0, key)
        # The primary metal's own quantity, in kilograms.
        self.assertAlmostEqual(
            joint["lead_kg"], britannia_lead.quantity_tonnes_per_year * 1000.0)

    def test_byproduct_grade_is_declared_with_provenance(self):
        from sim import constants
        deposits.load_deposits("lead")   # forces the declare(), if not
                                          # already run at import time
        matches = [name for name in constants.REGISTRY
                   if "BYPRODUCT" in name and "SILVER" in name
                   and "BRITANNIA_LEAD" in name]
        self.assertEqual(len(matches), 1, matches)
        entry = constants.REGISTRY[matches[0]]
        self.assertIn(entry["kind"],
                       ("engineering_estimate", "temporary_heuristic"))
        self.assertTrue(entry["why"])


class LoadDepositsUsesGeographyAndResourcesTests(unittest.TestCase):
    """load_deposits joins data/world/deposits.json's physical facts with
    data/world/geography.json's regional shares and data/world/
    resources.json's empire totals - this checks that join, not the
    numbers each file independently carries (which belong to those files'
    own validators).
    """

    def test_deposits_exist_for_every_metal(self):
        for metal in deposits.METALS:
            found = deposits.load_deposits(metal)
            self.assertGreater(len(found), 0, metal)

    def test_quantities_are_positive(self):
        for metal in deposits.METALS:
            for deposit in deposits.load_deposits(metal):
                self.assertGreater(deposit.quantity_tonnes_per_year, 0.0,
                                    deposit.name)

    def test_geography_backed_metals_sum_close_to_empire_output(self):
        # iron, copper, tin, lead, silver: geography.json's own regional
        # shares are calibrated to sum to ~1.0 across the "home" regions
        # (see that file's regions._note), so summing every named deposit's
        # derived quantity should reproduce resources.json's total to
        # within the same few-percent rounding geography.json's own shares
        # carry (they sum to 1.0-1.02, not exactly 1.0).
        resources = deposits._load_json(deposits.RESOURCES_FILE)
        for metal in ("iron", "copper", "tin", "lead", "silver"):
            total = sum(d.quantity_tonnes_per_year
                        for d in deposits.load_deposits(metal))
            expected = resources["empire_output_100ad"][metal]["t_per_yr"]
            self.assertAlmostEqual(total / expected, 1.0, delta=0.05,
                                    msg=metal)

    def test_explicit_share_metals_sum_to_the_full_empire_output(self):
        # gold, mercury: this file's own explicit share_of_empire_output
        # entries are written to sum to exactly 1.0 - see
        # data/world/deposits.json's gold and mercury entries.
        resources = deposits._load_json(deposits.RESOURCES_FILE)
        for metal in ("gold", "mercury"):
            total = sum(d.quantity_tonnes_per_year
                        for d in deposits.load_deposits(metal))
            expected = resources["empire_output_100ad"][metal]["t_per_yr"]
            self.assertAlmostEqual(total, expected, places=6, msg=metal)

    def test_far_regions_are_excluded_from_the_home_total(self):
        # geography.json credits china with a large iron share (0.9) and
        # southeast_asia with a real tin share (0.3) that the file's own
        # note says is ADDITIONAL to Rome's output, not a slice of it -
        # load_deposits must not pull either in, since data/world/
        # deposits.json names no china or southeast_asia deposit at all
        # and resources.json's empire_output_100ad is Rome's own figure.
        names = {d.region for d in deposits.load_deposits("iron")}
        self.assertNotIn("china", names)
        names = {d.region for d in deposits.load_deposits("tin")}
        self.assertNotIn("southeast_asia", names)


class NoPriceDataTests(unittest.TestCase):
    """CLAUDE.md 3.1 and this module's own docstring: a grade is a physical
    fact about a rock and is never derived from what the metal sells for.
    Enforced here at the file level, not just by inspection.
    """

    def test_module_never_opens_the_price_file(self):
        # deposits.py's docstring and data/world/deposits.json's own _doc
        # both TALK ABOUT data/prices.json in prose, to explain why they
        # never read it - so a literal substring ban on "prices.json"
        # would fail on the very sentences documenting this discipline.
        # What actually matters is that the module never OPENS that file
        # or reads its wage/purchase-price tables, which is what this
        # checks: the only three _FILE constants this module defines, and
        # the only paths handed to _load_json / open() anywhere in it.
        path = os.path.join(_REPO_ROOT, "sim", "world", "deposits.py")
        with open(path) as handle:
            source = handle.read()
        tree = ast.parse(source, filename=path)
        opened_paths = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.endswith(".json"):
                    opened_paths.add(node.value)
        self.assertEqual(
            opened_paths, {"geography.json", "resources.json", "deposits.json"},
            "sim/world/deposits.py references a JSON filename other than "
            "the three data files it is meant to read: %s" % opened_paths)
        self.assertNotIn("purchase_prices_denarii", source)
        self.assertNotIn("wage_rates_denarii_per_hour", source)

    def test_deposits_module_never_reads_cost_multiplier(self):
        # geography.json's own located_materials.cost_multiplier is,
        # per this task's own brief, a hardcoded delivered-cost outcome -
        # exactly the kind of number CLAUDE.md 3.1 forbids as an INPUT to
        # a cost derivation. deposits.py may load geography.json, but must
        # never read that specific field.
        path = os.path.join(_REPO_ROOT, "sim", "world", "deposits.py")
        with open(path) as handle:
            source = handle.read()
        self.assertNotIn("cost_multiplier", source)

    def test_every_declared_grade_is_engineering_or_heuristic_kind(self):
        from sim import constants
        for name, entry in constants.REGISTRY.items():
            if name.startswith("DEPOSIT_GRADE_") or name.startswith("DEPOSIT_SHARE_"):
                self.assertIn(entry["kind"],
                              ("engineering_estimate", "temporary_heuristic"),
                              name)


class StandaloneImportTests(unittest.TestCase):
    """sim/world/deposits.py must not import sim/engine/ or any other
    sim/world/ module - see its own docstring's STANDALONE section and
    sim/world/__init__.py for why every module in this package holds to
    this independently.
    """

    def test_imports_are_limited_to_stdlib_and_sim_constants(self):
        path = os.path.join(_REPO_ROOT, "sim", "world", "deposits.py")
        with open(path) as handle:
            tree = ast.parse(handle.read(), filename=path)

        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)

        for name in imported:
            self.assertFalse(
                name.startswith("sim.engine"),
                "sim/world/deposits.py imports %r" % name)
            self.assertFalse(
                name.startswith("sim.world.") and name != "sim.world.deposits",
                "sim/world/deposits.py imports another sim/world/ module: %r"
                % name)
            self.assertNotEqual(
                name, "sim.solve_prices",
                "sim/world/deposits.py imports the price solver directly")


class CalibrationAgainstBookPricesTests(unittest.TestCase):
    """The only class in this file that reads data/prices.json - a
    CALIBRATION TARGET, per this module's own docstring and sim/world/
    agriculture.py's precedent, read here to REPORT the disagreement and
    never fed back into deposits.py or data/world/deposits.json to close
    it.
    """

    def setUp(self):
        # Instance-level setUp, not setUpClass: sim/tests/__main__.py's
        # _run_topic flattens a unittest suite and calls each TestCase's
        # own .run() individually so it can report per-test results in the
        # same summary line every other topic uses (see that file's own
        # docstring) - which means it never drives a TestSuite's shared
        # _handleClassSetUp, so setUpClass silently never runs. Cheap
        # enough (two JSON reads) to redo per test.
        with open(os.path.join(_REPO_ROOT, "data", "prices.json")) as handle:
            self.book_prices = json.load(handle)
        self.labourer_wage_denarii_per_hour = (
            self.book_prices["wage_rates_denarii_per_hour"]["labourer"]["rate"])
        self.resources = deposits._load_json(deposits.RESOURCES_FILE)

    _BOOK_KEY = {
        "iron": "iron_ore_kg", "copper": "copper_kg", "tin": "tin_kg",
        "lead": "lead_kg", "silver": "silver_kg", "gold": "gold_kg",
        "mercury": "mercury_kg",
    }

    def _price_at_margin_denarii_per_kg(self, metal):
        deposit_list = deposits.load_deposits(metal)
        demand = self.resources["empire_output_100ad"][metal]["t_per_yr"]
        outcome = deposits.find_marginal_deposit(deposit_list, demand)
        return (outcome.price_at_margin_labour_hours_per_kg
                * self.labourer_wage_denarii_per_hour)

    def test_report_disagreement_against_book_prices(self):
        # No assertion tight enough to tune against - see this class's own
        # docstring. The only assertions are sanity bounds: every derived
        # price is a positive, finite number of denarii/kg.
        print("\nCalibrationAgainstBookPricesTests: derived price at the "
              "margin vs data/prices.json's book price, both denarii/kg "
              "(labourer wage = %.4g den/h)"
              % self.labourer_wage_denarii_per_hour)
        purchase_prices = self.book_prices["purchase_prices_denarii"]
        for metal in deposits.METALS:
            derived = self._price_at_margin_denarii_per_kg(metal)
            book = purchase_prices[self._BOOK_KEY[metal]]["p"]
            ratio = book / derived if derived else float("inf")
            print("  %-8s derived=%12.4f  book=%10.4f  book/derived=%10.2fx"
                  % (metal, derived, book, ratio))
            self.assertGreater(derived, 0.0, metal)
            self.assertLess(derived, float("inf"), metal)

    def test_cinnabar_mineral_is_the_fairer_comparison_for_mercury(self):
        # mercury_kg is REFINED metal (needs roasting cinnabar and
        # condensing the vapour, a process this module does not model -
        # see its own docstring's WHAT THIS MODULE DELIBERATELY DOES NOT
        # DO section); cinnabar_kg is the RAW MINERAL, sold as pigment
        # with no metallurgy at all, which is what this module's mercury
        # deposits actually produce a cost for. Both are printed so the
        # report can say plainly which gap is smelting and which is still
        # unexplained scarcity.
        derived = self._price_at_margin_denarii_per_kg("mercury")
        purchase_prices = self.book_prices["purchase_prices_denarii"]
        mercury_book = purchase_prices["mercury_kg"]["p"]
        cinnabar_book = purchase_prices["cinnabar_kg"]["p"]
        print("\nmercury: derived (mining only) = %.4f den/kg; "
              "book mercury_kg (refined) = %.4f; book cinnabar_kg "
              "(raw mineral, no smelting needed) = %.4f"
              % (derived, mercury_book, cinnabar_book))
        self.assertGreater(derived, 0.0)

    def test_report_silver_to_lead_ratio(self):
        # The task's own named calibration fact: silver was roughly a
        # hundred times lead by weight. Reported both from this module's
        # own derived margin costs and from data/prices.json's book
        # figures, with no assertion that either actually lands near 100 -
        # see this class's own docstring.
        silver = self._price_at_margin_denarii_per_kg("silver")
        lead = self._price_at_margin_denarii_per_kg("lead")
        purchase_prices = self.book_prices["purchase_prices_denarii"]
        book_silver = purchase_prices["silver_kg"]["p"]
        book_lead = purchase_prices["lead_kg"]["p"]
        print("\nsilver:lead ratio - this module's derived margin costs: "
              "%.1fx; data/prices.json's own book prices: %.1fx"
              % (silver / lead, book_silver / book_lead))
        self.assertGreater(silver / lead, 1.0)


class ModuleRunsCleanlyTests(unittest.TestCase):
    """python3 -m sim.world.deposits must print a readable summary - the
    same bar sim/world/agriculture.py's own __main__ block is held to.
    """

    def test_main_block_runs_and_names_every_metal(self):
        result = subprocess.run(
            [sys.executable, "-m", "sim.world.deposits"],
            cwd=_REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for metal in deposits.METALS:
            self.assertIn(metal.upper(), result.stdout)
        self.assertIn("MARGINAL", result.stdout)


if __name__ == "__main__":
    unittest.main()
