"""A second country's tiles in the one economy: its own people, techniques, labour markets, prices and output,
read from its own record; the home answers do not mix it in. The rules are called on a written-out two-country economy
(`country_stand_in`) or on the hand-built setup, never on a played one."""

QUICK_TOPIC = True

import unittest

from sim.economy import api as economy_api
from sim.economy import country_figures
from sim.economy.year_close import foreign_agents
from sim.markets.port_country import CountryAnswers
from sim.tests import economy_fixture as fixture
from sim.tests.country_stand_in import COIN_PER_UNIT, HOME, HOME_TILES, NORTH, NORTH_TILES, two_country_economy

NO_OFF_MAP_TRADE = lambda direction: 0.0   # nothing crossed the external edge


class TheSetup(unittest.TestCase):
    def test_the_setup_knows_its_countries(self):
        setup = fixture.two_country_setup()
        self.assertEqual(setup.countries(), (setup.civ_id, fixture.NORTH))
        self.assertEqual(setup.tiles_of(fixture.NORTH), (fixture.NORTH_FARMS, fixture.NORTH_PORT))
        self.assertTrue(setup.recipe_allowed(fixture.FARM, fixture.NORTH_FARMS))
        self.assertFalse(setup.recipe_allowed(fixture.MINE, fixture.NORTH_FARMS))
        self.assertTrue(setup.recipe_allowed(fixture.MINE, fixture.HILLS))

    def test_one_country_economies_are_unchanged(self):
        single = fixture.small_setup()
        self.assertEqual(single.countries(), (single.civ_id,))
        self.assertTrue(single.recipe_allowed(fixture.MINE, fixture.TOWN))


class WhoseProducers(unittest.TestCase):
    def test_a_country_has_the_producers_working_on_its_tiles(self):
        economy = two_country_economy()
        self.assertEqual(sorted(economy_api.producers_of(economy, NORTH)), ["producer:north_farm"])
        self.assertEqual(sorted(economy_api.producers_of(economy)), ["producer:farm", "producer:mine"])   # home when shared

    def test_the_other_country_does_not_own_the_home_mines(self):
        home = economy_api.producers_of(two_country_economy(), HOME)
        self.assertTrue(all(each.tile not in NORTH_TILES for each in home.values()))
        self.assertIn("mine", {each.recipe_id for each in home.values()})


class EachCountrysOwnFigures(unittest.TestCase):
    def test_a_country_counts_its_own_people_and_the_home_answers_leave_the_other_out(self):
        economy = two_country_economy()
        self.assertEqual(country_figures.population(economy, NORTH), 50.0)
        incomes = economy_api.cohort_incomes(economy)
        self.assertEqual(incomes, [(50.0, 50.0), (100.0, 200.0)])      # home cohorts only, poorest per head first
        self.assertEqual(sum(people for people, _income in incomes), country_figures.population(economy, HOME))

    def test_wages_are_the_hours_weighted_wage_of_the_countrys_own_labour_markets(self):
        economy = two_country_economy()
        self.assertEqual(country_figures.wages_per_hour(economy, NORTH), {"labourer": 0.8})
        self.assertEqual(country_figures.wages_per_hour(economy, HOME), {"labourer": 1.375, "miner": 3.0})

    def test_the_default_wage_is_the_home_countrys_where_the_economy_holds_two(self):
        economy = two_country_economy()
        self.assertEqual(economy_api.wages_by_trade_weighted(economy)["labourer"], country_figures.wages_per_hour(economy, HOME)["labourer"])

    def test_people_by_trade_is_the_countrys_labour_markets(self):
        economy = two_country_economy()
        self.assertEqual(country_figures.people_by_trade(economy, NORTH), {"labourer": 30.0, "scribe": 2.0})
        self.assertEqual(economy_api.people_by_trade(economy), {"labourer": 110.0, "miner": 5.0})   # home when shared
        self.assertEqual(economy_api.people_by_trade(economy, NORTH).get("miner", 0.0), 0.0)

    def test_a_country_has_its_own_prices_and_output_at_them(self):
        economy = two_country_economy()
        self.assertEqual(country_figures.prices(economy, NORTH), {"grain": 4.0})
        self.assertEqual(country_figures.prices(economy, HOME), {"grain": 2.0})
        self.assertEqual(country_figures.output_value(economy, NORTH), 5.0 * 10.0 * 4.0)      # runs times a run's grain at its price
        self.assertEqual(country_figures.output_value(economy, HOME), 6.0 * 10.0 * 2.0)       # the mine's ore has no price at home

    def test_a_country_with_no_tiles_has_no_figures(self):
        economy = two_country_economy()
        self.assertEqual(country_figures.wages_per_hour(economy, "nowhere"), {})
        self.assertIsNone(country_figures.output_value(economy, "nowhere"))

    def test_the_money_a_country_holds_is_its_own_agents_share(self):
        economy = two_country_economy()
        balances = {"household:north_farms": 7.0, "household:north_port": 1.0, "household:town": 100.0, "producer:north_farm": 2.0}
        economy.record.book = type("Book", (), {"balance": lambda self, agent, money: balances.get(agent, 0.0)})()
        self.assertEqual(country_figures.money_held(economy, NORTH), 10.0)
        self.assertEqual(country_figures.money_held(economy, HOME), 100.0)
        self.assertEqual(country_figures.money_held(economy, "nowhere"), 0.0)


class AnswersOfACountry(unittest.TestCase):
    def test_a_countrys_answers_give_its_trade_book_in_coin(self):
        economy = two_country_economy()
        economy.record.carried_goods = {"grain": {"north_farms": {"farms": [2.0, 10.0, 14.0]}},
                                        "ore": {"farms": {"north_farms": [1.0, 6.0, 9.0]}}}
        answers = CountryAnswers(economy, NORTH, off_map_trade=NO_OFF_MAP_TRADE)
        book = answers.trade_book()
        self.assertAlmostEqual(book["grain"]["out_value"], 10.0 * COIN_PER_UNIT)    # left north at the price there
        self.assertAlmostEqual(book["ore"]["in_value"], 9.0 * COIN_PER_UNIT)       # landed in north at the price there
        self.assertEqual(book["ore"]["in_tonnes"], 1.0)
        self.assertAlmostEqual(answers.trade_value("in"), 9.0 * COIN_PER_UNIT)
        self.assertAlmostEqual(answers.trade_value("out"), 10.0 * COIN_PER_UNIT)
        self.assertAlmostEqual(CountryAnswers(economy, HOME, off_map_trade=NO_OFF_MAP_TRADE).trade_value("in"), 14.0 * COIN_PER_UNIT)

    def test_a_countrys_answers_count_its_people_by_trade(self):
        economy = two_country_economy()
        north = CountryAnswers(economy, NORTH, off_map_trade=NO_OFF_MAP_TRADE)
        self.assertEqual(north.people_of_trade("labourer"), 30.0)
        self.assertEqual(north.people_of_trade("miner"), 0.0)
        self.assertEqual(north.people_of_trade("no such trade"), 0.0)

    def test_land_rent_is_received_by_the_countrys_own_cohorts(self):
        economy = two_country_economy()
        north = CountryAnswers(economy, NORTH, off_map_trade=NO_OFF_MAP_TRADE)
        curve = north.land_rent_curve()
        self.assertEqual(sum(people for people, _rent in curve), 50.0)
        self.assertEqual(sum(rent for _people, rent in curve), 5.0 * 2.0 * COIN_PER_UNIT)   # the runs the north's farm worked times its rent
        self.assertEqual(north.land_rent_curve(set()), [(people, 0.0) for people, _rent in curve])

    def test_a_countrys_site_rent_is_its_own_land_markets_not_the_home_mean(self):
        economy = two_country_economy()
        economy.record.land_rent = {"hills": 50.0}     # the home country lets land; the north none
        answers = CountryAnswers(economy, NORTH, off_map_trade=NO_OFF_MAP_TRADE)
        self.assertIsNone(answers.land_rent_at(None))   # nothing let in the country: none, never the home mean
        self.assertIsNone(answers.land_rent_at("north_farms"))
        economy.record.land_rent.update({"north_farms": 2.0, "north_port": 4.0})
        self.assertAlmostEqual(answers.land_rent_at("north_farms"), 2.0 * COIN_PER_UNIT)
        economy.record.land_rent["north_port"] = 0.0
        self.assertAlmostEqual(answers.land_rent_at("north_port"), 2.0 * COIN_PER_UNIT)   # none let there: the country's mean
        self.assertAlmostEqual(answers.land_rent_at("hills"), 2.0 * COIN_PER_UNIT)        # a home tile is not the country's


class TheHomeStateAssessesOnlyItsOwn(unittest.TestCase):
    def test_the_home_state_does_not_tax_the_other_country(self):
        economy = two_country_economy()
        economy.record.merchants = {}
        self.assertEqual(foreign_agents(economy.setup, economy.record),
                         {"household:north_farms", "household:north_port", "producer:north_farm"})

    def test_a_one_country_economy_has_nothing_away(self):
        economy = two_country_economy()
        economy.setup.countries = lambda: (HOME,)
        self.assertEqual(foreign_agents(economy.setup, economy.record), set())


if __name__ == "__main__":
    unittest.main()
