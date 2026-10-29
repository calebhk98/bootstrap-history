"""Complaint 640: the UI's memory (notes, watched goals, programmes) lives in `SimulationState.interface`, so every save, load
and fork carries it: `serialize_state` writes the slot into the blob, `deserialize_state` reads it back, and a blob with nothing
remembered gives an empty slot. Each is called once on a state built here; the slot's own rules are test_ui_memory."""
QUICK_TOPIC = True

import json
import unittest

from sim.engine.state import (EconomyState, FounderState, HoldingsState, HouseholdState,
                              ProjectsState, SimulationState, deserialize_state, serialize_state)

REMEMBERED = {"notes": {"next": 2, "rows": [{"n": 1, "year": 100, "text": "aqueduct for the mill town", "project": None}]},
              "goals": {"watched": ["steam_engine"]}}


def state(interface=None):
    built = SimulationState(
        household=HouseholdState(capital=1250.0), projects=ProjectsState(done={"bronze"}), economy=EconomyState(),
        holdings=HoldingsState(), founder=FounderState(policy={}))
    if interface is not None:
        built.interface = interface
    return built


class InterfaceSlotInSave(unittest.TestCase):
    def test_a_new_states_interface_slot_is_empty(self):
        self.assertEqual(state().interface, {})

    def test_serialize_state_writes_the_slot_into_the_blob(self):
        blob = serialize_state(state(REMEMBERED))
        self.assertEqual(blob["interface"], REMEMBERED)

    def test_deserialize_state_reads_the_slot_back(self):
        blob = json.loads(json.dumps(serialize_state(state(REMEMBERED))))
        self.assertEqual(deserialize_state(blob).interface, REMEMBERED)

    def test_a_blob_with_nothing_remembered_gives_an_empty_slot(self):
        blob = json.loads(json.dumps(serialize_state(state())))
        self.assertEqual(deserialize_state(blob).interface, {})


if __name__ == "__main__":
    unittest.main()
