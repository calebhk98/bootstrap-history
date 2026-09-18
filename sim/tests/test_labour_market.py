"""Regression tests for sim/world/labour_market.py.

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
"""
import ast
import os
import subprocess
import sys
import unittest

from sim.world import labour_market

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

class WorkforceStepConservationTests(unittest.TestCase):

    def test_total_hours_are_unchanged_by_one_step(self):
        workforce = labour_market.Workforce(
            {"smith": 1000.0, "labourer": 5000.0, "potter": 2000.0})
        total_before = workforce.total_hours()
        workforce.step({"smith": 2000.0, "labourer": 4000.0, "potter": 2000.0})
        self.assertAlmostEqual(workforce.total_hours(), total_before)

    def test_conservation_holds_across_many_steps_with_a_changing_trade_set(self):
        workforce = labour_market.Workforce({"smith": 1000.0, "potter": 3000.0})
        total_before = workforce.total_hours()
        # `mason` appears only in demand, never in the starting workforce -
        # exercises the union-of-trade-names path in `step`.
        for _ in range(20):
            workforce.step({"smith": 1500.0, "mason": 200.0})
        self.assertAlmostEqual(workforce.total_hours(), total_before)


class WorkforceStepDirectionTests(unittest.TestCase):

    def test_hours_move_from_surplus_into_shortage(self):
        workforce = labour_market.Workforce({"smith": 1000.0, "potter": 3000.0})
        flows = workforce.step({"smith": 1500.0, "potter": 2500.0})
        self.assertGreater(flows["smith"].hours_after, flows["smith"].hours_before)
        self.assertLess(flows["potter"].hours_after, flows["potter"].hours_before)

    def test_a_trade_exactly_at_its_requirement_does_not_move(self):
        workforce = labour_market.Workforce({"smith": 1000.0, "potter": 1000.0})
        flows = workforce.step({"smith": 1000.0, "potter": 500.0})
        self.assertAlmostEqual(flows["smith"].hours_after, 1000.0)

    def test_a_trade_at_zero_hours_cannot_grow_however_large_the_shortage(self):
        workforce = labour_market.Workforce({"electrician": 0.0, "potter": 3000.0})
        flows = workforce.step({"electrician": 1_000_000.0, "potter": 0.0})
        self.assertEqual(flows["electrician"].hours_after, 0.0)
        self.assertEqual(flows["electrician"].hours_moved_in, 0.0)

    def test_minimum_absorption_seeds_a_trade_a_caller_says_now_exists(self):
        workforce = labour_market.Workforce({"electrician": 0.0, "potter": 3000.0})
        flows = workforce.step(
            {"electrician": 1_000_000.0, "potter": 0.0},
            minimum_absorption_hours_by_trade={"electrician": 100.0})
        self.assertAlmostEqual(flows["electrician"].hours_after, 100.0)

    def test_tightness_ratio_above_one_means_short_below_one_means_slack(self):
        workforce = labour_market.Workforce({"smith": 1000.0, "potter": 1000.0})
        flows = workforce.step({"smith": 2000.0, "potter": 500.0})
        self.assertGreater(flows["smith"].tightness_ratio, 1.0)
        self.assertLess(flows["potter"].tightness_ratio, 1.0)

    def test_tightness_ratio_is_infinite_for_a_nonexistent_trade_still_required(self):
        workforce = labour_market.Workforce({"potter": 3000.0})
        flows = workforce.step({"electrician": 500.0, "potter": 0.0})
        self.assertEqual(flows["electrician"].tightness_ratio, float("inf"))


class WorkforceStepMobilityBoundTests(unittest.TestCase):

    def test_outflow_never_exceeds_the_mobility_rate_times_the_trades_own_size(self):
        workforce = labour_market.Workforce({"potter": 10_000.0, "smith": 100.0})
        flows = workforce.step({"potter": 0.0, "smith": 1_000_000.0},
                               mobility_rate_per_year=0.05)
        self.assertLessEqual(flows["potter"].hours_moved_out, 10_000.0 * 0.05 + 1e-9)

    def test_inflow_never_exceeds_the_mobility_rate_times_the_trades_own_size(self):
        workforce = labour_market.Workforce({"potter": 10_000.0, "smith": 100.0})
        flows = workforce.step({"potter": 0.0, "smith": 1_000_000.0},
                               mobility_rate_per_year=0.05)
        self.assertLessEqual(flows["smith"].hours_moved_in, 100.0 * 0.05 + 1e-9)

    def test_a_higher_mobility_rate_moves_more_in_one_step(self):
        slow = labour_market.Workforce({"potter": 10_000.0, "smith": 100.0})
        fast = labour_market.Workforce({"potter": 10_000.0, "smith": 100.0})
        slow_flows = slow.step({"potter": 5_000.0, "smith": 5_000.0},
                               mobility_rate_per_year=0.02)
        fast_flows = fast.step({"potter": 5_000.0, "smith": 5_000.0},
                               mobility_rate_per_year=0.20)
        self.assertGreater(fast_flows["smith"].hours_moved_in,
                           slow_flows["smith"].hours_moved_in)


class WorkforceStepProportionalSplitExactArithmeticTests(unittest.TestCase):
    """A hand-checkable case: two surplus trades of very different sizes,
    one shortage trade, mobility rate high enough that both surplus
    trades' caps are set by their SURPLUS rather than the mobility rate,
    so the split is exact arithmetic this test can verify by hand."""

    def test_shortage_trade_receives_the_smaller_of_supply_and_its_own_gap(self):
        # potter surplus: 500 h available to give up (mobility rate is not
        # the binding constraint here - the surplus itself is smaller).
        # smith surplus: 300 h available to give up, same reasoning.
        # labourer shortage: needs 400 h. Total supply (800h) exceeds the
        # 400h shortage, so labourer's inflow is capped at exactly 400h,
        # NOT at the full 800h available - `actual_total_moved` is the
        # smaller of the two totals by construction.
        workforce = labour_market.Workforce(
            {"potter": 10_000.0, "smith": 10_000.0, "labourer": 10_000.0})
        flows = workforce.step(
            {"potter": 10_000.0 - 500.0, "smith": 10_000.0 - 300.0,
             "labourer": 10_000.0 + 400.0},
            mobility_rate_per_year=1.0)
        self.assertAlmostEqual(flows["labourer"].hours_moved_in, 400.0)
        self.assertAlmostEqual(flows["labourer"].hours_after, 10_400.0)
        # The 400h actually moved is split across the two surplus trades
        # in proportion to their OWN capped outflow (500 and 300, out of
        # 800 total) - potter gives up 500/800 * 400 = 250h, smith gives
        # up 300/800 * 400 = 150h.
        self.assertAlmostEqual(flows["potter"].hours_moved_out, 250.0)
        self.assertAlmostEqual(flows["smith"].hours_moved_out, 150.0)


# ============================================================================
# THE FIXED POINT: solve_to_stable_allocation
# ============================================================================

class SolveToStableAllocationTests(unittest.TestCase):

    def test_converges_for_a_solvable_gap_within_available_slack(self):
        initial = {"potter": 10_000.0, "smith": 1_000.0}
        required = {"potter": 9_500.0, "smith": 1_500.0}
        workforce, periods, converged, history = labour_market.solve_to_stable_allocation(
            initial, required, tolerance_hours=1e-3)
        self.assertTrue(converged)
        self.assertGreater(periods, 1)   # friction means it is not instant
        self.assertAlmostEqual(workforce.hours_by_trade["smith"], 1_500.0, places=1)
        self.assertAlmostEqual(workforce.hours_by_trade["potter"], 9_500.0, places=1)

    def test_reports_unconverged_when_total_required_exceeds_total_available(self):
        initial = {"potter": 100.0, "smith": 100.0}
        required = {"potter": 100.0, "smith": 100_000.0}
        workforce, periods, converged, history = labour_market.solve_to_stable_allocation(
            initial, required, maximum_periods=50)
        self.assertFalse(converged)
        self.assertEqual(periods, 50)
        self.assertEqual(len(history), 50)
        # potter has nothing to give (it is exactly at its own
        # requirement), so smith cannot grow AT ALL from this starting
        # point - the honest "reallocation cannot solve this" answer.
        self.assertAlmostEqual(workforce.hours_by_trade["smith"], 100.0)

    def test_a_demand_vector_already_met_converges_on_the_first_period(self):
        initial = {"potter": 5_000.0, "smith": 500.0}
        required = dict(initial)
        workforce, periods, converged, history = labour_market.solve_to_stable_allocation(
            initial, required)
        self.assertTrue(converged)
        self.assertEqual(periods, 1)

    def test_history_length_matches_periods_used(self):
        initial = {"potter": 10_000.0, "smith": 1_000.0}
        required = {"potter": 9_000.0, "smith": 2_000.0}
        _, periods, _, history = labour_market.solve_to_stable_allocation(
            initial, required, tolerance_hours=1e-3)
        self.assertEqual(len(history), periods)


# ============================================================================
# THE CONSTANT
# ============================================================================

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


# ============================================================================
# STANDALONE ON PURPOSE
# ============================================================================

class StandaloneImportTests(unittest.TestCase):
    """sim/world/labour_market.py must not import sim/engine/, sim/
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
        path = os.path.join(_REPO_ROOT, "sim", "world", "labour_market.py")
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
                "sim/world/labour_market.py imports %r at module level" % name)
            self.assertFalse(
                name.startswith("sim.world.") and name != "sim.world.labour_market",
                "sim/world/labour_market.py imports another sim/world/ "
                "module at module level: %r" % name)
            self.assertNotEqual(
                name, "sim.solve_prices",
                "sim/world/labour_market.py imports the price solver "
                "directly at module level")

    def test_the_only_other_sim_world_import_is_inside_the_main_guard(self):
        path = os.path.join(_REPO_ROOT, "sim", "world", "labour_market.py")
        with open(path) as handle:
            tree = ast.parse(handle.read(), filename=path)
        top_level_kinds = {type(node) for node in tree.body}
        # There must be at least one `if __name__ == "__main__":` block
        # for the demo's own import to live inside, or this test would be
        # vacuously trusting an import that is not actually confined.
        self.assertIn(ast.If, top_level_kinds)

        agriculture_imports_outside_main_guard = []
        for node in tree.body:
            if isinstance(node, ast.If):
                continue   # the demo block - permitted to import agriculture
            for inner in ast.walk(node):
                if isinstance(inner, ast.ImportFrom) and inner.module == "sim.world":
                    for alias in inner.names:
                        if alias.name == "agriculture":
                            agriculture_imports_outside_main_guard.append(node)
        self.assertEqual(agriculture_imports_outside_main_guard, [])


# ============================================================================
# python3 -m sim.world.labour_market MUST RUN CLEANLY
# ============================================================================

class ModuleRunsCleanlyTests(unittest.TestCase):

    def test_main_block_runs_and_tells_both_scenarios(self):
        result = subprocess.run(
            [sys.executable, "-m", "sim.world.labour_market"],
            cwd=_REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SCENARIO 1", result.stdout)
        self.assertIn("SCENARIO 2", result.stdout)
        self.assertIn("smith", result.stdout)
        self.assertIn("labourer", result.stdout)


if __name__ == "__main__":
    unittest.main()
