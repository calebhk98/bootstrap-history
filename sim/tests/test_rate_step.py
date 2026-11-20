"""rate_step: the interest rate the economy remembers after a year's lending."""

QUICK_TOPIC = True

import unittest

from sim.economy.rate_step import the_cleared_rate, toward_the_cleared_rate


class TheClearedRate(unittest.TestCase):
    def test_the_years_cleared_rate_is_remembered_whole(self):
        self.assertEqual(the_cleared_rate(0.04, 0.12), 0.12)
        self.assertEqual(the_cleared_rate(None, 0.12), 0.12)


class TowardTheClearedRate(unittest.TestCase):
    def test_last_years_rate_moves_the_share_of_the_way(self):
        self.assertAlmostEqual(toward_the_cleared_rate(0.04, 0.12, share=0.5), 0.08)
        self.assertAlmostEqual(toward_the_cleared_rate(0.04, 0.12, share=0.25), 0.06)

    def test_a_rise_and_a_fall_of_equal_gaps_move_by_equal_amounts(self):
        rise = toward_the_cleared_rate(0.05, 0.07, share=0.5) - 0.05
        fall = 0.05 - toward_the_cleared_rate(0.05, 0.03, share=0.5)
        self.assertAlmostEqual(rise, fall)

    def test_a_rate_at_the_cleared_rate_stays(self):
        self.assertAlmostEqual(toward_the_cleared_rate(0.05, 0.05, share=0.5), 0.05)

    def test_with_no_rate_remembered_the_cleared_rate_is_taken_whole(self):
        self.assertEqual(toward_the_cleared_rate(None, 0.12, share=0.5), 0.12)

    def test_repeated_years_close_on_a_steady_cleared_rate(self):
        rate = 0.04
        for _year in range(30):
            rate = toward_the_cleared_rate(rate, 0.12, share=0.5)
        self.assertAlmostEqual(rate, 0.12, places=6)


if __name__ == "__main__":
    unittest.main()
