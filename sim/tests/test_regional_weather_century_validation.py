"""Baseline validation (CLAUDE.md 4.2, Complaint 46): with the weather drawn per land cell and pooled, an unshocked
rome_100ad century ends above 100 percent of its starting population. Slow-only; the weather rules are in
test_regional_weather_wiring.py.

The bar is the stakeholder's own for the pooled-weather work. A failure means the pooled weather or the granary no
longer carries the baseline (Complaints 46 and 44), not that the bar should move."""
import unittest

from .harness import *  # noqa: F401,F403


class UnshockedCenturyAcceptanceTests(unittest.TestCase):

    def test_unshocked_century_ends_above_its_starting_population(self):
        test_sim = sim(civ="rome_100ad", events=False)
        start = test_sim.population.total
        for year in range(101, 201):
            test_sim._demographic_recovery(year)
        end = test_sim.population.total
        self.assertGreater(end, start, ("baseline validation, Complaint 46", start, end))


if __name__ == "__main__":
    unittest.main()
