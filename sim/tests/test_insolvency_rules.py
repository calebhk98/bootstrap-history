"""Insolvency rules: what a write-off leaves owed, and when and in what order a default acts."""

QUICK_TOPIC = True

import unittest

from sim.engine.credit_freeze import settlement_owed
from sim.engine.economy_credit import CreditMixin


class SettlementOwed(unittest.TestCase):

    def test_a_share_of_the_line_that_stands_after_the_name_is_marked_down_is_left_owed(self):
        self.assertAlmostEqual(settlement_owed(1000.0, 800.0, 0.35), 280.0)

    def test_a_line_that_grew_never_raises_what_is_owed_past_the_line_the_debtor_had(self):
        self.assertAlmostEqual(settlement_owed(1000.0, 1500.0, 0.35), 350.0)

    def test_what_is_left_owed_is_inside_the_line_for_any_retained_fraction_below_one(self):
        for fraction in (0.0, 0.35, 0.99):
            self.assertLessEqual(settlement_owed(1000.0, 800.0, fraction), 800.0)


class StubDebtor(CreditMixin):
    """The real default rule over a purse and a line, with its answers recorded in order."""

    def __init__(self, capital, limit, bondage):
        self.calls = []
        self._limit = limit
        self._bondage = bondage
        self.state = type("State", (), {})()
        self.state.household = type("Household", (), {"capital": capital})()

    def answer_exhausted_credit(self, year):
        self.calls.append("answer")

    def credit_limit(self, _rev=None, _upkeep=None, _capital=None):
        return self._limit

    def enter_debt_bondage(self, year):
        self.calls.append("bondage")
        return self._bondage

    def settle_insolvency(self, year, limit):
        self.calls.append(("settle", limit))


class DefaultOnDebt(unittest.TestCase):

    def test_a_purse_inside_the_line_only_answers_exhausted_credit(self):
        debtor = StubDebtor(capital=-400.0, limit=1000.0, bondage=False)
        debtor.default_on_debt(100)
        self.assertEqual(debtor.calls, ["answer"])

    def test_a_purse_past_the_line_with_no_bondage_settles_at_the_line(self):
        debtor = StubDebtor(capital=-2000.0, limit=1000.0, bondage=False)
        debtor.default_on_debt(100)
        self.assertEqual(debtor.calls, ["answer", "bondage", ("settle", 1000.0)])

    def test_a_default_that_enters_bondage_does_not_also_settle(self):
        debtor = StubDebtor(capital=-2000.0, limit=1000.0, bondage=True)
        debtor.default_on_debt(100)
        self.assertEqual(debtor.calls, ["answer", "bondage"])


if __name__ == "__main__":
    unittest.main()
