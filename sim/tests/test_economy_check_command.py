"""`simulator.py economy-check` (Complaint 445): the command's loop and printing run on a literal health report."""
import contextlib
import io
import unittest

QUICK_TOPIC = True


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
        from sim.ui import cli_economy_check
        args = type("Args", (), {"years": 1, "seeds": "1", "civs": "rome_100ad", "metals": "", "staple": "",
                                 "payback": True})()
        output = io.StringIO()
        played = cli_economy_check.check_one
        cli_economy_check.check_one = lambda *arguments, **keywords: self.HEALTH
        try:
            with contextlib.redirect_stdout(output):
                cmd_economy_check(args)
        finally:
            cli_economy_check.check_one = played
        self.assertIn("diagnostic only", output.getvalue())


class StapleMeasuredTests(unittest.TestCase):
    def test_a_staple_whose_price_is_not_a_trade_is_unmeasured_with_its_cause(self):
        from sim.ui.cli_economy_check import staple_figure_cause
        self.assertEqual(staple_figure_cause("grain", {"grain": "thin_trade_blend"}), "price_not_a_trade")
        self.assertEqual(staple_figure_cause("grain", {}), "price_not_a_trade")
        self.assertIsNone(staple_figure_cause("grain", {"grain": "smoothed_trade"}))
        self.assertEqual(staple_figure_cause(None, {}), "no_good")

    def test_an_unmeasured_figure_prints_its_cause_not_a_number(self):
        from sim.ui.cli_economy_check import figure_text
        self.assertEqual(figure_text(0.0, "price_not_a_trade"), "unmeasured: price_not_a_trade")
        self.assertEqual(figure_text(0.125, None), "0.125")


if __name__ == "__main__":
    unittest.main()
