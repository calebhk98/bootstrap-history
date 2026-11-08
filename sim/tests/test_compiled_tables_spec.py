"""TableSpec: building tables from a documented column list."""
QUICK_TOPIC = True

import pickle
import unittest

import numpy

from sim.compiled_tables.example_loans import LOANS, Loans
from sim.compiled_tables.spec import Column, TableSpec


class NewTableTests(unittest.TestCase):
    def test_new_table_has_zeroed_columns_of_the_capacity_and_a_count(self):
        table = LOANS.new_table(Loans, 5, row_count=2)
        self.assertEqual(table.principal.tolist(), [0.0] * 5)
        self.assertEqual((int(table.row_count[0]), int(table.capacity[0])), (2, 5))

    def test_new_table_refuses_a_count_above_the_capacity(self):
        with self.assertRaises(ValueError):
            LOANS.new_table(Loans, 2, row_count=3)

    def test_columns_have_the_declared_dtypes(self):
        table = LOANS.new_table(Loans, 1)
        self.assertEqual((table.borrower.dtype, table.rate.dtype), (numpy.int64, numpy.float64))


class TableOfTests(unittest.TestCase):
    def test_table_of_fills_every_column_and_counts_the_rows(self):
        table = LOANS.table_of(Loans, borrower=[0, 1], lender=[1, 0], principal=[10.0, 20.0], rate=[0.1, 0.2])
        self.assertEqual((table.principal.tolist(), int(table.row_count[0])), ([10.0, 20.0], 2))

    def test_table_of_refuses_a_missing_column(self):
        with self.assertRaises(ValueError):
            LOANS.table_of(Loans, borrower=[0], lender=[1], principal=[1.0])


class SpecTests(unittest.TestCase):
    def test_a_column_named_like_a_tuple_method_is_refused(self):
        with self.assertRaises(ValueError):
            TableSpec("Bad", (Column("count", numpy.int64, "clashes with tuple.count", "none"),))

    def test_a_repeated_column_name_is_refused(self):
        column = Column("a", numpy.int64, "x", "none")
        with self.assertRaises(ValueError):
            TableSpec("Bad", (column, column))

    def test_describe_columns_gives_a_line_per_column_with_unit_and_meaning(self):
        text = LOANS.describe_columns()      # presentation: the documented text is what a reader sees
        self.assertIn("rate: float64 [fraction per year] interest added", text)

    def test_the_table_type_pickles_by_module_and_name_as_numba_caching_needs(self):
        self.assertIs(pickle.loads(pickle.dumps(Loans)), Loans)


if __name__ == "__main__":
    unittest.main()
