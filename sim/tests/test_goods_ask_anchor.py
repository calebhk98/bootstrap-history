"""A seller that sold out does not drift its ask down by construction: the pull of its expectation toward cost is
withheld while buyers go unserved (ask_adjust.regressive_weight), and a stock the seller expects to sell within the
year is asked at the price it expects, not at the lower price it would accept to carry it (seller_offers.expected_ask)."""

QUICK_TOPIC = True

import unittest

from sim.economy import ask_adjust, seller_offers


class RegressiveWeightTest(unittest.TestCase):
    def test_a_sold_out_seller_is_not_pulled_toward_cost(self):
        self.assertEqual(ask_adjust.regressive_weight(0.3, 1.0), 0.0)

    def test_a_seller_at_its_target_keeps_the_full_pull(self):
        self.assertEqual(ask_adjust.regressive_weight(0.3, 0.0), 0.3)

    def test_a_seller_holding_a_surplus_keeps_the_full_pull(self):
        self.assertEqual(ask_adjust.regressive_weight(0.3, -1.0), 0.3)

    def test_half_sold_out_is_half_the_pull(self):
        self.assertAlmostEqual(ask_adjust.regressive_weight(0.3, 0.5), 0.15)


class ExpectedAskTest(unittest.TestCase):
    def test_stock_within_expected_sales_asks_the_expected_price(self):
        self.assertEqual(seller_offers.expected_ask(0.9, 1.0, 50.0, 100.0), 1.0)

    def test_stock_beyond_expected_sales_keeps_the_holding_reservation(self):
        self.assertEqual(seller_offers.expected_ask(0.9, 1.0, 150.0, 100.0), 0.9)

    def test_no_expectation_keeps_the_reservation(self):
        self.assertEqual(seller_offers.expected_ask(0.9, None, 50.0, 100.0), 0.9)

    def test_an_expectation_under_the_reservation_keeps_the_reservation(self):
        self.assertEqual(seller_offers.expected_ask(0.9, 0.5, 50.0, 100.0), 0.9)

    def test_no_expected_sales_keeps_the_reservation(self):
        self.assertEqual(seller_offers.expected_ask(0.9, 1.0, 50.0, 0.0), 0.9)


if __name__ == "__main__":
    unittest.main()
