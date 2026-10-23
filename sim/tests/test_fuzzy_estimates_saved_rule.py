"""The estimates option and its salt are saved state: a state that has them on still has them, with the same salt (so
the same figures are drawn), after a save and a load. The rule is the state's own serialisation, called on a bare
`SimulationState`; that a refused `start` still states the real need is test_scenarios_batch3_saves."""

QUICK_TOPIC = True

import unittest

from sim.engine.state import FounderState, HouseholdState, ProjectsState, SimulationState, deserialize_state, serialize_state


def bare_state(fuzzy, salt):
    state = SimulationState(household=HouseholdState(capital=1.0), projects=ProjectsState(), founder=FounderState())
    state._fuzzy_estimates = fuzzy
    state._fuzzy_salt = salt
    return state


class FuzzyEstimatesSavedTests(unittest.TestCase):
    def test_the_option_and_its_salt_survive_a_save_and_a_load(self):
        loaded = deserialize_state(serialize_state(bare_state(True, 123456)))
        self.assertIs(loaded._fuzzy_estimates, True)
        self.assertEqual(loaded._fuzzy_salt, 123456)

    def test_an_option_left_off_stays_off(self):
        loaded = deserialize_state(serialize_state(bare_state(False, 0)))
        self.assertIs(loaded._fuzzy_estimates, False)
        self.assertEqual(loaded._fuzzy_salt, 0)


if __name__ == "__main__":
    unittest.main()
