"""reserve_staff (Complaint 176): the policy is off by default for a player and for the optimizer, and the policy switch and
the reserve sizes survive a save and load. `default_policy` and the state records, no game. The reserve rule is
test_reserve_staff_policy."""
import json
import unittest

from sim.engine.seat_defaults import default_policy
from sim.engine.state import (EconomyState, FounderState, GovernanceState, HoldingsState, HouseholdState, PopulationState,
                              ProjectsState, ScenarioState, SimulationState, deserialize_state, serialize_state)

QUICK_TOPIC = True


class DefaultPolicy(unittest.TestCase):

    def test_reserve_staff_is_listed_and_off_for_a_player_and_for_the_optimizer(self):
        for manual in (True, False):
            self.assertIs(default_policy(manual)["reserve_staff"], False)


class SavedReserve(unittest.TestCase):

    def test_the_switch_and_the_reserve_sizes_survive_a_save_and_load(self):
        state = SimulationState(
            household=HouseholdState(capital=1.0, reserve_craftsmen=5, reserve_scholars=1), projects=ProjectsState(),
            economy=EconomyState(), holdings=HoldingsState(), governance=GovernanceState(),
            founder=FounderState(policy={"reserve_staff": True}), scenario=ScenarioState(year=100), population=PopulationState())
        loaded = deserialize_state(json.loads(json.dumps(serialize_state(state))))
        self.assertIs(loaded.founder.policy["reserve_staff"], True)
        self.assertEqual((loaded.household.reserve_craftsmen, loaded.household.reserve_scholars), (5, 1))


if __name__ == "__main__":
    unittest.main()
