"""What a save carries (`serialize_state`) and what a load reads back (`deserialize_state`), each called once on inputs written
out here: the fields the next year reads must be in the blob, and a blob's flags come back as they were saved. (Complaint 320.)
Large-economy defects are found by `python3 -m sim.tests.fingerprint`."""
import json
import unittest

from sim.engine.state import (EconomyState, FounderState, HoldingsState, HouseholdState,
                              ProjectsState, SimulationState, deserialize_state, serialize_state)

QUICK_TOPIC = True

from sim.workforce.api import WorkforceSeat


def state(civ=None, reserve=(0, 0), policy=None, said=None):
    built = SimulationState(
        household=HouseholdState(capital=1250.0),
        projects=ProjectsState(done={"stone_cutting", "bronze"}), economy=EconomyState(), holdings=HoldingsState(),
        founder=FounderState(policy=policy or {}))
    built._civ = civ
    built.seats["founder"].modules["workforce"] = WorkforceSeat(reserve_craftsmen=reserve[0], reserve_scholars=reserve[1])
    built.seat_progress._said_explanations = said
    return built


def founder_seat(blob):
    return blob["seats"]["founder"]


class SerializeState(unittest.TestCase):

    def test_the_blob_is_plain_json(self):
        self.assertIsInstance(json.dumps(serialize_state(state())), str)

    def test_capital_is_in_the_blob(self):
        blob = serialize_state(state())
        self.assertEqual(founder_seat(blob)["household"]["capital"], 1250.0)

    def test_the_record_of_what_has_been_explained_once_is_in_the_blob(self):
        blob = serialize_state(state(said={"staffing_share": 100}))
        self.assertEqual(founder_seat(blob)["seat_progress"]["_said_explanations"], {"staffing_share": 100})

    def test_the_civilisation_is_in_the_blob(self):
        self.assertEqual(serialize_state(state(civ="england_1300"))["_civ"], "england_1300")

    def test_the_reserve_sizes_and_the_policy_switch_are_in_the_blob(self):
        blob = serialize_state(state(reserve=(5, 1), policy={"reserve_staff": True}))
        self.assertEqual((founder_seat(blob)["modules"]["workforce"]["reserve_craftsmen"], founder_seat(blob)["modules"]["workforce"]["reserve_scholars"]), (5, 1))
        self.assertIs(founder_seat(blob)["founder"]["policy"]["reserve_staff"], True)


class DeserializeState(unittest.TestCase):

    def test_the_civilisation_of_a_blob_comes_back(self):
        self.assertEqual(deserialize_state({"_civ": "england_1300", "_rng": None})._civ, "england_1300")


if __name__ == "__main__":
    unittest.main()
