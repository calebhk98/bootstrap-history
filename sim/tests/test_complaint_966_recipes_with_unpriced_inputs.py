"""Complaint 966: a recipe whose hard input or output has no opening price is not in the setup's
recipes, so no producer's output or input names a good the market-area map was not built for."""
QUICK_TOPIC = True

import unittest

from sim.economy.types import Recipe
from sim.markets.port_closure import runnable_recipes


def recipes():
    return {"salted_meat": Recipe("salted_meat", {"salted_meat": 1.0}, {"meat": 1.0, "salt": 0.1}, {"hand": 1.0}),
            "salt": Recipe("salt", {"salt": 1.0}, {}, {"hand": 1.0}),
            "bread": Recipe("bread", {"bread": 1.0}, {"flour": 1.0}, {"hand": 1.0})}


class RunnableRecipesTests(unittest.TestCase):
    def test_a_recipe_with_an_unpriced_hard_input_is_left_out(self):
        kept = runnable_recipes(recipes(), {"salt": 1.0, "flour": 1.0, "bread": 2.0, "salted_meat": 4.0})
        self.assertEqual(sorted(kept), ["bread", "salt"])

    def test_every_recipe_with_priced_inputs_stays(self):
        kept = runnable_recipes(recipes(), {"salt": 1.0, "flour": 1.0, "meat": 3.0, "bread": 2.0, "salted_meat": 4.0})
        self.assertEqual(sorted(kept), ["bread", "salt", "salted_meat"])

    def test_a_recipe_with_an_unpriced_output_is_left_out(self):
        kept = runnable_recipes(recipes(), {"salt": 1.0, "flour": 1.0, "meat": 3.0, "salted_meat": 4.0})
        self.assertEqual(sorted(kept), ["salt", "salted_meat"])


if __name__ == "__main__":
    unittest.main()
