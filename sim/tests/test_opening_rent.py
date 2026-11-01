"""The opening carries land rent: the prices cover it, the producers' working share counts it, and the households'
property income contains it, so a year after the opening sees the same rent and costs as the opening.

Each test calls one plain function with written-out inputs (sim/economy/opening_rent.py, opening_income.py)."""
import unittest

from sim.economy import opening_income, opening_rent
from sim.economy.types import Recipe

QUICK_TOPIC = True

FARM = Recipe("farm", {"grain": 1000.0}, {}, {"labourer": 300.0})
SMELT = Recipe("smelt", {"metal": 1.0}, {"ore": 1000.0}, {"smith": 30.0})


class CoveringPriceTests(unittest.TestCase):
    def test_a_price_that_only_paid_labour_rises_by_the_rent_share_of_revenue(self):
        prices = opening_rent.covering_prices({"farm": FARM}, {"grain": 0.3}, {"labourer": 1.0}, {"farm": 0.1}, {"farm"}, {})
        self.assertAlmostEqual(prices["grain"], 0.3 / 0.9)

    def test_a_price_that_already_pays_labour_and_rent_is_left_alone(self):
        prices = opening_rent.covering_prices({"farm": FARM}, {"grain": 0.4}, {"labourer": 1.0}, {"farm": 0.1}, {"farm"}, {})
        self.assertEqual(prices["grain"], 0.4)

    def test_a_recipe_the_prices_leave_short_of_its_cost_stays_short_by_as_much(self):
        short = opening_rent.covering_prices({"farm": FARM}, {"grain": 0.2}, {"labourer": 1.0}, {"farm": 0.0}, {"farm"}, {})
        self.assertEqual(short["grain"], 0.2)
        rented = opening_rent.covering_prices({"farm": FARM}, {"grain": 0.2}, {"labourer": 1.0}, {"farm": 0.1}, {"farm"}, {})
        self.assertAlmostEqual(rented["grain"], (300.0 / 0.9 - 100.0) / 1000.0)

    def test_a_recipe_not_run_leaves_its_price(self):
        prices = opening_rent.covering_prices({"farm": FARM}, {"grain": 0.3}, {"labourer": 1.0}, {"farm": 0.1}, set(), {})
        self.assertEqual(prices["grain"], 0.3)

    def test_a_dearer_input_raises_the_price_of_what_uses_it(self):
        recipes = {"mine": Recipe("mine", {"ore": 1000.0}, {}, {"miner": 40.0}), "smelt": SMELT}
        prices = opening_rent.covering_prices(recipes, {"ore": 0.05, "metal": 95.0}, {"miner": 1.2, "smith": 1.5},
                                              {"mine": 0.5}, {"mine", "smelt"}, {})
        self.assertAlmostEqual(prices["ore"], 48.0 / 0.5 / 1000.0)
        self.assertAlmostEqual(prices["metal"], 96.0 + 45.0)


class RentShareTests(unittest.TestCase):
    def test_the_share_is_rent_paid_over_revenue_of_the_runs(self):
        rows = [("farm", 100.0, 30.0, 300.0), ("farm", 300.0, 30.0, 300.0), ("mine", 50.0, 0.0, 50.0)]
        self.assertAlmostEqual(opening_rent.rent_share_of_revenue(rows)["farm"], 0.1)
        self.assertEqual(opening_rent.rent_share_of_revenue(rows)["mine"], 0.0)


class PropertyIncomeSplitTests(unittest.TestCase):
    def test_rent_is_paid_to_its_receivers_and_the_rest_of_the_property_income_scales_down(self):
        split = opening_rent.property_income_with_rent({"a": 60.0, "b": 40.0}, {"b": 50.0})
        self.assertAlmostEqual(split["a"], 30.0)
        self.assertAlmostEqual(split["b"], 70.0)
        self.assertAlmostEqual(sum(split.values()), 100.0)

    def test_rent_beyond_the_property_income_is_all_the_property_income_there_is_plus_the_excess(self):
        split = opening_rent.property_income_with_rent({"a": 10.0}, {"a": 30.0})
        self.assertAlmostEqual(split["a"], 30.0)


class WorkingShareTests(unittest.TestCase):
    def test_rent_lowers_the_share_of_the_plant_that_works(self):
        free = opening_income.working_share(FARM, {"grain": 0.4}, {"labourer": 1.0})
        rented = opening_income.working_share(FARM, {"grain": 0.4}, {"labourer": 1.0}, 1.0, 40.0)
        self.assertLess(rented, free)


if __name__ == "__main__":
    unittest.main()
