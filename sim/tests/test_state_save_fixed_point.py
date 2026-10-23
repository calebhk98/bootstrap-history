"""A game saved, loaded and saved again gives the same file (Complaint 320's guard, as a rule): `serialize_state` and
`deserialize_state` on a state built here, with no game. State the next year reads but the save does not carry shows up as
a field the second save lacks or changes. Large-economy defects are found by `python3 -m sim.tests.fingerprint`."""
import json
import unittest

from sim.engine.state import (EconomyState, FounderState, GovernanceState, HoldingsState, HouseholdState, PopulationState,
                              ProjectsState, ScenarioState, SimulationState, deserialize_state, serialize_state)

QUICK_TOPIC = True


def built_state():
    return SimulationState(
        household=HouseholdState(capital=1250.0), projects=ProjectsState(done={"stone_cutting", "bronze"}),
        economy=EconomyState(), holdings=HoldingsState(), governance=GovernanceState(gov=0.5),
        founder=FounderState(), scenario=ScenarioState(year=115), population=PopulationState())


def text_of(blob):
    return json.dumps(blob, sort_keys=True, default=str)


class SaveIsAFixedPoint(unittest.TestCase):

    def test_saving_a_loaded_save_gives_the_same_blob(self):
        first = serialize_state(built_state())
        loaded = deserialize_state(json.loads(json.dumps(first)))
        self.assertEqual(text_of(serialize_state(loaded)), text_of(first))

    def test_a_loaded_state_keeps_what_was_set(self):
        loaded = deserialize_state(json.loads(json.dumps(serialize_state(built_state()))))
        self.assertEqual((loaded.household.capital, loaded.scenario.year, loaded.projects.done),
                         (1250.0, 115, {"stone_cutting", "bronze"}))


if __name__ == "__main__":
    unittest.main()
