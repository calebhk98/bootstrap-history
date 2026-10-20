"""The concentration measures: top-decile share and Gini over holders' hectares."""

QUICK_TOPIC = True

import unittest

from sim.economy import titles_concentration


class MeasureTests(unittest.TestCase):
    def test_equal_holdings_have_no_inequality(self):
        self.assertAlmostEqual(titles_concentration.gini([5.0] * 10), 0.0)
        self.assertAlmostEqual(titles_concentration.top_decile_share([5.0] * 10), 0.1)

    def test_one_holder_with_everything_is_total_concentration(self):
        holdings = [0.0] * 9 + [100.0]
        self.assertAlmostEqual(titles_concentration.top_decile_share(holdings), 1.0)
        self.assertAlmostEqual(titles_concentration.gini(holdings), 0.9)

    def test_no_land_reads_as_zero(self):
        self.assertEqual(titles_concentration.gini([0.0, 0.0]), 0.0)
        self.assertEqual(titles_concentration.top_decile_share([]), 0.0)


if __name__ == "__main__":
    unittest.main()
