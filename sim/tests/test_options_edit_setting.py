"""The main menu's Options screen is generated from the settings table and saves what is set on it (Complaint 363).
`cli_options._edit_setting` is called with the typed answer fed in and the save replaced by a recorder; `screen_lines` is called
on a config written out. The table, the `options` command and the dice are rule tests in `test_options_from_settings_table`."""
import unittest
from unittest import mock

from sim.engine import settings_table
from sim.ui import cli_options

QUICK_TOPIC = True


def edited(key, typed):
    """(config after, what was saved) when `typed` is answered to the prompt for the setting `key`."""
    saved = []
    with mock.patch("builtins.input", side_effect=list(typed)), \
            mock.patch.object(cli_options.settings, "save_config", side_effect=lambda cfg: saved.append(dict(cfg))), \
            mock.patch("builtins.print"):
        cfg = cli_options._edit_setting({}, key)
    return cfg, saved


class EditSettingTests(unittest.TestCase):
    def test_commission_display_can_be_set_from_the_menu(self):
        cfg, saved = edited("commission_display", ["ready"])
        self.assertEqual(cfg["commission_display"], "ready")
        self.assertEqual(saved, [cfg])

    def test_a_default_seed_word_can_be_set_from_the_menu(self):
        cfg, _saved = edited("default_seed", ["dragon"])
        self.assertEqual(cfg["default_seed"], "dragon")

    def test_events_can_be_turned_off_from_the_menu(self):
        cfg, _saved = edited("default_events", ["n"])
        self.assertIs(cfg["default_events"], False)

    def test_deterministic_mode_can_be_turned_on_from_the_menu(self):
        cfg, _saved = edited("default_deterministic", ["y"])
        self.assertIs(cfg["default_deterministic"], True)

    def test_an_answer_that_does_not_fit_saves_nothing(self):
        cfg, saved = edited("commission_display", ["no such choice"])
        self.assertEqual((cfg, saved), ({}, []))


class ScreenTests(unittest.TestCase):
    # presentation: the screen's rows are text
    def test_the_screen_has_a_row_per_setting_and_marks_the_game_start_ones(self):
        lines = settings_table.screen_lines({})
        self.assertEqual(len(lines), len(settings_table.SETTINGS))
        for line, (key, spec) in zip(lines, settings_table.SETTINGS.items()):
            self.assertIn(spec.label, line)
            self.assertEqual("applies when a game starts" in line, bool(spec.at_game_start), key)


if __name__ == "__main__":
    unittest.main()
