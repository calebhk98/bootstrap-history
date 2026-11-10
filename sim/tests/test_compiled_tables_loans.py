"""The example loans table: a kernel reads and writes named columns; describe_row and Causes name what a kernel returns."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.compiled_tables.causes import Causes
from sim.compiled_tables.describe import describe_row
from sim.compiled_tables.example_loans import (CAUSES, LOANS, NEGATIVE_PRINCIPAL, TABLE_FULL, Loans, accrue_interest,
                                               lend, owed_by_agent)
from sim.compiled_tables.ids import IdTable


def two_loans():
    return LOANS.table_of(Loans, borrower=[1, 0], lender=[0, 1], principal=[100.0, 50.0], rate=[0.1, 0.2])


class LendTests(unittest.TestCase):
    def test_lend_writes_the_row_and_returns_its_number(self):
        table = LOANS.new_table(Loans, 2, row_count=1)
        self.assertEqual(lend(table, 3, 4, 10.0, 0.05), 1)
        self.assertEqual((table.borrower[1], table.lender[1], table.principal[1], table.rate[1]), (3, 4, 10.0, 0.05))

    def test_lend_into_a_full_table_returns_minus_the_table_full_code(self):
        self.assertEqual(lend(LOANS.new_table(Loans, 1, row_count=1), 0, 1, 1.0, 0.1), -TABLE_FULL)

    def test_lend_refuses_a_negative_principal_without_taking_a_row(self):
        table = LOANS.new_table(Loans, 2)
        self.assertEqual((lend(table, 0, 1, -1.0, 0.1), int(table.row_count[0])), (-NEGATIVE_PRINCIPAL, 0))


class KernelTests(unittest.TestCase):
    def test_accrue_interest_adds_each_loans_interest_and_returns_the_total(self):
        table = two_loans()
        total = accrue_interest(table)
        self.assertEqual((table.principal.tolist(), total), ([110.0, 60.0], 20.0))

    def test_owed_by_agent_sums_each_borrowers_principal(self):
        self.assertEqual(owed_by_agent(two_loans(), 3).tolist(), [50.0, 100.0, 0.0])


class DescribeTests(unittest.TestCase):
    def test_describe_row_translates_id_columns_to_names_and_leaves_numbers_alone(self):
        agents = IdTable("agent", ["bank", "farmer"])
        described = describe_row(LOANS, two_loans(), 0, {"agents": agents})
        self.assertEqual(described, {"borrower": "farmer#1", "lender": "bank#0", "principal": 100.0, "rate": 0.1})

    def test_describe_row_refuses_a_row_beyond_the_rows_in_use(self):
        with self.assertRaises(IndexError):
            describe_row(LOANS, two_loans(), 2)


class CausesTests(unittest.TestCase):
    def test_a_code_names_its_cause_on_the_refusal(self):
        refusal = CAUSES.refusal(TABLE_FULL, "No room for another loan.", row=7)
        self.assertEqual((refusal.cause, refusal.facts), ("table_full", {"row": 7}))

    def test_code_zero_is_ok_and_has_no_name(self):
        with self.assertRaises(ValueError):
            Causes(("a",)).name(0)


if __name__ == "__main__":
    unittest.main()
