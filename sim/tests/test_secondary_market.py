"""Complaint 106: holders sell claims they hold to other agents once a year at one price per claim, where the units
offered meet the units bids can pay for. Rules on built inputs (no game)."""

QUICK_TOPIC = True

import unittest

from sim.economy import secondary_market
from sim.economy.secondary_market import Ask, Bid, clear, clear_item, clearing_price, present_value


def paid_by_buyer(trades):
    paid = {}
    for trade in trades:
        paid[trade.buyer] = paid.get(trade.buyer, 0.0) + trade.quantity * trade.price
    return paid


def sold_by_seller(trades):
    sold = {}
    for trade in trades:
        sold[trade.seller] = sold.get(trade.seller, 0.0) + trade.quantity
    return sold


class PresentValue(unittest.TestCase):
    def test_a_claim_with_an_end_is_its_coupons_and_redemption_discounted(self):
        self.assertAlmostEqual(present_value(5.0, 100.0, 1, 0.10), 105.0 / 1.10)

    def test_a_coupon_at_the_discount_rate_is_worth_its_redemption(self):
        self.assertAlmostEqual(present_value(5.0, 100.0, 10, 0.05), 100.0)

    def test_a_higher_rate_lowers_the_value(self):
        values = [present_value(5.0, 100.0, 10, rate) for rate in (0.03, 0.05, 0.09)]
        self.assertGreater(values[0], values[1])
        self.assertGreater(values[1], values[2])

    def test_a_claim_with_no_end_is_a_perpetuity(self):
        self.assertAlmostEqual(present_value(20.0, 0.0, None, 0.05), 400.0)


class OneClaim(unittest.TestCase):
    def test_no_bid_reaching_an_ask_makes_no_trade(self):
        self.assertEqual(clear_item([Ask("a", "claim", 1.0, 100.0)], [Bid("b", "claim", 500.0, 90.0)]), [])
        self.assertIsNone(clearing_price([Ask("a", "claim", 1.0, 100.0)], [Bid("b", "claim", 500.0, 90.0)]))

    def test_a_buyer_with_more_funds_than_the_claim_costs_pays_the_sellers_reserve_when_supply_is_short_of_nothing(self):
        trades = clear_item([Ask("a", "claim", 1.0, 80.0)], [Bid("b", "claim", 500.0, 120.0)])
        self.assertEqual(len(trades), 1)
        self.assertAlmostEqual(trades[0].quantity, 1.0)
        self.assertGreaterEqual(trades[0].price, 80.0)
        self.assertLessEqual(trades[0].price, 120.0)

    def test_the_price_rises_as_buyers_bring_more_funds(self):
        asks = [Ask("a", "claim", 1.0, 50.0)]
        small = clearing_price(asks, [Bid("b", "claim", 60.0, 200.0)])
        large = clearing_price(asks, [Bid("b", "claim", 150.0, 200.0)])
        self.assertLess(small, large)

    def test_the_price_never_passes_the_limit_of_the_buyers_it_takes(self):
        asks = [Ask("a", "claim", 1.0, 50.0)]
        price = clearing_price(asks, [Bid("b", "claim", 10000.0, 120.0)])
        self.assertLessEqual(price, 120.0 + 1e-9)

    def test_buyers_pay_no_more_than_their_funds_and_sellers_sell_no_more_than_they_hold(self):
        asks = [Ask("a", "claim", 1.0, 40.0), Ask("c", "claim", 0.5, 60.0)]
        bids = [Bid("b", "claim", 70.0, 150.0), Bid("d", "claim", 30.0, 150.0)]
        trades = clear_item(asks, bids)
        for buyer, paid in paid_by_buyer(trades).items():
            self.assertLessEqual(paid, {"b": 70.0, "d": 30.0}[buyer] + 1e-9)
        for seller, sold in sold_by_seller(trades).items():
            self.assertLessEqual(sold, {"a": 1.0, "c": 0.5}[seller] + 1e-9)

    def test_money_paid_equals_money_received_and_all_trades_are_at_one_price(self):
        asks = [Ask("a", "claim", 1.0, 40.0), Ask("c", "claim", 0.5, 60.0)]
        bids = [Bid("b", "claim", 70.0, 150.0), Bid("d", "claim", 30.0, 150.0)]
        trades = clear_item(asks, bids)
        self.assertEqual(len({trade.price for trade in trades}), 1)
        self.assertAlmostEqual(sum(paid_by_buyer(trades).values()), sum(trade.quantity * trade.price for trade in trades))

    def test_a_seller_whose_reserve_is_above_the_price_keeps_its_claim(self):
        asks = [Ask("cheap", "claim", 1.0, 30.0), Ask("dear", "claim", 1.0, 400.0)]
        trades = clear_item(asks, [Bid("b", "claim", 100.0, 150.0)])
        self.assertEqual(sorted(sold_by_seller(trades)), ["cheap"])

    def test_the_dearest_reserve_the_buyers_can_pay_sets_the_price_when_supply_is_long(self):
        asks = [Ask("a", "claim", 1.0, 40.0), Ask("c", "claim", 1.0, 60.0)]
        trades = clear_item(asks, [Bid("b", "claim", 50.0, 150.0)])
        price = trades[0].price
        self.assertAlmostEqual(sum(trade.quantity for trade in trades) * price, 50.0)
        self.assertLessEqual(price, 150.0)

    def test_a_holder_does_not_buy_the_claim_it_sells(self):
        trades = clear_item([Ask("a", "claim", 1.0, 40.0)], [Bid("a", "claim", 1000.0, 500.0)])
        self.assertEqual(trades, [])

    def test_a_holder_short_of_cash_who_asks_less_sells_first_and_the_price_is_the_bids(self):
        hurried = clear_item([Ask("hurried", "claim", 1.0, 60.0), Ask("patient", "claim", 1.0, 95.0)],
                             [Bid("b", "claim", 70.0, 150.0)])
        self.assertEqual(sorted(sold_by_seller(hurried)), ["hurried"])
        self.assertLess(hurried[0].price, 95.0)


class SeveralClaims(unittest.TestCase):
    def test_a_buyers_funds_spent_on_one_claim_are_not_there_for_the_next(self):
        asks = [Ask("a", "claim:1", 1.0, 10.0), Ask("a", "claim:2", 1.0, 10.0)]
        bids = [Bid("b", "claim:1", 100.0, 100.0), Bid("b", "claim:2", 100.0, 100.0)]
        trades = clear(asks, bids)
        self.assertLessEqual(sum(paid_by_buyer(trades).values()), 100.0 + 1e-9)

    def test_claims_clear_in_id_order_and_each_at_its_own_price(self):
        asks = [Ask("a", "claim:1", 1.0, 10.0), Ask("a", "claim:2", 1.0, 70.0)]
        bids = [Bid("b", "claim:1", 30.0, 100.0), Bid("c", "claim:2", 90.0, 100.0)]
        prices = {trade.item: trade.price for trade in clear(asks, bids)}
        self.assertEqual(sorted(prices), ["claim:1", "claim:2"])
        self.assertLess(prices["claim:1"], prices["claim:2"])

    def test_the_result_does_not_depend_on_the_order_the_inputs_are_listed_in(self):
        asks = [Ask("a", "claim", 1.0, 40.0), Ask("c", "claim", 0.5, 60.0)]
        bids = [Bid("b", "claim", 70.0, 150.0), Bid("d", "claim", 30.0, 150.0)]
        self.assertEqual(clear(asks, bids), clear(list(reversed(asks)), list(reversed(bids))))


if __name__ == "__main__":
    unittest.main()
