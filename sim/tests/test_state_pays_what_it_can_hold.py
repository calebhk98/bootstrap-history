"""A state whose money is a deposit the pool cannot give back pays nothing rather than raising: the patron's grant and the
arrears settlement pay only what the transfer lets through, and a pay line that is refused stays owed. Called on a government
over a `Purses` whose pool is empty and whose lenders hold nothing."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agents.api import ActorRecord, ActorsState
from sim.agents import arrears
from sim.agents.government import Government
from sim.agents.purses import COIN, POOL
from sim.book import InsufficientFunds


def stuck_state():
    """A government that holds 100 as a deposit in a pool with nothing in it: its net position is 100, none of it payable."""
    state = ActorsState()
    government = Government("government:home", ActorRecord(kind="government"))
    government.attach(state.purses)
    state.purses.contracts.deposit(government.account_id, POOL, COIN, 100.0)
    return state, government


class PayPatron(unittest.TestCase):
    def test_a_grant_the_deposit_cannot_fund_is_not_paid_and_does_not_raise(self):
        state, government = stuck_state()
        world = SimpleNamespace(patronage=SimpleNamespace(patron_ask=lambda: 60.0),
                                setting=SimpleNamespace(edge=lambda name: state.edge(name)))
        government.pay_patron(1.0, world)
        self.assertEqual(government.record.patron_grant, 0.0)


class SettleArrears(unittest.TestCase):
    def test_a_line_whose_wages_are_refused_stays_owed(self):
        _state, government = stuck_state()
        government.record.arrears = {"army": 60.0}

        def refuse(payer, amount, purpose):
            raise InsufficientFunds("nothing payable")
        paid = arrears.settle(government, SimpleNamespace(labour=SimpleNamespace(pay_wages=refuse)))
        self.assertEqual(paid, {})
        self.assertEqual(government.record.arrears, {"army": 60.0})


if __name__ == "__main__":
    unittest.main()
