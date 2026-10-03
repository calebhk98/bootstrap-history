"""A sticky rate creeping up toward lenders' lowest ask must not freeze lending: when every lender asks
more than last year's rate but borrowers would pay that ask, the rate lifts to it and loans are made."""
import unittest

from sim.economy import credit
from sim.economy.types import FundsOffer, LoanRequest


class CreditFloorTests(unittest.TestCase):
    def test_a_rate_just_below_every_ask_still_lends_to_borrowers_who_would_pay_it(self):
        requests = [LoanRequest("state", "coin", 100.0, 0.15, 10.0, 1e6, "state deficit")]
        offers = [FundsOffer("saver", "coin", 1000.0, 0.05)]
        loans, rate, _unmet = credit.clear(requests, offers, "coin", 0.0496, {})
        self.assertGreaterEqual(rate, 0.05)
        self.assertAlmostEqual(sum(loan.principal for loan in loans), 100.0)

    def test_nobody_lends_when_borrowers_will_not_pay_the_ask(self):
        requests = [LoanRequest("state", "coin", 100.0, 0.04, 10.0, 1e6, "state deficit")]
        offers = [FundsOffer("saver", "coin", 1000.0, 0.05)]
        loans, _rate, _unmet = credit.clear(requests, offers, "coin", 0.0496, {})
        self.assertEqual(loans, [])


if __name__ == "__main__":
    unittest.main()
