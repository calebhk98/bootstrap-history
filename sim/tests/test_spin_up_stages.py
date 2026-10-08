"""The spin-up's second stage, after the workforce is trimmed, runs a bounded number of years on the economy
the first stage left; it settles wages and entry and does not wait for a tolerance that thin labour markets
never meet."""
QUICK_TOPIC = True

import unittest

from sim.engine import economy_port_year


class _CountingEconomy:
    def __init__(self):
        self.years = 0

    def step(self, inputs):
        self.years += 1


class TrimmedStageTests(unittest.TestCase):
    def test_the_stage_runs_its_declared_number_of_years_on_the_economy_it_is_given(self):
        economy = _CountingEconomy()
        economy_port_year.AgentEconomy._settle_trimmed(economy, object())
        self.assertEqual(economy.years, int(economy_port_year.SPIN_UP_TRIMMED_YEARS))

    def test_the_stage_is_shorter_than_the_first_stage_can_be(self):
        self.assertLess(economy_port_year.SPIN_UP_TRIMMED_YEARS, economy_port_year.SPIN_UP_MAXIMUM_YEARS)


if __name__ == "__main__":
    unittest.main()
