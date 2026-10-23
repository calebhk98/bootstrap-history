"""A year that raises is undone whole and described; a year that runs is left alone; a step whose first year failed is
not ok; a step that kept some years and then failed says where it stopped. The functions are called on a stand-in game
with the restore replaced (the restore is the save-load road, which has its own tests). The description of the failed
year is test_complaint_587_atomic_year."""
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.refusal import cause_of
from sim.ui.proto import step_atomic

QUICK_TOPIC = True

HELD = '{"year":100}'


class YearTransaction(unittest.TestCase):

    def setUp(self):
        self.game = SimpleNamespace(year=103)
        self.effects = []

    def run_year(self, fail):
        def phase():
            self.effects.append(self.game.year)
            if fail:
                raise RuntimeError("forced failure")
        with mock.patch.object(step_atomic, "restore_state_text") as restore:
            result = step_atomic.run_year_or_undo(self.game, HELD, phase, 2)
        return result, restore

    def test_a_year_that_runs_returns_none_and_restores_nothing(self):
        result, restore = self.run_year(fail=False)
        self.assertIsNone(result)
        restore.assert_not_called()

    def test_a_year_that_raises_restores_the_held_text_and_names_the_failure(self):
        result, restore = self.run_year(fail=True)
        restore.assert_called_once_with(self.game, HELD)
        self.assertEqual((result["cause"], result["exception_kind"], result["year"], result["years_ran"]),
                         ("year_failed", "RuntimeError", 103, 2))

    def test_the_retry_after_a_failure_runs_the_phase_once_more_and_succeeds(self):
        self.run_year(fail=True)
        result, _restore = self.run_year(fail=False)
        self.assertIsNone(result)
        self.assertEqual(self.effects, [103, 103])

    def test_a_failure_that_is_not_an_exception_subclass_of_exception_is_not_swallowed(self):
        def interrupted():
            raise KeyboardInterrupt
        with mock.patch.object(step_atomic, "restore_state_text"), self.assertRaises(KeyboardInterrupt):
            step_atomic.run_year_or_undo(self.game, HELD, interrupted, 0)


class StepReplies(unittest.TestCase):

    def failure(self):
        with mock.patch.object(step_atomic, "restore_state_text"):
            return step_atomic.failed_year(object(), HELD, RuntimeError("forced"), 103, 2)

    def test_a_step_failing_in_its_first_year_is_not_ok_and_carries_the_cause(self):
        reply = step_atomic.whole_step_failed_reply(self.failure())
        self.assertIs(reply["ok"], False)
        self.assertEqual((reply["exception_kind"], reply["year"]), ("RuntimeError", 103))
        self.assertEqual(cause_of(reply["error"]), "year_failed")

    def test_a_step_that_kept_years_reports_where_it_stopped(self):
        _text, kind, fields = step_atomic.partial_step_failure(self.failure(), 2, 5)
        self.assertEqual(kind, "year_failed")
        self.assertEqual(fields, {"cause": "year_failed", "exception_kind": "RuntimeError", "year": 103, "years_ran": 2})


if __name__ == "__main__":
    unittest.main()
