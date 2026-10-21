"""SCENARIO (Complaints 537, 543): the poorest-soiled civilisation opens with room to spare in its labour split. A farm share of
hours at its ceiling means its people cannot feed themselves with every hour, which is a broken opening, not an outcome. The cause
checked: the heavy-ground stand-in closing the best tile to the reference ard (rule test: test_tillage_and_silt)."""
import unittest

from .harness import *  # noqa: F401,F403

from sim.geography import food_land


class NorseOpening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = sim(civ="norse_900ad")

    def test_the_farm_share_of_hours_is_below_its_ceiling(self):
        self.assertLess(self.game.labour.farm_share_of_hours(), 0.9)

    def test_the_reference_ard_ploughs_the_whole_arable_share_of_the_best_tile(self):
        ard = self.game.farm_sites()["sweden_01"]
        self.assertAlmostEqual(ard.arable_hectares, food_land.arable_hectares(self.game.world_map, "sweden_01"), delta=1e-6 * ard.arable_hectares)
        self.assertGreater(ard.cropped_hectares, 0.0)


if __name__ == "__main__":
    unittest.main()
