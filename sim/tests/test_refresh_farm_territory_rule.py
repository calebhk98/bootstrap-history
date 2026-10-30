"""Complaint 543: the farm's ladder, arable ceiling and cleared ground follow the held tiles as they now are.
The agriculture module's `farm_territory` builds the ladder and ceiling from the tiles' crop sites (where the soil nitrogen
stock and the rotation have moved their yield factor and cropped hectares); the engine's `refresh_farm_territory`
sets them on the farm and re-sizes the cleared area on the new ladder. The labour side is a recorder; the sites are written out."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agriculture.commands import SetFarmTerritory
from sim.engine.farm_territory_refresh import refresh_farm_territory
from sim.tests import agriculture_stand_in
from sim.world.farming_technique import DEFAULT_TECHNIQUE


def site(yield_factor, cropped_hectares):
    return SimpleNamespace(yield_factor=yield_factor, cropped_hectares=cropped_hectares)


def territory_of(sites):
    farm = agriculture_stand_in.build(views={"farming_technique": DEFAULT_TECHNIQUE,
                                             "crop_sites": lambda share, factors, tillage_capacity: sites})
    return farm.farm_territory()


class TerritoryTests(unittest.TestCase):
    def test_the_ladder_runs_best_ground_first_and_the_ceiling_is_all_the_cropland(self):
        territory = territory_of({"a": site(0.6, 40.0), "b": site(1.1, 100.0), "c": site(0.9, 60.0)})
        self.assertEqual(territory.ladder, [(1.1, 100.0), (0.9, 60.0), (0.6, 40.0)])
        self.assertEqual(territory.cropped_hectares, 200.0)

    def test_ground_that_yields_nothing_is_not_cropland(self):
        self.assertEqual(territory_of({"a": site(0.0, 500.0), "b": site(1.0, 100.0)}).cropped_hectares, 100.0)

    def test_a_fall_in_yield_factor_lowers_the_ceiling_only_by_the_ground_that_stops_yielding(self):
        self.assertEqual(territory_of({"a": site(0.0, 40.0), "b": site(0.5, 100.0)}).cropped_hectares, 100.0)


class Farm:
    def __init__(self, territory, cleared_hectares):
        self.territory = territory
        self.cleared_hectares = cleared_hectares
        self.resized_to = []
        self.sent = []
        self.labour = SimpleNamespace(set_farm_area=self.resized_to.append)

    def view(self, name):
        return lambda: self.territory if name == "farm_territory" else SimpleNamespace(hectares=self.cleared_hectares)

    def send(self, command):
        self.sent.append(command)


class RefreshTests(unittest.TestCase):
    def test_the_ladder_and_ceiling_are_the_territorys(self):
        farm = Farm(SimpleNamespace(ladder=[(1.1, 100.0)], cropped_hectares=100.0), 50.0)
        refresh_farm_territory(farm)
        self.assertEqual(farm.sent, [SetFarmTerritory([(1.1, 100.0)], 100.0)])

    def test_the_cleared_area_is_kept_and_sized_again_on_the_new_ladder(self):
        farm = Farm(SimpleNamespace(ladder=[(1.1, 100.0)], cropped_hectares=100.0), 70.0)
        refresh_farm_territory(farm)
        self.assertEqual(farm.resized_to, [70.0])


if __name__ == "__main__":
    unittest.main()
