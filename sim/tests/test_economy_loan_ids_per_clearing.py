"""The working-capital clearing at the start of a year and the previous year's ordinary clearing carry the same year, and
both loans fall due together: their ids must differ, or a default forecloses another loan's collateral and two loans
merge into one ask on the secondary market."""

QUICK_TOPIC = True

import unittest

from sim.economy import credit
from sim.economy.types import FundsOffer, LoanRequest


def asked(borrower):
    return LoanRequest(borrower, "coin", 100.0, 0.5, 1.0, 500.0, "working capital")


class LoanIdsPerClearing(unittest.TestCase):
    def test_two_clearings_of_one_year_give_different_ids(self):
        offers = [FundsOffer("lender", "coin", 1000.0, 0.05)]
        ordinary, _rate, _unmet = credit.clear([asked("a")], offers, "coin", 0.05, {}, year=4)
        working, _rate, _unmet = credit.clear([asked("b")], offers, "coin", 0.05, {}, year=4, clearing="working_capital")
        self.assertNotEqual(ordinary[0].loan_id, working[0].loan_id)


if __name__ == "__main__":
    unittest.main()
