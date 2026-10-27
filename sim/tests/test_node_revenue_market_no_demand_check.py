"""Complaints/668: a seat's concern is paid for what buyers take, not for its physical output at the ask. The rules are
called on built inputs, not a game: the clearing's result per material (sim/engine/concern_sales.py), the share of an
output a forecast may count as sold, and the market factor that carries it (sim/engine/node_revenue_market.py)."""
QUICK_TOPIC = True

import unittest

from sim.production import concern_sales, node_revenue_market


COST = 10.0


def factor(tonnes, ask, outlook):
    return node_revenue_market.basket_market_factor({"acid": tonnes}, {}, {"acid": COST}, lambda material: ask, outlook)


class ClearingResultTests(unittest.TestCase):
    def test_a_seller_offering_far_more_than_buyers_want_is_paid_only_for_what_cleared(self):
        result = concern_sales.settle_sales({"acid": 1000.0}, {"acid": 990.0}, 500.0, {"acid": 50.0})["acid"]
        self.assertAlmostEqual(result.sold, 10.0)
        self.assertAlmostEqual(result.proceeds, 500.0)   # the money the account holds is what the 10 units fetched
        self.assertAlmostEqual(result.proceeds / result.sold, 50.0)

    def test_a_good_nobody_bought_pays_nothing_and_the_whole_offer_stays_unsold(self):
        result = concern_sales.settle_sales({"acid": 1000.0}, {"acid": 1000.0}, 0.0, {})["acid"]
        self.assertEqual((result.sold, result.proceeds), (0.0, 0.0))

    def test_proceeds_are_shared_among_materials_by_what_each_sold_at_its_price(self):
        results = concern_sales.settle_sales({"a": 10.0, "b": 10.0}, {"a": 0.0, "b": 5.0}, 150.0, {"a": 10.0, "b": 20.0})
        self.assertAlmostEqual(results["a"].proceeds, 75.0)
        self.assertAlmostEqual(results["b"].proceeds, 75.0)


class OutlookTests(unittest.TestCase):
    def test_the_seats_own_clearing_sets_the_share_and_the_price(self):
        taken = concern_sales.outlook(concern_sales.SaleResult(1000.0, 10.0, 500.0), None, 1000.0)
        self.assertEqual(taken.basis, concern_sales.CLEARED_LAST_YEAR)
        self.assertAlmostEqual(taken.share, 0.01)
        self.assertAlmostEqual(taken.price, 50.0)

    def test_nothing_sold_has_a_zero_share_and_no_price(self):
        taken = concern_sales.outlook(concern_sales.SaleResult(1000.0, 0.0, 0.0), 5000.0, 1000.0)
        self.assertEqual((taken.share, taken.price), (0.0, None))

    def test_before_the_seat_has_sold_buyers_last_year_bound_the_share(self):
        taken = concern_sales.outlook(None, 20.0, 1000.0)
        self.assertEqual(taken.basis, concern_sales.BUYERS_LAST_YEAR)
        self.assertAlmostEqual(taken.share, 0.02)
        self.assertEqual(concern_sales.outlook(None, 0.0, 1000.0).share, 0.0)

    def test_nothing_known_gives_no_outlook(self):
        self.assertIsNone(concern_sales.outlook(None, None, 1000.0))


class MarketFactorTests(unittest.TestCase):
    def test_without_an_outlook_the_factor_is_still_ask_over_cost(self):
        self.assertAlmostEqual(factor(100.0, 10.0, None), 1.0)
        self.assertAlmostEqual(factor(100.0, 2000.0, None), 200.0)

    def test_a_good_with_no_buyers_takes_nothing_however_high_the_ask(self):
        no_buyers = lambda material, quantity: concern_sales.outlook(None, 0.0, quantity)
        self.assertEqual(factor(100.0, 2000.0, no_buyers), 0.0)

    def test_takings_cannot_exceed_what_buyers_take_however_many_tonnes_are_made(self):
        buyers_take = 20.0
        outlook = lambda material, quantity: concern_sales.outlook(None, buyers_take, quantity)
        for tonnes in (20.0, 1.0e3, 1.0e6):
            takings = tonnes * COST * factor(tonnes, 50.0, outlook)
            self.assertLessEqual(takings, buyers_take * 50.0 + 1e-6)

    def test_the_cleared_price_replaces_the_ask_for_the_units_that_sold(self):
        cleared = lambda material, quantity: concern_sales.outlook(concern_sales.SaleResult(100.0, 50.0, 500.0), None, quantity)
        self.assertAlmostEqual(factor(100.0, 2000.0, cleared), 0.5 * 10.0 / COST)

    def test_what_is_bought_is_not_cut_by_the_sale_outlook(self):
        none_sell = lambda material, quantity: concern_sales.outlook(None, 0.0, quantity)
        with_input = node_revenue_market.basket_market_factor({"acid": 10.0}, {"ore": 10.0}, {"acid": 10.0, "ore": 1.0},
                                                              lambda material: 1.0, none_sell)
        self.assertEqual(with_input, 0.0)   # clamped: no sales against a bill for the input


if __name__ == "__main__":
    unittest.main()
