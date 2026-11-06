"""Interest arrears are paid from the purse and the deposit the actor holds, and the amount that reached the pool is what
the arrears fall by: nothing is cleared that was not paid. Called on a `Purses` and a firm built here."""

QUICK_TOPIC = True

import unittest

from sim.agents.api import ActorRecord, ActorsState
from sim.agents.firm import Firm
from sim.agents.purses import COIN, EDGE_OUTSIDE, POOL
from sim.book import Transfer

from .agents_fake_world import FakeWorld
from .pool_lenders import lend_from_savers


def depositor(purses, account, purse, deposit):
    purses.book.transfer(Transfer(EDGE_OUTSIDE, account, COIN, purse + deposit, "seed"))
    purses.book.transfer(Transfer(EDGE_OUTSIDE, POOL, COIN, deposit, "seed"))   # the pool holds what the deposit will be taken back from
    purses.contracts.deposit(account, POOL, COIN, deposit)
    purses.book.transfer(Transfer(account, EDGE_OUTSIDE, COIN, deposit, "seed"))


class ArrearsFromDeposit(unittest.TestCase):
    def test_purses_pay_arrears_takes_the_deposit_back_when_the_purse_is_short(self):
        state = ActorsState()
        lend_from_savers(state.purses, 1e9)
        depositor(state.purses, "firm:1", purse=2.0, deposit=10.0)
        paid = state.purses.pay_arrears("firm:1", 6.0)
        self.assertAlmostEqual(paid, 6.0)
        self.assertAlmostEqual(state.purses.interest_pending, 6.0)

    def test_purses_pay_arrears_pays_no_more_than_purse_and_deposit_together(self):
        state = ActorsState()
        lend_from_savers(state.purses, 1e9)
        depositor(state.purses, "firm:1", purse=2.0, deposit=3.0)
        self.assertAlmostEqual(state.purses.pay_arrears("firm:1", 100.0), 5.0)

    def test_the_arrears_fall_by_what_was_paid(self):
        state = ActorsState()
        world = FakeWorld()
        world.edge_book = state
        lend_from_savers(state.purses, 1e9)
        firm = Firm("firm:1", ActorRecord(kind="firm", founded_year=100))
        firm.attach(state.purses)
        depositor(state.purses, "firm:1", purse=0.0, deposit=10.0)
        firm.record.interest_arrears = 6.0
        firm.pay_arrears_from_purse()
        self.assertAlmostEqual(firm.record.interest_arrears, 0.0)
        self.assertAlmostEqual(state.purses.interest_pending, 6.0)


if __name__ == "__main__":
    unittest.main()
