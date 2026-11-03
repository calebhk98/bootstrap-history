"""The callable the purses draw through: `Credit.limit(account, amount)` is the borrower's own `draw_limit`, and the whole
draw for an account no borrower stands behind (an edge, a seat's household)."""
QUICK_TOPIC = True

import types
import unittest

from sim.actors.world_credit import Credit
from sim.book import InsufficientFunds


class Limit(unittest.TestCase):
    def credit(self):
        borrower = types.SimpleNamespace(draw_limit=lambda world, amount: min(amount, 5.0))
        return Credit(types.SimpleNamespace(registry=types.SimpleNamespace(actors={"firm:1": borrower})))

    def test_a_borrowers_account_is_limited_by_its_own_draw_limit(self):
        self.assertEqual(self.credit().limit("firm:1", 9.0), 5.0)

    def test_an_account_no_borrower_stands_behind_is_not_limited(self):
        self.assertEqual(self.credit().limit("edge:exchange", 9.0), 9.0)


class PayInterest(unittest.TestCase):
    def payer(self, refuse):
        def pay(account, owed):
            if refuse:
                raise InsufficientFunds("lenders refuse")
            return {"pool:credit": owed}
        return types.SimpleNamespace(account_id="firm:1", purses=types.SimpleNamespace(pay_interest=pay),
                                     arrears_book=types.SimpleNamespace(interest_arrears=2.0),
                                     payments=types.SimpleNamespace(note_outlay=lambda purpose, amount: None))

    def test_interest_the_lenders_refuse_is_carried_as_arrears_and_not_paid(self):
        payer = self.payer(True)
        self.assertEqual(Credit(None).pay_interest(payer, 6.0), 0.0)
        self.assertEqual(payer.arrears_book.interest_arrears, 8.0)

    def test_interest_paid_is_answered(self):
        self.assertEqual(Credit(None).pay_interest(self.payer(False), 6.0), 6.0)


if __name__ == "__main__":
    unittest.main()
