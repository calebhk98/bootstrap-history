"""`priced_need_tables.NeedBatch.tables` writes the need and good rows of the requests added, in request order, with the figures the per-request
lists gave."""
QUICK_TOPIC = True

import dataclasses
import math
import unittest

from sim.economy import priced_need_tables
from sim.economy.priced_need_tables import GOODS, NeedBatch
from sim.world.need_basket import NeedSpec

FOOD = NeedSpec("food", 2.0, 1.0, (("bread", 1.0), ("fish", 0.5)), qualities=(("fish", 2.0),), share_limits=(("bread", 0.6),))
LIGHT = NeedSpec("light", 0.0, 0.5, (("tallow", 1.0),))


class SpecRows(unittest.TestCase):
    def test_a_spec_with_another_floor_and_the_same_goods_gives_the_same_rows(self):
        rows = priced_need_tables.spec_rows(FOOD)
        self.assertEqual(rows[0], [GOODS.number["bread"], GOODS.number["fish"]])
        self.assertEqual(rows[1:3], ([1.0, 0.5], [1.0, 2.0]))
        self.assertEqual(rows[3][0], 0.6)
        self.assertTrue(math.isnan(rows[3][1]))
        self.assertIs(priced_need_tables.spec_rows(dataclasses.replace(FOOD, subsistence_per_person=5.0)), rows)

    def test_a_spec_with_other_goods_gives_other_rows(self):
        self.assertEqual(priced_need_tables.spec_rows(LIGHT)[0], [GOODS.number["tallow"]])


class TablesOfRequests(unittest.TestCase):
    def test_two_requests_make_their_needs_and_goods_in_order(self):
        first_basket, second_basket = (FOOD, LIGHT), (LIGHT,)
        batch = NeedBatch()
        self.assertEqual(batch.add(3, -1.0, first_basket), 0)
        self.assertEqual(batch.add(1, 0.25, second_basket), 1)
        needs, rows = batch.tables()
        self.assertEqual(needs.tile.tolist(), [3, 3, 1])
        self.assertEqual(needs.exponent.tolist(), [-1.0, -1.0, 0.25])
        self.assertEqual(needs.first_row.tolist(), [0, 2, 3])
        self.assertEqual(needs.end_row.tolist(), [2, 3, 4])
        names = GOODS.name_array()[rows.good].tolist()
        self.assertEqual(names, ["bread", "fish", "tallow", "tallow"])
        self.assertEqual(rows.effect.tolist(), [1.0, 0.5, 1.0, 1.0])
        self.assertEqual(rows.quality.tolist(), [1.0, 2.0, 1.0, 1.0])
        self.assertEqual(rows.limit[0], 0.6)
        self.assertTrue(all(math.isnan(each) for each in rows.limit[1:].tolist()))
        self.assertEqual(batch.owners, [0, 0, 1])
        self.assertEqual(batch.specs, [FOOD, LIGHT, LIGHT])
        self.assertTrue(batch.has_limits)

    def test_no_request_makes_empty_tables(self):
        needs, rows = NeedBatch().tables()
        self.assertEqual((len(needs.tile), len(rows.good)), (0, 0))
        self.assertEqual(NeedBatch().owners, [])


if __name__ == "__main__":
    unittest.main()
