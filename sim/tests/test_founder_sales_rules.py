"""The founder sells (Complaint 288): a concern goes to the buyer the exchange picks at the price it sets. Farmland sales are
test_farm_land_trade; the exchange's own terms are in test_exchange_sale_terms. The ventures module checks the seat runs the
concern and reports; the actors module addresses the exchange to the seat. Each method is called on a stand-in that holds
only what it reads."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.actors.module import Actors
from sim.actors import seat_exchange
from sim.agents.api import Business, CommandRejected
from sim.actors.api import SellSeatConcern
from sim.seats.api import SeatsSeat
from sim.tests import module_harness, ventures_host

NODE = "inn"


class SaleSetupTests(unittest.TestCase):
    def setup(self):
        module = module_harness.build(Actors, module_id="actors", world=SimpleNamespace(purses=None), views={
            "acting_seat": "seat:0", "seat_dealings": lambda seat_id: SeatsSeat(), "seat_business": lambda seat_id: Business()})
        module.actor_world = lambda: SimpleNamespace(concern_margin=lambda node_id: 7.0)
        module.cast = lambda: SimpleNamespace(
            of_kind=lambda kind: [SimpleNamespace(record=SimpleNamespace(exited_year=None), actor_id=kind + ":live"),
                                  SimpleNamespace(record=SimpleNamespace(exited_year=90), actor_id=kind + ":gone")],
            get=lambda actor_id: "found " + actor_id)
        return module._concern_sale_setup(NODE)

    def test_the_seller_carries_the_concerns_margin_and_the_buyers_are_the_live_firms_and_players(self):
        party, buyers, find_actor, _world = self.setup()
        self.assertEqual(party.margin_of(NODE), 7.0)
        self.assertEqual([buyer.actor_id for buyer in buyers], ["firm:live", "player:live"])
        self.assertEqual((find_actor("seat:0"), find_actor("firm:live")), (party, "found firm:live"))


class SellSeatConcernTests(unittest.TestCase):
    def sell(self, outcome):
        module = module_harness.build(Actors, module_id="actors", world=SimpleNamespace(purses=None), views={})
        module._concern_sale_setup = lambda node_id: ("party", [], None, "world")

        def sold(party, node_id, buyers, find_actor, world):
            if outcome == "refused":
                raise CommandRejected("no buyer")
            return {"buyer": "firm:rich", "price": 99.94}
        with mock.patch.object(seat_exchange.exchange_sale, "sell_concern", sold):
            return module.sell_seat_concern(SellSeatConcern(NODE))

    def test_a_sale_reports_the_buyer_and_the_price_the_exchange_set(self):
        self.assertEqual(self.sell("sold"), {"ok": True, "buyer": "firm:rich", "price": 99.94})

    def test_a_refusal_from_the_exchange_is_carried_back(self):
        self.assertEqual(self.sell("refused"), {"ok": False, "error": "no buyer"})


class SellConcernTests(unittest.TestCase):
    def module(self, operating=(), granted=(), sale=None, terms=None):
        return ventures_host.build(
            projects_record=ventures_host.projects_record(operating=set(operating), granted=set(granted)), acting_balance=1234.56,
            concern_sale_terms=lambda node_id: terms, answers={SellSeatConcern: sale})

    def test_a_concern_the_founder_does_not_run_has_nothing_to_sell(self):
        module = self.module()
        self.assertFalse(module.sell_concern(NODE)["ok"])
        self.assertEqual(module_harness.sent(module), [])

    def test_a_concern_the_society_has_is_not_the_founders_to_sell(self):
        module = self.module(operating={NODE}, granted={NODE})
        self.assertFalse(module.sell_concern(NODE)["ok"])
        self.assertEqual(module_harness.sent(module), [])

    def test_a_sale_reports_the_buyer_the_price_and_the_founders_capital(self):
        module = self.module(operating={NODE}, sale={"ok": True, "buyer": "firm:rich", "price": 99.94})
        self.assertEqual(module.sell_concern(NODE), {"ok": True, "sold": NODE, "buyer": "firm:rich", "price": 99.9, "capital": 1234.6})
        self.assertEqual(module_harness.sent(module), [SellSeatConcern(NODE)])

    def test_a_refusal_from_the_exchange_is_carried_back(self):
        module = self.module(operating={NODE}, sale={"ok": False, "error": "no buyer"})
        self.assertEqual(module.sell_concern(NODE), {"ok": False, "error": "no buyer"})

    def test_the_quote_names_the_buyer_and_the_price_and_sends_nothing(self):
        module = self.module(operating={NODE}, terms={"ok": True, "buyer": "firm:rich", "price": 99.94})
        self.assertEqual(module.quote_concern_sale(NODE), {"ok": True, "concern": NODE, "buyer": "firm:rich", "price": 99.9, "capital": 1234.6})
        self.assertEqual(module_harness.sent(module), [])

    def test_a_quote_the_exchange_refuses_is_carried_back(self):
        module = self.module(operating={NODE}, terms={"ok": False, "error": "no buyer"})
        self.assertEqual(module.quote_concern_sale(NODE), {"ok": False, "error": "no buyer"})


if __name__ == "__main__":
    unittest.main()
