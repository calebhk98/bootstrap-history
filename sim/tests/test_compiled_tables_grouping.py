"""group_starts and stable_order: ragged rows as slices of an order array."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.compiled_tables.grouping import group_starts, stable_order

GROUP_OF_ROW = numpy.array([2, 0, 2, 2, 0, 9], dtype=numpy.int64)      # the last entry is beyond row_count and ignored


class GroupingTests(unittest.TestCase):
    def test_group_starts_are_running_totals_of_each_groups_rows(self):
        self.assertEqual(group_starts(GROUP_OF_ROW, 5, 4).tolist(), [0, 2, 2, 5, 5])

    def test_stable_order_lists_each_groups_rows_in_append_order(self):
        starts = numpy.array([0, 2, 2, 5, 5], dtype=numpy.int64)
        self.assertEqual(stable_order(GROUP_OF_ROW, 5, starts).tolist(), [1, 4, 0, 2, 3])

    def test_an_empty_table_has_all_zero_starts(self):
        self.assertEqual(group_starts(GROUP_OF_ROW, 0, 2).tolist(), [0, 0, 0])


if __name__ == "__main__":
    unittest.main()
