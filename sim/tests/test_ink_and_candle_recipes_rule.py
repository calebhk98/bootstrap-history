"""Complaint 567: ink, a written page and a tallow candle each have a production recipe, so an opening can price them."""
QUICK_TOPIC = True

import unittest

from sim.labour import labour_market

GOODS = ("ink_kg", "written_page", "light_tallow_candle")


class RecipesMakeTheGoods(unittest.TestCase):
    def test_some_recipe_outputs_each_good_with_a_positive_yield_and_a_cost_in_labour_or_inputs(self):
        recipes = labour_market.production_data()
        for good in GOODS:
            with self.subTest(good=good):
                makers = [entry for entry in recipes.values()
                          if isinstance(entry, dict) and (entry.get("outputs") or {}).get(good, 0.0) > 0.0]
                self.assertTrue(makers)
                self.assertTrue(any(entry.get("labour_hours") or entry.get("inputs") for entry in makers))


if __name__ == "__main__":
    unittest.main()
