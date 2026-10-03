"""How far a good's price stands from what it costs to make: revenue over full cost (inputs, labour and
the plant's yearly charge) for the cheapest known recipe that makes it, at live prices and wages."""
import math
import unittest

from sim.economy import price_cost
from sim.economy.types import Recipe

BAR = Recipe("bar", outputs={"bar": 1.0}, inputs={"ore": 2.0}, labour_hours={"smith": 3.0})
CHEAP_BAR = Recipe("cheap_bar", outputs={"bar": 1.0}, inputs={"ore": 1.0}, labour_hours={"smith": 1.0})
MILL = Recipe("mill", outputs={"flour": 1.0}, inputs={"wheat": 1.0}, labour_hours={"miller": 1.0},
              plant_goods={"bar": 1.0}, plant_life_years=10.0)


class PriceToCostTests(unittest.TestCase):
    def test_a_price_at_full_cost_reads_one(self):
        ratios = price_cost.price_to_cost({"bar": BAR}, {"bar": 8.0, "ore": 1.0}, {"smith": 2.0}, 0.05)
        self.assertAlmostEqual(ratios["bar"], 1.0)

    def test_the_cheapest_recipe_sets_the_cost(self):
        ratios = price_cost.price_to_cost({"bar": BAR, "cheap_bar": CHEAP_BAR},
                                          {"bar": 6.0, "ore": 1.0}, {"smith": 2.0}, 0.05)
        self.assertAlmostEqual(ratios["bar"], 2.0)

    def test_the_plant_is_charged_at_the_live_rate(self):
        prices = {"flour": 3.0, "wheat": 1.0, "bar": 10.0}
        ratios = price_cost.price_to_cost({"mill": MILL}, prices, {"miller": 1.0}, 0.05)
        charge = 10.0 * 0.05 / (1.0 - 1.05 ** -10.0)
        self.assertAlmostEqual(ratios["flour"], 3.0 / (2.0 + charge))

    def test_a_good_no_recipe_can_price_is_left_out(self):
        ratios = price_cost.price_to_cost({"bar": BAR}, {"bar": 8.0}, {"smith": 2.0}, 0.05)
        self.assertNotIn("bar", ratios)

    def test_summary_names_the_median_and_the_worst_both_ways(self):
        summary = price_cost.summary({"a": 1.0, "b": 0.5, "c": 40.0})
        self.assertAlmostEqual(summary["median"], 1.0)
        self.assertEqual(summary["worst_good"], "c")
        self.assertAlmostEqual(summary["worst"], 40.0)
        self.assertTrue(math.isnan(price_cost.summary({})["median"]))


if __name__ == "__main__":
    unittest.main()
