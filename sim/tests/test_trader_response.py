"""Merchants have a cost and a response: a thin gap does not move goods (Complaints/339)."""

QUICK_TOPIC = True

import unittest

from sim.world import trader_response


class CostTests(unittest.TestCase):
    def test_cost_share_adds_margin_loss_and_interest_over_the_cycle(self):
        share = trader_response.cost_share_of_price(
            margin_share=0.02, loss_share=0.01, market_rate=0.10, cycle_years=0.5)
        self.assertAlmostEqual(share, 0.02 + 0.01 / 0.99 + 0.05)

    def test_a_longer_cycle_or_a_higher_rate_costs_more(self):
        base = trader_response.cost_share_of_price(0.02, 0.0, 0.10, 0.5)
        self.assertGreater(trader_response.cost_share_of_price(0.02, 0.0, 0.10, 1.0), base)
        self.assertGreater(trader_response.cost_share_of_price(0.02, 0.0, 0.20, 0.5), base)


if __name__ == "__main__":
    unittest.main()
