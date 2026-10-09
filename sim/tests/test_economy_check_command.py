"""`simulator.py economy-check` (Complaint 445): plays a short game and prints the agent economy's health."""
import contextlib
import io
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
        for _year in range(2):
            cls.game.step()

    def test_the_port_reports_the_economys_health(self):
        report = self.game.economy.health()
        self.assertEqual(report["years"], 2)
        self.assertTrue(report["staple"])
        for figure in ("staple_volatility", "metal_volatility", "hired_share", "hunger_share", "staple_over_labour",
                       "unskilled_wage", "wage_floor", "wage_over_floor"):
            self.assertIn(figure, report["figures"])
        self.assertTrue(0.0 <= report["figures"]["hunger_share"] <= 1.0)


class EconomyCheckRendering(unittest.TestCase):
    """The command's own loop and printing, on a literal health report instead of a played game."""

    HEALTH = {"years": 2, "staple": "grain", "metals": ["iron", "copper"],
              "figures": {"staple_volatility": 0.12, "metal_volatility": 0.05, "hired_share": 0.8,
                          "hunger_share": 0.01, "staple_over_labour": 1.5, "unskilled_wage": 0.15,
                          "wage_floor": 0.1, "wage_over_floor": 1.5}}

    def test_the_command_prints_a_section_per_civilisation_and_seed(self):
        from sim.ui import cli_economy_check
        from sim.ui.cli_economy_check import cmd_economy_check
        args = type("Args", (), {"years": 2, "seeds": "1", "civs": "rome_100ad", "metals": "", "staple": ""})()
        output = io.StringIO()
        played = cli_economy_check.check_one
        cli_economy_check.check_one = lambda *arguments, **keywords: self.HEALTH
        try:
            with contextlib.redirect_stdout(output):
                cmd_economy_check(args)
        finally:
            cli_economy_check.check_one = played
        text = output.getvalue()
        for expected in ("rome_100ad", "seed 1", "staple", "hired_share", "hunger_share", "staple_over_labour",
                         "wage_over_floor"):
            self.assertIn(expected, text)

    def test_the_payback_flag_prints_the_diagnostic_section(self):
        from sim.ui.cli_economy_check import cmd_economy_check
        args = type("Args", (), {"years": 1, "seeds": "1", "civs": "rome_100ad", "metals": "", "staple": "",
                                 "payback": True})()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_economy_check(args)
        self.assertIn("diagnostic only", output.getvalue())


if __name__ == "__main__":
    unittest.main()
