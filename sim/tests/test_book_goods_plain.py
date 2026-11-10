"""`goods_nested` gives what sorting the stock rows as tuples of names gave."""

QUICK_TOPIC = True

import json
import random
import unittest

import numpy

from sim.book_goods_plain import goods_nested
from sim.compiled_tables.ids import IdTable
from sim.tests.book_goods_nested_reference import nested_by_tuples


def _tables(agent_names, good_names, tile_names):
    return IdTable("agent", agent_names), IdTable("good", good_names), IdTable("tile", tile_names)


class GoodsNestedTests(unittest.TestCase):
    def test_written_out_rows(self):
        ids = _tables(["zed", "abe"], ["wheat", "iron"], ["rome", "ostia"])
        agents, goods, tiles = numpy.array([1, 0, 0, 1]), numpy.array([0, 1, 0, 0]), numpy.array([0, 1, 0, 1])
        quantities = numpy.array([1.5, 2.0, 3.25, 4.0])
        nested = goods_nested(agents, goods, tiles, quantities, *ids)
        self.assertEqual(json.dumps(nested), json.dumps(nested_by_tuples(agents, goods, tiles, quantities, *ids)))
        self.assertEqual(nested, {"abe": {"iron": {"ostia": 3.25}, "wheat": {"rome": 2.0}}, "zed": {"iron": {"ostia": 1.5, "rome": 4.0}}})
        self.assertEqual(list(nested), ["abe", "zed"])

    def test_no_rows(self):
        ids = _tables(["a"], ["g"], ["t"])
        empty = numpy.array([], dtype=numpy.int64)
        self.assertEqual(goods_nested(empty, empty, empty, numpy.array([]), *ids), {})

    def test_a_repeated_holder_good_and_tile_is_sorted_by_quantity(self):
        ids = _tables(["a"], ["g"], ["t"])
        agents = goods = tiles = numpy.array([0, 0])
        quantities = numpy.array([5.0, 2.0])
        self.assertEqual(goods_nested(agents, goods, tiles, quantities, *ids), nested_by_tuples(agents, goods, tiles, quantities, *ids))

    def test_random_rows(self):
        for seed in range(40):
            generator = numpy.random.default_rng(seed)
            names = random.Random(seed)
            ids = _tables(["a%d" % number for number in names.sample(range(20), 8)], ["g%d" % number for number in names.sample(range(20), 5)],
                          ["t%d" % number for number in names.sample(range(20), 6)])
            count = int(generator.integers(0, 40))
            agents, goods, tiles = generator.integers(0, 8, count), generator.integers(0, 5, count), generator.integers(0, 6, count)
            quantities = generator.random(count) * 100
            self.assertEqual(json.dumps(goods_nested(agents, goods, tiles, quantities, *ids)),
                             json.dumps(nested_by_tuples(agents, goods, tiles, quantities, *ids)), seed)


if __name__ == "__main__":
    unittest.main()
