"""Opening prices are a closed set (Complaint 566): `makeable_prices` keeps a good some production entry makes only when a recipe the
society can run makes it from goods that are themselves kept, and keeps every good no entry makes. Hand-built recipes; no game."""
import unittest

from sim.economy.types import Recipe
from sim.engine.economy_port_closure import makeable_prices

QUICK_TOPIC = True

PRODUCTION = {"lamp": {"outputs": {"lamp": 1.0}}, "oil": {"outputs": {"oil": 1.0}}, "wick": {"outputs": {"wick": 1.0}},
              "_note": {"outputs": {"ghost": 1.0}}}
PRICES = {"lamp": 3.0, "oil": 1.0, "wick": 0.5, "flax": 0.2, "ghost": 9.0}


def recipe(good, *inputs):
    return Recipe(good, {good: 1.0}, {item: 1.0 for item in inputs}, {"labourer": 1.0})


class MakeablePricesTests(unittest.TestCase):
    def test_a_good_whose_inputs_are_all_kept_keeps_its_price(self):
        recipes = {"lamp": recipe("lamp", "oil", "wick"), "oil": recipe("oil", "flax"), "wick": recipe("wick", "flax")}
        self.assertEqual(makeable_prices(PRICES, PRODUCTION, recipes), PRICES)

    def test_a_good_no_runnable_recipe_makes_loses_its_price(self):
        kept = makeable_prices(PRICES, PRODUCTION, {"lamp": recipe("lamp", "flax")})
        self.assertNotIn("oil", kept)
        self.assertNotIn("wick", kept)

    def test_the_loss_carries_to_every_good_made_from_it(self):
        recipes = {"lamp": recipe("lamp", "oil"), "wick": recipe("wick", "flax")}
        kept = makeable_prices(PRICES, PRODUCTION, recipes)
        self.assertNotIn("oil", kept)
        self.assertNotIn("lamp", kept)
        self.assertIn("wick", kept)

    def test_a_good_no_production_entry_makes_keeps_its_price(self):
        kept = makeable_prices(PRICES, PRODUCTION, {})
        self.assertEqual(kept["flax"], PRICES["flax"])

    def test_every_kept_good_a_production_entry_makes_has_a_recipe_from_kept_goods(self):
        recipes = {"lamp": recipe("lamp", "oil", "wick"), "oil": recipe("oil", "tallow"), "wick": recipe("wick", "flax")}
        kept = makeable_prices(PRICES, PRODUCTION, recipes)
        made_by_entries = {good for entry_id, entry in PRODUCTION.items() if not entry_id.startswith("_") for good in entry["outputs"]}
        for good in kept:
            if good in made_by_entries:
                self.assertTrue(any(good in each.outputs and all(item in kept for item in each.hard_inputs)
                                    for each in recipes.values()), good)

    def test_the_prices_themselves_are_not_changed(self):
        recipes = {"wick": recipe("wick", "flax")}
        self.assertEqual(makeable_prices(PRICES, PRODUCTION, recipes)["wick"], PRICES["wick"])


if __name__ == "__main__":
    unittest.main()
