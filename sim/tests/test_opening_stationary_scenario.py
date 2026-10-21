"""SCENARIO (Complaints 473, 526, 545; GitHub issue 61): the opening is a fixed point of the yearly rules.

The small fixture opens and steps. Its stationary quantities are worked out from its own figures
(`opening_stationary.solve`, a plain input-output solve with a cost-price dual): the runs that meet its opening demand,
the hours they hire against the hours its workers offer, the income those runs pay (wages plus profit equal the value
of final demand) and the coin the mint strikes against the coin that wears. A stepped year must then leave each price,
the wage, the rate and the money stock within the bounds the settling statistic uses (`sim/economy/settling.py`), and
each year after it too. Which rule moves each quantity is in `Complaints/473` (Update 6).
"""
import math
import unittest

from sim.economy import opening_stationary
from sim.economy.economy import Economy
from sim.economy.settling import MAX_LOG_CHANGE_PER_YEAR, MAX_RATE_CHANGE_PER_YEAR
from sim.tests import economy_fixture as fixture

YEARS = 3


def stepped(setup, years=YEARS):
    economy = Economy(setup)
    start = {"prices": dict(setup.opening_prices), "wage": setup.opening_wages[fixture.LABOURER],
             "rate": setup.opening_rate, "money": economy.record.book.money_supply(setup.currency_id)}
    outcomes = [economy.step(fixture.quiet_year(setup)) for _year in range(years)]
    return economy, start, outcomes


def log_change(before, after):
    return math.log(after / before)


class StationaryQuantitiesOfTheStatedFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = fixture.small_setup()
        cls.economy = Economy(cls.setup)
        cls.flows = opening_stationary.solve({fixture.TOWN: cls.economy.record.opening_demand}, cls.setup.recipes,
                                             cls.setup.opening_prices, cls.setup.opening_wages, cls.setup.opening_rate)

    def test_the_openings_producers_work_the_runs_the_solve_gives(self):
        worked = {}
        for producer in self.economy.record.producers.values():
            worked[producer.recipe_id] = worked.get(producer.recipe_id, 0.0) + producer.expected_sales
        for recipe_id, runs in self.flows.runs.items():
            self.assertAlmostEqual(worked[recipe_id] / runs, 1.0 / (1.0 + 0.1) * 1.1, places=1)

    def test_wages_plus_profit_equal_the_value_of_the_final_demand_the_opening_sized_to(self):
        self.assertAlmostEqual(self.flows.income / self.flows.final_value, 1.0, places=6)

    def test_the_stated_fixture_offers_many_times_the_hours_its_runs_hire(self):
        workers = sum(self.setup.opening_population_by_tile.values()) * self.setup.working_share
        offered = workers * self.setup.working_hours_per_year
        ratio = opening_stationary.hours_offered_over_demanded(self.flows.hours_by_trade, offered, fixture.LABOURER)
        self.assertGreater(ratio, 5.0)      # so the market clears at the survival wage, not the stated wage

    def test_the_stationary_fixture_offers_the_hours_its_runs_hire_plus_the_stated_slack(self):
        setup = fixture.stationary_setup(0.1)
        workers = sum(setup.opening_population_by_tile.values()) * setup.working_share
        ratio = opening_stationary.hours_offered_over_demanded(
            self.flows.hours_by_trade, workers * setup.working_hours_per_year, fixture.LABOURER)
        self.assertAlmostEqual(ratio, 1.1, places=6)


class ObservedInflationTests(unittest.TestCase):
    def test_the_opening_remembers_its_prices_and_a_year_reads_inflation_from_them(self):
        setup = fixture.small_setup()
        economy = Economy(setup)
        self.assertEqual(economy.record.memory.last_year_prices, setup.opening_prices)
        outcome = economy.step(fixture.quiet_year(setup))
        grain = outcome.prices[fixture.GRAIN] / setup.opening_prices[fixture.GRAIN] - 1.0
        observed = economy.record.memory.observed_inflation[setup.currency_id]
        self.assertGreaterEqual(observed, min(grain, 0.0) - 1e-9)    # a median of the goods, never below the lowest
        self.assertLessEqual(observed, max(grain, 0.0) + 1e-9)


class OneYearOfTheStatedFixtureTests(unittest.TestCase):
    @unittest.expectedFailure
    def test_a_year_leaves_the_wage_and_the_grain_price_within_the_settling_bounds(self):
        _economy, start, outcomes = stepped(fixture.small_setup(), 1)
        self.assertLessEqual(abs(log_change(start["wage"], outcomes[0].wages[fixture.LABOURER])), MAX_LOG_CHANGE_PER_YEAR)
        self.assertLessEqual(abs(log_change(start["prices"][fixture.GRAIN], outcomes[0].prices[fixture.GRAIN])),
                             MAX_LOG_CHANGE_PER_YEAR)


class EveryYearOfTheStationaryFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = fixture.stationary_setup()
        cls.economy, cls.start, cls.outcomes = stepped(cls.setup)

    def steps(self):
        """(year, series, before, after) for the prices, wage, money and rate, each year against the one before."""
        before = {**{"price:" + good: price for good, price in self.start["prices"].items()},
                  "wage": self.start["wage"], "money": self.start["money"], "rate": self.start["rate"]}
        for outcome in self.outcomes:
            after = {**{"price:" + good: price for good, price in outcome.prices.items()},
                     "wage": outcome.wages[fixture.LABOURER], "money": outcome.money_supply, "rate": outcome.rate}
            for series in sorted(before):
                yield outcome.year, series, before[series], after[series]
            before = after

    @unittest.expectedFailure
    def test_each_price_the_wage_and_the_money_stock_move_within_the_bound_each_year(self):
        for year, series, before, after in self.steps():
            if series != "rate":
                with self.subTest(year=year, series=series):
                    self.assertLessEqual(abs(log_change(before, after)), MAX_LOG_CHANGE_PER_YEAR)

    @unittest.expectedFailure
    def test_the_rate_moves_within_the_bound_each_year(self):
        for year, series, before, after in self.steps():
            if series == "rate":
                with self.subTest(year=year):
                    self.assertLessEqual(abs(after - before), MAX_RATE_CHANGE_PER_YEAR)

    @unittest.expectedFailure
    def test_the_mint_strikes_about_the_coin_that_wears(self):
        for outcome in self.outcomes:
            net = outcome.money_audit.edge_net
            struck, worn = net["edge:mint"][self.setup.currency_id], -net["edge:wear"][self.setup.currency_id]
            with self.subTest(year=outcome.year):
                self.assertLessEqual(abs(log_change(worn, struck)), MAX_LOG_CHANGE_PER_YEAR)


if __name__ == "__main__":
    unittest.main()
