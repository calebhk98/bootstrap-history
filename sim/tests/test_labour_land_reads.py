"""A tenant's outside options (land_lease_year.py) and the names of the labour offers' markets equal the
reads made one pair of tiles or one name at a time, on written-out and seeded random inputs."""
QUICK_TOPIC = True

import random
import unittest
from unittest import mock

import numpy

from sim.compiled_tables.ids import IdTable
from sim.economy import land_lease_year
from sim.economy.labour_offers_table import LabourIds
from sim.tests.labour_land_plain import plain_market_names, plain_outside_options


class MarketNamesTests(unittest.TestCase):
    def test_names_of_markets_written_out(self):
        ids = LabourIds(IdTable("cohort", {"c"}), IdTable("trade", {"smith", "baker"}), IdTable("area", {"work@b", "work@a"}))
        trades, areas = numpy.array([0, 1, 1]), numpy.array([1, 0, 1])
        self.assertEqual(ids.market_names(trades, areas), [("baker", "work@b"), ("smith", "work@a"), ("smith", "work@b")])

    def test_seeded_random_markets_equal_the_name_by_name_read(self):
        generator = random.Random(3)
        ids = LabourIds(IdTable("cohort", {"c"}), IdTable("trade", {"t%d" % number for number in range(9)}),
                        IdTable("area", {"work@%d" % number for number in range(30)}))
        for _ in range(20):
            count = generator.randrange(0, 50)
            trades = numpy.array([generator.randrange(9) for _ in range(count)], dtype=numpy.int64)
            areas = numpy.array([generator.randrange(30) for _ in range(count)], dtype=numpy.int64)
            self.assertEqual(ids.market_names(trades, areas), plain_market_names(ids, trades, areas))


class OutsideOptionTests(unittest.TestCase):
    def test_equal_to_the_pairwise_plain_read_when_tiles_share_areas(self):
        generator = random.Random(11)
        area = lambda tile: "work@" + str(int(tile[1:]) // 3)       # three tiles to a labour area
        for _ in range(100):
            tiles = ["t%d" % number for number in generator.sample(range(20), generator.randrange(1, 12))]
            margins = {tile: (generator.choice((float("inf"), float("nan"), generator.uniform(-5.0, 9.0))), "r") for tile in tiles}
            posted = {tile: generator.uniform(0.0, 4.0) for tile in tiles if generator.random() < 0.7}
            with mock.patch.object(land_lease_year, "labour_area", area):
                found = land_lease_year._outside_options(None, margins, posted)
            self.assertEqual(list(found), list(margins))
            self.assertEqual(found, plain_outside_options(margins, posted, area))

    def test_a_tile_that_is_its_own_area_has_no_outside_option(self):
        self.assertEqual(land_lease_year._outside_options(None, {"a": (5.0, "r"), "b": (7.0, "r")}, {}), {"a": 0.0, "b": 0.0})


if __name__ == "__main__":
    unittest.main()
