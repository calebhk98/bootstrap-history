"""Complaint 549: demography is fed what the agent economy's households ate, not the engine's own harvest.

The economy half (the national figure) is test_national_food_eaten_rule. This half calls the engine methods that book the
figure and hand it to the regions, on a stand-in `self`; a region fed its own booked figure is test_regional_hunger_is_the_regions_own."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.engine import regional_people
from sim.engine.food_eaten import FoodEatenMixin
from sim.engine.regional_people import RegionalPeopleMixin
from sim.tests.test_national_food_eaten_rule import _accounts


def population_state(**fields):
    return SimpleNamespace(**{"food_eaten_over_need": None, "regional_eaten_over_need": {}, **fields})


class BookingTheFigure(unittest.TestCase):
    def test_the_economys_year_books_the_national_and_each_tiles_figure(self):
        game = SimpleNamespace(state=SimpleNamespace(population=population_state()))
        FoodEatenMixin.record_food_eaten(game, SimpleNamespace(accounts=_accounts({"town": 90.0, "farms": 100.0})))
        self.assertAlmostEqual(game.state.population.food_eaten_over_need, 0.95, places=9)
        self.assertEqual(game.state.population.regional_eaten_over_need, {"town": 0.9, "farms": 1.0})

    def test_an_outcome_without_accounts_books_nothing(self):
        game = SimpleNamespace(state=SimpleNamespace(population=population_state(food_eaten_over_need=0.8,
                                                                                  regional_eaten_over_need={"town": 0.8})))
        FoodEatenMixin.record_food_eaten(game, SimpleNamespace())
        self.assertIsNone(game.state.population.food_eaten_over_need)
        self.assertEqual(game.state.population.regional_eaten_over_need, {})


class ReadingTheFigure(unittest.TestCase):
    def test_before_an_economy_year_has_closed_the_farm_model_feeds_demography(self):
        game = SimpleNamespace(state=SimpleNamespace(population=population_state()))
        self.assertIsNone(FoodEatenMixin.household_food_kcal_per_day(game, 1000.0))

    def test_after_one_the_calories_follow_the_booked_figure(self):
        hungry = SimpleNamespace(state=SimpleNamespace(population=population_state(food_eaten_over_need=0.6)))
        fed = SimpleNamespace(state=SimpleNamespace(population=population_state(food_eaten_over_need=1.0)))
        self.assertAlmostEqual(FoodEatenMixin.household_food_kcal_per_day(hungry, 1000.0),
                               0.6 * FoodEatenMixin.household_food_kcal_per_day(fed, 1000.0), places=6)

    def test_each_region_is_fed_from_its_booked_figure_with_the_harvest_as_the_fallback(self):
        game = SimpleNamespace(state=SimpleNamespace(population=population_state(regional_eaten_over_need={"town": 0.6})),
                               relief_kcal_per_day=lambda: 7.0, home_tiles_held=lambda: ["town", "farms"])
        recorded = []
        with mock.patch.object(regional_people.regional_population, "kcal_per_day_by_region",
                               lambda *arguments: recorded.append(arguments) or {"town": 1.0}), \
                mock.patch.object(regional_people.settlement, "population_shares", lambda tiles: {tile: 0.5 for tile in tiles}):
            fed = RegionalPeopleMixin.regional_kcal_per_day(game, {"town": "region"}, 4000.0)
        self.assertEqual(fed, {"town": 1.0})
        self.assertEqual(recorded, [({"town": "region"}, {"town": 0.6}, 4000.0, 7.0, {"town": 0.5, "farms": 0.5})])


if __name__ == "__main__":
    unittest.main()
