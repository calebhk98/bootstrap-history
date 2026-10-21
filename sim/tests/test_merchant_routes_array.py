"""The array route search (`merchants_routes_array`) gives exactly the rows of the scalar search: the same
floats, the same destination on ties, the same sources. Exact equality, not a tolerance, because the array
arithmetic repeats the scalar arithmetic operation for operation (a changed order of operations would show here)."""

QUICK_TOPIC = True

import random
import unittest

from sim.economy import merchants, merchants_routes_array
from sim.economy.types import GoodSpec, MarketArea

from .test_merchant_good_routes_exact import KeptCarriage, LineCarriage, TILES


class ArrayRoutesTests(unittest.TestCase):
    def setUp(self):
        self.areas = [MarketArea("area%d" % number, "salt", (tile,), tile) for number, tile in enumerate(TILES)]

    def both(self, prices, spec, rate, carriage, source_ids=None):
        by_area = {area.area_id: price for area, price in zip(self.areas, prices)}
        scalar = merchants._good_routes("salt", spec, self.areas, by_area, carriage, rate, source_ids)
        by_source = lambda rows: sorted(rows, key=lambda row: row[2].area_id)
        self.assertEqual(by_source(merchants_routes_array.good_routes("salt", spec, self.areas, by_area, carriage, rate, source_ids)),
                         by_source(scalar))
        self.assertEqual(by_source(merchants_routes_array.good_routes_aligned("salt", spec, self.areas, prices, carriage, rate, source_ids)),
                         by_source(scalar))
        return scalar

    def test_random_prices_give_the_scalar_rows(self):
        generator = random.Random(3)
        found = 0
        for _trial in range(500):
            spec = GoodSpec("salt", generator.choice((1000.0, 250.0, 0.0)), generator.choice((0.0, 0.3, 1.0)), 0.0, "food")
            carriage = LineCarriage(generator.choice((0.0, 0.05, 0.4)), generator.choice((10.0, 200.0, 900.0)))
            prices = [generator.choice((None, 0.0, 1.0, generator.uniform(0.5, 6.0))) for _ in self.areas]
            rows = self.both(prices, spec, generator.choice((0.0, 0.05, 0.4)), carriage,
                             generator.choice((None, {"area1", "area3", "area5"})))
            found += bool(rows)
        self.assertGreater(found, 20)

    def test_equal_best_nets_go_to_the_same_destination(self):
        spec = GoodSpec("salt", 1000.0, 0.0, 0.0, "food")
        prices = [1.0, 1.0, 5.0, 5.0, 5.0, 1.0, None]
        rows = self.both(prices, spec, 0.05, LineCarriage(0.0, 10.0))
        self.assertTrue(rows)

    def test_a_repriced_table_is_read_afresh(self):
        generator = random.Random(5)
        spec = GoodSpec("salt", 1000.0, 0.3, 0.0, "food")
        carriage = KeptCarriage(0.05, 200.0)
        for rate in (0.05, 0.4, 1.5):
            carriage.reprice(rate)
            for _again in range(3):
                prices = [generator.choice((None, 1.0, generator.uniform(0.5, 6.0))) for _ in self.areas]
                self.both(prices, spec, 0.05, carriage)


if __name__ == "__main__":
    unittest.main()
