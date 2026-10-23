"""The agent economy's yearly accounts (Complaint 554): what was made, used up in making, eaten, built and left in
stock, per good, and food eaten against need per cohort. Built on the engine-free fixture; the identity is the test."""

QUICK_TOPIC = True
import math
import unittest

from sim.economy.economy import Economy
from sim.tests import economy_fixture as fixture


def first_year(households_grow_food=False):
    """One quiet year. With `households_grow_food` the setup gives the farm recipe a land requirement, so
    households put their unhired hours into their own plots (households_own.py); otherwise they buy their food."""
    setup = fixture.small_setup(land_per_run={fixture.FARM: 1.0} if households_grow_food else {})
    economy = Economy(setup)
    outcome = economy.step(fixture.quiet_year(setup))
    return setup, economy, outcome


class YearAccountsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup, cls.economy, cls.outcome = first_year()
        cls.grown_setup, cls.grown_economy, cls.grown_outcome = first_year(households_grow_food=True)
        cls.accounts = cls.outcome.accounts

    def test_the_outcome_carries_accounts_for_its_year(self):
        self.assertEqual(self.accounts.year, self.outcome.year)
        self.assertTrue(self.accounts.goods)

    def test_each_goods_flows_balance(self):
        """production less intermediate use is final consumption plus investment plus inventory change, once the
        other places goods go (spoilage, the state, over the border) are counted."""
        for good, account in self.accounts.goods.items():
            scale = max(account.production, account.intermediate_use, account.final_consumption, 1.0)
            self.assertAlmostEqual(account.residual() / scale, 0.0, places=6, msg=good)

    def test_the_flows_balance_in_later_years_too(self):
        _economy, outcomes = fixture.run(years=4)
        for outcome in outcomes:
            for good, account in outcome.accounts.goods.items():
                scale = max(account.production, account.intermediate_use, account.final_consumption, 1.0)
                self.assertAlmostEqual(account.residual() / scale, 0.0, places=6, msg=(outcome.year, good))

    def test_the_stock_change_is_read_from_the_stocks_not_from_the_flows(self):
        book = self.economy.record.book
        for good, account in self.accounts.goods.items():
            held = math.fsum(book.stock(agent, good, tile)
                             for agent in book.agents() if not agent.startswith("edge:")
                             for tile in self.setup.tiles)
            self.assertAlmostEqual(held - account.stock_at_start, account.stock_change, places=6, msg=good)

    def test_production_and_intermediate_use_follow_the_recipes(self):
        goods = self.accounts.goods
        self.assertGreater(goods[fixture.GRAIN].production, 0.0)
        self.assertGreater(goods[fixture.ORE].intermediate_use, 0.0)       # smelting takes ore
        self.assertEqual(goods[fixture.GRAIN].intermediate_use, 0.0)       # no recipe takes grain

    def test_bought_food_is_consumed_and_is_market_turnover(self):
        grain = self.accounts.goods[fixture.GRAIN]
        self.assertEqual(grain.production_grown, 0.0)
        self.assertGreater(grain.final_consumption_bought, 0.0)
        self.assertAlmostEqual(grain.final_consumption_bought, grain.market_turnover, delta=0.01 * grain.market_turnover)

    def test_self_grown_food_is_consumed_but_is_not_market_turnover(self):
        grain = self.grown_outcome.accounts.goods[fixture.GRAIN]
        self.assertGreater(grain.production_grown, 0.0)
        self.assertGreater(grain.final_consumption_grown, 0.0)
        # what households grow is eaten without a market clearing it: the same year with households buying all their
        # food clears the same grain, whatever share of the food they grow (households_hours_offered)
        bought_grain = self.accounts.goods[fixture.GRAIN]
        self.assertAlmostEqual(grain.market_turnover, bought_grain.market_turnover, delta=1e-6 * bought_grain.market_turnover)
        self.assertGreater(grain.market_turnover, 0.0)
        self.assertAlmostEqual(grain.residual() / grain.production, 0.0, places=6)
        for cohort in self.grown_outcome.accounts.cohorts:
            self.assertGreater(cohort.own_plot_per_head, 0.0)

    def test_calories_eaten_per_head_are_reported_by_cohort_against_need(self):
        need = next(spec for spec in self.setup.basket.needs if spec.need_id == self.setup.hunger_need)
        self.assertTrue(self.accounts.cohorts)
        for cohort in self.accounts.cohorts:
            self.assertEqual(cohort.need_per_head, need.subsistence_per_person)
            self.assertGreaterEqual(cohort.eaten_per_head, 0.0)
            self.assertAlmostEqual(cohort.eaten_per_head, cohort.bought_per_head + cohort.own_plot_per_head,
                                   places=6)

    def test_tiles_sum_their_cohorts(self):
        for tile in self.accounts.tiles:
            members = [cohort for cohort in self.accounts.cohorts if cohort.tile == tile.tile]
            people = math.fsum(cohort.people for cohort in members)
            eaten = math.fsum(cohort.people * cohort.eaten_per_head for cohort in members)
            self.assertAlmostEqual(tile.people, people, places=6)
            self.assertAlmostEqual(tile.eaten_per_head * people, eaten, places=6)

    def test_the_real_wage_is_set_against_the_openings_basket(self):
        wage = self.accounts.real_wages[self.setup.unskilled_trade]
        self.assertGreater(wage.basket_cost_per_head_opening, 0.0)
        self.assertGreater(wage.basket_cost_per_head, 0.0)
        expected = (wage.wage_per_hour / wage.basket_cost_per_head) / (
            wage.wage_per_hour_opening / wage.basket_cost_per_head_opening)
        self.assertAlmostEqual(wage.real_wage_index, expected, places=9)


class AccountsTextTests(unittest.TestCase):
    def test_the_printout_names_each_good_and_cohort(self):  # presentation: the command's layout lists what the accounts hold
        from sim.ui.cli_economy_accounts import format_accounts
        _setup, _economy, outcome = first_year()
        text = format_accounts(outcome.accounts)
        for name in (fixture.GRAIN, fixture.ORE, "household:farms:0", fixture.LABOURER):
            self.assertIn(name, text)


if __name__ == "__main__":
    unittest.main()
