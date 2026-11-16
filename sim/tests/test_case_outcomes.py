"""The test runner's record of a test class's outcomes (`sim.tests.__main__._CaseOutcomes`): a test marked as an expected
failure that passes is a problem, and a skip is recorded with its reason, so neither reads as an ordinary pass."""
QUICK_TOPIC = True

import unittest

from sim.tests.__main__ import _CaseOutcomes


def _cases():
    """A class of sample tests, built here so the runner does not collect it as one of this topic's own."""
    class Cases(unittest.TestCase):
        @unittest.expectedFailure
        def test_marked_but_passes(self):
            pass

        @unittest.skip("needs a module this machine lacks")
        def test_skipped(self):
            pass
    return Cases


def _run(name):
    outcomes = _CaseOutcomes()
    case = _cases()(name)
    case.run(outcomes)
    return outcomes, case.id()


class CaseOutcomesTests(unittest.TestCase):
    def test_an_expected_failure_that_passes_is_a_problem(self):
        outcomes, test_id = _run("test_marked_but_passes")
        self.assertIn("unexpectedly passed", outcomes.problems.get(test_id, ""))

    def test_a_skip_is_recorded_with_its_reason(self):
        outcomes, test_id = _run("test_skipped")
        self.assertEqual(outcomes.skips.get(test_id), "needs a module this machine lacks")
        self.assertNotIn(test_id, outcomes.problems)


if __name__ == "__main__":
    unittest.main()
