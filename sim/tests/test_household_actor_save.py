"""Complaint 185, Complaint 640: a seat as a party to the exchange takes its money, staff, knowledge and concerns from the modules that
own them and holds none of its own; the actors' records are written to the save by field detection and round-trip. Over small
fixtures, no game."""
QUICK_TOPIC = True

import json
import unittest

from sim.agents.api import ActorsState, Business
from sim.agents.records import ActorRecord
from sim.seats.api import SeatsSeat
from sim.tests.money_host import MoneyHost
from sim.engine.state import deserialize_state, serialize_state


class SeatPartyIsAnActorOverItsOwners(unittest.TestCase):
    def setUp(self):
        self.host = MoneyHost(capital=100.0)
        self.business = Business()
        self.host.employees = {"smith": 2.0}
        self.host.known = {"fire"}
        self.party = self.host.party("founder", dealings=SeatsSeat(), business=self.business)

    def test_its_money_is_the_purse_it_started_with_and_writes_through(self):
        self.assertEqual(self.party.money, 100.0)
        self.party.money = 1234.0
        self.assertEqual((self.party.money, self.host.view("acting_balance")()), (1234.0, 1234.0))

    def test_a_purse_set_elsewhere_is_what_the_party_reads(self):
        self.host.purses.set_net("founder", 55.0, "test")
        self.assertEqual(self.party.money, 55.0)

    def test_its_staff_and_knowledge_are_the_owners_and_its_concerns_the_businesss_open_set(self):
        self.assertIs(self.party.workforce, self.host.employees)
        self.assertEqual(self.party.knowledge, {"fire"})
        self.business.operating().add("mill")
        self.assertEqual(set(self.party.concerns), {"mill"})

    def test_it_holds_the_surface_an_exchange_deals_with(self):
        for name in ("money", "workforce", "knowledge", "concerns", "purses", "account_id", "actor_id", "record", "kind"):
            self.assertTrue(hasattr(self.party, name), name)


class ActorRecordsSave(unittest.TestCase):
    def test_the_actors_records_round_trip_through_the_serialised_state(self):
        state = ActorsState(home_country="rome_100ad")   # the actors module's world slot
        state.records["firm:1"] = ActorRecord(kind="firm", money=500.0, target="mill")
        state.records["firm:1"].income["takings"] = 40.0
        saved = json.loads(json.dumps(serialize_state(state)))
        self.assertIn("firm:1", saved["records"])
        loaded = deserialize_state(saved, ActorsState)
        self.assertEqual(loaded.records, state.records)
        self.assertEqual(loaded.records["firm:1"].income, {"takings": 40.0})


if __name__ == "__main__":
    unittest.main()
