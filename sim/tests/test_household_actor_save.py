"""Complaint 185, Complaint 640: the founder's household is an Actor whose money, staff, knowledge and concerns are the
game's own state and which never chooses through a policy of its own; the actors' records are written to the save by
field detection and round-trip. Over small fixtures, no game."""
QUICK_TOPIC = True

import json
import unittest

from sim.agents.api import Actor, ActorsState, Household
from sim.agents.policy import IdlePolicy
from sim.agents.records import ActorRecord
from sim.engine.agents_port_household import HouseholdPort
from sim.engine.state import SimulationState, deserialize_state, serialize_state


class HouseholdIsAnActor(unittest.TestCase):
    def setUp(self):
        self.household = Household(starting_capital=100.0, port=HouseholdPort())

    def test_it_is_an_actor_that_never_chooses_through_a_policy(self):
        self.assertIsInstance(self.household, Actor)
        self.assertIsInstance(self.household.decision_policy, IdlePolicy)

    def test_its_money_is_the_capital_it_started_with_and_writes_through(self):
        self.assertEqual(self.household.capital, 100.0)
        self.household.money = 1234.0
        self.assertEqual(self.household.capital, 1234.0)

    def test_its_staff_knowledge_and_concerns_are_the_existing_state_not_copies(self):
        self.assertIs(self.household.workforce, self.household.employees)
        self.assertIs(self.household.knowledge, self.household.done)
        self.assertIs(self.household.concerns, self.household.operating)
        for name in ("money", "workforce", "knowledge", "concerns", "works", "decision_policy"):
            self.assertTrue(hasattr(self.household, name), name)


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
