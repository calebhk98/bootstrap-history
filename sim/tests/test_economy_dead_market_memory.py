"""Complaint 502: a market that trades next to nothing does not keep its remembered price indefinitely: the
memory relaxes toward what the good costs to make, at the no-offer rate, the less the trade reaches what counts
as a representative trade of the market's usual volume; a market that trades representatively is untouched."""

QUICK_TOPIC = True

import unittest

from sim.economy.market_memory_asks import REPRESENTATIVE_TRADE_SHARE
from sim.economy.market_memory_offers import NO_OFFER_MEMORY_SHARE, price_after_thin_trade


class DeadMarketMemoryTests(unittest.TestCase):
    def test_a_representative_trade_leaves_the_price_alone(self):
        self.assertEqual(price_after_thin_trade(100.0, 10.0, 1000.0 * REPRESENTATIVE_TRADE_SHARE, 1000.0), 100.0)

    def test_no_trade_closes_the_no_offer_share_of_the_gap_to_cost(self):
        expected = 100.0 + NO_OFFER_MEMORY_SHARE * (10.0 - 100.0)
        self.assertAlmostEqual(price_after_thin_trade(100.0, 10.0, 0.0, 1000.0), expected)

    def test_a_sliver_of_trade_relaxes_almost_as_far_as_none(self):
        none = price_after_thin_trade(100.0, 10.0, 0.0, 1000.0)
        sliver = price_after_thin_trade(100.0, 10.0, 1.0, 1000.0)
        half = price_after_thin_trade(100.0, 10.0, 0.5 * REPRESENTATIVE_TRADE_SHARE * 1000.0, 1000.0)
        self.assertLess(none, sliver)
        self.assertLess(sliver, half)
        self.assertLess(half, 100.0)

    def test_a_price_below_cost_is_left_to_the_no_offer_rule(self):
        self.assertEqual(price_after_thin_trade(1.0, 10.0, 0.0, 1000.0), 1.0)

    def test_without_a_cost_or_a_volume_the_price_stands(self):
        self.assertEqual(price_after_thin_trade(100.0, None, 0.0, 1000.0), 100.0)
        self.assertEqual(price_after_thin_trade(100.0, 10.0, 0.0, 0.0), 100.0)


if __name__ == "__main__":
    unittest.main()
