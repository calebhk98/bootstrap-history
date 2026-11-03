"""payroll.share_out: when a payment is refused, the earlier payees give their money back by direct postings and the
draw made for the batch is given back once."""

QUICK_TOPIC = True

import unittest

from sim.agents import payroll
from sim.book import InsufficientFunds


class StandInPayments:
    def __init__(self, notes):
        self.notes = notes

    def note_outlay(self, purpose, amount):
        self.notes.append(("outlay", amount))

    def note_income(self, purpose, amount):
        self.notes.append(("income", amount))


class StandInPurses:
    """A purse book that records its calls and refuses the payment to `refused_payee`."""

    def __init__(self, refused_payee):
        self.refused_payee = refused_payee
        self.calls = []

    def cover(self, payer, amount):
        self.calls.append(("cover", payer, amount))
        return lambda: self.calls.append(("give_back", payer))

    def transfer(self, payer, payee, amount, purpose):
        if payee == self.refused_payee:
            raise InsufficientFunds("refused")
        self.calls.append(("transfer", payer, payee, amount))

    def reverse(self, payee, payer, amount, purpose):
        self.calls.append(("reverse", payee, payer, amount))


class StandInActor:
    def __init__(self, purses, account_id):
        self.purses = purses
        self.account_id = account_id
        self.notes = []
        self.payments = StandInPayments(self.notes)


class ShareOutUndo(unittest.TestCase):
    def test_a_refused_payment_reverses_earlier_payees_directly_and_gives_the_draw_back_once(self):
        purses = StandInPurses("payee:third")
        payer = StandInActor(purses, "payer")
        payees = [StandInActor(purses, "payee:first"), StandInActor(purses, "payee:second"), StandInActor(purses, "payee:third")]
        with self.assertRaises(InsufficientFunds):
            payroll.share_out(payer, payees, [1.0, 1.0, 1.0], 30.0, "wages")
        self.assertEqual(purses.calls, [
            ("cover", "payer", 30.0),
            ("transfer", "payer", "payee:first", 10.0),
            ("transfer", "payer", "payee:second", 10.0),
            ("reverse", "payee:second", "payer", 10.0),
            ("reverse", "payee:first", "payer", 10.0),
            ("give_back", "payer"),
        ])
        self.assertEqual(sum(amount for kind, amount in payer.notes if kind == "outlay"), 0.0)


if __name__ == "__main__":
    unittest.main()
