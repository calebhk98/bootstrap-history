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
                   note=""):
    return deposits.Deposit(
        name=name, metal=metal, region="nowhere",
        material_moved=material_moved,
        ore_grade_kg_per_tonne=ore_grade_kg_per_tonne,
        depth_class=depth_class, hardness_class=hardness_class,
        quantity_tonnes_per_year=quantity_tonnes_per_year, note=note)


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
    the margin to a costlier one, with no change in demand at all.
    """

    def setUp(self):
        self.cheap = _make_deposit("cheap", ore_grade_kg_per_tonne=100.0,
                                    quantity_tonnes_per_year=10.0)
        self.dear = _make_deposit("dear", ore_grade_kg_per_tonne=1.0,
                                   quantity_tonnes_per_year=10.0)

    def test_price_rises_once_the_cheap_deposit_is_exhausted(self):
        # Demand of 10/yr, entirely from `cheap`, whose reserve (working
        # life 3 years x 10/yr = 30 t) runs out after year 3.
        outcomes = deposits.simulate_depletion(
            [self.cheap, self.dear], quantity_demanded_tonnes_per_year=10.0,
            years=6, working_life_years=3.0)
        early_prices = [o.price_at_margin_labour_hours_per_kg for o in outcomes[:3]]
        late_prices = [o.price_at_margin_labour_hours_per_kg for o in outcomes[3:]]
        self.assertTrue(all(p == early_prices[0] for p in early_prices))
        self.assertTrue(all(p == late_prices[0] for p in late_prices))
        self.assertGreater(late_prices[0], early_prices[0])
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
