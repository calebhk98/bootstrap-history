"""A mortality shock's wage premium is logged for the player: `Sim._refresh_demographic_indexes` on a stand-in game."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine.core import Sim
from sim.refusal import cause_of, facts_of


def game(wage_index, said=-1000, base=1.0, elasticity=0.5):
    return SimpleNamespace(wage_index=wage_index, _wage_index_base=base, WAGE_SCARCITY_ELASTICITY=elasticity,
                           state=SimpleNamespace(scenario=SimpleNamespace(_said_wage_cascade=said), household=SimpleNamespace(log=[])))


class WageCascadeLog(unittest.TestCase):
    def test_a_premium_is_logged_with_its_size_and_the_shortfall_behind_it(self):
        stand_in = game(wage_index=1.5)
        Sim._refresh_demographic_indexes(stand_in, 1348)
        (year, line), = stand_in.state.household.log
        self.assertEqual((year, cause_of(line)), (1348, "wage_cascade"))
        self.assertEqual(facts_of(line), {"population_below_trend_percent": 100, "wage_premium_percent": 50})
        self.assertEqual(stand_in.state.scenario._said_wage_cascade, 1348)

    def test_a_premium_under_half_a_percent_is_not_logged(self):
        stand_in = game(wage_index=1.004)
        Sim._refresh_demographic_indexes(stand_in, 1348)
        self.assertEqual(stand_in.state.household.log, [])

    def test_it_is_not_repeated_within_fifteen_years(self):
        stand_in = game(wage_index=1.5, said=1340)
        Sim._refresh_demographic_indexes(stand_in, 1348)
        self.assertEqual(stand_in.state.household.log, [])
        Sim._refresh_demographic_indexes(stand_in, 1355)
        self.assertEqual(len(stand_in.state.household.log), 1)


if __name__ == "__main__":
    unittest.main()
