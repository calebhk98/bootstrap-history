"""The compatibility facade (ForwardingPropertiesMixin) keeps no storage of its own: the purse it names is the ledger's view and
command, so a write through either path is seen through the other."""
QUICK_TOPIC = True

import unittest

from sim.engine.core_properties import ForwardingPropertiesMixin
from sim.tests.money_host import MoneyHost


class _Facade(ForwardingPropertiesMixin):
    def __init__(self):
        self.money = MoneyHost(capital=1000.0)
        self.state, self.view, self.send = self.money.state, self.money.view, self.money.send


class Facade(unittest.TestCase):
    def test_a_write_through_the_facade_lands_in_the_seats_account(self):
        facade = _Facade()
        facade.capital = 1250.0
        self.assertEqual(facade.money.purses.net("founder"), 1250.0)

    def test_a_write_to_the_account_is_read_back_through_the_facade(self):
        facade = _Facade()
        facade.money.purses.set_net("founder", 1250.0, "test")
        self.assertEqual(facade.capital, 1250.0)


if __name__ == "__main__":
    unittest.main()
