"""Complaints 554 and 473, the short part: the first years of the Rome agent economy's hidden first stage (fixed
people, no shocks) keep physically feasible accounts. A rule of the books, so a few years hold it. The checks that
need the spin-up's whole length (the mint replaces wear, the economy settles) are in
test_baseline_rome_full_length.py (Complaint 640)."""
import unittest

from sim.economy import api as economy_api
from sim.economy.baseline_checks import feasibility
from sim.engine.economy_port_setup import build_setup
from sim.engine.economy_port_year import YearInputs
from sim.tests import harness

FEASIBILITY_YEARS = 4


class RomeBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = harness.sim()

    def test_the_first_years_accounts_are_physically_feasible(self):
        setup = build_setup(self.game, self.game.state.economy.agent_economy["opening"])
        economy = economy_api.blank_economy(setup)
        economy_api.begin_spin_up(economy)
        inputs = YearInputs(year=0, population_by_tile={}, working_age_share=setup.working_share,
                            yield_factor_by_producer={}, engine_orders={})
        accounts = [economy.step(inputs).accounts for _year in range(FEASIBILITY_YEARS)]
        self.assertEqual(feasibility(accounts), [])


if __name__ == "__main__":
    unittest.main()
