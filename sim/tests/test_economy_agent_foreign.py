"""Foreign trade on the agent economy: partners buy and sell through edge:external at the port, and what they pay in or take
out shows in the balance of payments (Complaint 389). The orders, the clearing at the landed price and the settlement of a
partner's purchase are test_economy_foreign; here the market clears written-out bids and offers, one market at a time."""

QUICK_TOPIC = True

import math
import types
import unittest

from sim.economy import foreign, goods_market
from sim.economy.types import EDGE_EXTERNAL, Bid, Offer

GRAIN, AREA, PORT = "grain", "port@grain", "port"


def farm(quantity=100.0, price=0.3):
    return Offer("farm", GRAIN, AREA, PORT, quantity, price)


def household(quantity=100.0, reference=0.3):
    return Bid("household", GRAIN, AREA, PORT, 0.0, quantity, reference, 1.0, 1e9)


def partner_buys(quantity, price):
    return Bid(EDGE_EXTERNAL, GRAIN, AREA, PORT, 0.0, quantity, price, foreign.EXTERNAL_BID_ELASTICITY, math.inf,
               maximum_price=price)


def partner_sells(quantity, price):
    return Offer(EDGE_EXTERNAL, GRAIN, AREA, PORT, quantity, price)


def clear(bids, offers):
    return goods_market.clear(bids, offers, GRAIN, AREA, "coin", 0.3)


class ExportTests(unittest.TestCase):
    def test_a_partner_that_will_not_pay_the_price_buys_nothing(self):
        result = clear([household(), partner_buys(1000.0, 0.0001)], [farm()])
        self.assertEqual([fill.quantity for fill in result.fills if fill.agent == EDGE_EXTERNAL], [])

    def test_a_partner_paying_well_for_our_grain_takes_some_of_it_at_the_sellers_ask(self):
        # buyers pay a seller's ask, so a partner's high bid wins it a share of the stock, not a higher price for sellers
        abroad = clear([household(), partner_buys(1000.0, 3.0)], [farm(quantity=1000.0)])
        exported = [fill for fill in abroad.fills if fill.agent == EDGE_EXTERNAL]
        self.assertGreater(sum(fill.quantity for fill in exported), 0.0)
        self.assertAlmostEqual(abroad.price, 0.3)

    def test_a_partner_buying_exports_does_not_lower_the_domestic_price_of_the_good(self):
        home = clear([household()], [farm()])
        abroad = clear([household(), partner_buys(1000.0, 3.0)], [farm()])
        self.assertGreaterEqual(abroad.price, home.price)


class ImportTests(unittest.TestCase):
    def test_cheap_imports_lower_the_domestic_price_of_the_good(self):
        home = clear([household()], [farm()])
        flooded = clear([household()], [farm(), partner_sells(700.0, 0.02)])
        self.assertLess(flooded.price, home.price)


class BalanceTests(unittest.TestCase):
    def test_imports_and_exports_together_net_to_the_difference(self):
        # 100 coin moved over the external edge in all, 40 more paid in than taken out: 70 received, 30 paid
        book = types.SimpleNamespace(edge_volume=lambda edge, currency: 100.0, edge_net=lambda edge, currency: 40.0)
        paid = foreign.balance_of_payments(book, "coin")
        self.assertAlmostEqual(paid.exports_received, 70.0)
        self.assertAlmostEqual(paid.imports_paid, 30.0)
        self.assertAlmostEqual(paid.net_outflow, paid.imports_paid - paid.exports_received)

    def test_no_money_over_the_edge_is_no_flow(self):
        book = types.SimpleNamespace(edge_volume=lambda edge, currency: 0.0, edge_net=lambda edge, currency: 0.0)
        self.assertEqual(foreign.balance_of_payments(book, "coin"), foreign.BalanceOfPayments(0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
