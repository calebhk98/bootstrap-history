"""Scenarios: the starting workforce of a played game is the same for the same seed (Complaint 640: the rules, including
the yearly allocation, are in test_workforce_spinup)."""
import unittest

from .harness import *  # noqa: F401,F403


class StartingWorkforceScenarios(unittest.TestCase):

    def _first_year(self, civ_id):
        test_sim = unopened_sim(civ=civ_id, events=False)
        test_sim._demographic_recovery(test_sim.civ.get("year", 100) + 1)
        return test_sim, test_sim.state.economy.society_labour_hours

    def test_the_same_seed_gives_the_same_starting_workforce(self):
        first, _hours = self._first_year("rome_100ad")
        second, _hours = self._first_year("rome_100ad")
        self.assertEqual(first.state.economy.society_labour_hours, second.state.economy.society_labour_hours)


if __name__ == "__main__":
    unittest.main()
