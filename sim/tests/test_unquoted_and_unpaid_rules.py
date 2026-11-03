"""Plain rules that a missing price or a refused payment must not turn into a free good or a dropped charge, each on written-out inputs."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agents import revenue_bases
from sim.agents.exchange_commands import side_worth
from sim.agents.player_commands import CommandRejected, number_of
from sim.agents.purses import Purses
from sim.book import InsufficientFunds
from sim.coin.exposure import actor_exposure
from sim.freight import rules
from sim.freight.route import Leg, Route
from sim.ledger.api import pay_edge_or_log
from sim.refusal import Refusal, cause_of


def quotes_of(prices):
    return SimpleNamespace(quotes=SimpleNamespace(material_price=prices.get))


class PayEdgeOrLog(unittest.TestCase):
    def test_a_refusal_is_logged_with_its_cause_and_reported_unpaid(self):
        sent = []

        def send(command):
            sent.append(command)
            return Refusal("cannot_pay", "no funds") if type(command).__name__ == "PayEdge" else None
        refusal = pay_edge_or_log(send, "edge:suppliers", 5.0, "running costs")
        self.assertIsInstance(refusal, Refusal)
        self.assertEqual(cause_of(refusal), "cannot_pay")
        event = sent[1]
        self.assertEqual((event.kind, event.facts["cause"], event.facts["amount"]), ("unpaid_charge", "cannot_pay", 5.0))

    def test_a_paid_charge_logs_nothing(self):
        sent = []
        self.assertIsNone(pay_edge_or_log(lambda command: sent.append(command), "edge:suppliers", 5.0, "running costs"))
        self.assertEqual(len(sent), 1)


class UnquotedMaterial(unittest.TestCase):
    def test_a_harvest_of_a_good_with_no_price_has_no_base(self):
        world = SimpleNamespace(quotes=SimpleNamespace(material_price=lambda material: None, staple_material=lambda: "grain"),
                                revenue=SimpleNamespace(harvest_tonnes=lambda: 10.0))
        self.assertIsNone(revenue_bases.harvest(world))

    def test_an_offer_of_a_store_with_no_price_cannot_be_weighed(self):
        taker = SimpleNamespace(imitation_worth=lambda node_id, world: 0.0)
        self.assertIsNone(side_worth({"stores": {"grain": 2.0}}, taker, None, quotes_of({})))
        self.assertEqual(side_worth({"stores": {"grain": 2.0}}, taker, None, quotes_of({"grain": 3.0})), 6.0)

    def test_a_store_with_no_price_is_not_exposed_to_theft(self):
        exposure = actor_exposure("firm", 0.0, {"grain": 5.0}, lambda material: None, lambda: 0.0, 0.0)
        self.assertEqual(exposure.lots, [])


class HullLoss(unittest.TestCase):
    def test_a_route_that_sails_needs_a_priced_hull(self):
        route = Route((Leg("a", "b", "sail", 100.0, 1.0, 5.0),))
        with self.assertRaises(ValueError):
            rules.cargo_loss_share(route, {}, None)
        self.assertEqual(rules.cargo_loss_share(Route((Leg("a", "b", "cart", 100.0, 1.0, 5.0),)), {}, None), 0.0)


class NumberOf(unittest.TestCase):
    def test_a_word_is_refused_and_a_numeric_string_read(self):
        self.assertEqual(number_of("2.5", "amount"), 2.5)
        for bad in ("many", None, True, [1]):
            with self.assertRaises(CommandRejected):
                number_of(bad, "amount")


class RefusedPosting(unittest.TestCase):
    def test_a_posting_the_book_refuses_leaves_no_draw_on_the_facility(self):
        purses = Purses()
        purses.transfer("edge:outside the book", "seat", 10.0, "seed")
        real = purses.book.transfer

        def refuse_boom(transfer):
            if transfer.purpose == "boom":
                raise InsufficientFunds("refused")
            real(transfer)
        purses.book.transfer = refuse_boom
        with self.assertRaises(InsufficientFunds):
            purses.transfer("seat", "edge:officials", 50.0, "boom")
        self.assertEqual((purses.purse("seat"), purses.debt("seat")), (10.0, 0.0))


if __name__ == "__main__":
    unittest.main()
