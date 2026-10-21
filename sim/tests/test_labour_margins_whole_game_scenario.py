"""Scenarios (Complaint 640; the baseline validation is test_labour_margins_baseline_validation): the economy a game
opens with is built from its civilisation's own draught animals."""
import functools
import random
import unittest

from . import harness  # noqa: F401  (sets the short spin-up the suite's games open on)
from sim.engine.ui_port import Sim, load, load_civ


@functools.lru_cache(maxsize=None)
def opened(civ_id):
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ_id))
    game.done_year = {}
    return game


class DraughtAnimalRecipes(unittest.TestCase):
    def test_a_society_that_keeps_draught_animals_ploughs_with_a_team(self):
        recipes = opened("rome_100ad").economy.agent.economy().setup.recipes
        self.assertIn("wheat_kg", recipes)
        self.assertIn("draught_animal_kg", recipes["wheat_kg"].plant_goods)

    def test_a_society_without_draught_animals_grows_wheat_and_its_other_crops_by_hand(self):
        # opening the game builds the economy, which fixes the recipes
        recipes = opened("mexica_1500").economy.agent.economy().setup.recipes
        self.assertNotIn("wheat_kg", recipes)
        self.assertIn("wheat_hoe_kg", recipes)
        for recipe in recipes.values():
            self.assertNotIn("draught_animal_kg", recipe.plant_goods)


if __name__ == "__main__":
    unittest.main()
