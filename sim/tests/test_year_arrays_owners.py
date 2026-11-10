"""`year_arrays_owners` gives per producer row what the per-producer loops it replaced gave."""
QUICK_TOPIC = True

import types
import unittest

import numpy as np

from sim.economy.year_arrays_owners import debts_by_row, eligible_owners


def columns_of(ids, owner_names, owner_number):
    names = types.SimpleNamespace(name_list=owner_names)
    return types.SimpleNamespace(ids=tuple(ids), row={name: row for row, name in enumerate(ids)}, owner_number=np.array(owner_number, dtype=np.int64),
                                 store=types.SimpleNamespace(names={"owners": names}))


class EligibleOwnersTests(unittest.TestCase):
    def test_a_producer_is_eligible_when_its_owner_is_a_cohort(self):
        columns = columns_of(["p0", "p1", "p2", "p3"], ["household:a", "state", "household:b"], [0, 1, 2, 0])
        found = eligible_owners(columns, {"household:a", "household:b"})
        self.assertEqual(found.tolist(), [True, False, True, True])
        self.assertEqual(found.dtype, np.bool_)

    def test_no_producers_have_no_rows(self):
        self.assertEqual(eligible_owners(columns_of([], ["x"], []), {"x"}).tolist(), [])


class DebtsByRowTests(unittest.TestCase):
    def test_a_borrower_has_its_debt_and_the_others_owe_nothing(self):
        columns = columns_of(["p0", "p1", "p2"], [], [])
        found = debts_by_row(columns, {"p2": 7.5, "p0": 1.25, "not_a_producer": 3.0})
        self.assertEqual(found.tolist(), [1.25, 0.0, 7.5])
        self.assertEqual(found.dtype, np.float64)


if __name__ == "__main__":
    unittest.main()
