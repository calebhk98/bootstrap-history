"""The seed a `play` sitting uses (ui/cli_interactive.resolve_seed): the one asked for, else the one the environment
fixes, else a fresh draw. Asked seeds are normalised as the game keeps them (normal_seed, test_seed_saved_both_modes)."""
QUICK_TOPIC = True

import os
import unittest
from unittest import mock

from sim.ui.cli_interactive import DEFAULT_SEED_ENV, resolve_seed


class ResolveSeedTests(unittest.TestCase):
    def test_an_asked_seed_is_kept_as_the_game_keeps_it(self):
        with mock.patch.dict(os.environ, {DEFAULT_SEED_ENV: "99"}):
            self.assertEqual(resolve_seed("7"), 7)
            self.assertEqual(resolve_seed("Dragon"), "dragon")

    def test_without_one_asked_the_environments_fixed_seed_is_used(self):
        with mock.patch.dict(os.environ, {DEFAULT_SEED_ENV: "99"}):
            self.assertEqual(resolve_seed(None), 99)

    def test_a_fixed_word_seed_is_lower_case(self):
        with mock.patch.dict(os.environ, {DEFAULT_SEED_ENV: "Rome42"}):
            self.assertEqual(resolve_seed(None), "rome42")

    def test_with_neither_the_seed_is_a_fresh_positive_whole_number(self):
        with mock.patch.dict(os.environ):
            os.environ.pop(DEFAULT_SEED_ENV, None)
            drawn = resolve_seed(None)
        self.assertIsInstance(drawn, int)
        self.assertTrue(0 < drawn < 2 ** 31)


if __name__ == "__main__":
    unittest.main()
