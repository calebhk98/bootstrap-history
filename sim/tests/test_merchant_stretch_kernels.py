"""Complaints/517: the packed route search (`merchants_plan.candidate_rows`, `merchants_batch`) leaves out the areas outside a
merchant's stretch exactly as the reference search (`merchants.candidate_routes`) does, on random worlds and random stretches."""

QUICK_TOPIC = True

import random
import unittest

import numpy as np

from sim.economy import merchants, merchants_batch, merchants_book, merchants_plan
from sim.tests.test_year_speed_merchants import SPECS, TILES, close, random_world

SEEDS = 40


def keyed(rows):
    return [(row[1], row[2].area_id, row[3].area_id) for row in rows]


class StretchKernelTests(unittest.TestCase):
    def stretched(self, seed):
        who, view, carriage, area_map, held, _shares = random_world(seed)
        rng = random.Random(seed + 1000)
        who.traded_tiles = {tile: 0 for tile in TILES if rng.random() < 0.2}
        return who, view, carriage, area_map, held

    def test_the_packed_search_gives_the_reference_rows_for_a_stretch(self):
        gated = 0
        for seed in range(SEEDS):
            who, view, carriage, area_map, held = self.stretched(seed)
            reference = merchants.candidate_routes(who, view, carriage, area_map, held, SPECS, 0.05)
            packed = merchants_plan.candidate_rows(who, view, carriage, area_map, held, SPECS, 0.05)
            self.assertEqual(sorted(keyed(packed)), sorted(keyed(reference)), seed)
            for row in packed:
                match = [other for other in reference if keyed([other]) == keyed([row])][0]
                self.assertTrue(close(row[0], match[0]), seed)
            full = random_world(seed)[0]
            gated += len(keyed(merchants.candidate_routes(full, view, carriage, area_map, held, SPECS, 0.05))) > len(keyed(reference))
        self.assertGreater(gated, 5)      # a stretch does cut routes in these worlds

    def test_the_batched_search_gives_the_single_search_rows_for_a_stretch(self):
        for seed in range(SEEDS):
            who, view, carriage, area_map, held = self.stretched(seed)
            route = merchants_book.route_pass(view, carriage, area_map, SPECS)
            expected = merchants_book.merchant_array(route.book, who.expected_prices)
            many = merchants_batch.search_many(route, np.stack([expected]), [who.home_tile], 0.05, merchants.MERCHANT_MARGIN_SHARE,
                                               [who.traded_tiles])[0]
            alone = merchants_book.search(route, expected, who.home_tile, 0.05, merchants.MERCHANT_MARGIN_SHARE,
                                          traded_tiles=who.traded_tiles)
            for name in ("good", "source", "destination", "rank", "price_here", "outlay", "ceiling"):
                self.assertTrue(np.array_equal(getattr(many, name), getattr(alone, name)), (seed, name))

    def test_rows_kept_ahead_are_not_used_for_another_stretch(self):
        who, view, carriage, area_map, _held = self.stretched(3)
        route = merchants_book.route_pass(view, carriage, area_map, SPECS)
        merchants_plan.prepare_rows(route, [who], 0.04)
        expected = merchants_book.merchant_array(route.book, who.expected_prices)
        args = (route, who.agent_id, 0.04, who.home_tile, expected)
        self.assertIsNotNone(merchants_batch.rows_for(*args, who.traded_tiles))
        self.assertIsNone(merchants_batch.rows_for(*args, {**who.traded_tiles, "elsewhere": 0}))


if __name__ == "__main__":
    unittest.main()
