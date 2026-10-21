"""Complaint 587: a year that raises leaves the game as it was, and the reply says so with a cause. The description of the
failed year is `step_atomic.failed_year`, called with the restore stubbed out. (A whole game failing in a year, the retry
running the year once, and a multi-year step keeping the years before the failure: test_scenario_atomic_year.)"""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.refusal import cause_of, facts_of
from sim.ui.proto import step_atomic

HELD = '{"year":100}'


class FailedYearTests(unittest.TestCase):
    def failed(self, error=None, year=101, years_ran=2):
        game = object()
        with mock.patch.object(step_atomic, "restore_state_text") as restore:
            description = step_atomic.failed_year(game, HELD, error or RuntimeError("forced failure"), year, years_ran)
        return game, restore, description

    def test_the_game_is_restored_from_the_text_held_before_the_year(self):
        game, restore, _description = self.failed()
        restore.assert_called_once_with(game, HELD)

    def test_the_description_has_the_cause_year_failed(self):
        description = self.failed()[2]
        self.assertEqual(description["cause"], "year_failed")
        self.assertEqual(cause_of(description["text"]), "year_failed")

    def test_it_names_the_exceptions_kind(self):
        self.assertEqual(self.failed(RuntimeError("x"))[2]["exception_kind"], "RuntimeError")
        self.assertEqual(self.failed(KeyError("x"))[2]["exception_kind"], "KeyError")
        self.assertEqual(facts_of(self.failed(KeyError("x"))[2]["text"])["exception_kind"], "KeyError")

    def test_it_says_which_year_failed_and_how_many_ran_before_it(self):
        description = self.failed(year=103, years_ran=2)[2]
        self.assertEqual((description["year"], description["years_ran"]), (103, 2))
        self.assertEqual(facts_of(description["text"])["year"], 103)

    def test_the_text_says_the_game_is_as_it_was_and_to_step_again(self):
        # presentation: the sentence a player reads
        text = str(self.failed()[2]["text"])
        self.assertIn("the game is as it was before that year", text)
        self.assertIn("Step again to retry it", text)


class SnapshotTests(unittest.TestCase):
    def test_the_snapshot_is_the_games_state_text(self):
        with mock.patch.object(step_atomic, "state_text", lambda game: HELD):
            self.assertEqual(step_atomic.snapshot(object()), HELD)


if __name__ == "__main__":
    unittest.main()
