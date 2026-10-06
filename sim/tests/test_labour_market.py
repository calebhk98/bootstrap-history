"""Regression tests for sim/labour/labour_market.py.

Written as unittest.TestCase classes, like sim/tests/test_deposits.py,
sim/tests/test_land.py and sim/tests/test_demand.py: this module has no
dependency on sim/engine/ or any other sim/world/ module (see labour_
market.py's own STANDALONE section), so importing sim/tests/harness.py
would pull in the whole engine for no reason. sim/tests/__main__.py's own
_run_topic already runs both styles identically - this file's module name
for that registration is sim.tests.test_labour_market.

These checks are ORDERINGS AND STRUCTURAL PROPERTIES wherever a real
data/production/ figure is involved (a labour coefficient can be re-
authored at any confidence level without breaking this suite, exactly the
discipline sim/tests/test_deposits.py's own ExtractionCostMechanicsTests
docstring states for ore data), and EXACT ARITHMETIC wherever the input is
a small, hand-built synthetic fixture this file controls itself.

sim/labour/labour_market.py: what the recipe graph asks of each trade, and how fast the farm hours move.
"""
import ast
import os
import unittest

from sim.labour import labour_market

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def _entry(outputs, labour_hours=None, capital=None):
    entry = {"outputs": outputs}
    if labour_hours is not None:
        entry["labour_hours"] = labour_hours
    if capital is not None:
        entry["capital"] = capital
    return entry


# ============================================================================
# DEMAND SIDE: HOURS REQUIRED PER TRADE FROM A PLANNED OUTPUT
# ============================================================================

class LabourHoursCoefficientsTests(unittest.TestCase):

    def test_single_output_single_trade_divides_by_the_batch_size(self):
        production = {"axe_kg": _entry({"axe_kg": 10.0}, {"smith": 5.0})}
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "axe_kg", production)
        self.assertAlmostEqual(coefficients["smith"], 0.5)

    def test_several_trades_each_get_their_own_coefficient(self):
        production = {"iron_bar_kg": _entry(
            {"iron_bar_kg": 1000.0}, {"furnaceman": 80.0, "smith": 120.0})}
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "iron_bar_kg", production)
        self.assertAlmostEqual(coefficients["furnaceman"], 0.08)
        self.assertAlmostEqual(coefficients["smith"], 0.12)

    def test_dominant_output_is_the_largest_by_mass_not_the_first_key(self):
        # zinc_electrolytic_kg-shaped entry: a tiny byproduct listed before
        # the real basis output. The coefficient must still be divided by
        # the BIG number, exactly as sim.world.demand's identical-shaped
        # helper does for `inputs`.
        production = {"smelt": _entry(
            {"byproduct_g": 0.5, "zinc_kg": 1000.0}, {"furnaceman": 200.0})}
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "smelt", production)
        self.assertAlmostEqual(coefficients["furnaceman"], 0.2)

    def test_capital_build_labour_hours_are_amortised_over_the_lifetime(self):
        production = {"pot_kg": _entry(
            {"pot_kg": 1000.0}, {"potter": 500.0},
            capital=[{"service_life_years": 10.0, "annual_output_at_basis": 1000.0,
                     "build_labour_hours": {"mason": 200.0}}])}
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "pot_kg", production)
        # 200 h to build, spread over 10 years * 1000 kg/year = 10,000 kg
        # of lifetime output -> 0.02 h/kg.
        self.assertAlmostEqual(coefficients["mason"], 0.02)
        self.assertAlmostEqual(coefficients["potter"], 0.5)

    def test_a_capital_item_missing_service_life_or_output_is_skipped_not_raised(self):
        production = {"widget_kg": _entry(
            {"widget_kg": 100.0}, {"labourer": 10.0},
            capital=[{"build_labour_hours": {"mason": 50.0}}])}
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "widget_kg", production)
        self.assertNotIn("mason", coefficients)

    def test_unknown_recipe_raises_key_error(self):
        with self.assertRaises(KeyError):
            labour_market.labour_hours_coefficients_per_unit_output(
                "not_a_real_recipe", {})

    def test_zero_basis_quantity_raises_value_error(self):
        production = {"broken": _entry({"broken_kg": 0.0}, {"labourer": 1.0})}
        with self.assertRaises(ValueError):
            labour_market.labour_hours_coefficients_per_unit_output(
                "broken", production)


class LabourHoursRequiredByTradeTests(unittest.TestCase):

    def setUp(self):
        self.production = {
            "wheat_kg": _entry({"wheat_kg": 577.5}, {"labourer": 150.0}),
            "iron_bar_kg": _entry({"iron_bar_kg": 1000.0},
                                  {"furnaceman": 80.0, "smith": 120.0}),
        }

    def test_aggregates_across_recipes_that_share_a_trade(self):
        production = {
            "a": _entry({"a_kg": 1.0}, {"labourer": 2.0}),
            "b": _entry({"b_kg": 1.0}, {"labourer": 3.0}),
        }
        hours_by_trade, _ = labour_market.labour_hours_required_by_trade(
            {"a": 10.0, "b": 10.0}, production)
        self.assertAlmostEqual(hours_by_trade["labourer"], 20.0 + 30.0)

    def test_breakdown_names_which_recipe_contributed_how_much(self):
        hours_by_trade, contributors = labour_market.labour_hours_required_by_trade(
            {"wheat_kg": 577.5, "iron_bar_kg": 1000.0}, self.production)
        self.assertAlmostEqual(hours_by_trade["labourer"], 150.0)
        self.assertAlmostEqual(hours_by_trade["smith"], 120.0)
        self.assertAlmostEqual(contributors["smith"]["iron_bar_kg"], 120.0)

    def test_a_recipe_not_in_production_is_silently_skipped(self):
        hours_by_trade, _ = labour_market.labour_hours_required_by_trade(
            {"no_such_recipe": 1000.0}, self.production)
        self.assertEqual(hours_by_trade, {})

    def test_a_zero_output_level_contributes_nothing(self):
        hours_by_trade, _ = labour_market.labour_hours_required_by_trade(
            {"wheat_kg": 0.0}, self.production)
        self.assertEqual(hours_by_trade, {})

    def test_output_level_scales_linearly(self):
        hours_at_1x, _ = labour_market.labour_hours_required_by_trade(
            {"wheat_kg": 577.5}, self.production)
        hours_at_3x, _ = labour_market.labour_hours_required_by_trade(
            {"wheat_kg": 3 * 577.5}, self.production)
        self.assertAlmostEqual(hours_at_3x["labourer"], 3 * hours_at_1x["labourer"])


class RealProductionDataSmokeTests(unittest.TestCase):
    """A light touch of the real data/production/*.json files - enough to
    prove the loader and the aggregation work against the genuine schema,
    never enough to assert a particular authored number (that is
    data/production/'s own owner's call, not this module's - see
    data/production/_SCHEMA.md and CLAUDE.md section 4)."""

    def test_wheat_kg_is_present_and_booked_to_labourer(self):
        production = labour_market.production_data()
        self.assertIn("wheat_kg", production)
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "wheat_kg", production)
        self.assertIn("labourer", coefficients)
        self.assertGreater(coefficients["labourer"], 0.0)

    def test_iron_bar_kg_needs_both_furnaceman_and_smith(self):
        production = labour_market.production_data()
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "iron_bar_kg", production)
        self.assertIn("furnaceman", coefficients)
        self.assertIn("smith", coefficients)

    def test_labour_hours_required_by_trade_runs_over_real_data(self):
        production = labour_market.production_data()
        hours_by_trade, _ = labour_market.labour_hours_required_by_trade(
            {"wheat_kg": 1_000_000.0, "iron_bar_kg": 10_000.0}, production)
        self.assertGreater(hours_by_trade.get("labourer", 0.0), 0.0)
        self.assertGreater(hours_by_trade.get("smith", 0.0), 0.0)


# ============================================================================
# THE BRIDGE TO A MARGINAL PRODUCT
# ============================================================================

class AdditionalHoursToCloseAShortfallTests(unittest.TestCase):

    def test_is_the_plain_inverse_of_the_marginal_product(self):
        self.assertAlmostEqual(
            labour_market.additional_hours_to_close_a_shortfall(100.0, 2.0), 50.0)

    def test_zero_marginal_product_raises_rather_than_dividing_by_zero(self):
        with self.assertRaises(ValueError):
            labour_market.additional_hours_to_close_a_shortfall(100.0, 0.0)

    def test_negative_marginal_product_also_raises(self):
        with self.assertRaises(ValueError):
            labour_market.additional_hours_to_close_a_shortfall(100.0, -1.0)


# ============================================================================
# THE ALLOCATION: Workforce.step
# ============================================================================

class GapResponsiveMobilityRateTests(unittest.TestCase):
    """Direct, hand-checkable coverage of the two pure functions THE
    FRICTION section's rate schedule is built from - see labour_market.py's
    own `relative_gap_size` and `gap_responsive_mobility_rate`."""

    def testrelative_gap_size_is_the_plain_ratio_when_basis_is_positive(self):
        self.assertAlmostEqual(labour_market.relative_gap_size(-50.0, 100.0), 0.5)
        self.assertAlmostEqual(labour_market.relative_gap_size(300.0, 100.0), 3.0)

    def testrelative_gap_size_is_zero_when_there_is_no_gap(self):
        self.assertEqual(labour_market.relative_gap_size(0.0, 0.0), 0.0)
        self.assertEqual(labour_market.relative_gap_size(0.0, 500.0), 0.0)

    def testrelative_gap_size_is_infinite_when_basis_is_zero_and_a_gap_exists(self):
        self.assertEqual(labour_market.relative_gap_size(50.0, 0.0), float("inf"))

    def test_zero_relative_gap_returns_exactly_the_base_rate(self):
        self.assertAlmostEqual(
            labour_market.gap_responsive_mobility_rate(0.05, 0.0), 0.05)

    def test_rate_rises_monotonically_with_relative_gap_up_to_the_ceiling(self):
        rate_at_small_gap = labour_market.gap_responsive_mobility_rate(0.05, 0.1)
        rate_at_large_gap = labour_market.gap_responsive_mobility_rate(0.05, 10.0)
        ceiling = labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR
        self.assertGreater(rate_at_large_gap, rate_at_small_gap)
        self.assertLessEqual(rate_at_large_gap, ceiling)
        self.assertAlmostEqual(rate_at_large_gap, ceiling)

    def test_infinite_relative_gap_returns_exactly_the_ceiling(self):
        self.assertAlmostEqual(
            labour_market.gap_responsive_mobility_rate(0.05, float("inf")),
            labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR)


class OccupationalMobilityRateTests(unittest.TestCase):

    def test_is_a_plausible_fraction_strictly_between_zero_and_one(self):
        self.assertGreater(labour_market.OCCUPATIONAL_MOBILITY_RATE_PER_YEAR, 0.0)
        self.assertLess(labour_market.OCCUPATIONAL_MOBILITY_RATE_PER_YEAR, 1.0)

    def test_is_declared_as_a_labelled_temporary_heuristic(self):
        from sim import constants
        entry = constants.REGISTRY["OCCUPATIONAL_MOBILITY_RATE_PER_YEAR"]
        self.assertEqual(entry["kind"], "temporary_heuristic")
        self.assertTrue(entry["why"])
        self.assertTrue(entry["source"])


class MobilityFrictionConstantsTests(unittest.TestCase):
    """The three constants THE FRICTION section added alongside the
    original steady-state rate, each labelled per CLAUDE.md SS3.4."""

    def test_gap_response_gain_is_positive_and_labelled(self):
        from sim import constants
        self.assertGreater(labour_market.OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN, 0.0)
        entry = constants.REGISTRY["OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN"]
        self.assertEqual(entry["kind"], "temporary_heuristic")
        self.assertTrue(entry["why"])

    def test_rate_ceiling_is_above_the_steady_state_rate_and_below_one(self):
        from sim import constants
        self.assertGreater(labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR,
                           labour_market.OCCUPATIONAL_MOBILITY_RATE_PER_YEAR)
        self.assertLess(labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR, 1.0)
        entry = constants.REGISTRY["OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR"]
        self.assertEqual(entry["kind"], "temporary_heuristic")
        self.assertTrue(entry["why"])

    def test_walkable_seed_share_is_a_small_positive_fraction(self):
        from sim import constants
        self.assertGreater(labour_market.WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS, 0.0)
        self.assertLess(labour_market.WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS, 1.0)
        entry = constants.REGISTRY["WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS"]
        self.assertEqual(entry["kind"], "temporary_heuristic")
        self.assertTrue(entry["why"])


# ============================================================================
# STANDALONE ON PURPOSE
# ============================================================================

class StandaloneImportTests(unittest.TestCase):
    """sim/labour/labour_market.py must not import sim/engine/, sim/
    solve_prices.py, or any other sim/world/ module AS PART OF ITS
    IMPORTABLE SURFACE - see its own docstring's STANDALONE section and
    sim/world/__init__.py for why every module in this package holds to
    this independently. The ONE deliberate exception (see the module
    docstring) is its own `__main__` demonstration block, which imports
    sim.world.agriculture to get a real marginal-product number for the
    worked example - this test checks the TOP-LEVEL module body only, so
    that exception does not silently widen into the importable surface
    other modules actually depend on.
    """

    def _top_level_imports(self):
        path = os.path.join(_REPO_ROOT, "sim", "labour", "labour_market.py")
        with open(path) as handle:
            tree = ast.parse(handle.read(), filename=path)
        imported = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        return imported

    def test_top_level_imports_are_limited_to_stdlib_and_sim_constants(self):
        imported = self._top_level_imports()
        for name in imported:
            self.assertFalse(
                name.startswith("sim.engine"),
                "sim/labour/labour_market.py imports %r at module level" % name)
            self.assertFalse(
                name.startswith("sim.world.") and name != "sim.labour.labour_market",
                "sim/labour/labour_market.py imports another sim/world/ "
                "module at module level: %r" % name)
            self.assertNotEqual(
                name, "sim.engine.solve_prices",
                "sim/labour/labour_market.py imports the price solver "
                "directly at module level")

    def test_nothing_imports_sim_world_agriculture(self):
        path = os.path.join(_REPO_ROOT, "sim", "labour", "labour_market.py")
        with open(path) as handle:
            tree = ast.parse(handle.read(), filename=path)
        agriculture_imports = [
            inner for inner in ast.walk(tree)
            if isinstance(inner, ast.ImportFrom) and inner.module == "sim.world"
            and any(alias.name == "agriculture" for alias in inner.names)]
        self.assertEqual(agriculture_imports, [])


if __name__ == "__main__":
    unittest.main()
