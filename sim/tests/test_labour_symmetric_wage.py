"""wage_step.symmetric_wage: last year's wage moved a share of the way to where it is headed (the goal, or the floor where that is higher), under the ceiling."""

QUICK_TOPIC = True

import unittest

from sim.labour.market.wage_step import symmetric_wage

NO_CEILING = 1e9


class SymmetricWage(unittest.TestCase):
    def test_no_last_wage_gives_the_goal(self):
        self.assertEqual(symmetric_wage(None, 3.0, 1.0, NO_CEILING, share=0.5), 3.0)

    def test_a_rise_moves_the_share_of_the_gap(self):
        self.assertAlmostEqual(symmetric_wage(2.0, 4.0, 1.0, NO_CEILING, share=0.5), 2.0 + 0.5 * (4.0 - 2.0))
        self.assertAlmostEqual(symmetric_wage(2.0, 4.0, 1.0, NO_CEILING, share=0.25), 2.0 + 0.25 * (4.0 - 2.0))

    def test_a_rise_and_a_fall_of_equal_gaps_move_by_equal_amounts(self):
        for share in (0.5, 0.25):
            rise = symmetric_wage(3.0, 5.0, 1.0, NO_CEILING, share=share) - 3.0
            fall = 3.0 - symmetric_wage(3.0, 1.0, 0.0, NO_CEILING, share=share)
            self.assertAlmostEqual(rise, fall)
            self.assertAlmostEqual(rise, share * 2.0)

    def test_last_equal_to_goal_stays(self):
        self.assertAlmostEqual(symmetric_wage(2.5, 2.5, 1.0, NO_CEILING, share=0.5), 2.5)

    def test_a_goal_under_the_floor_heads_for_the_floor(self):
        # the wage heads for the floor of 2.0, not for the goal of 0.0: 3.0 + 0.5 * (2.0 - 3.0)
        self.assertAlmostEqual(symmetric_wage(3.0, 0.0, 2.0, NO_CEILING, share=0.5), 2.5)
        self.assertEqual(symmetric_wage(None, 0.5, 2.0, NO_CEILING, share=0.5), 2.0)

    def test_a_floor_that_rose_above_last_years_wage_is_approached_by_the_share_and_not_jumped_to(self):
        # 1.0 + 0.5 * (3.0 - 1.0)
        self.assertAlmostEqual(symmetric_wage(1.0, 0.5, 3.0, NO_CEILING, share=0.5), 2.0)
        self.assertAlmostEqual(symmetric_wage(1.0, 0.5, 3.0, NO_CEILING, share=0.25), 1.5)

    def test_a_wage_at_or_above_the_floor_does_not_cross_under_it(self):
        for last in (2.0, 2.5, 7.0):
            for goal in (0.0, 1.0, 2.0, 9.0):
                self.assertGreaterEqual(symmetric_wage(last, goal, 2.0, NO_CEILING, share=0.5), 2.0)

    def test_ceiling_caps(self):
        # 2.0 + 0.5 * (10.0 - 2.0) = 6.0, over the ceiling of 4.0
        self.assertEqual(symmetric_wage(2.0, 10.0, 1.0, 4.0, share=0.5), 4.0)

    def test_ceiling_below_floor_returns_the_floor(self):
        self.assertEqual(symmetric_wage(2.0, 3.0, 2.0, 1.0, share=0.5), 2.0)


if __name__ == "__main__":
    unittest.main()
