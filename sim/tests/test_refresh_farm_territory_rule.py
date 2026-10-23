"""Complaint 543: the farm's ladder, arable ceiling and cleared ground follow the held tiles as they now are.
`refresh_farm_territory` rebuilds the ladder and ceiling from the tiles' crop sites (where the soil nitrogen stock and the
rotation have moved their yield factor and cropped hectares) and re-sizes the cleared area on the new ladder. The labour
side is a recorder; the sites are written out."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine.soil_nitrogen_year import SoilNitrogenMixin


def site(yield_factor, cropped_hectares):
    return SimpleNamespace(yield_factor=yield_factor, cropped_hectares=cropped_hectares)


class Farm(SoilNitrogenMixin):
    def __init__(self, sites, cleared_hectares):
        self.sites = sites
        self.farm_land = SimpleNamespace(hectares=cleared_hectares)
        self.resized_to = []
        self.labour = SimpleNamespace(set_farm_area=self.resized_to.append)

    def farm_sites(self):
        return self.sites


class RefreshTests(unittest.TestCase):
    def test_the_ladder_runs_best_ground_first_and_the_ceiling_is_all_the_cropland(self):
        farm = Farm({"a": site(0.6, 40.0), "b": site(1.1, 100.0), "c": site(0.9, 60.0)}, 50.0)
        farm.refresh_farm_territory()
        self.assertEqual(farm._farm_ladder, [(1.1, 100.0), (0.9, 60.0), (0.6, 40.0)])
        self.assertEqual(farm._farm_arable_ceiling, 200.0)

    def test_ground_that_yields_nothing_is_not_cropland(self):
        farm = Farm({"a": site(0.0, 500.0), "b": site(1.0, 100.0)}, 50.0)
        farm.refresh_farm_territory()
        self.assertEqual(farm._farm_arable_ceiling, 100.0)

    def test_the_cleared_area_is_kept_and_sized_again_on_the_new_ladder(self):
        farm = Farm({"b": site(1.1, 100.0)}, 70.0)
        farm.refresh_farm_territory()
        self.assertEqual(farm.resized_to, [70.0])

    def test_a_fall_in_yield_factor_lowers_the_ceiling_only_by_the_ground_that_stops_yielding(self):
        farm = Farm({"a": site(0.0, 40.0), "b": site(0.5, 100.0)}, 50.0)
        farm.refresh_farm_territory()
        self.assertEqual(farm._farm_arable_ceiling, 100.0)


if __name__ == "__main__":
    unittest.main()
