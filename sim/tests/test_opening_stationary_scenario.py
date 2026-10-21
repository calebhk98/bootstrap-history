"""SCENARIO (Complaints 473, 526, 545; GitHub issue 61): the opening is a fixed point of the yearly rules.

The small fixture opens and steps. Its stationary quantities are worked out from its own figures
(`opening_stationary.solve`, a plain input-output solve with a cost-price dual): the runs that meet its opening demand,
the hours they hire against the hours its workers offer, the income those runs pay (wages plus profit equal the value
of final demand) and the coin the mint strikes against the coin that wears. A stepped year must then leave each price,
the wage, the rate and the money stock within the bounds the settling statistic uses (`sim/economy/settling.py`), and
each year after it too. Which rule moves each quantity is in `Complaints/473` (Update 6).
"""
import dataclasses
import math
import unittest

from sim.economy import household_hours_year, opening_leisure, opening_stationary, year_labour
from sim.economy.economy import Economy
from sim.economy.setup import EconomySetup
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
        economy = Economy(setup)
        view = economy.view()
        offers = year_labour.labour_offers(setup, economy.record, view, year_labour.outside_option_by_tile(setup, economy.record, view))
        kept = household_hours_year.decide(setup, economy.record, view, offers, economy._own_plot_options(),
                                           economy._hectares_held())
        offered = sum(offer.hours for offer in offers) - sum(kept.values())      # what the households sell, after the plot
        ratio = opening_stationary.hours_offered_over_demanded(self.flows.hours_by_trade, offered, fixture.LABOURER)
        self.assertAlmostEqual(ratio, 1.1, places=2)


class OpeningHoursTests(unittest.TestCase):
    """The opening's households split their time so the hours they sell equal the hours its runs hire (opening_leisure.py)."""
    def sold_and_hired(self, setup):
        economy = Economy(setup)
        view = economy.view()
        outside = year_labour.outside_option_by_tile(setup, economy.record, view)
        offers = year_labour.labour_offers(setup, economy.record, view, outside)
        supply = economy._hour_supply(offers, view, outside)
        sold = {}
        for offer in offers:
            wage = view.wage(offer.trade, offer.area) or offer.reservation_wage
            sold[offer.trade] = sold.get(offer.trade, 0.0) + supply.split(offer, wage)[0]
        hired = opening_leisure.hours_hired_by_trade(economy.record.producers, setup.recipes)
        return sold, hired

    def test_the_stated_fixtures_workers_with_two_thousand_hours_sell_the_hours_its_runs_hire(self):
        sold, hired = self.sold_and_hired(fixture.small_setup(land_per_run={fixture.FARM: fixture.PLOT_LAND_PER_RUN}))
        self.assertAlmostEqual(sold[fixture.LABOURER] / hired[fixture.LABOURER], 1.0, places=6)

    def test_the_hours_the_workers_do_not_sell_are_leisure_not_idleness_the_plot_could_use(self):
        setup = fixture.small_setup(land_per_run={fixture.FARM: fixture.PLOT_LAND_PER_RUN})
        economy = Economy(setup)
        self.assertGreater(economy.record.leisure_anchor_wage[fixture.LABOURER], 0.0)

    def test_no_scenario_states_the_incomes_of_its_households(self):
        self.assertNotIn("opening_income_per_head", {field.name for field in dataclasses.fields(EconomySetup)})


class KnifeEdgeTests(unittest.TestCase):
    """A few per cent more hours than the runs hire moved the wage down a third in the first year (473 Update 7); the
    hours sold now rise with the wage, so the wage moves a few per cent. The excess is given after the opening has split
    its households' time, so it is hours the opening did not count."""
    def first_year_wage_change(self, excess):
        setup = fixture.stationary_setup()
        economy = Economy(setup)
        economy.setup = dataclasses.replace(setup, working_hours_per_year=setup.working_hours_per_year * (1.0 + excess))
        outcome = economy.step(fixture.quiet_year(economy.setup))
        return log_change(setup.opening_wages[fixture.LABOURER], outcome.wages[fixture.LABOURER])

    def test_the_first_years_wage_moves_by_at_most_three_times_the_excess_of_hours(self):
        # the plot alone makes hours sold rise by about half a per cent for each per cent of wage; before the schedule
        # three per cent of excess moved the wage by thirty-five per cent, twelve times the excess
        for excess in (0.03, 0.1):
            with self.subTest(excess=excess):
                self.assertLess(abs(self.first_year_wage_change(excess)), 3.0 * excess)

    def test_the_wage_moves_less_than_the_excess_hours_would_move_it_if_all_were_offered_at_the_ask(self):
        self.assertLess(abs(self.first_year_wage_change(0.03)), abs(self.first_year_wage_change(0.1)))


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
    @unittest.expectedFailure       # cause: the stated fixture's workers have far more hours than its runs hire, and nothing at home uses them (it has no plots)
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

    def test_the_wage_the_grain_price_and_the_money_stock_move_within_the_bound_each_year(self):
        for year, series, before, after in self.steps():
            if series in ("wage", "money", "price:" + fixture.GRAIN, "price:" + fixture.METAL):
                with self.subTest(year=year, series=series):
                    self.assertLessEqual(abs(log_change(before, after)), MAX_LOG_CHANGE_PER_YEAR)

    @unittest.expectedFailure       # cause: households add to their own cash each year and no lender returns it, so the farms' cash, and the runs it pays for (producers.plan, `affordable`), fall (607, 606)
    def test_the_hours_hired_hold_from_year_to_year(self):
        hired = [outcome.hired_hours for outcome in self.outcomes]
        for before, after in zip(hired, hired[1:]):
            self.assertGreater(after, 0.9 * before)

    def test_the_cash_the_households_add_in_the_first_year_is_the_cash_the_producers_lose(self):
        setup = fixture.stationary_setup()
        economy = Economy(setup)

        def cash(agents):
            return sum(economy.record.book.balance(agent, setup.currency_id) for agent in agents)
        households, producers = list(economy.record.cohorts), list(economy.record.producers)
        households_before, producers_before = cash(households), cash(producers)
        economy.step(fixture.quiet_year(setup))
        added, lost = cash(households) - households_before, producers_before - cash(producers)
        self.assertGreater(added, 0.0)
        self.assertAlmostEqual(added / lost, 1.0, delta=0.2)

    @unittest.expectedFailure       # cause: the ore price, which the smelters' bids lift to the ask band's cap in year 2 (473 mover 3)
    def test_the_ore_price_moves_within_the_bound_each_year(self):
        for year, series, before, after in self.steps():
            if series == "price:" + fixture.ORE:
                with self.subTest(year=year):
                    self.assertLessEqual(abs(log_change(before, after)), MAX_LOG_CHANGE_PER_YEAR)

    def test_the_rate_moves_within_the_bound_each_year(self):
        for year, series, before, after in self.steps():
            if series == "rate":
                with self.subTest(year=year):
                    self.assertLessEqual(abs(after - before), MAX_RATE_CHANGE_PER_YEAR)

    @unittest.expectedFailure       # cause: the metal demand the opening sizes is met by capacity the chain places elsewhere (473 mover 4)
    def test_the_mint_strikes_about_the_coin_that_wears(self):
        for outcome in self.outcomes:
            net = outcome.money_audit.edge_net
            struck, worn = net["edge:mint"][self.setup.currency_id], -net["edge:wear"][self.setup.currency_id]
            with self.subTest(year=outcome.year):
                self.assertLessEqual(abs(log_change(worn, struck)), MAX_LOG_CHANGE_PER_YEAR)


if __name__ == "__main__":
    unittest.main()
