"""The agent economy's workforce is the labour core's market state, and the core sets its wages."""
import json
import unittest

from sim.economy.market_memory import market_key
from sim.economy.record import EconomyRecord
from sim.economy.setup import labour_area
from sim.labour.api import MarketState, people_in
from sim.tests import economy_fixture as fixture


def worked(years=4):
    return fixture.run(fixture.small_setup(), years=years)[0]


class WorkforceIsTheCoresStateTests(unittest.TestCase):
    def test_the_record_holds_a_market_state_with_every_tiles_working_people(self):
        economy = worked(years=0)
        state = economy.record.workforce
        self.assertIsInstance(state, MarketState)
        for tile, people in economy.setup.opening_population_by_tile.items():
            self.assertAlmostEqual(people_in(state, labour_area(tile)), people * economy.setup.working_share, places=6)

    def test_the_wage_everyone_is_quoted_is_the_one_the_core_settled(self):
        economy = worked()
        state = economy.record.workforce
        for area, by_trade in state.wages.items():
            for trade, wage in by_trade.items():
                self.assertAlmostEqual(economy.record.memory.wages[market_key(trade, area)], wage)

    def test_the_state_survives_a_save_and_load(self):
        economy = worked()
        saved = json.loads(json.dumps(economy.record.to_record()))
        self.assertEqual(EconomyRecord.from_record(saved).workforce, economy.record.workforce)

    def test_people_are_not_created_or_lost_by_the_year(self):
        economy = worked(years=0)
        before = people_in(economy.record.workforce)
        economy.step(fixture.quiet_year(economy.setup))
        self.assertAlmostEqual(people_in(economy.record.workforce), before, places=6)


if __name__ == "__main__":
    unittest.main()
