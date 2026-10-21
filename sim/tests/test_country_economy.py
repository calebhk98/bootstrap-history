"""A second country's tiles in the one economy: its own people, techniques, labour markets, prices and output,
read from its own record; the home answers do not mix it in (the hand-built fixture, no game)."""

QUICK_TOPIC = True

import unittest

from sim.economy import api as economy_api
from sim.economy import country_figures
from sim.economy.economy import Economy
from sim.economy.types import is_edge
from sim.tests import economy_fixture as fixture


NO_OFF_MAP_TRADE = lambda direction: 0.0   # nothing crossed the external edge


class CountryEconomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = fixture.two_country_setup()
        cls.economy, cls.outcomes = fixture.run(cls.setup, years=4)

    def test_the_setup_knows_its_countries(self):
        setup = self.setup
        self.assertEqual(setup.countries(), (setup.civ_id, fixture.NORTH))
        self.assertEqual(setup.tiles_of(fixture.NORTH), (fixture.NORTH_FARMS, fixture.NORTH_PORT))
        self.assertTrue(setup.recipe_allowed(fixture.FARM, fixture.NORTH_FARMS))
        self.assertFalse(setup.recipe_allowed(fixture.MINE, fixture.NORTH_FARMS))
        self.assertTrue(setup.recipe_allowed(fixture.MINE, fixture.HILLS))

    def test_one_country_economies_are_unchanged(self):
        single = fixture.small_setup()
        self.assertEqual(single.countries(), (single.civ_id,))
        self.assertTrue(single.recipe_allowed(fixture.MINE, fixture.TOWN))

    def test_a_country_runs_only_the_recipes_its_techniques_allow(self):
        producers = economy_api.producers_of(self.economy, fixture.NORTH)
        self.assertTrue(producers)
        self.assertEqual({producer.recipe_id for producer in producers.values()}, {fixture.FARM})
        self.assertTrue(all(producer.tile in (fixture.NORTH_FARMS, fixture.NORTH_PORT) for producer in producers.values()))

    def test_the_other_country_does_not_own_the_home_mines(self):
        home = economy_api.producers_of(self.economy)
        self.assertTrue(all(producer.tile not in (fixture.NORTH_FARMS, fixture.NORTH_PORT) for producer in home.values()))
        self.assertIn(fixture.MINE, {producer.recipe_id for producer in home.values()})

    def test_each_country_shows_its_own_people_and_pay(self):
        north_people = country_figures.population(self.economy, fixture.NORTH)
        self.assertAlmostEqual(north_people, 4000.0, delta=1e-6 + 0.5 * 4000.0)
        self.assertGreater(north_people, 0.0)
        wages = country_figures.wages_per_hour(self.economy, fixture.NORTH)
        self.assertIn(fixture.LABOURER, wages)
        self.assertGreater(wages[fixture.LABOURER], 0.0)
        default = economy_api.wages_by_trade_weighted(self.economy)
        home = country_figures.wages_per_hour(self.economy, self.setup.civ_id)
        self.assertEqual(default, home)

    def test_the_home_answers_leave_the_other_country_out(self):
        incomes = economy_api.cohort_incomes(self.economy)
        home_people = country_figures.population(self.economy, self.setup.civ_id)
        self.assertAlmostEqual(sum(people for people, _income in incomes), home_people, places=6)
        trades = economy_api.people_by_trade(self.economy)
        north_trades = economy_api.people_by_trade(self.economy, fixture.NORTH)
        self.assertLess(north_trades.get(fixture.MINER, 0.0), 0.05 * trades[fixture.MINER])   # no mines, so only seed hands
        self.assertGreater(trades.get(fixture.MINER, 0.0), 0.0)

    def test_a_country_has_its_own_prices_and_output(self):
        output = country_figures.output_value(self.economy, fixture.NORTH)
        self.assertIsNotNone(output)
        self.assertGreater(output, 0.0)
        floors = country_figures.need_floor_costs_per_person_year(self.economy, fixture.NORTH)
        self.assertGreater(floors.get(fixture.FOOD, 0.0), 0.0)
        self.assertGreater(country_figures.prices(self.economy, fixture.NORTH).get(fixture.GRAIN, 0.0), 0.0)

    def test_the_money_a_country_holds_is_its_own_agents_share(self):
        record, money = self.economy.record, self.setup.currency_id
        north, home = (country_figures.money_held(self.economy, country) for country in (fixture.NORTH, self.setup.civ_id))
        self.assertGreater(north, 0.0)
        self.assertGreater(home, 0.0)
        everyone = sum(record.book.balance(agent, money) for agent in record.book.agents() if not is_edge(agent))
        self.assertLessEqual(north + home, everyone + 1e-6)
        self.assertEqual(country_figures.money_held(self.economy, "nowhere"), 0.0)

    def test_a_countrys_answers_give_its_trade_book_in_coin(self):
        from sim.engine.economy_port_country import CountryAnswers
        record = self.economy.record
        kept = record.carried_goods
        record.carried_goods = {fixture.GRAIN: {fixture.NORTH_FARMS: {fixture.FARMS: [2.0, 10.0, 14.0]}},
                                fixture.ORE: {fixture.FARMS: {fixture.NORTH_FARMS: [1.0, 6.0, 9.0]}}}
        try:
            answers = CountryAnswers(self.economy, fixture.NORTH, off_map_trade=NO_OFF_MAP_TRADE)
            coin = self.setup.coin_per_unit
            book = answers.trade_book()
            self.assertAlmostEqual(book[fixture.GRAIN]["out_value"], 10.0 * coin)    # left north at the price there
            self.assertAlmostEqual(book[fixture.ORE]["in_value"], 9.0 * coin)       # landed in north at the price there
            self.assertEqual(book[fixture.ORE]["in_tonnes"], 1.0)
            self.assertAlmostEqual(answers.trade_value("in"), 9.0 * coin)
            self.assertAlmostEqual(answers.trade_value("out"), 10.0 * coin)
            self.assertAlmostEqual(CountryAnswers(self.economy, self.setup.civ_id, off_map_trade=NO_OFF_MAP_TRADE).trade_value("in"), 14.0 * coin)
        finally:
            record.carried_goods = kept

    def test_a_countrys_answers_count_its_people_by_trade(self):
        from sim.engine.economy_port_country import CountryAnswers
        answers = CountryAnswers(self.economy, fixture.NORTH, off_map_trade=NO_OFF_MAP_TRADE)
        self.assertEqual(answers.people_of_trade(fixture.LABOURER), country_figures.people_by_trade(self.economy, fixture.NORTH)[fixture.LABOURER])
        self.assertLess(answers.people_of_trade(fixture.MINER), 0.05 * CountryAnswers(self.economy, self.setup.civ_id, off_map_trade=NO_OFF_MAP_TRADE).people_of_trade(fixture.MINER))
        self.assertEqual(answers.people_of_trade("no such trade"), 0.0)

    def test_land_rent_is_received_by_the_countrys_own_cohorts(self):
        from sim.engine.economy_port_country import CountryAnswers
        north = [c for c in self.economy.record.cohorts.values() if c.tile in self.setup.tiles_of(fixture.NORTH) and c.people > 0.0]
        curve = CountryAnswers(self.economy, fixture.NORTH, off_map_trade=NO_OFF_MAP_TRADE).land_rent_curve()
        self.assertEqual(sum(people for people, _rent in curve), sum(c.people for c in north))
        self.assertEqual(CountryAnswers(self.economy, fixture.NORTH, off_map_trade=NO_OFF_MAP_TRADE).land_rent_curve(set()), [(p, 0.0) for p, _ in curve])

    def test_a_countrys_site_rent_is_its_own_land_markets_not_the_home_mean(self):
        from sim.engine.economy_port_country import CountryAnswers
        record, coin = self.economy.record, self.setup.coin_per_unit
        kept = dict(record.land_rent)
        north_tiles = set(self.setup.tiles_of(fixture.NORTH))
        answers = CountryAnswers(self.economy, fixture.NORTH, off_map_trade=NO_OFF_MAP_TRADE)
        try:
            for tile in north_tiles:
                record.land_rent.pop(tile, None)
            record.land_rent[fixture.HILLS] = 50.0     # the home country lets land; the north none
            self.assertIsNone(answers.land_rent_at(None))   # nothing let in the country: none, never the home mean
            self.assertIsNone(answers.land_rent_at(fixture.NORTH_FARMS))
            record.land_rent[fixture.NORTH_FARMS] = 2.0
            record.land_rent[fixture.NORTH_PORT] = 4.0
            self.assertAlmostEqual(answers.land_rent_at(fixture.NORTH_FARMS), 2.0 * coin)
            record.land_rent[fixture.NORTH_PORT] = 0.0
            self.assertAlmostEqual(answers.land_rent_at(fixture.NORTH_PORT), 2.0 * coin)   # none let there: the country's mean
            self.assertAlmostEqual(answers.land_rent_at(fixture.HILLS), 2.0 * coin)        # a home tile is not the country's
        finally:
            record.land_rent.clear()
            record.land_rent.update(kept)

    def test_a_country_with_no_tiles_has_no_figures(self):
        self.assertEqual(country_figures.wages_per_hour(self.economy, "nowhere"), {})
        self.assertIsNone(country_figures.output_value(self.economy, "nowhere"))

    def test_money_and_goods_are_conserved_across_countries(self):
        self.assertEqual(self.economy.record.book.check_conservation(1e-6).breaches, ())

    def test_the_home_state_does_not_tax_the_other_country(self):
        from sim.economy.year_close import foreign_agents
        away = foreign_agents(self.setup, self.economy.record)
        self.assertTrue(away)
        self.assertTrue(all(agent.startswith(("household:north", "producer:")) or agent.startswith("merchant:") for agent in away))
        self.assertEqual(foreign_agents(fixture.small_setup(), Economy(fixture.small_setup()).record), set())


if __name__ == "__main__":
    unittest.main()
