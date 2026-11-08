"""ordered_total: the left-to-right sum a compiled and a plain run share."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.compiled_tables.sums import ordered_total


class OrderedTotalTests(unittest.TestCase):
    def test_it_adds_left_to_right_exactly_as_a_python_loop_does(self):
        values = numpy.random.default_rng(0).uniform(0, 1e6, 5000) * numpy.where(numpy.arange(5000) % 2, 1e-7, 1.0)
        expected = 0.0
        for value in values.tolist():
            expected += value
        self.assertEqual(ordered_total(values, len(values)), expected)

    def test_it_adds_only_the_rows_in_use(self):
        self.assertEqual(ordered_total(numpy.array([1.0, 2.0, 99.0]), 2), 3.0)

    def test_no_rows_add_to_zero(self):
        self.assertEqual(ordered_total(numpy.array([5.0]), 0), 0.0)


if __name__ == "__main__":
    unittest.main()
