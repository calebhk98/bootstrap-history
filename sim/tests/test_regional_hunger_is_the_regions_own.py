"""Complaint 549: a region is fed what its own households ate, or what its own land gave, never the nation's average.

A region short of food has its own nutrition and mortality raised; the other regions and the nation's booked figure do
not feed it."""
import unittest

from sim.world import regional_population
from sim.world.demography import Population


def _regions():
    return {"fertile": Population.stationary(100000.0), "barren": Population.stationary(100000.0)}


def _per_person(kcal_by_region, regions):
    return {tile: kcal_by_region[tile] / regional_population.adult_equivalents(regions[tile]) for tile in regions}


class HungerBelongsToTheRegionTests(unittest.TestCase):
    def test_without_booked_food_a_region_gets_its_lands_share_of_the_harvest(self):
        regions = _regions()
        harvest = 2.0 * sum(regional_population.kcal_per_day_fed(region, 1.0) for region in regions.values()) / 2.0
        fed = regional_population.kcal_per_day_by_region(regions, {}, harvest, 0.0, {"fertile": 3.0, "barren": 1.0})
        per_person = _per_person(fed, regions)
        self.assertGreater(per_person["fertile"], per_person["barren"])
        self.assertAlmostEqual(sum(fed.values()), harvest)

    def test_a_barren_region_starves_while_the_fertile_one_is_fed(self):
        regions = _regions()
        need = regional_population.kcal_per_day_fed(regions["fertile"], 1.0)
        fed = regional_population.kcal_per_day_by_region(regions, {}, 2.0 * need, 0.0, {"fertile": 9.0, "barren": 1.0})
        flows = regional_population.step_regions(regions, fed, 1.0, {}, None, {}, {})
        self.assertGreater(flows["barren"].deaths / flows["barren"].start_total,
                           flows["fertile"].deaths / flows["fertile"].start_total)

    def test_a_booked_region_keeps_its_own_figure_whatever_the_harvest(self):
        regions = _regions()
        eaten = {"fertile": 1.1, "barren": 0.6}
        small = regional_population.kcal_per_day_by_region(regions, eaten, 1.0, 0.0, {"fertile": 1.0, "barren": 1.0})
        large = regional_population.kcal_per_day_by_region(regions, eaten, 1.0e12, 0.0, {"fertile": 1.0, "barren": 1.0})
        self.assertEqual(small, large)
        self.assertAlmostEqual(small["barren"], regional_population.kcal_per_day_fed(regions["barren"], 0.6))

    def test_a_region_without_a_booked_figure_is_not_fed_the_average_of_the_booked_ones(self):
        regions = _regions()
        fed = regional_population.kcal_per_day_by_region(
            regions, {"fertile": 1.5}, 0.0, 0.0, {"fertile": 1.0, "barren": 1.0})
        self.assertEqual(fed["barren"], 0.0)

    def test_relief_is_shared_by_need(self):
        regions = {"big": Population.stationary(300000.0), "small": Population.stationary(100000.0)}
        fed = regional_population.kcal_per_day_by_region(
            regions, {"big": 1.0, "small": 1.0}, 0.0, 400.0, {"big": 1.0, "small": 1.0})
        extra = {tile: fed[tile] - regional_population.kcal_per_day_fed(regions[tile], 1.0) for tile in regions}
        self.assertAlmostEqual(extra["big"], 3.0 * extra["small"])


if __name__ == "__main__":
    unittest.main()
