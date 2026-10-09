"""Whole games (slow; builds the agent economy, about half an hour cold): idle labour, the wage against its
floor, and price over labour cost, as `simulator.py economy-check` prints them (Complaint 398). Prints the
figures so a run can be compared before and after a change; asserts only what must hold whatever the
numbers are. Run with `python3 -m sim.tests --slow --only labour_margins_whole_game`."""

import math
import random
import unittest

from sim.engine.ui_port import Sim, load, load_civ
from sim.ui.cli_economy_check import FIGURE_LABELS

YEARS = 12


def play(civ_id, seed=1):
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(seed), events=False, manual=True, civ=load_civ(civ_id),
               cfg={"agent_economy": True})
    game.done_year = {}
    for _year in range(YEARS):
        game.step()
    return game


class WholeGameFigures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rome = play("rome_100ad")
        cls.report = cls.rome.economy.health()
        for key, meaning in FIGURE_LABELS:
            print("rome_100ad %-20s %s  %s" % (key, cls.report["figures"].get(key), meaning))

    def test_every_decomposition_figure_is_reported(self):
        for key, _meaning in FIGURE_LABELS:
            self.assertIn(key, self.report["figures"])

    def test_some_hours_are_hired_and_none_beyond_those_offered(self):
        self.assertTrue(0.0 < self.report["figures"]["hired_share"] <= 1.0)

    def test_the_unskilled_wage_never_falls_below_the_floor(self):
        figures = self.report["figures"]
        if not math.isnan(figures["wage_over_floor"]):
            self.assertGreaterEqual(figures["wage_over_floor"], 1.0 - 1e-6)

    def test_no_one_starves_on_the_new_floor(self):
        self.assertLess(self.report["figures"]["hunger_share"], 0.2)

    def test_a_society_that_keeps_draught_animals_ploughs_with_a_team(self):
        recipes = self.rome.economy.agent.economy().setup.recipes
        self.assertIn("wheat_kg", recipes)
        self.assertIn("draught_animal_kg", recipes["wheat_kg"].plant_goods)

    def test_a_society_without_draught_animals_grows_wheat_and_its_other_crops_by_hand(self):
        recipes = play("mexica_1500").economy.agent.economy().setup.recipes
        self.assertNotIn("wheat_kg", recipes)
        self.assertIn("wheat_hoe_kg", recipes)
        for recipe in recipes.values():
            self.assertNotIn("draught_animal_kg", recipe.plant_goods)


if __name__ == "__main__":
    unittest.main()
