"""A line typed at the Options menu that is not a choice is handed back to the game prompt, so a piped command still runs
(Complaints/161). `_ingame_options` called on a stand-in game with `input` supplied; nothing is built. Whether the menu prints
once is presentation and is not asserted."""
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.ui import cli_interactive

QUICK_TOPIC = True


def options_with(typed_lines):
    game = SimpleNamespace(civ={"id": "rome_100ad", "name": "Rome"}, cfg={"start_year": 100, "horizon_years": 500, "immortal": True},
                           fog=False, fuzzy_estimates=False, year=100, end_year=600)
    cli_interactive.LINES_PUSHED_BACK.clear()
    with mock.patch("builtins.input", side_effect=list(typed_lines)), mock.patch("builtins.print"), \
            mock.patch.object(cli_interactive.cli_units_options, "summary_line", return_value="units"), \
            mock.patch.object(cli_interactive.settings, "load_config", return_value={}):
        returned = cli_interactive._ingame_options(game, None)
    pushed = list(cli_interactive.LINES_PUSHED_BACK)
    cli_interactive.LINES_PUSHED_BACK.clear()
    return returned, pushed


class OptionsMenuPushback(unittest.TestCase):

    def test_a_line_that_is_not_a_choice_goes_back_to_the_game_prompt(self):
        returned, pushed = options_with(["state"])
        self.assertIsNone(returned)
        self.assertEqual(pushed, ["state"])

    def test_back_pushes_nothing(self):
        _returned, pushed = options_with(["b"])
        self.assertEqual(pushed, [])

    def test_an_empty_line_pushes_nothing(self):
        _returned, pushed = options_with([""])
        self.assertEqual(pushed, [])

    def test_the_line_is_pushed_as_typed(self):
        _returned, pushed = options_with(["Step 3"])
        self.assertEqual(pushed, ["Step 3"])


if __name__ == "__main__":
    unittest.main()
