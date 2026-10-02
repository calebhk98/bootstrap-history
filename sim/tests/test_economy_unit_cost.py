"""What a run costs and earns at live prices."""
import math
import unittest

from sim.economy import unit_cost
from sim.economy.types import Recipe

SMELT = Recipe("smelt", {"metal": 10.0, "silver": 1.0}, {"ore": 20.0}, {"smith": 5.0},
               {"stone": 100.0}, {"mason": 10.0}, 20.0)
PRICES = {"ore": 1.0, "stone": 2.0}
WAGES = {"smith": 3.0, "mason": 4.0}


class UnitCostTests(unittest.TestCase):
    def test_variable_cost_is_inputs_plus_labour(self):
        self.assertAlmostEqual(unit_cost.variable_cost_per_run(SMELT, PRICES, WAGES), 20.0 + 15.0)

    def test_a_missing_price_makes_the_run_unaffordable(self):
        self.assertTrue(math.isinf(unit_cost.variable_cost_per_run(SMELT, {}, WAGES)))

    def test_capital_charge_uses_the_recovery_factor_at_the_live_rate(self):
        value = 100.0 * 2.0 + 10.0 * 4.0
        factor = 0.05 / (1.0 - 1.05 ** -20.0)
        self.assertAlmostEqual(unit_cost.capital_charge_per_run(SMELT, PRICES, WAGES, 0.05), value * factor)
        self.assertAlmostEqual(unit_cost.capital_charge_per_run(SMELT, PRICES, WAGES, 0.0), value / 20.0)

    def test_a_dearer_rate_raises_the_charge(self):
        low = unit_cost.capital_charge_per_run(SMELT, PRICES, WAGES, 0.02)
        self.assertGreater(unit_cost.capital_charge_per_run(SMELT, PRICES, WAGES, 0.10), low)

    def test_margin_counts_every_joint_output(self):
        both = unit_cost.expected_margin(SMELT, {"metal": 4.0, "silver": 30.0}, PRICES, WAGES, 0.0)
        metal_only = unit_cost.expected_margin(SMELT, {"metal": 4.0}, PRICES, WAGES, 0.0)
        self.assertAlmostEqual(both - metal_only, 30.0)
        self.assertAlmostEqual(metal_only, 40.0 - 35.0 - 240.0 / 20.0)

    def test_return_on_capital_is_surplus_over_plant_plus_working_capital(self):
        got = unit_cost.return_on_capital(SMELT, {"metal": 10.0, "silver": 10.0}, PRICES, WAGES)
        self.assertAlmostEqual(got, (110.0 - 35.0) / (240.0 + 35.0))


if __name__ == "__main__":
    unittest.main()
