"""Scenarios: the starting workforce of a played game is the same for the same seed, and the yearly allocation
continues from the spun-up split (Complaint 640: the rules are in test_workforce_spinup)."""
import unittest

from .harness import *  # noqa: F401,F403
from sim.labour import labour_allocation


class StartingWorkforceScenarios(unittest.TestCase):

    def _first_year(self, civ_id):
        test_sim = sim(civ=civ_id, events=False)
        test_sim._demographic_recovery(test_sim.civ.get("year", 100) + 1)
        return test_sim, test_sim.state.economy.society_labour_hours

    def test_the_same_seed_gives_the_same_starting_workforce(self):
        first, _hours = self._first_year("rome_100ad")
        second, _hours = self._first_year("rome_100ad")
        self.assertEqual(first.state.economy.society_labour_hours, second.state.economy.society_labour_hours)

    def test_yearly_allocation_continues_from_the_spun_up_split(self):
        test_sim, first = self._first_year("rome_100ad")
        first = dict(first)
        test_sim._demographic_recovery(102)
        second = test_sim.state.economy.society_labour_hours
        rest_first = {trade: hours for trade, hours in first.items() if trade != labour_allocation.FARM_TRADE}
        rest_second = {trade: hours for trade, hours in second.items() if trade != labour_allocation.FARM_TRADE}
        total_first, total_second = sum(rest_first.values()), sum(rest_second.values())
        for trade, hours in rest_first.items():
            self.assertAlmostEqual(hours / total_first, rest_second[trade] / total_second, delta=0.02)

    def test_a_short_harvest_in_a_played_game_still_pulls_hours_to_the_farm(self):
        test_sim, hours = self._first_year("rome_100ad")
        farm = labour_allocation.FARM_TRADE
        before = hours[farm]
        for trade in hours:
            hours[trade] *= 0.5 if trade == farm else 1.0
        test_sim._demographic_recovery(102)
        self.assertGreater(test_sim.state.economy.society_labour_hours[farm], before * 0.5)


if __name__ == "__main__":
    unittest.main()
