"""`state_owes`: what the state owes is its claims in the actors' book plus the pay it has not paid, rounded to a tenth.
Called on the finance module with the treasury and the purses it reads given as plain values."""

QUICK_TOPIC = True

from types import SimpleNamespace
import unittest

from sim.finance.module import Finance
from sim.tests import module_harness


def module(debt, arrears):
    treasury = SimpleNamespace(actor_id="state", arrears_owed=lambda: arrears)
    purses = SimpleNamespace(debt=lambda actor_id: debt if actor_id == "state" else 0.0)
    return module_harness.build(Finance, views={"state_treasury": treasury, "debt_owed": purses.debt})


class StateOwes(unittest.TestCase):
    def test_it_is_the_book_debt_plus_the_unpaid_pay_to_a_tenth(self):
        self.assertEqual(module(debt=100.04, arrears=50.03).state_owes(), 150.1)

    def test_unpaid_pay_alone_is_owed(self):
        self.assertEqual(module(debt=0.0, arrears=600.0).state_owes(), 600.0)


if __name__ == "__main__":
    unittest.main()
