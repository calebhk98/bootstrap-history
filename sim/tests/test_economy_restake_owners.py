"""An owner puts cash back into a producer only when a run pays after the plant's wear, the test a newcomer and an expansion
face (`unit_cost.return_after_recovery`), not on the gross return that ignores the wear. `restake_owners` is called on a
record written out here."""
QUICK_TOPIC = True

import types
import unittest

from sim.economy.entry_year import restake_owners
from sim.tests.test_economy_producers import View, farmer
from sim.tests.test_economy_unit_cost import PRICES, SMELT, WAGES


class Book:
    def __init__(self, balances):
        self.balances, self.transfers = balances, []

    def balance(self, agent, currency):
        return self.balances.get(agent, 0.0)

    def transfer(self, transfer):
        self.transfers.append(transfer)


def restaked(metal_price):
    """The transfers the owner makes to a smelter short of 100 in cash when a rate of five in a hundred is asked."""
    producer = farmer(recipe_id="smelt", owner="lord", cash_target=100.0)
    record = types.SimpleNamespace(producers={"f1": producer}, book=Book({"lord": 1000.0}))
    setup = types.SimpleNamespace(currency_id="coin", recipes={"smelt": SMELT})
    view = View({**PRICES, "metal": metal_price}, WAGES, rate=0.05)
    restake_owners(setup, record, view)
    return record.book.transfers


class RestakeOwners(unittest.TestCase):
    def test_a_run_that_pays_after_the_plants_wear_is_restaked(self):
        self.assertEqual([each.payee for each in restaked(8.0)], ["f1"])

    def test_a_run_that_pays_only_before_the_plants_wear_is_not(self):
        self.assertEqual(restaked(5.0), [])      # return on capital 0.054 beats 0.05, after recovery 0.028 does not


if __name__ == "__main__":
    unittest.main()
