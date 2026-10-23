"""Complaint 648: a holder pays the keep of the bonded people it holds only from what it holds, however many rows it owes."""

QUICK_TOPIC = True

import unittest

from sim.economy.bondage_hours import payable_keep


class PayableKeepTests(unittest.TestCase):
    def test_several_rows_of_one_holder_never_pay_more_than_its_balance(self):
        rows = payable_keep([("works", "cohort:a", 6.0), ("works", "cohort:b", 6.0)], {"works": 10.0}.get)
        self.assertAlmostEqual(sum(amount for _employer, _cohort, amount in rows), 10.0)

    def test_a_holder_with_enough_pays_every_row_in_full(self):
        rows = payable_keep([("works", "cohort:a", 3.0), ("works", "cohort:b", 4.0)], {"works": 10.0}.get)
        self.assertEqual(rows, [("works", "cohort:a", 3.0), ("works", "cohort:b", 4.0)])

    def test_a_holder_with_nothing_pays_nothing(self):
        self.assertEqual(payable_keep([("works", "cohort:a", 3.0)], {"works": -1e-13}.get), [])


if __name__ == "__main__":
    unittest.main()
