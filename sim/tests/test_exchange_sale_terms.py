"""Selling a concern (agents/exchange_sale.py): the price is the concern's margin over the valuation horizon, the buyer
is the eligible actor with the most money left over, and the sale itself is made at exactly those terms, which is what
`quote sell concern` shows. Run on stand-in actors and a stand-in exchange."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.agents.api import CommandRejected, exchange_sale
from sim.agents.tuning import VALUE_HORIZON_YEARS


def actor(actor_id, money, controller="ai", concerns=(), margin=None):
    margins = {node_id: margin for node_id in concerns}
    return types.SimpleNamespace(
        actor_id=actor_id, money=money, concerns=set(concerns), record=types.SimpleNamespace(controller=controller, last_margin=0.0),
        margin_of=lambda node_id: margins.get(node_id), concern_count=lambda: len(concerns))


class SaleTermsTests(unittest.TestCase):
    def setUp(self):
        self.refused_buyers = set()
        patcher = mock.patch.object(exchange_sale.exchange, "problem",
                                    lambda seller, buyer, give, take, world: "refused" if buyer.actor_id in self.refused_buyers else "")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.seller = actor("seat", 0.0, concerns=("mill",), margin=10.0)

    def test_the_price_is_the_margin_over_the_valuation_horizon(self):
        terms = exchange_sale.sale_terms(self.seller, "mill", [actor("rich", 1e9)], None)
        self.assertAlmostEqual(terms["price"], 10.0 * VALUE_HORIZON_YEARS)

    def test_the_buyer_is_the_one_left_with_most_money_ties_by_id(self):
        buyers = [actor("b", 5000.0), actor("a", 5000.0), actor("c", 400.0)]
        self.assertEqual(exchange_sale.sale_terms(self.seller, "mill", buyers, None)["buyer"].actor_id, "a")
        buyers.append(actor("d", 9000.0))
        self.assertEqual(exchange_sale.sale_terms(self.seller, "mill", buyers, None)["buyer"].actor_id, "d")

    def test_only_ai_actors_that_the_exchange_allows_are_eligible(self):
        self.refused_buyers = {"blocked"}
        buyers = [actor("blocked", 1e9), actor("human", 1e9, controller="player"), actor("fine", 1000.0)]
        self.assertEqual([buyer.actor_id for buyer in exchange_sale.eligible_buyers(self.seller, "mill", 150.0, buyers, None)],
                         ["fine"])

    def test_the_seller_is_never_its_own_buyer(self):
        self.seller.money = 1e9
        self.seller.record.controller = "ai"
        with self.assertRaises(CommandRejected):
            exchange_sale.sale_terms(self.seller, "mill", [self.seller], None)

    def test_a_concern_not_run_is_refused(self):
        with self.assertRaises(CommandRejected):
            exchange_sale.sale_terms(self.seller, "loom", [actor("rich", 1e9)], None)

    def test_a_concern_that_earns_nothing_is_refused(self):
        idle = actor("seat", 0.0, concerns=("mill",), margin=-3.0)
        with self.assertRaises(CommandRejected):
            exchange_sale.sale_terms(idle, "mill", [actor("rich", 1e9)], None)

    def test_with_no_eligible_buyer_it_is_refused(self):
        self.refused_buyers = {"poor"}
        with self.assertRaises(CommandRejected):
            exchange_sale.sale_terms(self.seller, "mill", [actor("poor", 1.0)], None)


class SellConcernTests(unittest.TestCase):
    def test_the_sale_is_offered_and_accepted_at_the_quoted_buyer_and_price(self):
        seller = actor("seat", 0.0, concerns=("mill",), margin=10.0)
        buyers = [actor("rich", 1e9), actor("richer", 2e9)]
        offers = []
        with mock.patch.object(exchange_sale.exchange, "problem", lambda *arguments: ""), \
                mock.patch.object(exchange_sale.exchange, "make_offer",
                                  lambda giver, receiver, give, take, world: offers.append((receiver, give, take)) or {"id": "o1"}), \
                mock.patch.object(exchange_sale.exchange, "accept", lambda buyer, offer_id, find_actor, world: offers.append(buyer)):
            terms = exchange_sale.sale_terms(seller, "mill", buyers, None)
            sale = exchange_sale.sell_concern(seller, "mill", buyers, lambda actor_id: None, None)
        self.assertEqual(sale, {"buyer": terms["buyer"].actor_id, "price": terms["price"]})
        self.assertEqual(offers[0], (terms["buyer"], {"concern": "mill"}, {"money": terms["price"]}))
        self.assertIs(offers[1], terms["buyer"])


if __name__ == "__main__":
    unittest.main()
