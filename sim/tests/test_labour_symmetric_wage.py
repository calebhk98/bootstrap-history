"""wage_step.symmetric_wage: last year's wage moved a share of the way to the goal, held between floor and ceiling."""

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

    def test_never_under_the_floor(self):
        # 3.0 + 0.5 * (0.0 - 3.0) = 1.5, under the floor of 2.0
        self.assertEqual(symmetric_wage(3.0, 0.0, 2.0, NO_CEILING, share=0.5), 2.0)
        self.assertEqual(symmetric_wage(None, 0.5, 2.0, NO_CEILING, share=0.5), 2.0)

    def test_ceiling_caps(self):
        # 2.0 + 0.5 * (10.0 - 2.0) = 6.0, over the ceiling of 4.0
        self.assertEqual(symmetric_wage(2.0, 10.0, 1.0, 4.0, share=0.5), 4.0)

    def test_ceiling_below_floor_returns_the_floor(self):
        self.assertEqual(symmetric_wage(2.0, 3.0, 2.0, 1.0, share=0.5), 2.0)


if __name__ == "__main__":
    unittest.main()
