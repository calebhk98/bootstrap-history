"""Foreign partners as external sellers and buyers: imports offered at the landed price on the port tile,
exports bid at the partner's price less carriage, and the balance of payments read from the book."""

QUICK_TOPIC = True

import unittest

from sim.economy import foreign, goods_market, settlement
from sim.economy.accounts import Book
from sim.economy.types import EDGE_EXTERNAL, EDGE_MINT, EDGE_PRODUCTION, Bid, GoodsMove, Offer, Transfer


def area_of(good, tile):
    return "%s@%s" % (tile, good)


def orders(**changes):
    arguments = dict(landed_prices={"wine": 3.0}, export_prices={"grain": 5.0},
                     quantities_available={"wine": 40.0}, quantities_wanted={"grain": 25.0},
                     area_of=area_of, port_tile="port")
    arguments.update(changes)
    return foreign.external_orders(**arguments)


def households(good, quantity, reference):
    return Bid("importer", good, area_of(good, "port"), "port", 0.0, quantity, reference, 1.0, 1e9)


class OrdersTests(unittest.TestCase):
    def test_imports_are_offered_at_the_landed_price_at_the_port(self):
        offer = orders().offers[0]
        self.assertEqual((offer.seller, offer.good, offer.tile, offer.area), (EDGE_EXTERNAL, "wine", "port", "port@wine"))
        self.assertEqual((offer.quantity, offer.reservation_price), (40.0, 3.0))

    def test_exports_are_bid_at_the_partners_price_less_carriage(self):
        bid = orders(export_carriage_per_unit={"grain": 1.5}).bids[0]
        self.assertEqual((bid.buyer, bid.good, bid.flexible_quantity), (EDGE_EXTERNAL, "grain", 25.0))
        self.assertAlmostEqual(bid.reference_price, 3.5)

    def test_no_bid_when_carriage_eats_the_partners_price(self):
        self.assertEqual(orders(export_carriage_per_unit={"grain": 5.0}).bids, ())

    def test_the_partners_purchases_are_bounded_by_the_money_it_has(self):
        # a partner cannot pay out coin it does not hold: its bids share what it can spend, by value
        bids = orders(export_prices={"grain": 5.0, "oil": 10.0}, quantities_wanted={"grain": 25.0, "oil": 5.0},
                      export_budget=100.0).bids
        self.assertAlmostEqual(sum(bid.budget for bid in bids), 100.0)
        by_good = {bid.good: bid.budget for bid in bids}
        self.assertAlmostEqual(by_good["grain"] / by_good["oil"], (25.0 * 5.0) / (5.0 * 10.0))

    def test_without_a_stated_budget_the_bids_are_unbounded(self):
        self.assertEqual(orders().bids[0].budget, float("inf"))

    def test_nothing_available_means_no_offer(self):
        self.assertEqual(orders(quantities_available={"wine": 0.0}).offers, ())


class ClearingTests(unittest.TestCase):
    def test_imports_clear_at_the_landed_price_when_supply_meets_demand_there(self):
        result = goods_market.clear([households("wine", 40.0, 3.0)], orders().offers, "wine", "port@wine", "coin", None)
        self.assertAlmostEqual(result.price, 3.0, places=6)
        self.assertAlmostEqual(result.quantity, 40.0)

    def test_scarce_imports_clear_above_the_landed_price(self):
        result = goods_market.clear([households("wine", 100.0, 3.0)], orders().offers, "wine", "port@wine", "coin", None)
        self.assertGreater(result.price, 3.0)
        self.assertAlmostEqual(result.quantity, 40.0)

    def test_imports_do_not_clear_below_the_landed_price(self):
        offers = orders().offers
        result = goods_market.clear([households("wine", 5.0, 1.0)], offers, "wine", "port@wine", "coin", None)
        self.assertGreaterEqual(result.price, 3.0 - 1e-9)

    def test_the_balance_of_payments_counts_both_directions(self):
        book = Book()
        book.transfer(Transfer(EDGE_MINT, "importer", "coin", 1000.0, "test"))
        wine = goods_market.clear([households("wine", 20.0, 3.0)], orders().offers, "wine", "port@wine", "coin", None)
        settlement.settle_goods(book, wine)
        paid_for_wine = book.edge_volume(EDGE_EXTERNAL, "coin")
        report = foreign.balance_of_payments(book, "coin")
        self.assertAlmostEqual(report.imports_paid, paid_for_wine)
        self.assertEqual(report.exports_received, 0.0)
        self.assertAlmostEqual(report.net_outflow, paid_for_wine)


class ExportSettlementTests(unittest.TestCase):
    def test_a_partner_buying_our_goods_pays_into_the_economy(self):
        book = Book()
        book.move(GoodsMove(EDGE_PRODUCTION, "farmer", "grain", "port", 10.0, "test"))
        result = goods_market.clear(list(orders().bids), [Offer("farmer", "grain", "port@grain", "port", 10.0, 1.0)],
                                    "grain", "port@grain", "coin", None)
        settlement.settle_goods(book, result)
        self.assertGreater(book.balance("farmer", "coin"), 0.0)
        report = foreign.balance_of_payments(book, "coin")
        self.assertAlmostEqual(report.exports_received, book.balance("farmer", "coin"))
        self.assertEqual(report.imports_paid, 0.0)
        self.assertLess(report.net_outflow, 0.0)

    def test_the_orders_are_deterministic(self):
        self.assertEqual(orders(), orders())


if __name__ == "__main__":
    unittest.main()
