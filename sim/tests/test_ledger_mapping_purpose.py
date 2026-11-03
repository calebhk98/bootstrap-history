"""A payment named by a mapping of label to amount books each part as paid: a transfer of less than the mapping's total books the
parts in proportion."""

QUICK_TOPIC = True

import unittest

from sim.agents import ledger


class Party:
    def __init__(self):
        self.income, self.outlay = {}, {}
        self.payments = self

    def note_income(self, purpose, amount):
        for name, part in ledger.parts(purpose, amount).items():
            self.income[name] = self.income.get(name, 0.0) + part

    def note_outlay(self, purpose, amount):
        for name, part in ledger.parts(purpose, amount).items():
            self.outlay[name] = self.outlay.get(name, 0.0) + part

    def debit(self, amount, purpose):
        self.note_outlay(purpose, amount)

    def credit(self, amount, purpose):
        self.note_income(purpose, amount)


class Transfer(unittest.TestCase):
    def test_a_full_payment_books_each_part_as_named(self):
        payer, payee = Party(), Party()
        ledger.transfer(payer, payee, 10.0, {"tax": 6.0, "tithe": 4.0})
        self.assertEqual(payee.income, {"tax": 6.0, "tithe": 4.0})

    def test_a_smaller_payment_books_the_parts_in_proportion(self):
        payer, payee = Party(), Party()
        ledger.transfer(payer, payee, 5.0, {"tax": 6.0, "tithe": 4.0})
        self.assertAlmostEqual(payee.income["tax"], 3.0)
        self.assertAlmostEqual(payer.outlay["tithe"], 2.0)

    def test_a_single_label_is_booked_whole(self):
        payer, payee = Party(), Party()
        ledger.transfer(payer, payee, 5.0, "tax")
        self.assertEqual(payee.income, {"tax": 5.0})


if __name__ == "__main__":
    unittest.main()
