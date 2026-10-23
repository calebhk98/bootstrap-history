"""Complaints/416: the engine keeps the roads and track an actor has built. The saved state is a round trip of built
state, checked on a built record. Building, labour, purse, routes and the command are the named scenarios in
test_built_ways_scenario."""
import unittest

from sim.engine.state import deserialize_state, serialize_state, EconomyState


class BuiltWaysTests(unittest.TestCase):

    def test_the_built_and_building_ways_survive_save_and_load(self):
        economy = EconomyState()
        economy.improvements = {"a|b": {"road": True, "canal": True}}
        economy.ways_under_construction = {"b|c": {"road": {"due": 130, "crew_trade": "labourer", "hours_a_year": 4000.0,
                                                          "engineered": False, "pressed": 128}}}
        copy = deserialize_state(serialize_state(economy), EconomyState)
        self.assertEqual(copy.improvements, economy.improvements)
        self.assertEqual(copy.ways_under_construction, economy.ways_under_construction)


if __name__ == "__main__":
    unittest.main()
