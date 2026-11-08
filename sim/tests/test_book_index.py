"""The book's hash index: packing three ids into one key, finding a row by key, adding to the index, growing the table."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.book_index import EMPTY, KeyedRows, index_add, index_build, index_find, index_size_for, pack_key, unpack_key
from sim.book_tables import STOCKS, Stocks


def small_index(keys, size=16):
    index = numpy.full(size, EMPTY, dtype=numpy.int64)
    column = numpy.array(keys, dtype=numpy.int64)
    for row in range(len(keys)):
        index_add(column, index, row)
    return column, index


class PackKeyTests(unittest.TestCase):
    def test_three_ids_unpack_to_themselves(self):
        self.assertEqual(unpack_key(pack_key(9000, 311, 70000)), (9000, 311, 70000))

    def test_the_third_id_defaults_to_zero(self):
        self.assertEqual(unpack_key(pack_key(5, 6)), (5, 6, 0))

    def test_keys_differing_in_one_id_differ(self):
        keys = {pack_key(1, 2, 3), pack_key(2, 2, 3), pack_key(1, 3, 3), pack_key(1, 2, 4)}
        self.assertEqual(len(keys), 4)


class IndexFindTests(unittest.TestCase):
    def test_find_answers_the_row_holding_the_key(self):
        keys, index = small_index([40, 41, 42])
        self.assertEqual([index_find(keys, index, key) for key in (40, 41, 42)], [0, 1, 2])

    def test_find_answers_empty_for_an_absent_key(self):
        keys, index = small_index([40, 41])
        self.assertEqual(index_find(keys, index, 99), EMPTY)

    def test_keys_that_probe_to_the_same_place_are_all_found(self):
        keys, index = small_index(list(range(0, 1000, 7)), size=256)
        self.assertEqual([index_find(keys, index, int(key)) for key in keys], list(range(len(keys))))


class IndexBuildTests(unittest.TestCase):
    def test_build_indexes_only_live_rows(self):
        keys = numpy.array([10, 11, 12], dtype=numpy.int64)
        live = numpy.array([1, 0, 1], dtype=numpy.uint8)
        index = numpy.full(16, EMPTY, dtype=numpy.int64)
        index_build(keys, live, 3, index)
        self.assertEqual([index_find(keys, index, key) for key in (10, 11, 12)], [0, EMPTY, 2])


class IndexSizeTests(unittest.TestCase):
    def test_the_size_is_a_power_of_two_at_least_twice_the_capacity(self):
        for capacity in (1, 8, 9, 100, 1000):
            size = index_size_for(capacity)
            self.assertTrue(size >= 2 * capacity and size & (size - 1) == 0)


class KeyedRowsTests(unittest.TestCase):
    def test_reserve_keeps_every_key_findable_after_the_table_grows(self):
        rows = KeyedRows(STOCKS, Stocks, 4)
        for row in range(4):
            rows.table.key[row] = 100 + row
            rows.table.live[row] = 1
            index_add(rows.table.key, rows.index, row)
        rows.table.row_count[0] = 4
        rows.reserve(10)
        self.assertEqual([rows.find(100 + row) for row in range(4)], [0, 1, 2, 3])
        self.assertGreaterEqual(int(rows.table.capacity[0]), 14)

    def test_clear_forgets_every_row(self):
        rows = KeyedRows(STOCKS, Stocks, 4)
        rows.table.key[0] = 5
        rows.table.live[0] = 1
        rows.table.row_count[0] = 1
        index_add(rows.table.key, rows.index, 0)
        rows.clear()
        self.assertEqual((rows.rows, rows.find(5)), (0, EMPTY))


if __name__ == "__main__":
    unittest.main()
