"""A second country's tiles in the one economy: its own people, techniques, labour markets, prices and output,
read from its own record; the home answers do not mix it in (the hand-built fixture, no game)."""

QUICK_TOPIC = True

import unittest

from sim.economy import api as economy_api
from sim.economy import country_figures
from sim.economy.economy import Economy
from sim.tests import economy_fixture as fixture


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
