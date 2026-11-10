"""reserve_rows and claim_row: spare capacity, a count, no write past the end."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.compiled_tables.example_loans import LOANS, Loans
from sim.compiled_tables.growth import NO_ROOM, claim_row, reserve_rows
from sim.compiled_tables.spec import Column, TableSpec


class ReserveRowsTests(unittest.TestCase):
    def test_the_same_table_comes_back_when_the_rows_fit(self):
        table = LOANS.new_table(Loans, 4, row_count=1)
        self.assertIs(reserve_rows(table, 3), table)

    def test_a_full_table_grows_to_at_least_double_and_keeps_its_rows(self):
        table = LOANS.table_of(Loans, borrower=[3, 4], lender=[0, 0], principal=[1.5, 2.5], rate=[0.1, 0.1])
        bigger = reserve_rows(table, 1)
        self.assertEqual((int(bigger.capacity[0]), bigger.principal[:2].tolist(), int(bigger.row_count[0])), (4, [1.5, 2.5], 2))

    def test_a_large_request_grows_to_exactly_what_is_needed(self):
        table = LOANS.new_table(Loans, 2)
        self.assertEqual(int(reserve_rows(table, 50).capacity[0]), 50)

    def test_grown_columns_are_whole_contiguous_arrays(self):
        table = reserve_rows(LOANS.new_table(Loans, 2, row_count=2), 10)
        self.assertTrue(table.principal.flags["C_CONTIGUOUS"] and table.principal.base is None)


class WideColumnTests(unittest.TestCase):
    """A column of several values a row (people per band) is a 2-d array and grows with its table."""

    def test_a_wide_column_keeps_its_width_when_the_table_grows(self):
        spec = TableSpec("Wide", (Column("market", numpy.int64, "a market", "row"), Column("people", numpy.float64, "people per band", "people", width=0)))
        wide = spec.make_type(__name__)
        table = spec.new_table(wide, 2, row_count=2, widths={"people": 3})
        table.people[1] = [1.0, 2.0, 3.0]
        bigger = reserve_rows(table, 5)
        self.assertEqual((bigger.people.shape, bigger.people[1].tolist(), bigger.market.shape), ((7, 3), [1.0, 2.0, 3.0], (7,)))


class ClaimRowTests(unittest.TestCase):
    def test_claim_row_gives_the_next_row_and_counts_it(self):
        table = LOANS.new_table(Loans, 3, row_count=1)
        self.assertEqual((claim_row(table), int(table.row_count[0])), (1, 2))

    def test_claim_row_on_a_full_table_answers_no_room_and_changes_nothing(self):
        table = LOANS.new_table(Loans, 2, row_count=2)
        self.assertEqual((claim_row(table), int(table.row_count[0])), (NO_ROOM, 2))


if __name__ == "__main__":
    unittest.main()
