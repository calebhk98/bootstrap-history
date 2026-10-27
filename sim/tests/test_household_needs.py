"""The budget scaling of what households buy for themselves (sim/markets/household_needs.py)."""

QUICK_TOPIC = True

import unittest

from sim.markets import household_needs
from sim.world.material_units import tonnes_per_unit


class BudgetScaledFinalTonnesTest(unittest.TestCase):

    UNITS = {"wheat_kg": 100.0, "iron_kg": 50.0}
    PRICES = {"wheat_kg": 2.0, "iron_kg": 4.0}      # labour hours a unit: spending 400
    FINAL = frozenset(["wheat_kg"])

    def test_spending_within_the_income_is_not_scaled(self):
        tonnes = household_needs.budget_scaled_final_tonnes(self.UNITS, self.PRICES, 1.0, self.FINAL)
        self.assertEqual(tonnes, {"wheat_kg": 100.0 * tonnes_per_unit("wheat_kg")})

    def test_spending_over_the_income_scales_every_good_alike(self):
        population = 400.0 / household_needs.MEAN_INCOME_HOURS_PER_CAPITA / 2.0     # income is half the spending
        tonnes = household_needs.budget_scaled_final_tonnes(self.UNITS, self.PRICES, population, self.FINAL)
        self.assertAlmostEqual(tonnes["wheat_kg"], 50.0 * tonnes_per_unit("wheat_kg"))

    def test_goods_bought_only_as_inputs_are_left_out(self):
        tonnes = household_needs.budget_scaled_final_tonnes(self.UNITS, self.PRICES, 1.0, self.FINAL)
        self.assertNotIn("iron_kg", tonnes)

    def test_nothing_priced_means_no_scaling(self):
        tonnes = household_needs.budget_scaled_final_tonnes(self.UNITS, {}, 1.0, self.FINAL)
        self.assertEqual(tonnes, {"wheat_kg": 100.0 * tonnes_per_unit("wheat_kg")})


if __name__ == "__main__":
    unittest.main()
