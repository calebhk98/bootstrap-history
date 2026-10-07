"""The agent economy's workforce is the labour core's market state, and the core sets its wages."""
import dataclasses
import json
import unittest

from sim.economy.market_memory import market_key
from sim.economy.record import EconomyRecord
from sim.economy.setup import TradeSpec, labour_area
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


def smith_to_labourer_wage_ratio(smith_training_years, years=45, settled_after=20):
    """Mean over the settled years of the smith wage over the labourer wage in the town's labour area."""
    setup = fixture.small_setup()
    trades = {fixture.LABOURER: TradeSpec(fixture.LABOURER), fixture.MINER: TradeSpec(fixture.MINER, 1.0),
              fixture.SMITH: TradeSpec(fixture.SMITH, smith_training_years)}
    setup = dataclasses.replace(setup, trades=trades)
    economy = fixture.Economy(setup)
    ratios = []
    for year in range(years):
        economy.step(fixture.quiet_year(setup))
        wages = economy.record.workforce.wages[labour_area(fixture.TOWN)]
        if year >= settled_after and wages.get(fixture.SMITH) and wages.get(fixture.LABOURER):
            ratios.append(wages[fixture.SMITH] / wages[fixture.LABOURER])
    return sum(ratios) / len(ratios)


class TrainingPremiumEmergesTests(unittest.TestCase):
    """No premium is written anywhere: a trade that takes years to learn pays more than one that does
    not because entrants will not take it up for the floor, and a trade anyone can take up does not."""

    def test_a_long_training_trade_pays_over_the_labourers_wage_once_settled(self):
        self.assertGreater(smith_to_labourer_wage_ratio(5.0), 1.5)

    def test_a_trade_needing_no_training_pays_what_the_labourer_gets(self):
        self.assertLess(smith_to_labourer_wage_ratio(0.0), 1.1)

    def test_longer_training_keeps_a_higher_premium(self):
        self.assertGreater(smith_to_labourer_wage_ratio(8.0), smith_to_labourer_wage_ratio(2.0))


if __name__ == "__main__":
    unittest.main()
