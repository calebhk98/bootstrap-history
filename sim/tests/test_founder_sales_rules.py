"""The founder sells (Complaint 288): a concern goes to the buyer the exchange picks at the price it sets. Farmland sales are
test_farm_land_trade; the exchange's own terms are in test_exchange_sale_terms. Each method is called on a stand-in that holds
only what it reads."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.agents.api import CommandRejected
from sim.tests import ventures_host
from sim.ventures import sales

NODE = "inn"


class SaleSetupTests(unittest.TestCase):
    def setup(self, operating, granted=()):
        module = ventures_host.build(
            legacy_projects=ventures_host.projects_record(operating=set(operating), granted=set(granted)),
            seat_party_with_margins=lambda seat, margins: SimpleNamespace(actor_id="seat:0", margins=margins),
            actor_world=SimpleNamespace(concern_margin=lambda node_id: 7.0),
            cast=SimpleNamespace(
                of_kind=lambda kind: [SimpleNamespace(record=SimpleNamespace(exited_year=None), actor_id=kind + ":live"),
                                      SimpleNamespace(record=SimpleNamespace(exited_year=90), actor_id=kind + ":gone")],
                get=lambda actor_id: "found " + actor_id))
        return module._concern_sale_setup(NODE)

    def test_a_concern_the_founder_does_not_run_has_nothing_to_sell(self):
        self.assertIsNone(self.setup(operating=set())[0])

    def test_a_concern_the_society_has_is_not_the_founders_to_sell(self):
        self.assertIsNone(self.setup(operating={NODE}, granted={NODE})[0])

    def test_the_seller_carries_the_concerns_margin_and_the_buyers_are_the_live_firms_and_players(self):
        (party, buyers, find_actor, _world), error = self.setup(operating={NODE})
        self.assertIsNone(error)
        self.assertEqual(party.margins, {NODE: 7.0})
        self.assertEqual([buyer.actor_id for buyer in buyers], ["firm:live", "player:live"])
        self.assertEqual((find_actor("seat:0"), find_actor("firm:live")), (party, "found firm:live"))


class SellConcernTests(unittest.TestCase):
    def sell(self, outcome):
        module = ventures_host.build(acting_balance=1234.56)
        module._concern_sale_setup = lambda node_id: (("party", [], None, "world"), None) if outcome != "none" else (None, "not running")

        def sold(party, node_id, buyers, find_actor, world):
            if outcome == "refused":
                raise CommandRejected("no buyer")
            return {"buyer": "firm:rich", "price": 99.94}
        with mock.patch.object(sales.exchange_sale, "sell_concern", sold):
            return module.sell_concern(NODE)

    def test_a_sale_reports_the_buyer_the_price_and_the_founders_capital(self):
        self.assertEqual(self.sell("sold"), {"ok": True, "sold": NODE, "buyer": "firm:rich", "price": 99.9, "capital": 1234.6})

    def test_a_refusal_from_the_exchange_is_carried_back(self):
        self.assertEqual(self.sell("refused"), {"ok": False, "error": "no buyer"})

    def test_a_concern_not_run_is_refused_with_the_setups_reason(self):
        self.assertEqual(self.sell("none"), {"ok": False, "error": "not running"})


if __name__ == "__main__":
    unittest.main()
