"""An actor whose class sets `lends_from_purse` is offered to borrowers by the credit market (Complaint 636), and a
variant civilisation is not played beside its base as a foreign partner.

Each rule is called on the real method of the finance module, over plain values for the views it reads."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agents.registry import ActorRegistry
from sim.agents.api import EDGE_SAVERS
from sim.engine.foreign_economy_data import foreign_economy_records
from sim.finance.module import Finance
from sim.foreign_trade.module import ForeignTrade
from sim.tests import harness, module_harness  # noqa: F401  (harness isolates the home directory)


def actor(actor_id, lends, exited_year=None):
    return SimpleNamespace(actor_id=actor_id, lends_from_purse=lends, record=SimpleNamespace(exited_year=exited_year))


class Purses:
    def __init__(self, purses, deposits):
        self.purses, self.deposits = purses, deposits

    def purse(self, actor_id):
        return self.purses.get(actor_id, 0.0)

    def deposit(self, actor_id):
        return self.deposits.get(actor_id, 0.0)


class Lenders(unittest.TestCase):
    def test_the_registry_lists_lending_actors_in_play_in_id_order(self):
        registry = SimpleNamespace(actors={"b": actor("b", True), "a": actor("a", True), "c": actor("c", False),
                                           "gone": actor("gone", True, exited_year=100)})
        self.assertEqual([found.actor_id for found in ActorRegistry.purse_lenders(registry)], ["a", "b"])

    def lenders_market(self, purses, firms, lenders):
        return module_harness.build(Finance, views={
            "state_treasury": SimpleNamespace(actor_id="state"), "cast_state": SimpleNamespace(purses=purses),
            "cast": SimpleNamespace(active_firms=lambda: firms, purse_lenders=lambda: lenders)})

    def test_a_lending_actors_purse_is_offered_as_a_firms_is(self):
        purses = Purses({"abbey": 700.0, "firm": 50.0}, {"abbey": 30.0})
        market = self.lenders_market(purses, [SimpleNamespace(actor_id="firm")], [actor("abbey", True)])
        offers = market.lender_offers({"households": 5.0, "state": 9.0})
        self.assertEqual(offers["abbey"], 730.0)
        self.assertEqual(offers["firm"], 50.0)
        self.assertEqual(offers["state"], 9.0)

    def test_no_lending_actor_changes_no_offer(self):
        offers = self.lenders_market(Purses({}, {}), [], []).lender_offers({"households": 1.0, "state": 2.0})
        self.assertEqual(offers, {EDGE_SAVERS: 1.0, "state": 2.0})


class VariantPartners(unittest.TestCase):
    def partners(self, civ):
        return module_harness.build(ForeignTrade, views={
            "foreign_economy_records": foreign_economy_records(), "year": 100, "civilisation": civ}).partners()

    def test_a_variant_is_played_without_its_base_as_a_partner(self):
        partner = next(record["civilization"] for record in foreign_economy_records()
                       if record.get("enabled", False) and record["from_year"] <= 100 <= record["until_year"])
        self.assertIn(partner, self.partners({"id": "rome_100ad"}))
        self.assertNotIn(partner, self.partners({"id": "mod:variant", "variant_of": partner}))
        self.assertNotIn(partner, self.partners({"id": partner}))


if __name__ == "__main__":
    unittest.main()
