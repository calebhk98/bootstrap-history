"""One search for many merchants (`merchants_batch.search_many`) gives each merchant the rows `merchants_book.search` gives it
alone, bit for bit, on random worlds (merchants that count the same prices in a good share one search)."""

QUICK_TOPIC = True

import random
import unittest

import numpy as np

from sim.economy import merchants, merchants_batch, merchants_book, merchants_plan
from sim.tests.test_year_speed_merchants import SPECS, random_world

COLUMNS = ("good", "source", "destination", "source_slot", "destination_slot", "rank", "price_here", "outlay", "ceiling")


class SearchManyTest(unittest.TestCase):
    def worlds(self, seed, count):
        rng = random.Random(seed)
        _who, view, carriage, area_map, _held, _shares = random_world(seed)
        route = merchants_book.route_pass(view, carriage, area_map, SPECS)
        arrays = []
        homes = []
        for number in range(count):
            other = random_world(rng.randrange(10 ** 6))[0]
            if number % 3 == 2 and arrays:
                arrays.append(arrays[-1].copy())      # a merchant counting what the one before it counts
                homes.append(homes[-1])
                continue
            arrays.append(merchants_book.merchant_array(route.book, other.expected_prices))
            homes.append(other.home_tile)
        return route, np.stack(arrays), homes

    def test_rows_equal_the_search_of_each_merchant(self):
        for seed in range(25):
            route, expected, homes = self.worlds(seed, 6)
            rate = 0.03 + 0.001 * seed
            many = merchants_batch.search_many(route, expected, homes, rate, merchants.MERCHANT_MARGIN_SHARE)
            for position, home in enumerate(homes):
                alone = merchants_book.search(route, expected[position], home, rate, merchants.MERCHANT_MARGIN_SHARE)
                for name in COLUMNS:
                    self.assertTrue(np.array_equal(getattr(many[position], name), getattr(alone, name)), (seed, position, name))

    def test_no_merchants_gives_no_rows(self):
        route = self.worlds(1, 1)[0]
        self.assertEqual(merchants_batch.search_many(route, np.zeros((0, route.book.slots)), [], 0.05, 0.05), [])

    def test_rows_kept_ahead_are_used_only_for_the_same_figures(self):
        who, view, carriage, area_map, _held, _shares = random_world(3)
        route = merchants_book.route_pass(view, carriage, area_map, SPECS)
        merchants_plan.prepare_rows(route, [who], 0.04)
        expected = merchants_book.merchant_array(route.book, who.expected_prices)
        self.assertIsNotNone(merchants_batch.rows_for(route, who.agent_id, 0.04, who.home_tile, expected, who.traded_tiles))
        self.assertIsNone(merchants_batch.rows_for(route, who.agent_id, 0.05, who.home_tile, expected, who.traded_tiles))
        moved = expected.copy()
        moved[~np.isnan(moved)] *= 1.5
        self.assertIsNone(merchants_batch.rows_for(route, who.agent_id, 0.04, who.home_tile, moved, who.traded_tiles))


if __name__ == "__main__":
    unittest.main()
