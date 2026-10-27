"""A year that raises is undone whole and described; a year that runs is left alone; a step whose first year failed is
not ok; a step that kept some years and then failed says where it stopped. The functions are called on a stand-in game
with the restore replaced (the restore is the save-load road, which has its own tests). The description of the failed
year is test_complaint_587_atomic_year."""
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.refusal import Refusal
from sim.ui.proto import step_atomic
from sim.tests.ui_stand_in import Game

QUICK_TOPIC = True

HELD = '{"year":100}'


class YearTransaction(unittest.TestCase):

    def setUp(self):
        self.game = Game(year=103)
        self.effects = []

    def run_year(self, fail):
        def phase():
            self.effects.append(self.game.year)
            if fail:
                raise RuntimeError("forced failure")
        with mock.patch.object(step_atomic, "failed_year", return_value="described") as described:
            result = step_atomic.run_year_or_undo(self.game, HELD, phase, 2)
        return result, described

    def test_a_year_that_runs_returns_none(self):
        self.assertIsNone(self.run_year(fail=False)[0])

    def test_a_year_that_runs_describes_no_failure(self):
        self.run_year(fail=False)[1].assert_not_called()

    def test_a_year_that_raises_returns_the_failures_description(self):
        self.assertEqual(self.run_year(fail=True)[0], "described")

    def test_a_year_that_raises_hands_the_held_text_the_error_the_year_and_the_years_run_to_the_description(self):
        _result, described = self.run_year(fail=True)
        (game, held, error, year, years_ran), _kwargs = described.call_args
        self.assertEqual((game, held, type(error), year, years_ran), (self.game, HELD, RuntimeError, 103, 2))

    def test_the_phase_is_run_each_time_it_is_called(self):
        self.run_year(fail=True)
        self.run_year(fail=False)
        self.assertEqual(self.effects, [103, 103])

    def test_an_interrupt_is_not_swallowed(self):
        def interrupted():
            raise KeyboardInterrupt
        with mock.patch.object(step_atomic, "failed_year"), self.assertRaises(KeyboardInterrupt):
            step_atomic.run_year_or_undo(self.game, HELD, interrupted, 0)


FAILURE = {"cause": "year_failed", "exception_kind": "RuntimeError", "year": 103, "years_ran": 2,
           "text": Refusal("year_failed", "year 103 did not run", exception_kind="RuntimeError", year=103)}


class StepReplies(unittest.TestCase):

    def test_a_step_failing_in_its_first_year_is_not_ok(self):
        self.assertIs(step_atomic.whole_step_failed_reply(FAILURE)["ok"], False)

    def test_a_step_failing_in_its_first_year_carries_the_kind_and_year(self):
        reply = step_atomic.whole_step_failed_reply(FAILURE)
        self.assertEqual((reply["exception_kind"], reply["year"]), ("RuntimeError", 103))

    def test_a_step_failing_in_its_first_year_carries_the_failures_text_as_its_error(self):
        self.assertIs(step_atomic.whole_step_failed_reply(FAILURE)["error"], FAILURE["text"])

    def test_a_step_that_kept_years_reports_where_it_stopped(self):
        _text, kind, fields = step_atomic.partial_step_failure(FAILURE, 2, 5)
        self.assertEqual(kind, "year_failed")
        self.assertEqual(fields, {"cause": "year_failed", "exception_kind": "RuntimeError", "year": 103, "years_ran": 2})


if __name__ == "__main__":
    unittest.main()
