"""The staffing wage reference is a typical wage, not one dragged up by a scarce trade."""
QUICK_TOPIC = True

import unittest

from sim.labour.staff_wage_reference import blended_annual_wage


class BlendedAnnualWageTests(unittest.TestCase):
    def test_a_scarce_trade_far_above_the_rest_does_not_move_the_reference_out_of_the_range_of_the_others(self):
        ordinary = [20.0, 30.0, 40.0, 50.0, 60.0]
        reference = blended_annual_wage(ordinary + [600000.0])
        self.assertGreaterEqual(reference, min(ordinary))
        self.assertLessEqual(reference, max(ordinary))

    def test_equal_wages_blend_to_that_wage(self):
        self.assertEqual(blended_annual_wage([40.0, 40.0, 40.0]), 40.0)

    def test_no_wages_give_none_not_zero(self):
        self.assertIsNone(blended_annual_wage([]))


if __name__ == "__main__":
    unittest.main()
