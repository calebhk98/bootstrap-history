"""Area cache test."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.tests.test_economy_market_areas import AreaMapTests as Fixture


class AreasCacheTests(Fixture):
    def test_repeated_calls_return_the_same_areas(self):
        area_map = self.build()
        first = area_map.areas("grain_kg")
        self.assertIs(area_map.areas("grain_kg"), first)

    def test_areas_name_their_good_and_goods_do_not_mix(self):
        area_map = self.build()
        for good in ("grain_kg", "silver_kg"):
            self.assertTrue(all(area.good_id == good for area in area_map.areas(good)))

    def test_cached_areas_equal_a_fresh_replacement(self):
        area_map = self.build()
        for good in area_map.goods():
            partition = area_map._partitions[area_map._bucket_of_good[good]]
            fresh = tuple(dataclasses.replace(area, good_id=good) for area in partition)
            self.assertEqual(area_map.areas(good), fresh)


if __name__ == "__main__":
    unittest.main()
