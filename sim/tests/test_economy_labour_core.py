"""The agent economy's workforce is the labour core's market state, and the core sets its wages."""
import dataclasses
import json
import unittest

from sim.economy.market_memory import market_key
from sim.economy.record import EconomyRecord
from sim.economy.setup import TradeSpec, labour_area
from sim.labour.api import MarketState, people_in
from sim.labour.wages import training_premium
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


def smith_wage_over_labourer_wage(smith_training_years, years=30, settled_after=10):
    """Mean over the settled years of the smith wage over the labourer wage, and the training premium the
    smith's training years justify at the economy's rate."""
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
    return sum(ratios) / len(ratios), training_premium(smith_training_years, setup.opening_rate)


def smith_premium_in_floors(smith_training_years, years=30, settled_after=10):
    """Mean over the settled years of how far the smith wage is over the labourer wage, in the labourer's
    opening wage (the family's floor per hour). The labourer's ask falls with idle hands, so the ratio of
    the two wages is not used: it blows up as the labourer wage nears nothing."""
    setup = fixture.small_setup()
    trades = {fixture.LABOURER: TradeSpec(fixture.LABOURER), fixture.MINER: TradeSpec(fixture.MINER, 1.0),
              fixture.SMITH: TradeSpec(fixture.SMITH, smith_training_years)}
    setup = dataclasses.replace(setup, trades=trades)
    economy = fixture.Economy(setup)
    premiums, floor = [], None
    for year in range(years):
        economy.step(fixture.quiet_year(setup))
        wages = economy.record.workforce.wages[labour_area(fixture.TOWN)]
        if floor is None:
            floor = wages[fixture.LABOURER]
        if year >= settled_after and wages.get(fixture.SMITH) and wages.get(fixture.LABOURER):
            premiums.append((wages[fixture.SMITH] - wages[fixture.LABOURER]) / floor)
    return sum(premiums) / len(premiums)


class TrainingPremiumEmergesTests(unittest.TestCase):
    """No premium is written anywhere: a trade that takes years to learn pays more than one that does
    not because entrants will not take it up for the floor, and a trade anyone can take up does not."""

    def test_a_long_training_trade_never_pays_above_its_trained_substitute(self):
        # entrants train into a trade while it pays more than the unskilled wage times the training premium
        # and not beyond: the premium is a substitution bound, so scarcity of hands cannot lift it higher
        ratio, premium = smith_wage_over_labourer_wage(5.0)
        self.assertLessEqual(ratio, premium * 1.05)

    def test_a_trade_needing_no_training_pays_what_the_labourer_gets(self):
        self.assertLess(smith_premium_in_floors(0.0), 0.2)

    def test_longer_training_keeps_a_higher_premium(self):
        self.assertGreater(smith_premium_in_floors(8.0), smith_premium_in_floors(2.0))


if __name__ == "__main__":
    unittest.main()
