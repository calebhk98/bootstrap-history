"""What a goods market that traded nothing tells its sellers about the price next year."""
import unittest

from sim.economy.types import Bid, Offer
from sim.economy.year_goods import _unsold_signal


def bid(maximum_price):
    return Bid("buyer", "timber", "area", "tile", 10.0, 0.0, 1.0, 1.0, 1e9, 0, maximum_price=maximum_price)


def offer(reservation, quantity=5.0):
    return Offer("seller", "timber", "area", "tile", quantity, reservation)


class UnsoldSignalTests(unittest.TestCase):
    def test_sellers_asking_above_every_buyer_learn_the_most_a_buyer_would_pay(self):
        self.assertEqual(_unsold_signal([bid(3.0), bid(4.0)], [offer(6.0)]), 4.0)

    def test_a_seller_asking_less_than_buyers_pay_learns_nothing_from_a_dry_market(self):
        # nothing traded because nothing real was on offer (rounding dust), not because the ask was too high
        self.assertIsNone(_unsold_signal([bid(3.0), bid(4.0)], [offer(0.0, quantity=1e-10)]))

    def test_no_offers_no_signal(self):
        self.assertIsNone(_unsold_signal([bid(4.0)], []))


if __name__ == "__main__":
    unittest.main()
