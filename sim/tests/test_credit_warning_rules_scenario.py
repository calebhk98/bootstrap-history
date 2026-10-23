"""SCENARIO (Complaint 640): the credit warnings and the halt as a real household's log and projects show them.
The rules themselves (the warning band, the halt) are tested in test_credit_warning_rules.py."""

import unittest

from .harness import *  # noqa: F401,F403


def game_owing(share_of_limit):
    game = unopened_sim(civ="rome_100ad", capital=500.0)
    game.capital = -share_of_limit * game.credit_limit()
    return game


def kinds(game):
    return [line.kind for _year, line in game.state.household.log if hasattr(line, "kind")]


class CreditWarningsInAGame(unittest.TestCase):
    def test_the_warning_is_logged_once_while_in_the_band_and_again_after_recovery(self):
        game = game_owing(0.8)
        game.warn_near_the_limit(game.year)
        game.warn_near_the_limit(game.year + 1)
        self.assertEqual(kinds(game).count("credit_near_limit"), 1)
        game.capital = 0.0
        game.warn_near_the_limit(game.year + 2)
        game.capital = -0.8 * game.credit_limit()
        game.warn_near_the_limit(game.year + 3)
        self.assertEqual(kinds(game).count("credit_near_limit"), 2)

    def test_past_the_limit_work_in_hand_stops_credit_freezes_and_the_line_says_so(self):
        game = game_owing(1.5)
        game.state.projects.active["a_project"] = {"spent": 40.0}
        year = game.year
        game.answer_exhausted_credit(year)
        self.assertNotIn("a_project", game.state.projects.active)
        self.assertEqual(game.state.household.credit_frozen_until, year + game.CREDIT_FREEZE_YEARS_AFTER_HALT)
        self.assertIn("credit_exhausted", kinds(game))
        self.assertEqual(game.state.projects.paid_towards["a_project"], 40.0)

    def test_inside_the_limit_nothing_is_stopped(self):
        game = game_owing(0.5)
        game.state.projects.active["a_project"] = {"spent": 40.0}
        game.answer_exhausted_credit(game.year)
        self.assertIn("a_project", game.state.projects.active)
        self.assertNotIn("credit_exhausted", kinds(game))


if __name__ == "__main__":
    unittest.main()
