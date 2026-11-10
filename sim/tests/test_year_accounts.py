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
                            opening_prices=OPENING_PRICES, working_hours_per_year=2000.0, recipes={}, currency_id="coin")
    cohort = Cohort(COHORT, TILE, 0, PEOPLE, PEOPLE / 2, 0.3, last_year_income=4000.0)
    record = SimpleNamespace(book=book, cohorts={COHORT: cohort}, producers={}, goods=SimpleNamespace(opening_basket={GRAIN: PEOPLE}, index_base_prices={}),
                             memory=SimpleNamespace(year=3, opening_wage_levels={}))
    ledger = SimpleNamespace(received={COHORT: {GRAIN: 60.0 - grown}}, grown={COHORT: {GRAIN: grown}} if grown else {},
                             clearings=[SimpleNamespace(good=GRAIN, quantity=60.0 - grown)], delivered_by_market={(GRAIN, "area"): 60.0 - grown},
                             plant_worn={})
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


def reference_cohorts(setup, record, ledger, prices):
    """The cohort rows as they were read from the ledger one cohort and one good at a time."""
    cost = year_accounts.basket_cost_per_head(record.goods, prices, math.fsum(setup.opening_population_by_tile.values()))
    rows = []
    for cohort_id, cohort in sorted(record.cohorts.items()):
        need = next((spec for spec in setup.basket_for(cohort.tile).needs if spec.need_id == setup.hunger_need), None)
        if need is None or cohort.people <= 0.0:
            continue

        def units(goods):
            return math.fsum(goods.get(good, 0.0) * effect for good, effect in need.goods if not setup.specs[good].service_life_years > 0.0)
        bought, own = units(ledger.received.get(cohort_id, {})), units(ledger.grown.get(cohort_id, {}))
        rows.append(year_accounts.CohortAccount(
            cohort=cohort_id, tile=cohort.tile, income_class=cohort.income_class, people=cohort.people,
            need_per_head=need.subsistence_per_person, eaten_per_head=(bought + own) / cohort.people,
            bought_per_head=bought / cohort.people, own_plot_per_head=own / cohort.people,
            real_income_per_head=cohort.last_year_income / cohort.people / cost if cost is not None and cost > 0.0 else math.nan))
    return rows


def awkward_year(ledger):
    """A setup with two tiles (one has no hunger need), a durable good the need counts but the cohort rows leave out, and cohorts with
    no people, none eaten, and sums that only an exact addition keeps."""
    from sim.economy.households_cohort import Cohort
    goods = ("grain", "fish", "plough", "wine")
    specs = {good: GoodSpec(good, 1.0, 0.0, 20.0 if good == "plough" else 0.0, good) for good in goods}
    hunger = SimpleNamespace(need_id="food", subsistence_per_person=2.5, goods=[("grain", 0.1), ("fish", 0.3), ("plough", 9.0), ("wine", -0.2)])
    other = SimpleNamespace(need_id="cloth", subsistence_per_person=1.0, goods=[("grain", 1.0)])
    baskets = {"farms": SimpleNamespace(needs=[other, hunger]), "hills": SimpleNamespace(needs=[hunger]), "bare": SimpleNamespace(needs=[other])}
    setup = SimpleNamespace(specs=specs, hunger_need="food", basket_for=lambda tile: baskets[tile], opening_population_by_tile={"farms": 1e16, "hills": 1.0},
                            opening_wages={}, opening_prices={}, working_hours_per_year=1.0, recipes={}, currency_id="coin")
    cohorts = {}
    for number, (tile, people) in enumerate([("farms", 100.0), ("hills", 0.0), ("hills", 33.0), ("bare", 5.0), ("farms", 7.0), ("farms", 3.0)]):
        cohorts["household:%s:%d" % (tile, number)] = Cohort("household:%s:%d" % (tile, number), tile, number % 3, people, people / 2, 0.3, last_year_income=4000.0 + number)
    record = SimpleNamespace(cohorts=cohorts, goods=SimpleNamespace(opening_basket={"grain": 1.0, "fish": 2.0}, index_base_prices={}))
    for number, name in enumerate(sorted(cohorts)):
        ledger.received[name] = {"grain": 1e16 * (number % 2) + 0.1 * number, "fish": 1.0 / 3.0, "plough": 4.0, "wine": 1e-9}
        if number % 2:
            ledger.grown[name] = {"grain": 1.0 / 7.0, "plough": 2.0}
    return setup, record, {"grain": 1.0, "fish": 2.0}


class PlainLedgerReadTests(unittest.TestCase):
    def test_cohort_rows_from_the_ledger_block_are_those_read_one_good_at_a_time(self):
        from sim.economy.year_ledger import YearLedger
        for ledger in (YearLedger(), SimpleNamespace(received={}, grown={})):
            setup, record, prices = awkward_year(ledger)
            rows = year_accounts._cohorts(setup, record, ledger, prices)
            expected = reference_cohorts(setup, record, ledger, prices)
            self.assertEqual(len(rows), len(expected))
            self.assertEqual(len(rows), 4)       # the empty cohort and the tile without a hunger need leave no row
            for row, wanted in zip(rows, expected):
                for name in ("cohort", "tile", "people", "need_per_head", "eaten_per_head", "bought_per_head", "own_plot_per_head"):
                    self.assertEqual(getattr(row, name), getattr(wanted, name), name)
                self.assertEqual(row.real_income_per_head, wanted.real_income_per_head)

    def test_a_cohort_without_rows_eats_nothing(self):
        from sim.economy.year_ledger import YearLedger
        ledger = YearLedger()
        setup, record, prices = awkward_year(ledger)
        ledger.received.clear()
        ledger.grown.clear()
        rows = year_accounts._cohorts(setup, record, ledger, prices)
        self.assertEqual([row.eaten_per_head for row in rows], [0.0] * 4)


class AccountsTextTests(unittest.TestCase):
    def test_the_printout_names_each_good_and_cohort(self):  # presentation: the command's layout lists what the accounts hold
        from sim.ui.cli_economy_accounts import format_accounts
        _setup, accounts = accounts_of()
        text = format_accounts(accounts)
        for name in (GRAIN, ORE, COHORT, LABOURER):
            self.assertIn(name, text)


if __name__ == "__main__":
    unittest.main()
