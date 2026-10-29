"""Complaints 484 and 486: the stability phase runs right after the campaigns, and a state's unrest, hold, risings, land
taken and registered people are saved state. The phase order is the shipped list of year phases; the fields are a state
record put through the state's own serialisation. No game is built; the phase in a real game is test_stability_scenario."""

QUICK_TOPIC = True

import unittest

from sim.agents.api import ActorRecord, ActorsState
from sim.engine import year_phases
from sim.engine.state import FounderState, HouseholdState, SimulationState, deserialize_state, serialize_state

ACTOR_ID = "state:test"
STABILITY_FIELDS = {
    "unrest_by_tile": {"a": 0.25, "b": 0.5},
    "hold_by_tile": {"a": 0.75, "b": 1.0},
    "land_taken_by_tile": {"a": 1.0},
    "registered_people": {"a": 1200.0, "b": 300.0},
    "risings": [{"year": 101, "tile": "a", "kind": "put_down", "soldiers": 40.0}],
}


class StabilityPhaseOrderTests(unittest.TestCase):
    def test_the_revolts_phase_runs_right_after_the_campaigns(self):
        names = [phase.name for phase in year_phases.SHIPPED]
        self.assertEqual(names.index("revolts"), names.index("campaigns") + 1)


class StabilityFieldsSavedTests(unittest.TestCase):
    def test_a_states_unrest_hold_risings_land_taken_and_registered_people_survive_a_save(self):
        state = ActorsState()   # the actors module's world slot
        state.records[ACTOR_ID] = ActorRecord(kind="state", **STABILITY_FIELDS)
        loaded = deserialize_state(serialize_state(state), ActorsState)
        record = loaded.records[ACTOR_ID]
        for field_name, value in STABILITY_FIELDS.items():
            self.assertEqual(getattr(record, field_name), value, field_name)


if __name__ == "__main__":
    unittest.main()
