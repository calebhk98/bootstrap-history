"""The farm is sized on the soil and climate of the civilisation's own tiles: the cleared area's quality is the mean of the
best-first ground it covers (`_set_farm_area`), clearing brings in the next ground and so lowers it (`_apply_land_clearing`),
and the arable ground not yet cleared is what a farm can still clear (`_clearable_hectares`). The ladder arithmetic is
test_farm_land_quality; the stand-in world holds only a ladder, a ceiling and the farm's land."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.demography.api import SetClearedFarmland
from sim.labour.labour_allocation import LabourAllocationMixin
from sim.world import agriculture

LADDER = [(1.2, 100.0), (0.8, 100.0), (0.2, 100.0)]
CLEARING_HOURS_PER_HECTARE = agriculture.CLEARING_LABOUR_HOURS_PER_HECTARE


class Farm(LabourAllocationMixin):
    def __init__(self, hectares, ladder=LADDER, ceiling=300.0):
        self.sent = []
        self._world = SimpleNamespace(farm_ladder=ladder, farm_arable_ceiling=ceiling,
                                      farm_land=agriculture.Land(hectares, 1.0), send=self.sent.append)
        self._world.set_farm_land = lambda hectares, quality: setattr(self._world, "farm_land", agriculture.Land(hectares, quality))

    def sized(self):
        self._set_farm_area(self._world.farm_land.hectares)
        return self


class FarmAreaTests(unittest.TestCase):
    def test_the_quality_of_the_cleared_area_is_the_mean_of_the_best_ground_it_covers(self):
        farm = Farm(150.0).sized()
        self.assertAlmostEqual(farm._world.farm_land.quality, (1.2 * 100.0 + 0.8 * 50.0) / 150.0)

    def test_the_cleared_area_is_recorded(self):
        farm = Farm(150.0).sized()
        self.assertEqual(farm.sent, [SetClearedFarmland(150.0)])
        self.assertEqual(farm._world.farm_land.hectares, 150.0)

    def test_a_farm_that_covers_only_the_best_parcel_has_its_fertility(self):
        self.assertAlmostEqual(Farm(60.0).sized()._world.farm_land.quality, 1.2)

    def test_with_no_ladder_the_farm_has_the_reference_quality(self):
        self.assertEqual(Farm(80.0, ladder=[]).sized()._world.farm_land.quality, 1.0)

    def test_clearing_hours_open_ground_and_the_next_ground_lowers_the_mean(self):
        farm = Farm(100.0)
        before = 1.2
        farm._world.farm_land = agriculture.Land(100.0, before)
        farm._clearing_hours_this_year = 50.0 * CLEARING_HOURS_PER_HECTARE
        farm._apply_land_clearing()
        self.assertAlmostEqual(farm._world.farm_land.hectares, 150.0)
        self.assertLess(farm._world.farm_land.quality, before)

    def test_clearing_never_passes_the_arable_ground_held(self):
        farm = Farm(250.0)
        farm._clearing_hours_this_year = 1e12
        farm._apply_land_clearing()
        self.assertAlmostEqual(farm._world.farm_land.hectares, 300.0)

    def test_the_ground_not_yet_cleared_is_what_can_still_be_cleared(self):
        self.assertAlmostEqual(Farm(120.0)._clearable_hectares(), 180.0)
        self.assertEqual(Farm(120.0, ceiling=None)._clearable_hectares(), 0.0)
        self.assertEqual(Farm(300.0)._clearable_hectares(), 0.0)


if __name__ == "__main__":
    unittest.main()
