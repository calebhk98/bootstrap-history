"""`year_arrays_worths.packed_stock` reads the book's stocks in one kernel call and gives what the per-producer read gave: the same
rows, columns and quantities (compared exactly), and the same value for goods the matrices have no column for."""

QUICK_TOPIC = True

import math
import unittest

import numpy as np

from sim.economy.year_arrays import YearArrays
from sim.economy.year_arrays_worths import packed_stock
from sim.tests.year_close_fixture import economy_of


def plain_packed_stock(record, view, ids, records, matrices):
    """The reference: the book read one producer at a time through `goods_of`."""
    goods_row = matrices.goods.row
    rows, goods, quantities = [], [], []
    extra = np.zeros(len(ids))
    for row, producer_id in enumerate(ids):
        for good, by_tile in record.book.goods_of(producer_id).items():
            positive = [quantity for quantity in by_tile.values() if quantity > 0.0]
            if not positive:
                continue
            total = positive[0] if len(positive) == 1 else math.fsum(positive)
            column = goods_row.get(good)
            if column is None:
                price = view.price(good, view.area_of(good, records[row].tile))
                if price is not None and price > 0.0:
                    extra[row] += price * total
                continue
            rows.append(row)
            goods.append(column)
            quantities.append(total)
    rows, goods = np.array(rows, dtype=np.int64), np.array(goods, dtype=np.int64)
    order = np.lexsort((goods, rows))
    return rows[order], goods[order], np.array(quantities, dtype=np.float64)[order], extra


class PackedStock(unittest.TestCase):
    def test_packed_stock_is_the_per_producer_read(self):
        compared = 0
        for seed in range(8):
            setup, record, view, _ledger, area_map = economy_of(seed, producer_count=60)
            arrays = YearArrays.build(setup, record, area_map, view)
            ids = sorted(record.producers)
            records = [record.producers[each] for each in ids]
            new = packed_stock(record, view, ids, records, arrays.matrices)
            old = plain_packed_stock(record, view, ids, records, arrays.matrices)
            for got, want in zip(new, old):
                self.assertEqual(got.tolist(), want.tolist())
            compared += len(old[0])
        self.assertGreater(compared, 100)


if __name__ == "__main__":
    unittest.main()
