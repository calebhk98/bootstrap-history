"""The estimates option and its salt are saved state: a scenario world that has them on still has them, with the same salt (so
the same figures are drawn), after a save and a load. The rule is the state's own serialisation, called on the scenario module's
world state; the start reply's estimate is test_complaint_188_fuzzy_estimates."""

QUICK_TOPIC = True

import json
import unittest

from sim.engine.state import deserialize_state, serialize_state
from sim.scenario.state import ScenarioWorld


def round_trip(world):
    return deserialize_state(json.loads(json.dumps(serialize_state(world))), ScenarioWorld)


class FuzzyEstimatesSavedTests(unittest.TestCase):
    def test_the_option_and_its_salt_survive_a_save_and_a_load(self):
        loaded = round_trip(ScenarioWorld(fuzzy_estimates=True, fuzzy_salt=123456))
        self.assertIs(loaded.fuzzy_estimates, True)
        self.assertEqual(loaded.fuzzy_salt, 123456)

    def test_an_option_left_off_stays_off(self):
        loaded = round_trip(ScenarioWorld(fuzzy_estimates=False, fuzzy_salt=0))
        self.assertIs(loaded.fuzzy_estimates, False)
        self.assertEqual(loaded.fuzzy_salt, 0)

    def test_the_year_the_fog_and_the_notices_said_survive_a_save_and_a_load(self):
        loaded = round_trip(ScenarioWorld(year=115, fog=True, said_condition={"plague"}))
        self.assertEqual((loaded.year, loaded.fog, loaded.said_condition), (115, True, {"plague"}))


if __name__ == "__main__":
    unittest.main()
