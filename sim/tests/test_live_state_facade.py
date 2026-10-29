"""The compatibility facade (ForwardingPropertiesMixin) keeps no storage of its own: every field it names reads and
writes the one authoritative subsystem state, so a write through either path is seen through the other."""
QUICK_TOPIC = True

import unittest

from sim.engine.core_properties import ForwardingPropertiesMixin
from sim.engine.state import EconomyState, FounderState, HouseholdState, SimulationState

# facade name -> (value to write, path of the field that must hold it on the state)
SCALARS = {
    "capital": (1250.0, "household.capital"),
    "goal": ("test_goal", "_goal"),
}
# facade name -> path of the collection it must be (the same object, not a copy)
COLLECTIONS = {
    "policy": "founder.policy",
}


class _Facade(ForwardingPropertiesMixin):
    def __init__(self):
        self.state = SimulationState(
            household=HouseholdState(capital=1000.0), founder=FounderState(),
            economy=EconomyState())

    def forget_goal_caches(self):
        pass


def _at(state, path):
    for part in path.split("."):
        state = getattr(state, part)
    return state


def _set(state, path, value):
    *parents, last = path.split(".")
    setattr(_at(state, ".".join(parents)) if parents else state, last, value)


class Facade(unittest.TestCase):
    def test_a_write_through_the_facade_lands_on_the_state_field(self):
        for name, (value, path) in SCALARS.items():
            facade = _Facade()
            setattr(facade, name, value)
            self.assertEqual(_at(facade.state, path), value, name)

    def test_a_write_to_the_state_field_is_read_back_through_the_facade(self):
        for name, (value, path) in SCALARS.items():
            facade = _Facade()
            _set(facade.state, path, value)
            self.assertEqual(getattr(facade, name), value, name)

    def test_a_collection_is_the_states_own_object(self):
        facade = _Facade()
        for name, path in COLLECTIONS.items():
            self.assertIs(getattr(facade, name), _at(facade.state, path), name)


if __name__ == "__main__":
    unittest.main()
