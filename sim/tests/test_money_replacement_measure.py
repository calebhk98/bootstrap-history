"""`money_replacement` (Complaint 473): the coin the mint struck, net of what it melted, over the coin worn. A rule
test: the rows are built here, no game is run."""
import math
import unittest

from sim.economy.baseline_checks import money_replacement

QUICK_TOPIC = True


def rows_of(struck_by_year, wear_per_year=10.0):
    return [{"wear": wear_per_year, "struck": struck} for struck in struck_by_year]


class MoneyReplacementMeasure(unittest.TestCase):
    def test_striking_equal_to_wear_is_full_replacement(self):
        self.assertAlmostEqual(money_replacement(rows_of([10.0, 10.0]), 2), 1.0)

    def test_a_year_of_melting_counts_against_the_years_that_struck(self):
        # the mint sells metal when it is dearer than coin; coin taken back for it is struck less melted
        self.assertAlmostEqual(money_replacement(rows_of([20.0, -20.0]), 2), 0.0)

    def test_net_melting_over_the_window_is_negative_replacement(self):
        self.assertLess(money_replacement(rows_of([5.0, -15.0]), 2), 0.0)

    def test_only_the_last_window_years_are_read(self):
        self.assertAlmostEqual(money_replacement(rows_of([-100.0, 10.0]), 1), 1.0)

    def test_no_wear_is_unbounded_replacement(self):
        self.assertTrue(math.isinf(money_replacement(rows_of([3.0], wear_per_year=0.0), 1)))


if __name__ == "__main__":
    unittest.main()
