"""The goods-market root finder bisects when both ends of its bracket show the same excess (a crossing landed
exactly on a buyer's ceiling) instead of dividing by their difference; the full Rome spin-up met this."""
QUICK_TOPIC = True

import unittest

from sim.economy import goods_market_solve


class EqualExcessTests(unittest.TestCase):
    def test_a_bracket_with_equal_excess_at_both_ends_still_returns_a_price_inside_it(self):
        supply = 10.0
        price = goods_market_solve._root(lambda _price: supply, 1.0, 0.0, 2.0, 0.0, supply)
        self.assertTrue(1.0 <= price <= 2.0)


if __name__ == "__main__":
    unittest.main()
