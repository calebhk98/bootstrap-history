"""`state_owes`: what the state owes is its claims in the actors' book plus the pay it has not paid, rounded to a tenth.
Called on a stand-in game carrying the treasury and the purses it reads."""

QUICK_TOPIC = True

from types import SimpleNamespace
import unittest

from sim.engine.economy_capital_market import CapitalMarketMixin


def game(debt, arrears):
    treasury = SimpleNamespace(actor_id="state", arrears_owed=lambda: arrears)
    purses = SimpleNamespace(debt=lambda actor_id: debt if actor_id == "state" else 0.0)
    return SimpleNamespace(state_treasury=lambda: treasury, actors=SimpleNamespace(state=SimpleNamespace(purses=purses)))


class StateOwes(unittest.TestCase):
    def test_it_is_the_book_debt_plus_the_unpaid_pay_to_a_tenth(self):
        self.assertEqual(CapitalMarketMixin.state_owes(game(debt=100.04, arrears=50.03)), 150.1)

    def test_unpaid_pay_alone_is_owed(self):
        self.assertEqual(CapitalMarketMixin.state_owes(game(debt=0.0, arrears=600.0)), 600.0)


if __name__ == "__main__":
    unittest.main()
