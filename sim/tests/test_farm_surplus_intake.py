"""Complaint 513: farm work follows the value of a farm hour against the wage elsewhere, so food beyond
need is eaten up to the biological satiation level instead of being given back as freed hands."""
import unittest

from .harness import *  # noqa: F401,F403

from sim.labour import farm_intake
from sim.world import agriculture

from .test_population_farm_technique_scenario import _complete, _rome, _run_years

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
        # Open: Complaint 513 (food is not yet cleared against farm effort). With the sourced hours per hectare
        # (Complaint 646) the opening's cleared land is fully worked, so the technique frees too little to lift intake;
        # the surplus premise of this check is unsettled, not met. Left red.
        self.assertGreater(improved_mean, 1.25, "Complaint 513: no intake surplus after a food technique on fully worked land")
        self.assertGreater(improved_mean, control_mean)
        self.assertLessEqual(improved_mean, agriculture.MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE + 1e-9)
        self.assertGreater(improved_population, control_population)

    def test_cheap_food_lets_farmers_leave(self):
        # The rule on built inputs: a farm hour worth less than the wage lets hands go; one worth more keeps today's.
        current, satiation, land = 1000.0, 3000.0, 2000.0
        elasticity = agriculture.LABOUR_OUTPUT_ELASTICITY
        cheap = farm_intake.kept_farm_workers(current, satiation, land, 0.5, elasticity)
        dear = farm_intake.kept_farm_workers(current, satiation, land, 1.5, elasticity)
        self.assertLess(cheap, dear)
        self.assertEqual(dear, current)
        self.assertEqual(farm_intake.kept_farm_workers(current, satiation, land, None, elasticity), 0.0)


if __name__ == "__main__":
    unittest.main()
