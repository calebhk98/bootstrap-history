"""Money paid outside the markets (tenant rent, keep of bonded people, a steward's pay) reaches the year's ledger,
which the households close their year on. Each test calls one ledger method with written-out postings."""

QUICK_TOPIC = True

import unittest

from sim.economy.types import Transfer
from sim.economy.year_ledger import YearLedger


class PaidOutsideMarketsTests(unittest.TestCase):
    def test_the_payer_spent_what_it_paid_and_the_payee_earned_no_wage(self):
        ledger = YearLedger()
        ledger.note_paid_outside_markets([Transfer("tenant", "lessor", "gold", 7.0, "tenant_rent"),
                                          Transfer("tenant", "lessor", "gold", 3.0, "tenant_rent")])
        self.assertEqual(ledger.money_out, {"tenant": 10.0})
        self.assertEqual(ledger.wages_in, {})

    def test_a_steward_paid_outside_the_market_earned_a_wage_the_payer_spent(self):
        ledger = YearLedger()
        ledger.note_wages_outside_markets(iter([Transfer("tenant", "steward", "gold", 4.0, "steward_pay")]))
        self.assertEqual(ledger.money_out, {"tenant": 4.0})
        self.assertEqual(ledger.wages_in, {"steward": 4.0})


if __name__ == "__main__":
    unittest.main()
