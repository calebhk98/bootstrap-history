"""The expected calendar years to succeed at a project are never below the earliest it can finish, and with no risk of
failure they are exactly that (Complaint 230). `expected_years_to_succeed` is called on written-out risks and retains."""
QUICK_TOPIC = True

import unittest

from sim.projects.completion_schedule import expected_years_to_succeed

FLOOR = 8.0


def expected(risk, served=None, retain=0.5, first_attempt=0):
    return expected_years_to_succeed(FLOOR, served, first_attempt, lambda attempt: retain, lambda attempt: risk, 500)


class ExpectedYearsTests(unittest.TestCase):
    def test_with_no_risk_of_failure_the_expectation_is_the_floor(self):
        self.assertAlmostEqual(expected(0.0), FLOOR)

    def test_a_risk_of_failure_adds_the_retries_the_dice_force(self):
        self.assertGreater(expected(0.3), FLOOR)

    def test_a_retry_after_one_failure_takes_the_share_of_the_floor_a_failure_does_not_bank(self):
        # one attempt at the floor, then (with chance one half) one more at half the floor, then a sure success
        calls = []

        def risk(attempt):
            calls.append(attempt)
            return 0.5 if attempt == 0 else 0.0
        total = expected_years_to_succeed(FLOOR, None, 0, lambda attempt: 0.25, risk, 500)
        self.assertAlmostEqual(total, FLOOR + 0.5 * FLOOR * 0.75)
        self.assertEqual(calls, [0, 1])

    def test_an_attempt_already_running_has_its_served_years_taken_off_the_first_attempt(self):
        self.assertAlmostEqual(expected(0.0, served=3.0), FLOOR - 3.0)

    def test_an_attempt_served_past_the_floor_has_nothing_left(self):
        self.assertEqual(expected(0.0, served=FLOOR + 1.0), 0.0)

    def test_a_certain_failure_stops_at_the_cap_on_extra_attempts(self):
        total = expected_years_to_succeed(FLOOR, None, 0, lambda attempt: 0.0, lambda attempt: 1.0, 3)
        self.assertAlmostEqual(total, 4 * FLOOR)


if __name__ == "__main__":
    unittest.main()
