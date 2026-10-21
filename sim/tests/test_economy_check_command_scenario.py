"""SCENARIO: a short game is played and the economy's health report is read (`simulator.py economy-check` renders it;
the rendering rules are in test_economy_check_command.py)."""
import random
import unittest

from sim.engine.ui_port import Sim, load, load_civ


class EconomyCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _tree, _prices, nodes, _wages, _goods = load()
        cls.game = Sim(nodes, [], random.Random(1), events=False, manual=True,
                       civ=load_civ("rome_100ad"))
        cls.game.done_year = {}
        cls.game.step()

    def test_scenario_the_port_reports_the_economys_health(self):
        report = self.game.economy.health()
        self.assertEqual(report["years"], 1)
        self.assertTrue(report["staple"])
        for figure in ("staple_volatility", "metal_volatility", "hired_share", "hunger_share", "staple_over_labour",
                       "unskilled_wage", "wage_floor", "wage_over_floor"):
            self.assertIn(figure, report["figures"])
        self.assertTrue(0.0 <= report["figures"]["hunger_share"] <= 1.0)


if __name__ == "__main__":
    unittest.main()
