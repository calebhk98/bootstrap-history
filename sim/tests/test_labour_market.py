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

sim/labour/labour_market.py: what the recipe graph asks of each trade, and 
"""

QUICK_TOPIC = True

import unittest

from sim.labour import labour_market
from sim.world.demand import production_data


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


class RealProductionDataSmokeTests(unittest.TestCase):
    """A light touch of the real data/production/*.json files - enough to
    prove the loader and the aggregation work against the genuine schema,
    never enough to assert a particular authored number (that is
    data/production/'s own owner's call, not this module's - see
    data/production/_SCHEMA.md and CLAUDE.md section 4)."""

    def test_wheat_kg_is_present_and_booked_to_the_farmer(self):
        production = production_data()
        self.assertIn("wheat_kg", production)
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "wheat_kg", production)
        self.assertIn("farmer", coefficients)
        self.assertGreater(coefficients["farmer"], 0.0)

    def test_iron_bar_kg_needs_both_furnaceman_and_smith(self):
        production = production_data()
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "iron_bar_kg", production)
        self.assertIn("furnaceman", coefficients)
        self.assertIn("smith", coefficients)


if __name__ == "__main__":
    unittest.main()
