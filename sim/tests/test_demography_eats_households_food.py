"""SCENARIO (Complaint 549): demography is fed what the agent economy's households ate, not the engine's own harvest.

Population is one national record, so the hunger is national; a tile's own hunger waits on a population tracked
by tile (Complaint 603). The economy half (the national figure) is test_national_food_eaten_rule; this half runs on a game whose
economy has not opened, since the demographic step needs no economy year."""
import copy
import unittest

from sim.tests.harness import unopened_sim
from sim.tests.test_national_food_eaten_rule import _accounts


class DemographyReadsTheHouseholdsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = unopened_sim(civ="rome_100ad")
        cls.start_population = copy.deepcopy(cls.game.population)

    def _step_when_households_ate(self, eaten_over_need):
        game = self.game
        game.population = copy.deepcopy(self.start_population)
        game.state.population.food_eaten_over_need = eaten_over_need
        # each region is fed what its own households ate (regional_people.py, Complaint 603); the nation's figure is the record beside
        game.state.population.regional_eaten_over_need = {tile: eaten_over_need for tile in game.home_tiles_held()}
        game._demographic_recovery(game.state.scenario.year)
        return game._last_demographic_step

    def test_a_national_food_shortfall_in_the_economys_book_raises_mortality(self):
        fed = self._step_when_households_ate(1.0)
        hungry = self._step_when_households_ate(0.6)
        self.assertLess(hungry.nutrition_ratio, fed.nutrition_ratio)
        self.assertGreater(hungry.deaths, fed.deaths)

    def test_the_nutrition_is_the_households_not_the_farm_models(self):
        step = self._step_when_households_ate(0.6)
        self.assertAlmostEqual(step.nutrition_ratio, 0.6, delta=0.05)

    def test_the_figure_is_recorded_when_the_economys_year_closes(self):
        self.game.state.population.food_eaten_over_need = None
        outcome = type("Outcome", (), {"accounts": _accounts({"town": 90.0})})()
        self.game.record_food_eaten(outcome)
        self.assertIsNotNone(self.game.state.population.food_eaten_over_need)

    def test_before_an_economy_year_has_closed_the_farm_model_feeds_demography(self):
        self.game.state.population.food_eaten_over_need = None
        self.assertIsNone(self.game.household_food_kcal_per_day(1000.0))


if __name__ == "__main__":
    unittest.main()
