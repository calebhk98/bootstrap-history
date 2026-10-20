"""Land concentration over a long no-intervention run stays within the range pre-industrial agrarian
societies show (CLAUDE.md 4.2): a validation of a distribution, not a target the model aims at.

Band: land Gini between 0.3 and 0.85 and the top tenth of holders holding between 0.25 and 0.85 of the land.
Source (recalled, not looked up): estimates of landholding inequality in pre-industrial agrarian economies
put the Gini roughly from the low 0.4s (classical Attica smallholding) to the 0.8s (latifundia, colonial
estates); the band is deliberately wide. The measured path is printed so a failure shows the trajectory.
"""
import unittest

from sim.economy import titles_concentration
from sim.economy.economy import Economy
from sim.tests import economy_fixture

GINI_BAND = (0.3, 0.85)               # recalled, see module docstring
TOP_DECILE_BAND = (0.25, 0.85)        # recalled, see module docstring
YEARS = 100
SAMPLE_EVERY = 10
LEAN_HARVEST_FACTOR = 0.35
LEAN_HARVEST_EVERY = 4


def path(harvest_for_year):
    setup = economy_fixture.small_setup()
    economy = Economy(setup)
    measured = [titles_concentration.summary(setup.tiles, economy.record)]
    for year in range(YEARS):
        economy.step(economy_fixture.quiet_year(setup, harvest_factor=harvest_for_year(year)))
        if (year + 1) % SAMPLE_EVERY == 0:
            measured.append(titles_concentration.summary(setup.tiles, economy.record))
    return measured


class RangeCheckTests(unittest.TestCase):
    def assert_in_band(self, measured):
        print("land concentration path (top decile share, gini):",
              [(round(row["top_decile_share"], 3), round(row["gini"], 3)) for row in measured])
        for row in measured:
            self.assertGreaterEqual(row["gini"], GINI_BAND[0])
            self.assertLessEqual(row["gini"], GINI_BAND[1])
            self.assertGreaterEqual(row["top_decile_share"], TOP_DECILE_BAND[0])
            self.assertLessEqual(row["top_decile_share"], TOP_DECILE_BAND[1])

    def test_a_quiet_baseline_stays_in_the_agrarian_band(self):
        self.assert_in_band(path(lambda year: 1.0))

    def test_a_run_with_a_failed_harvest_every_few_years_stays_in_the_agrarian_band(self):
        self.assert_in_band(path(lambda year: LEAN_HARVEST_FACTOR if year % LEAN_HARVEST_EVERY == 1 else 1.0))


if __name__ == "__main__":
    unittest.main()
