"""The present value of a claim paying a coupon and a redemption: one function for the state's bonds and the economy's securities."""

QUICK_TOPIC = True

import unittest

from sim.world.capital_market import bullet_value


class BulletValue(unittest.TestCase):
    def test_a_claim_whose_coupon_is_the_rate_is_worth_its_redemption(self):
        self.assertAlmostEqual(bullet_value(5.0, 100.0, 10, 0.05), 100.0)

    def test_one_year_is_the_coupon_and_redemption_discounted_once(self):
        self.assertAlmostEqual(bullet_value(5.0, 100.0, 1, 0.10), 105.0 / 1.10)

    def test_under_a_year_counts_as_one_year(self):
        self.assertAlmostEqual(bullet_value(5.0, 100.0, 0.2, 0.10), 105.0 / 1.10)


if __name__ == "__main__":
    unittest.main()
