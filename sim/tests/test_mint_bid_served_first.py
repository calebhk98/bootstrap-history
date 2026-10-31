"""A mint that pays more for bullion than the market asks is served ahead of buyers who pay the ask
(sim/economy/mint.py, goods_market_ration.ration; Complaint 473)."""

QUICK_TOPIC = True

import unittest

from sim.economy import mint
from sim.economy.goods_market_ration import ration
from sim.economy.types import EDGE_MINT, Bid

METAL = "silver_kg"


def household_style_bid(priority):
    return Bid("ornament_maker", METAL, "area", "t1", 0.0, 100.0, 1.0, 0.0, float("inf"), priority)


class MintBidPriority(unittest.TestCase):
    def test_scarce_bullion_goes_to_the_mint_before_buyers_who_pay_no_more_than_the_ask(self):
        mint_bid = Bid(EDGE_MINT, METAL, "area", "t1", 0.0, 60.0, 95.0, 0.0, float("inf"), mint.MINT_PRIORITY,
                       maximum_price=95.0)
        bids = sorted([household_style_bid(0), household_style_bid(1), mint_bid], key=lambda bid: bid.priority)
        served = ration(bids, [bid.flexible_quantity for bid in bids], 70.0)
        self.assertEqual(served[bids.index(mint_bid)], 60.0)


if __name__ == "__main__":
    unittest.main()
