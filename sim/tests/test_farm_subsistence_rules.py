"""The farm model at its edges, as rules on built inputs. Food one year's harvest yields, net of seed, over the year's
food need, is proportional to the hectares the hands crop and rises with the ground's fertility, so there is ground on
which everyone farming feeds less than the people need, and a toolkit that doubles what a worker crops lifts it over
subsistence (`agriculture.Storage.step`, `hectares_cropped_per_farm_worker`). `labour_allocation.farm_hours_after`
moves hours off the farm no faster than the mobility ceiling and never past what the farm is needed for. Barren land:
no cropped hectares give no harvest. The ladder over unfarmable ground is in test_farm_edges; the population's response
to hunger is in test_demography."""
QUICK_TOPIC = True

import unittest

from sim.labour import labour_allocation, labour_market
from sim.world import agriculture

WORKERS = 60.0
ADULT_EQUIVALENTS = 100.0


def food_ratio(fertility, hectares):
    """Food one year's harvest yields, net of seed, over the year's food need, on `hectares` of `fertility` (one
    `Storage.step`)."""
    year = agriculture.Storage(stock_kg=0.0, seed=0).step(
        agriculture.Land(hectares, fertility), hectares * agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE,
        ADULT_EQUIVALENTS, crop=agriculture.DEFAULT_CROP, rotation=agriculture.DEFAULT_ROTATION,
        toolkit=agriculture.DEFAULT_TOOLKIT, worker_count=WORKERS, weather_multiplier=1.0)
    return (year.gross_harvest_kg - year.seed_sown_kg) / year.food_demand_kg


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
        year = agriculture.Storage(stock_kg=0.0, seed=0).step(
            agriculture.Land(0.0, 1.0), 0.0, ADULT_EQUIVALENTS, crop=agriculture.DEFAULT_CROP,
            rotation=agriculture.DEFAULT_ROTATION, toolkit=agriculture.DEFAULT_TOOLKIT, worker_count=WORKERS,
            weather_multiplier=1.0)
        self.assertEqual(year.gross_harvest_kg, 0.0)
        self.assertLess(year.consumption_kg, year.food_demand_kg)


class HectaresPerWorkerTests(unittest.TestCase):
    def test_a_reaper_twice_as_fast_and_half_the_hours_a_hectare_doubles_what_a_worker_crops(self):
        base = agriculture.DEFAULT_TOOLKIT
        doubled = base._replace(reaping_rate_multiplier=base.reaping_rate_multiplier * 2.0,
                                labour_hours_multiplier=base.labour_hours_multiplier / 2.0)
        self.assertAlmostEqual(agriculture.hectares_cropped_per_farm_worker(agriculture.DEFAULT_CROP, doubled),
                               2.0 * agriculture.hectares_cropped_per_farm_worker(agriculture.DEFAULT_CROP, base), places=9)


class FarmHoursAfterTests(unittest.TestCase):
    TOTAL = 1000.0

    def follow(self, start, needed, years):
        hours = [start]
        for _ in range(years):
            hours.append(labour_allocation.farm_hours_after(hours[-1], needed, self.TOTAL))
        return hours

    def test_a_farm_with_too_many_hands_sheds_them_no_faster_than_the_mobility_ceiling(self):
        ceiling = labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR
        hours = self.follow(900.0, 400.0, 12)
        for before, after in zip(hours, hours[1:]):
            self.assertLessEqual(after, before + 1e-9)
            self.assertGreaterEqual(after, before * (1.0 - ceiling) - 1e-9)
        self.assertLess(hours[-1], hours[0])

    def test_hands_leave_toward_what_the_farm_is_needed_for_and_never_past_it(self):
        hours = self.follow(900.0, 400.0, 40)
        self.assertTrue(all(value >= 400.0 - 1e-9 for value in hours))
        self.assertAlmostEqual(hours[-1], 400.0, places=3)

    def test_a_farm_short_of_hands_gains_them_toward_the_need_and_never_past_it(self):
        hours = self.follow(100.0, 600.0, 40)
        self.assertTrue(all(value <= 600.0 + 1e-9 for value in hours))
        self.assertGreater(hours[1], hours[0])
        self.assertAlmostEqual(hours[-1], 600.0, places=3)

    def test_the_farm_never_has_more_hours_than_the_society_has(self):
        self.assertLessEqual(labour_allocation.farm_hours_after(990.0, 5000.0, self.TOTAL), self.TOTAL)

    def test_a_farm_already_at_its_need_stays(self):
        self.assertAlmostEqual(labour_allocation.farm_hours_after(400.0, 400.0, self.TOTAL), 400.0)


if __name__ == "__main__":
    unittest.main()
