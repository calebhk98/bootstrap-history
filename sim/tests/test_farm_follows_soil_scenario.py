"""SCENARIO (Complaint 543): in a real game the national farm model reads the soil nitrogen stock each year, so continuous
cropping lowers the national harvest, and the farm ceiling follows a change of rotation. The rules (legumes raise the stock,
the rotation has no yield multiplier) are in test_farm_follows_soil.py."""
import unittest
from unittest import mock

from .harness import *  # noqa: F401,F403
from sim.world import agriculture, land

YEARS = 30


def _harvest_weight(game):
    """Cropped hectares times yield factor over the farm's ladder: what the held ground gives against the reference field."""
    return sum(factor * hectares for factor, hectares in game._farm_ladder)


def _years_under(rotation):
    """(harvest weight before, after, stock before, stock after, farm quality before, after) over YEARS of cropping."""
    game = unopened_sim()
    technique = game.labour.farming_technique()._replace(rotation=rotation)
    with mock.patch.object(game.labour, "farming_technique", return_value=technique):
        game.refresh_farm_territory()
        before = (_harvest_weight(game), game.farm_land.quality)
        for _year in range(YEARS):
            game.step_soil_nitrogen()
            game.refresh_farm_territory()
        stock = game.state.economy.soil_nitrogen
        return (before[0], _harvest_weight(game), 1.0, sum(stock.values()) / len(stock), before[1], game.farm_land.quality)


class FarmFollowsSoilInAGame(unittest.TestCase):
    def test_continuous_cropping_lowers_the_national_harvest(self):
        continuous = agriculture.DEFAULT_ROTATION._replace(name="continuous", fallow_share_of_holding=0.0)
        before, after, _stock_before, stock_after, quality_before, quality_after = _years_under(continuous)
        self.assertLess(stock_after, 1.0)
        self.assertLess(quality_after, quality_before)
        self.assertLess(after, before)

    def test_the_ceiling_follows_a_change_of_rotation(self):
        game = unopened_sim()
        two_field = game._farm_arable_ceiling
        technique = game.labour.farming_technique()._replace(rotation=agriculture.THREE_FIELD)
        with mock.patch.object(game.labour, "farming_technique", return_value=technique):
            game.refresh_farm_territory()
            sites_ceiling = land.territory_cropland(game.farm_sites()).cropped_hectares
        self.assertGreater(game._farm_arable_ceiling, two_field)
        self.assertEqual(sites_ceiling, game._farm_arable_ceiling)


if __name__ == "__main__":
    unittest.main()
