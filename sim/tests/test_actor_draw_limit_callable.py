"""The callable the purses draw through: `Credit.limit(account, amount)` is the borrower's own `rule_limit`, and the whole
draw for an account no borrower stands behind (an edge, a seat's household)."""
QUICK_TOPIC = True

import contextlib
import types
import unittest

from sim.actors.world_credit import Credit
from sim.book import InsufficientFunds


class Limit(unittest.TestCase):
    def credit(self, balance=0.0, line=50.0):
        borrower = types.SimpleNamespace(rule_limit=lambda world, amount: min(amount, 5.0))
        needs = types.SimpleNamespace(seat_list=lambda: {"households": ["seat:a"]}, act_as=lambda seat_id: contextlib.nullcontext(),
                                      acting_balance=lambda: balance, credit_limit=lambda: line)
        return Credit(types.SimpleNamespace(registry=types.SimpleNamespace(actors={"firm:1": borrower}), needs=needs))

    def test_a_seat_household_is_limited_to_its_credit_line_less_what_it_owes(self):
        self.assertEqual(self.credit(balance=-20.0, line=50.0).limit("seat:a", 100.0), 30.0)

    def test_a_seat_household_within_its_line_may_draw_all_it_asks(self):
        self.assertEqual(self.credit(balance=10.0, line=50.0).limit("seat:a", 12.0), 12.0)

    def test_a_seat_household_at_or_past_its_line_may_draw_nothing(self):
        self.assertEqual(self.credit(balance=-60.0, line=50.0).limit("seat:a", 5.0), 0.0)

    def test_a_borrowers_account_is_limited_by_its_own_rule_limit(self):
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

    def test_interest_the_lenders_refuse_is_not_paid_and_left_for_the_caller_to_carry(self):
        payer = self.payer(True)
        self.assertEqual(Credit(None).pay_interest(payer, 6.0), 0.0)
        self.assertEqual(payer.arrears_book.interest_arrears, 2.0)

    def test_interest_paid_is_answered(self):
        self.assertEqual(Credit(None).pay_interest(self.payer(False), 6.0), 6.0)


if __name__ == "__main__":
    unittest.main()
