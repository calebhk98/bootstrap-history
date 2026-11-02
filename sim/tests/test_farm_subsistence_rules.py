"""The farm model at its edges, as rules on built inputs. Food one year's harvest yields, net of seed, over the year's
food need, is proportional to the hectares the hands crop and rises with the ground's fertility, so there is ground on
which everyone farming feeds less than the people need, and a toolkit that doubles what a worker crops lifts it over
subsistence (`agriculture.gross_harvest_kg`, `hectares_cropped_per_farm_worker`). Barren land:
no cropped hectares give no harvest. The ladder over unfarmable ground is in test_farm_edges; the population's response
to hunger is in test_demography."""
QUICK_TOPIC = True

import unittest

from sim.world import agriculture

WORKERS = 60.0
ADULT_EQUIVALENTS = 100.0


def food_ratio(fertility, hectares):
    """What one year's harvest yields on `hectares` of `fertility` (`gross_harvest_kg`), net of the seed sown, over the
    year's food need of the adult equivalents (the energy requirement a year over the crop's energy per kilogram)."""
    crop = agriculture.DEFAULT_CROP
    harvest = agriculture.gross_harvest_kg(
        agriculture.Land(hectares, fertility), hectares * agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE,
        crop=crop, rotation=agriculture.DEFAULT_ROTATION, toolkit=agriculture.DEFAULT_TOOLKIT, worker_count=WORKERS,
        weather_multiplier=1.0)
    need = (ADULT_EQUIVALENTS * agriculture.HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY * agriculture.DAYS_PER_YEAR
            / crop.energy_kcal_per_kg)
    return (harvest - crop.planting_material_kg_per_ha * hectares) / need


class FoodRatioTests(unittest.TestCase):
    def test_the_ratio_rises_with_fertility(self):
        self.assertLess(food_ratio(0.3, 100.0), food_ratio(0.6, 100.0))
        self.assertLess(food_ratio(0.6, 100.0), food_ratio(1.2, 100.0))

    def test_the_ratio_is_proportional_to_the_hectares_cropped(self):
        self.assertAlmostEqual(food_ratio(0.8, 100.0), 0.5 * food_ratio(0.8, 200.0), places=6)

    def test_there_is_ground_where_everyone_farming_feeds_less_than_the_people_need(self):
        self.assertLess(food_ratio(0.5, 100.0), 1.0)

    def test_twice_the_hectares_a_worker_crops_lifts_that_ground_over_subsistence(self):
        self.assertGreater(food_ratio(0.5, 200.0), 1.0)

    def test_no_cropped_ground_gives_no_harvest(self):
        self.assertEqual(agriculture.gross_harvest_kg(
            agriculture.Land(0.0, 1.0), 0.0, crop=agriculture.DEFAULT_CROP, rotation=agriculture.DEFAULT_ROTATION,
            toolkit=agriculture.DEFAULT_TOOLKIT, worker_count=WORKERS, weather_multiplier=1.0), 0.0)


class HectaresPerWorkerTests(unittest.TestCase):
    def test_a_reaper_twice_as_fast_and_half_the_hours_a_hectare_doubles_what_a_worker_crops(self):
        base = agriculture.DEFAULT_TOOLKIT
        doubled = base._replace(reaping_rate_multiplier=base.reaping_rate_multiplier * 2.0,
                                labour_hours_multiplier=base.labour_hours_multiplier / 2.0)
        self.assertAlmostEqual(agriculture.hectares_cropped_per_farm_worker(agriculture.DEFAULT_CROP, doubled),
                               2.0 * agriculture.hectares_cropped_per_farm_worker(agriculture.DEFAULT_CROP, base), places=9)


if __name__ == "__main__":
    unittest.main()
