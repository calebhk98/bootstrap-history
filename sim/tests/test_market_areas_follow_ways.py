"""Complaints/416: market-area partitions follow the built ways. When the live economy's ways change, its
areas are partitioned again over the new carriage table and what the economy remembers about each market
(prices, volumes, merchants' expectations) moves to the area that now holds the old market's anchor."""
QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import api as economy_api
from sim.economy.economy import Economy
from sim.economy.market_memory import KEY_SEPARATOR, market_key
from sim.geography import api as geography_api
from sim.tests import economy_fixture as fixture

RATES = {"cart": 0.5, "road": 0.01}
GOOD = fixture.GRAIN


def ways():
    return {geography_api.edge_key(fixture.TOWN, fixture.FARMS): {"road": True},
            geography_api.edge_key(fixture.FARMS, fixture.HILLS): {"road": True}}


def economy_before_the_roads():
    return Economy(fixture.small_setup(carriage_rates=dict(RATES)))


def good_keys(economy, mapping):
    return [key for key in mapping if key.split(KEY_SEPARATOR)[0] in economy.area_map.goods()]


class FollowTests(unittest.TestCase):

    def test_roads_between_the_tiles_join_what_the_carriage_split(self):
        economy = economy_before_the_roads()
        self.assertEqual(len(economy.area_map.areas(GOOD)), 3)
        self.assertTrue(economy_api.set_improvements(economy, ways()))
        self.assertEqual(len(economy.area_map.areas(GOOD)), 1)

    def test_the_partition_matches_one_opened_with_the_ways(self):
        economy = economy_before_the_roads()
        economy_api.set_improvements(economy, ways())
        opened = Economy(dataclasses.replace(fixture.small_setup(carriage_rates=dict(RATES)), improvements=ways()))
        for good in opened.area_map.goods():
            self.assertEqual(economy.area_map.areas(good), opened.area_map.areas(good))

    def test_unchanged_ways_leave_the_areas_alone(self):
        economy = economy_before_the_roads()
        before = economy.area_map
        self.assertFalse(economy_api.set_improvements(economy, {}))
        self.assertIs(economy.area_map, before)

    def test_remembered_prices_move_to_the_new_area_of_the_old_anchor(self):
        economy = economy_before_the_roads()
        old_price = {tile: economy.record.memory.prices[market_key(GOOD, economy.area_map.area_of(GOOD, tile))]
                     for tile in economy.setup.tiles}
        economy_api.set_improvements(economy, ways())
        new_area = economy.area_map.areas(GOOD)[0]
        remembered = economy.record.memory.prices[market_key(GOOD, new_area.area_id)]
        self.assertEqual(remembered, old_price[new_area.anchor_tile])

    def test_every_remembered_market_names_an_area_that_exists(self):
        economy = economy_before_the_roads()
        economy_api.set_improvements(economy, ways())
        memory = economy.record.memory
        for mapping in (memory.prices, memory.usual_prices):
            for key in good_keys(economy, mapping):
                good, area_id = key.split(KEY_SEPARATOR)
                self.assertIn(area_id, [area.area_id for area in economy.area_map.areas(good)], key)

    def test_the_economy_runs_on_after_its_areas_change(self):
        economy = economy_before_the_roads()
        economy.step(fixture.quiet_year(economy.setup))
        economy_api.set_improvements(economy, ways())
        outcome = economy.step(fixture.quiet_year(economy.setup))
        self.assertGreater(len(outcome.output), 0)


if __name__ == "__main__":
    unittest.main()
