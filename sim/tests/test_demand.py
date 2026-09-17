"""Regression tests for sim/world/demand.py.

Written as unittest.TestCase classes, like sim/tests/test_agriculture.py
and sim/tests/test_deposits.py: this module has no dependency on
sim/engine/, sim/solve_prices.py, or any other sim/world/ module (see
demand.py's own STANDALONE section), so importing sim/tests/harness.py
would pull in the whole engine for no reason. sim/tests/__main__.py's
_run_topic already runs both styles identically.

CalibrationAgainstHistoricalTargetsTests is the one class that reads
data/prices.json - the CALIBRATION TARGETS demand.py's own docstring
promises are read only by tests, never by the module's own functions (see
sim/world/agriculture.py's and sim/world/deposits.py's own precedent for
the same discipline). It reports the disagreement; it never asserts a
tolerance tight enough to tempt anyone into retuning a marginal budget
share or the Gini coefficient to close it.
"""
import ast
import json
import os
import subprocess
import sys
import unittest

from sim.world import demand

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


class IncomeDistributionTests(unittest.TestCase):
    """income_bins() turns one inequality parameter into a population of
    income classes - these checks are on the DISTRIBUTION's properties
    (it conserves population and total income exactly, richer bins really
    are richer, more inequality really does concentrate more income at
    the top), not on any particular number it produces.
    """

    def test_bins_conserve_total_population(self):
        bins = demand.income_bins(1000.0, 500.0, gini=0.4, num_bins=10)
        self.assertAlmostEqual(demand.total_population(bins), 1000.0, places=6)

    def test_bins_conserve_total_income_exactly(self):
        # Each bin's income is the ANALYTICALLY EXACT conditional mean of
        # its population slice (see _pareto_bin_mean_multiple_of_scale's
        # own docstring), so this must hold to floating-point precision
        # for ANY num_bins, not just approximately for a large one.
        for num_bins in (1, 2, 5, 20, 97):
            bins = demand.income_bins(1_000_000.0, 500.0, gini=0.4, num_bins=num_bins)
            self.assertAlmostEqual(
                demand.total_income(bins), 1_000_000.0 * 500.0,
                delta=1.0, msg="num_bins=%d" % num_bins)

    def test_bins_are_sorted_richest_first_and_strictly_decreasing(self):
        bins = demand.income_bins(1000.0, 500.0, gini=0.4, num_bins=10)
        incomes = [income_bin.income_per_capita_per_year for income_bin in bins]
        self.assertEqual(incomes, sorted(incomes, reverse=True))
        for richer_income, poorer_income in zip(incomes, incomes[1:]):
            self.assertGreater(richer_income, poorer_income)

    def test_more_inequality_makes_the_top_bin_richer(self):
        equal_ish = demand.income_bins(1000.0, 500.0, gini=0.15, num_bins=10)
        unequal = demand.income_bins(1000.0, 500.0, gini=0.6, num_bins=10)
        self.assertGreater(unequal[0].income_per_capita_per_year,
                            equal_ish[0].income_per_capita_per_year)
        self.assertLess(unequal[-1].income_per_capita_per_year,
                         equal_ish[-1].income_per_capita_per_year)

    def test_near_zero_gini_gives_much_less_spread_than_realistic_gini(self):
        near_equal = demand.income_bins(1000.0, 500.0, gini=0.01, num_bins=10)
        realistic = demand.income_bins(1000.0, 500.0, gini=0.4, num_bins=10)
        spread = lambda bins: (bins[0].income_per_capita_per_year
                                - bins[-1].income_per_capita_per_year)
        self.assertLess(spread(near_equal), 0.1 * spread(realistic))

    def test_rejects_bad_gini(self):
        with self.assertRaises(ValueError):
            demand.income_bins(1000.0, 500.0, gini=0.0, num_bins=10)
        with self.assertRaises(ValueError):
            demand.income_bins(1000.0, 500.0, gini=1.0, num_bins=10)


class HouseholdDemandShapeTests(unittest.TestCase):
    """The Stone-Geary properties the task itself asks for: demand falls
    as price rises, and a necessity (positive subsistence floor) falls
    LESS than a luxury (subsistence floor of zero) for the same price
    change - see demand.py's own HOUSEHOLD DEMAND section for why this
    falls out of the algebra rather than being asserted with two
    different elasticities.
    """

    def setUp(self):
        self.basket = demand.DEFAULT_BASKET
        self.income = 1000.0

    def _quantity(self, good, price, other_price=1.0):
        prices = {basket_good.name: other_price for basket_good in self.basket}
        prices[good.name] = price
        return demand.household_quantity_demanded_per_capita(
            good, prices, self.income, self.basket)

    def test_demand_falls_as_own_price_rises(self):
        for good in self.basket:
            low_price_qty = self._quantity(good, 1.0)
            high_price_qty = self._quantity(good, 2.0)
            self.assertGreater(low_price_qty, high_price_qty, good.name)

    def test_necessity_is_less_elastic_than_luxury(self):
        # Percentage fall in quantity for the same percentage rise in
        # price, food (positive subsistence floor) against silver
        # (subsistence floor of zero) at the same income and same
        # starting price.
        def pct_fall(good):
            quantity_before = self._quantity(good, 1.0)
            quantity_after = self._quantity(good, 1.5)
            return (quantity_before - quantity_after) / quantity_before

        food_fall = pct_fall(demand.FOOD)
        silver_fall = pct_fall(demand.SILVER)
        self.assertLess(food_fall, silver_fall)

    def test_silver_demand_is_unit_elastic_in_expenditure(self):
        # A good with a subsistence floor of zero spends a CONSTANT
        # surplus expenditure share regardless of price - price times
        # quantity should be invariant to price for SILVER specifically
        # (see market_clearing_price's own docstring for the closed form
        # this is a special case of).
        expenditure_at = [price * self._quantity(demand.SILVER, price)
                           for price in (0.5, 1.0, 3.0, 10.0)]
        for value in expenditure_at[1:]:
            self.assertAlmostEqual(value, expenditure_at[0], delta=1e-6)

    def test_below_subsistence_household_gets_scaled_down_floor_not_negative(self):
        basket = demand.DEFAULT_BASKET
        prices = {basket_good.name: 10.0 for basket_good in basket}
        # income far below what even the food floor costs at this price
        poor_income = 1.0
        quantity = demand.household_quantity_demanded_per_capita(
            demand.FOOD, prices, poor_income, basket)
        self.assertGreaterEqual(quantity, 0.0)
        self.assertLess(quantity, demand.FOOD.subsistence_quantity_per_capita_per_year)

    def test_basket_must_sum_shares_to_one(self):
        bad_basket = (
            demand.Good("first_good", 0.0, 0.5),
            demand.Good("second_good", 0.0, 0.6),
        )
        with self.assertRaises(ValueError):
            demand.validate_basket(bad_basket)


class AggregateDemandAndInequalityTests(unittest.TestCase):
    """Household demand aggregated over an unequal population, and why
    the inequality parameter is load-bearing rather than decorative -
    silver's demand should come overwhelmingly from the population's
    surplus-holding top, not spread evenly.
    """

    def test_top_bin_buys_far_more_silver_per_capita_than_bottom_bin(self):
        bins = demand.income_bins(1_000_000.0, 500.0, gini=0.45, num_bins=10)
        prices = {"wheat_kg": 0.3, "manufactures": 1.0, "silver_kg": 50.0}
        richest, poorest = bins[0], bins[-1]
        rich_qty = demand.household_quantity_demanded_per_capita(
            demand.SILVER, prices, richest.income_per_capita_per_year,
            demand.DEFAULT_BASKET)
        poor_qty = demand.household_quantity_demanded_per_capita(
            demand.SILVER, prices, poorest.income_per_capita_per_year,
            demand.DEFAULT_BASKET)
        self.assertGreater(rich_qty, poor_qty)

    def test_inequality_shape_moves_who_buys_not_the_aggregate_clearing_price(self):
        # Same population, same mean income, same fixed silver supply -
        # only the distribution's SHAPE changes. This is a real, slightly
        # counter-intuitive property of the linear (Stone-Geary) demand
        # system, not a bug: as long as every bin's surplus stays
        # positive, aggregate demand for a good with no subsistence floor
        # depends only on TOTAL income and TOTAL population (see
        # market_clearing_price's own closed-form derivation,
        # floor_quantity + surplus_income_available / price, where
        # surplus_income_available is built from totals alone) -
        # inequality changes WHO holds the surplus, which
        # test_top_bin_buys_far_more_silver_per_capita_than_bottom_bin
        # above is what actually isolates, but not how much AGGREGATE
        # surplus exists to chase a fixed quantity of silver at the
        # market level. This is worth stating plainly rather than
        # silently assuming the opposite: inequality's real effect in
        # this model is on concentration and on which bins can afford
        # the good at all once some fall below subsistence (see
        # HouseholdDemandShapeTests' below-subsistence test), not on the
        # aggregate price for a population that can all afford its own
        # necessities.
        population, mean_income, supply = 1_000_000.0, 500.0, 10.0
        other_prices = {"wheat_kg": 0.3, "manufactures": 1.0}
        unequal_bins = demand.income_bins(population, mean_income, gini=0.55)
        equal_bins = demand.income_bins(population, mean_income, gini=0.15)
        price_unequal = demand.market_clearing_price(
            demand.SILVER, supply, other_prices, unequal_bins, demand.DEFAULT_BASKET)
        price_equal = demand.market_clearing_price(
            demand.SILVER, supply, other_prices, equal_bins, demand.DEFAULT_BASKET)
        self.assertAlmostEqual(price_unequal, price_equal, delta=1e-6)


class ClosedFormMatchesDirectSummationTests(unittest.TestCase):
    """market_clearing_price's closed form (see its own module-docstring
    derivation) must agree with a plain per-bin sum of the Stone-Geary
    formula, to floating-point precision - this is the check that the
    algebra in the docstring is the algebra in the code.
    """

    def test_closed_form_price_reproduces_the_target_quantity_by_direct_sum(self):
        bins = demand.income_bins(2_000_000.0, 400.0, gini=0.42, num_bins=15)
        other_prices = {"wheat_kg": 0.28, "manufactures": 1.2}
        target_quantity = 5000.0
        price = demand.market_clearing_price(
            demand.SILVER, target_quantity, other_prices, bins, demand.DEFAULT_BASKET)

        full_prices = dict(other_prices, silver_kg=price)
        direct_quantity = demand.aggregate_household_demand(
            demand.SILVER, full_prices, bins, demand.DEFAULT_BASKET)
        self.assertAlmostEqual(direct_quantity, target_quantity, delta=1e-3)

    def test_raises_when_quantity_is_below_the_price_insensitive_floor(self):
        bins = demand.income_bins(1000.0, 500.0, gini=0.4)
        other_prices = {"manufactures": 1.0, "silver_kg": 1.0}
        # FOOD has a positive subsistence floor, so it has a positive
        # floor quantity (population times its subsistence floor times
        # (1 minus its marginal budget share)); asking for less than that
        # floor cannot be cleared by demand.
        with self.assertRaises(ValueError):
            demand.market_clearing_price(
                demand.FOOD, 1.0, other_prices, bins, demand.DEFAULT_BASKET)


class DerivedDemandTests(unittest.TestCase):
    """The producer/derived-demand side: input coefficients read straight
    out of data/production/*.json, and the intermediate quantity demanded
    scaling exactly with whatever output level a caller says is planned -
    the concrete mechanism behind "an industrial base is its own customer".
    """

    def test_lead_kg_is_its_own_dominant_output(self):
        # lead_kg's own entry outputs both lead_kg (1000) and silver_kg
        # (0.46) - lead is overwhelmingly dominant by mass, so recipe
        # inputs should be read as "per kg of lead", not "per kg of
        # anything else".
        production = demand.production_data()
        entry = production["lead_kg"]
        self.assertEqual(demand._dominant_output_key(entry), "lead_kg")

    def test_zinc_electrolytic_dominant_output_is_zinc_not_the_trace_byproducts(self):
        # The sharpest case in the data: an entry named after a PROCESS
        # (zinc_electrolytic_kg) whose own key never appears in its own
        # outputs at all - see input_coefficients_per_unit_output's own
        # docstring.
        production = demand.production_data()
        entry = production["zinc_electrolytic_kg"]
        self.assertNotIn("zinc_electrolytic_kg", entry["outputs"])
        self.assertEqual(demand._dominant_output_key(entry), "zinc_kg")

    def test_input_coefficients_scale_linearly_with_output_level(self):
        coefficients = demand.input_coefficients_per_unit_output("lead_kg")
        total_10, _ = demand.derived_intermediate_demand(
            "galena_kg", {"lead_kg": 10.0})
        total_20, _ = demand.derived_intermediate_demand(
            "galena_kg", {"lead_kg": 20.0})
        self.assertAlmostEqual(total_20, 2.0 * total_10, delta=1e-9)
        self.assertAlmostEqual(total_10, coefficients["galena_kg"] * 10.0, delta=1e-9)

    def test_derived_demand_is_zero_when_nothing_is_planned(self):
        total, by_recipe = demand.derived_intermediate_demand("galena_kg", {})
        self.assertEqual(total, 0.0)
        self.assertEqual(by_recipe, {})

    def test_industrial_base_is_its_own_customer_for_intermediate_goods(self):
        # The concrete test of the stakeholder's own argument (Complaints/
        # 35 SS4) for the half of it this module CAN represent: deciding to
        # run more zinc_electrolytic_kg and sulfuric_acid_kg (both real
        # downstream consumers of lead_kg's capital build) creates real,
        # non-hardcoded demand for lead - it is not zero, and it grows
        # with the planned output level, with no number invented for this
        # test beyond the output levels themselves.
        consumers = demand.consumers_of("lead_kg")
        self.assertIn("zinc_electrolytic_kg", consumers)
        self.assertIn("sulfuric_acid_kg", consumers)
        modest_plan = {consumer: 1000.0 for consumer in consumers}
        larger_plan = {consumer: 100_000.0 for consumer in consumers}
        modest_demand, _ = demand.derived_intermediate_demand("lead_kg", modest_plan)
        larger_demand, breakdown = demand.derived_intermediate_demand(
            "lead_kg", larger_plan)
        self.assertGreater(modest_demand, 0.0)
        self.assertGreater(larger_demand, modest_demand)
        for consumer in consumers:
            self.assertIn(consumer, breakdown)


class JointOutputValueShareTests(unittest.TestCase):
    """joint_output_value_shares is the actual Complaints/29 deliverable:
    a split that is NOT a mass split whenever the two outputs' prices
    differ - see joint_output_mass_shares' own docstring for the split
    it replaces.
    """

    def test_equal_prices_reduce_value_share_to_mass_share(self):
        outputs = {"lead_kg": 1000.0, "silver_kg": 0.46}
        equal_prices = {"lead_kg": 2.0, "silver_kg": 2.0}
        value_shares = demand.joint_output_value_shares(outputs, equal_prices)
        mass_shares = demand.joint_output_mass_shares(outputs)
        for key in outputs:
            self.assertAlmostEqual(value_shares[key], mass_shares[key], places=9)

    def test_a_much_higher_silver_price_gives_silver_most_of_the_value_despite_tiny_mass(self):
        outputs = {"lead_kg": 1000.0, "silver_kg": 0.46}
        prices = {"lead_kg": 0.14, "silver_kg": 4000.0}
        shares = demand.joint_output_value_shares(outputs, prices)
        mass_shares = demand.joint_output_mass_shares(outputs)
        self.assertGreater(shares["silver_kg"], mass_shares["silver_kg"])
        self.assertGreater(shares["silver_kg"], shares["lead_kg"])

    def test_shares_sum_to_one_and_missing_price_raises(self):
        outputs = {"lead_kg": 1000.0, "silver_kg": 0.46}
        shares = demand.joint_output_value_shares(outputs, {"lead_kg": 1.0, "silver_kg": 5.0})
        self.assertAlmostEqual(sum(shares.values()), 1.0, places=9)
        with self.assertRaises(KeyError):
            demand.joint_output_value_shares(outputs, {"lead_kg": 1.0})

    def test_value_shares_for_recipe_reads_outputs_from_production_data(self):
        shares = demand.joint_output_value_shares_for_recipe(
            "lead_kg", {"lead_kg": 0.14, "silver_kg": 4000.0})
        self.assertIn("silver_kg", shares)
        self.assertIn("lead_kg", shares)


class NoBookPriceHardcodeTests(unittest.TestCase):
    """CLAUDE.md 3.1 and the task's own explicit warning: no demand
    parameter may be set so a computed price matches data/prices.json,
    which would be undetectable inside a demand model precisely because
    it never reads that file. Enforced at the file level, not just by
    inspection.
    """

    def test_module_never_opens_the_price_file(self):
        # demand.py's docstring and its SILVER_TO_LEAD_PRICE_RATIO_HISTORICAL
        # declaration both TALK ABOUT data/prices.json in prose (to explain
        # why the ratio it states should not be expected to match that
        # file's own book ratio exactly) - see sim/world/deposits.py's own
        # NoPriceDataTests for the identical situation there. What actually
        # matters is that the module never OPENS that file or reads its
        # wage/purchase-price tables, which is what this checks: the only
        # JSON filenames it ever opens as a literal.
        path = os.path.join(_REPO_ROOT, "sim", "world", "demand.py")
        with open(path) as handle:
            source = handle.read()
        tree = ast.parse(source, filename=path)
        opened_paths = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.endswith(".json") and node.value != ".json":
                    opened_paths.add(node.value)
        self.assertEqual(
            opened_paths, {"resources.json"},
            "sim/world/demand.py references a JSON filename other than "
            "resources.json (its own __main__ illustrative-scale source, "
            "same as sim/world/deposits.py's precedent): %s" % opened_paths)
        # data/prices.json is never one of the files ABOVE, so its
        # wage/purchase-price tables cannot be read regardless of what the
        # docstring prose says about it - a subscript check on top of the
        # opened-files check would only be checking the same fact twice.

    def test_surplus_budget_shares_are_declared_as_temporary_heuristic_not_calibrated(self):
        from sim import constants
        for name in ("FOOD_SURPLUS_BUDGET_SHARE", "MANUFACTURES_SURPLUS_BUDGET_SHARE",
                     "SILVER_SURPLUS_BUDGET_SHARE", "GINI_COEFFICIENT_PREINDUSTRIAL_AGRARIAN"):
            self.assertEqual(constants.REGISTRY[name]["kind"], "temporary_heuristic", name)


class StandaloneImportTests(unittest.TestCase):
    """sim/world/demand.py must not import sim/engine/, sim/solve_prices.py,
    or any other sim/world/ module - see its own docstring's STANDALONE
    section and sim/world/__init__.py for why every module in this package
    holds to this independently.
    """

    def test_imports_are_limited_to_stdlib_and_sim_constants(self):
        path = os.path.join(_REPO_ROOT, "sim", "world", "demand.py")
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
                "sim/world/demand.py imports %r" % name)
            self.assertFalse(
                name.startswith("sim.world.") and name != "sim.world.demand",
                "sim/world/demand.py imports another sim/world/ module: %r" % name)
            self.assertNotEqual(
                name, "sim.solve_prices",
                "sim/world/demand.py imports the price solver directly")


class CalibrationAgainstHistoricalTargetsTests(unittest.TestCase):
    """The only class in this file that reads data/prices.json - both
    CALIBRATION TARGETS demand.py's own docstring names, read here to
    REPORT the disagreement and never fed back into demand.py's marginal
    budget shares or Gini coefficient to close it. See demand.py's own __main__
    block for the same computation with printed intermediate steps.
    """

    def setUp(self):
        # Instance-level setUp, not setUpClass - sim/tests/__main__.py's
        # _run_topic flattens a unittest suite and never drives
        # _handleClassSetUp (see sim/tests/test_deposits.py's own
        # CalibrationAgainstBookPricesTests for the same note). Cheap
        # enough to redo per test.
        with open(os.path.join(_REPO_ROOT, "data", "prices.json")) as handle:
            self.book_prices = json.load(handle)
        with open(os.path.join(_REPO_ROOT, "data", "world", "resources.json")) as handle:
            self.resources = json.load(handle)
        self.population = 55_000_000.0
        self.mean_income = 550.0
        self.bins = demand.income_bins(self.population, self.mean_income)
        self.wheat_price = demand._illustrative_recursive_labour_content_price_per_kg("wheat_kg")
        self.lead_price = demand._illustrative_recursive_labour_content_price_per_kg("lead_kg")
        self.manufactures_price = 1.0

    def test_report_food_budget_share(self):
        prices = {"wheat_kg": self.wheat_price,
                  "manufactures": self.manufactures_price,
                  "silver_kg": self._silver_price()}
        food_share = demand.household_budget_share(
            demand.FOOD, prices, self.bins, demand.DEFAULT_BASKET)
        print("\nCalibrationAgainstHistoricalTargetsTests: household food "
              "budget share = %.1f%% (historical target %.0f-%.0f%%)"
              % (100.0 * food_share,
                 100.0 * demand.HOUSEHOLD_FOOD_BUDGET_SHARE_LOW,
                 100.0 * demand.HOUSEHOLD_FOOD_BUDGET_SHARE_HIGH))
        self.assertGreater(food_share, 0.0)
        self.assertLess(food_share, 1.0)

    def _silver_price(self):
        lead_entry = demand.production_data()["lead_kg"]
        outputs = lead_entry["outputs"]
        annual_lead_kg = self.resources["empire_output_100ad"]["lead"]["t_per_yr"] * 1000.0
        annual_silver_kg = annual_lead_kg * outputs["silver_kg"] / outputs["lead_kg"]
        return demand.market_clearing_price(
            demand.SILVER, annual_silver_kg,
            {"wheat_kg": self.wheat_price, "manufactures": self.manufactures_price},
            self.bins, demand.DEFAULT_BASKET)

    def test_report_silver_to_lead_ratio(self):
        silver_price = self._silver_price()
        book_prices = self.book_prices["purchase_prices_denarii"]
        book_silver = book_prices["silver_kg"]["p"]
        book_lead = book_prices["lead_kg"]["p"]
        print("\nCalibrationAgainstHistoricalTargetsTests: derived "
              "silver:lead ratio = %.1fx (task's own stated historical "
              "target ~%.0fx; data/prices.json's own book ratio = %.1fx, "
              "which is not quite the same measurement - silver_kg's book "
              "price is DEFINITIONAL, 1 denarius = ~3.15g fine silver by "
              "fiat, not an observed market price)"
              % (silver_price / self.lead_price,
                 demand.SILVER_TO_LEAD_PRICE_RATIO_HISTORICAL,
                 book_silver / book_lead))
        print("  derived silver price: %.2f h/kg vs book-implied %.2f h/kg "
              "(book/wage: %.2f den/kg / %.4f den/h)"
              % (silver_price, book_silver / self._labourer_wage(),
                 book_silver, self._labourer_wage()))
        print("  derived lead price (recursive labour content only, no "
              "rent/capital): %.4f h/kg vs book-implied %.2f h/kg"
              % (self.lead_price, book_lead / self._labourer_wage()))
        self.assertGreater(silver_price, 0.0)
        self.assertGreater(silver_price, self.lead_price)

    def _labourer_wage(self):
        return self.book_prices["wage_rates_denarii_per_hour"]["labourer"]["rate"]


class ModuleRunsCleanlyTests(unittest.TestCase):
    """python3 -m sim.world.demand must print a readable summary - the
    same bar sim/world/agriculture.py's and sim/world/deposits.py's own
    __main__ blocks are held to.
    """

    def test_main_block_runs_and_reports_headline_numbers(self):
        result = subprocess.run(
            [sys.executable, "-m", "sim.world.demand"],
            cwd=_REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("COMPLAINTS/29", result.stdout)
        self.assertIn("silver:lead price ratio", result.stdout)
        self.assertIn("food budget share", result.stdout)


if __name__ == "__main__":
    unittest.main()
