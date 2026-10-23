"""Complaint 513, ONE_PRICE_OWNER_PLAN stage 8: in a game the farm's share of hours follows the economy's unskilled wage.
The rule (hands kept on the land against the value of a farm hour) is in test_farm_hands_margin_rule and
test_farm_satiation."""
import unittest

from .harness import *  # noqa: F401,F403

from sim.labour import labour_allocation

from .test_population_farm_technique_scenario import _complete, _rome, _run_years

# Mechanisation frees the most hands per hectare.
FOOD_TECHNIQUE = ("horse_collar", "fud_heavy_mouldboard_plough_coulter", "fud_mechanical_reaper", "ag2_reaper")
YEARS = 12


def _nutrition_ratio(game):
    return game._last_demographic_step.nutrition_ratio


def _farm_share_after_wage_multiple(multiple):
    game = _rome()
    _complete(game, FOOD_TECHNIQUE)
    world = game.labour._world
    wage = world.economy_unskilled_wage
    world.economy_unskilled_wage = lambda: (wage() or 0.0) * multiple
    _run_years(game, YEARS)
    hours = game.state.economy.society_labour_hours
    return hours[labour_allocation.FARM_TRADE] / sum(hours.values()), _nutrition_ratio(game)


class FarmHoursFollowTheWageTests(unittest.TestCase):
    def test_farm_hours_fall_as_the_wage_elsewhere_rises(self):
        results = [_farm_share_after_wage_multiple(multiple) for multiple in (1.0, 12.0)]
        shares = [share for share, _nutrition in results]
        nutrition = [value for _share, value in results]
        self.assertEqual(shares, sorted(shares, reverse=True))
        self.assertLess(shares[-1], shares[0])
        self.assertEqual(nutrition, sorted(nutrition, reverse=True))


if __name__ == "__main__":
    unittest.main()
