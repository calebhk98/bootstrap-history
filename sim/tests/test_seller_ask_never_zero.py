"""A costed good's ask is never zero: a seller whose reservation is nothing (a perishable, a distressed holder) opens at
the price it expects, and a flooded perishable's search ends at the price that earns most, not at zero."""

QUICK_TOPIC = True

import unittest

from sim.economy import seller_offers, unsold_search


class OpenedAskTests(unittest.TestCase):
    def test_zero_reservation_of_a_costed_good_opens_at_the_expected_price(self):
        self.assertEqual(seller_offers.opened_ask(0.0, 1.4, 1.3, 4.2), 1.3)

    def test_expected_price_is_held_to_the_band_edge(self):
        self.assertEqual(seller_offers.opened_ask(0.0, 1.4, 9.0, 4.2), 4.2)

    def test_negative_reservation_opens_too(self):
        self.assertEqual(seller_offers.opened_ask(-0.2, 1.4, 1.3, 4.2), 1.3)

    def test_positive_reservation_is_left_alone(self):
        self.assertIsNone(seller_offers.opened_ask(0.5, 1.4, 1.3, 4.2))

    def test_waste_with_no_cost_stays_zero(self):
        self.assertIsNone(seller_offers.opened_ask(0.0, None, 1.3, 4.2))
        self.assertIsNone(seller_offers.opened_ask(0.0, float("inf"), 1.3, 4.2))

    def test_no_expected_price_gives_no_opening(self):
        self.assertIsNone(seller_offers.opened_ask(0.0, 1.4, None, 4.2))
        self.assertIsNone(seller_offers.opened_ask(0.0, 1.4, 0.0, 4.2))


class FloodPriceTests(unittest.TestCase):
    def test_budget_bound_demand_earns_the_same_at_every_price_so_the_highest_is_taken(self):
        price = unsold_search.flood_price(lambda price: min(100.0, 50.0 / price), 1000.0, 0.01, 2.0)
        self.assertAlmostEqual(price, 2.0, delta=0.01)

    def test_buyers_priced_out_above_a_ceiling_give_the_ceiling(self):
        price = unsold_search.flood_price(lambda price: 100.0 if price <= 1.0 else 0.0, 1000.0, 0.01, 2.0)
        self.assertTrue(0.95 <= price <= 1.0, price)

    def test_stock_smaller_than_demand_takes_the_highest(self):
        price = unsold_search.flood_price(lambda price: 100.0, 10.0, 0.01, 2.0)
        self.assertAlmostEqual(price, 2.0, delta=0.01)


if __name__ == "__main__":
    unittest.main()
