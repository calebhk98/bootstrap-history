"""SCENARIO (Complaint 473, GitHub issue 61): on the stationary fixture the staple's supply does not collapse in the years
after the opening. Producers plan to expected sales and work excess stock off over several years, idle capacity is shed
only where expected sales do not need it, and an input's bid is bounded by its value in use. The rules are tested in
test_economy_stock_drawdown, test_economy_idle_capacity_life, test_economy_input_ceiling_share and
test_economy_ask_band_chain; this is the year loop that joins them."""

QUICK_TOPIC = False

import unittest

from sim.economy.economy import Economy
from sim.tests import economy_fixture as fixture

YEARS = 5
MOST_STAPLE_RUNS_LOST_IN_FIVE_YEARS = 0.3      # measured on the fixture: 28 per cent lost (34 per cent before this change)


def grain_runs(economy):
    return sum(max(producer.last_runs, 0.0) for producer in economy.record.producers.values()
               if producer.recipe_id == fixture.FARM)


class SupplyCollapseScenarioTests(unittest.TestCase):
    def test_the_staples_runs_do_not_collapse_over_the_first_years(self):
        setup = fixture.stationary_setup()
        economy = Economy(setup)
        economy.step(fixture.quiet_year(setup))
        first = grain_runs(economy)
        for _year in range(YEARS - 1):
            economy.step(fixture.quiet_year(setup))
        self.assertGreater(grain_runs(economy), (1.0 - MOST_STAPLE_RUNS_LOST_IN_FIVE_YEARS) * first)


if __name__ == "__main__":
    unittest.main()
