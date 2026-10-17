"""Complaint 513: farm work follows the value of a farm hour against the wage elsewhere, so food beyond
need is eaten up to the biological satiation level instead of being given back as freed hands."""
import unittest

from .harness import *  # noqa: F401,F403

from sim.labour import labour_allocation
from sim.world import agriculture

from .test_population_farm_technique import _complete, _rome, _run_years

# Mechanisation frees the most hands per hectare, so the surplus is large enough to see within a few decades.
FOOD_TECHNIQUE = ("horse_collar", "fud_heavy_mouldboard_plough_coulter", "fud_mechanical_reaper", "ag2_reaper")
YEARS = 30


def _nutrition_ratio(game):
    return game._last_demographic_step.nutrition_ratio


class SurplusRaisesIntakeTests(unittest.TestCase):
    def test_a_better_technique_with_spare_land_raises_nutrition_above_need_capped_at_satiation(self):
        def run(technique):
            game = _rome()
            _complete(game, technique)
            nutrition = []
            for _ in range(YEARS):
                _run_years(game, 1)
                nutrition.append(_nutrition_ratio(game))
            return sum(nutrition[10:]) / len(nutrition[10:]), game.population.total
        improved_mean, improved_population = run(FOOD_TECHNIQUE)
        control_mean, control_population = run(())
        # Hands stay on the land while farming pays, so intake holds well above need after adoption,
        # not only during the lag while hands leave.
        self.assertGreater(improved_mean, 1.25)
        self.assertGreater(improved_mean, control_mean)
        self.assertLessEqual(improved_mean, agriculture.MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE + 1e-9)
        self.assertGreater(improved_population, control_population)

    def test_cheap_food_lets_farmers_leave(self):
        kept = _rome()
        cheap = _rome()
        _complete(kept, FOOD_TECHNIQUE)
        _complete(cheap, FOOD_TECHNIQUE)
        cheap.labour._farm_hour_value_over_wage = lambda technique: 0.5
        _run_years(kept, 12)
        _run_years(cheap, 12)
        hours = lambda game: game.state.economy.society_labour_hours
        trade = labour_allocation.FARM_TRADE
        self.assertLess(hours(cheap)[trade] / sum(hours(cheap).values()),
                        hours(kept)[trade] / sum(hours(kept).values()))
        self.assertLess(_nutrition_ratio(cheap), _nutrition_ratio(kept))


if __name__ == "__main__":
    unittest.main()
