"""What a save carries (`serialize_state`) and what a load reads back (`deserialize_state`), each called once on inputs written
out here: the fields the next year reads must be in the blob, and a blob's flags come back as they were saved. (Complaint 320.)
Large-economy defects are found by `python3 -m sim.tests.fingerprint`."""
import json
import unittest

from sim.engine.state import (EconomyState, FounderState, GovernanceState, HoldingsState, HouseholdState,
                              ProjectsState, ScenarioState, SimulationState, deserialize_state, serialize_state)

QUICK_TOPIC = True


def state(fog=False, civ=None, reserve=(0, 0), policy=None, said=None):
    built = SimulationState(
        household=HouseholdState(capital=1250.0, reserve_craftsmen=reserve[0], reserve_scholars=reserve[1]),
        projects=ProjectsState(done={"stone_cutting", "bronze"}), economy=EconomyState(), holdings=HoldingsState(),
        governance=GovernanceState(gov=0.5), founder=FounderState(policy=policy or {}), scenario=ScenarioState(year=115))
    built._fog, built._civ = fog, civ
    built.seat_progress._said_explanations = said
    return built


def founder_seat(blob):
    return blob["seats"]["founder"]


class SerializeState(unittest.TestCase):

    def test_the_blob_is_plain_json(self):
        self.assertIsInstance(json.dumps(serialize_state(state())), str)

    def test_capital_and_year_are_in_the_blob(self):
        blob = serialize_state(state())
        self.assertEqual(founder_seat(blob)["household"]["capital"], 1250.0)
        self.assertEqual(blob["scenario"]["year"], 115)

    def test_the_record_of_what_has_been_explained_once_is_in_the_blob(self):
        blob = serialize_state(state(said={"staffing_share": 100}))
        self.assertEqual(founder_seat(blob)["seat_progress"]["_said_explanations"], {"staffing_share": 100})

    def test_the_fog_flag_and_the_civilisation_are_in_the_blob(self):
        blob = serialize_state(state(fog=True, civ="england_1300"))
        self.assertEqual((blob["_fog"], blob["_civ"]), (True, "england_1300"))

    def test_a_game_without_fog_is_saved_as_without_fog(self):
        self.assertIs(serialize_state(state(fog=False))["_fog"], False)

    def test_the_reserve_sizes_and_the_policy_switch_are_in_the_blob(self):
        blob = serialize_state(state(reserve=(5, 1), policy={"reserve_staff": True}))
        self.assertEqual((founder_seat(blob)["household"]["reserve_craftsmen"], founder_seat(blob)["household"]["reserve_scholars"]), (5, 1))
        self.assertIs(founder_seat(blob)["founder"]["policy"]["reserve_staff"], True)


class DeserializeState(unittest.TestCase):

    def test_the_fog_flag_and_civilisation_of_a_blob_come_back(self):
        loaded = deserialize_state({"_fog": True, "_civ": "england_1300", "_rng": None})
        self.assertEqual((loaded._fog, loaded._civ), (True, "england_1300"))

    def test_a_blob_without_fog_loads_as_without_fog(self):
        self.assertIs(deserialize_state({"_fog": False})._fog, False)


if __name__ == "__main__":
    unittest.main()
