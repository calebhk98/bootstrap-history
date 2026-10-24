"""The agent economy's yearly accounts (Complaint 554): what was made, used up in making, eaten, built and left in
stock, per good, and food eaten against need per cohort. `year_accounts.build` is called on a book, a ledger and a setup
written out here, with the flows of one year already in the book; no year is run."""

QUICK_TOPIC = True
import math
import unittest
from types import SimpleNamespace

from sim.book import Book, GoodsMove
from sim.economy import year_accounts
from sim.economy.households_cohort import Cohort
from sim.economy.types import EDGE_CONSUMPTION, EDGE_PRODUCTION, GoodSpec

GRAIN, ORE, LABOURER = "grain", "ore", "labourer"
COHORT = "household:farms:0"
TILE = "farms"
PEOPLE = 1000.0
NEED_PER_HEAD = 0.1          # grain units a person needs
OPENING_PRICES = {GRAIN: 2.0, ORE: 5.0}
PRICES_NOW = {GRAIN: 3.0, ORE: 5.0}
WAGE_NOW, WAGE_OPENING = 1.5, 1.0


def accounts_of(grown=0.0, stocks_at_start=None):
    """The accounts built from a year in which the farms made 100 grain (`grown` of it on households' own plots),
    households ate 60 and 20 ore was used up in making metal, the mine having made 50."""
    book = Book()
    farm, mine = "producer:farm", "producer:mine"
    for move in (GoodsMove(EDGE_PRODUCTION, farm, GRAIN, TILE, 100.0 - grown, "production"),
                 GoodsMove(EDGE_PRODUCTION, COHORT, GRAIN, TILE, grown, year_accounts.GROWN_PURPOSE),
                 GoodsMove(farm, COHORT, GRAIN, TILE, 60.0 - grown, "sale"),
                 GoodsMove(COHORT, EDGE_CONSUMPTION, GRAIN, TILE, 60.0, year_accounts.CONSUMPTION_PURPOSE),
                 GoodsMove(EDGE_PRODUCTION, mine, ORE, TILE, 50.0, "production"),
                 GoodsMove(mine, EDGE_CONSUMPTION, ORE, TILE, 20.0, year_accounts.INPUT_PURPOSE)):
        book.move(move)
    hunger = SimpleNamespace(need_id="food", subsistence_per_person=NEED_PER_HEAD * 10.0, goods=[(GRAIN, 10.0)])
    specs = {good: GoodSpec(good, 1.0, 0.0, 0.0, good) for good in (GRAIN, ORE)}
    setup = SimpleNamespace(specs=specs, hunger_need="food", basket_for=lambda tile: SimpleNamespace(needs=[hunger]),
                            opening_population_by_tile={TILE: PEOPLE}, opening_wages={LABOURER: WAGE_OPENING},
                            opening_prices=OPENING_PRICES, working_hours_per_year=2000.0, recipes={})
    cohort = Cohort(COHORT, TILE, 0, PEOPLE, PEOPLE / 2, 0.3, last_year_income=4000.0)
    record = SimpleNamespace(book=book, cohorts={COHORT: cohort}, producers={}, opening_basket={GRAIN: PEOPLE},
                             index_base_prices={}, memory=SimpleNamespace(year=3))
    ledger = SimpleNamespace(received={COHORT: {GRAIN: 60.0 - grown}}, grown={COHORT: {GRAIN: grown}} if grown else {},
                             clearings=[SimpleNamespace(good=GRAIN, quantity=60.0 - grown)], plant_worn={})
    accounts = year_accounts.build(setup, record, ledger, {} if stocks_at_start is None else stocks_at_start,
                                   PRICES_NOW, {LABOURER: WAGE_NOW})
    return setup, accounts


class YearAccountsTests(unittest.TestCase):
    def test_the_accounts_are_for_the_records_year_and_hold_each_good(self):
        _setup, accounts = accounts_of()
        self.assertEqual(accounts.year, 3)
        self.assertEqual(set(accounts.goods), {GRAIN, ORE})

    def test_each_goods_flows_balance(self):
        """production less intermediate use is final consumption plus investment plus inventory change, once the
        other places goods go (spoilage, the state, over the border) are counted."""
        for grown in (0.0, 30.0):
            _setup, accounts = accounts_of(grown)
            for good, account in accounts.goods.items():
                scale = max(account.production, account.intermediate_use, account.final_consumption, 1.0)
                self.assertAlmostEqual(account.residual() / scale, 0.0, places=6, msg=(grown, good))

    def test_the_stock_change_is_read_from_the_stocks_not_from_the_flows(self):
        _setup, accounts = accounts_of(stocks_at_start={GRAIN: 3.0, ORE: 0.0})
        self.assertAlmostEqual(accounts.goods[GRAIN].stock_change, 40.0 - 3.0)
        self.assertAlmostEqual(accounts.goods[GRAIN].stock_at_start, 3.0)
        self.assertAlmostEqual(accounts.goods[ORE].stock_change, 30.0)

    def test_production_and_intermediate_use_follow_the_flows(self):
        _setup, accounts = accounts_of()
        self.assertEqual(accounts.goods[GRAIN].production, 100.0)
        self.assertEqual(accounts.goods[ORE].intermediate_use, 20.0)        # smelting takes ore
        self.assertEqual(accounts.goods[GRAIN].intermediate_use, 0.0)       # no recipe takes grain

    def test_bought_food_is_consumed_and_is_market_turnover(self):
        _setup, accounts = accounts_of()
        grain = accounts.goods[GRAIN]
        self.assertEqual(grain.production_grown, 0.0)
        self.assertAlmostEqual(grain.final_consumption_bought, 60.0)
        self.assertAlmostEqual(grain.market_turnover, 60.0)

    def test_self_grown_food_is_consumed_but_is_not_market_turnover(self):
        _setup, accounts = accounts_of(grown=30.0)
        grain = accounts.goods[GRAIN]
        self.assertAlmostEqual(grain.production_grown, 30.0)
        self.assertAlmostEqual(grain.final_consumption_grown, 30.0)
        self.assertAlmostEqual(grain.final_consumption_bought, 30.0)
        self.assertAlmostEqual(grain.market_turnover, 30.0)         # only what a market cleared
        self.assertAlmostEqual(accounts.cohorts[0].own_plot_per_head, 30.0 * 10.0 / PEOPLE)

    def test_food_eaten_per_head_is_reported_by_cohort_against_need(self):
        setup, accounts = accounts_of(grown=30.0)
        cohort, = accounts.cohorts
        self.assertEqual(cohort.need_per_head, NEED_PER_HEAD * 10.0)
        self.assertAlmostEqual(cohort.eaten_per_head, cohort.bought_per_head + cohort.own_plot_per_head, places=6)
        self.assertAlmostEqual(cohort.eaten_per_head, 60.0 * 10.0 / PEOPLE)

    def test_tiles_sum_their_cohorts(self):
        _setup, accounts = accounts_of(grown=30.0)
        for tile in accounts.tiles:
            members = [cohort for cohort in accounts.cohorts if cohort.tile == tile.tile]
            people = math.fsum(cohort.people for cohort in members)
            eaten = math.fsum(cohort.people * cohort.eaten_per_head for cohort in members)
            self.assertAlmostEqual(tile.people, people, places=6)
            self.assertAlmostEqual(tile.eaten_per_head * people, eaten, places=6)
        self.assertEqual([tile.tile for tile in accounts.tiles], [TILE])

    def test_the_real_wage_is_set_against_the_openings_basket(self):
        _setup, accounts = accounts_of()
        wage = accounts.real_wages[LABOURER]
        self.assertAlmostEqual(wage.basket_cost_per_head, PRICES_NOW[GRAIN])
        self.assertAlmostEqual(wage.basket_cost_per_head_opening, OPENING_PRICES[GRAIN])
        expected = (WAGE_NOW / PRICES_NOW[GRAIN]) / (WAGE_OPENING / OPENING_PRICES[GRAIN])
        self.assertAlmostEqual(wage.real_wage_index, expected, places=9)


class AccountsTextTests(unittest.TestCase):
    def test_the_printout_names_each_good_and_cohort(self):  # presentation: the command's layout lists what the accounts hold
        from sim.ui.cli_economy_accounts import format_accounts
        _setup, accounts = accounts_of()
        text = format_accounts(accounts)
        for name in (GRAIN, ORE, COHORT, LABOURER):
            self.assertIn(name, text)


if __name__ == "__main__":
    unittest.main()
