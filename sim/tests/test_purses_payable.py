"""What an account can pay is one answer the draw itself uses: purse, deposit and what the limit and the economy's lenders allow.
A refused payment moves nothing, not even the deposit it took back first; the economy's lenders are told of their interest and loss."""

QUICK_TOPIC = True

import unittest

from sim.agents.purses import COIN, EDGE_OUTSIDE, POOL, Purses
from sim.book import InsufficientFunds, Transfer
from sim.contracts import Contracts

from .pool_lenders import UNIT, lend_through


def purses_with(lenders, held=0.0, coin_per_unit=2.0):
    purses = Purses()
    lend_through(purses, lenders, coin_per_unit)
    if held:
        purses.book.transfer(Transfer(EDGE_OUTSIDE, "firm:1", COIN, held, "seed"))
    return purses


class Payable(unittest.TestCase):
    def test_the_purse_and_what_the_lenders_hold_are_payable(self):
        purses = purses_with({"cohort:a": (10.0, 0.05)}, held=5.0)   # 10 units are 20 coin
        self.assertAlmostEqual(purses.payable("firm:1", 100.0), 25.0)

    def test_with_no_lenders_listed_only_the_purse_is_payable(self):
        purses = Purses()
        purses.book.transfer(Transfer(EDGE_OUTSIDE, "firm:1", COIN, 5.0, "seed"))
        self.assertEqual(purses.payable("firm:1", 100.0), 5.0)

    def test_the_borrowers_limit_cuts_what_is_payable(self):
        purses = purses_with({"cohort:a": (100.0, 0.05)}, held=5.0)
        purses.limit = lambda account, amount: min(amount, 8.0)
        self.assertAlmostEqual(purses.payable("firm:1", 100.0), 13.0)

    def test_an_amount_inside_the_purse_is_wholly_payable(self):
        self.assertEqual(purses_with({}, held=50.0).payable("firm:1", 30.0), 30.0)

    def test_an_edge_is_never_short(self):
        self.assertEqual(Purses().payable(EDGE_OUTSIDE, 1e9), 1e9)

    def test_a_payment_up_to_what_is_payable_is_not_refused(self):
        for held, offered, limit in ((5.0, 10.0, 8.0), (0.0, 3.0, 1000.0), (40.0, 1.0, 2.0)):
            purses = purses_with({"cohort:a": (offered, 0.05)}, held=held)
            purses.limit = lambda account, amount, bound=limit: min(amount, bound)
            affordable = purses.payable("firm:1", 500.0)
            purses.transfer("firm:1", "firm:2", affordable, "test")   # raises InsufficientFunds if the gate lied
            self.assertAlmostEqual(purses.purse("firm:2"), affordable)

    def test_pay_up_to_pays_what_it_can_and_answers_it(self):
        purses = purses_with({"cohort:a": (10.0, 0.05)}, held=5.0)
        paid = purses.pay_up_to("firm:1", "firm:2", 100.0, "test")
        self.assertAlmostEqual(paid, 25.0)
        self.assertAlmostEqual(purses.purse("firm:2"), 25.0)
        self.assertAlmostEqual(purses.debt("firm:1"), 20.0)

    def test_pay_up_to_with_nothing_to_pay_with_pays_nothing_and_does_not_raise(self):
        purses = Purses()
        self.assertEqual(purses.pay_up_to("firm:1", "firm:2", 10.0, "test"), 0.0)


class RefusedPayment(unittest.TestCase):
    maxDiff = None
    def test_a_refused_transfer_leaves_the_book_and_the_contracts_exactly_as_they_were(self):
        purses = purses_with({"cohort:a": (100.0, 0.05)})
        purses.book.transfer(Transfer(EDGE_OUTSIDE, "firm:1", COIN, 30.0, "seed"))
        purses.set_offers({"firm:1": 30.0})   # all of its 30 is a deposit in the pool
        purses.limit = lambda account, amount: 0.0
        book, contracts = purses.book.to_record(), purses.contracts.to_records(facilities=True)
        with self.assertRaises(InsufficientFunds):
            purses.transfer("firm:1", "firm:2", 50.0, "test")   # takes the 30 back, then the 20 it lacks is refused
        self.assertEqual(purses.book.to_record(), book)
        self.assertEqual(purses.contracts.to_records(facilities=True), contracts)
        self.assertAlmostEqual(purses.deposit("firm:1"), 30.0)


class UnitLenders(unittest.TestCase):
    def test_an_economy_lender_is_told_its_interest_in_the_economys_unit(self):
        purses = purses_with({"cohort:a": (100.0, 0.05)})
        told = []
        purses.unit_observer = lambda account, signed, label: told.append((account, signed, label))
        purses.cover("firm:1", 100.0)
        purses.pay_interest("firm:1", 10.0)
        purses.settle_interest()
        self.assertEqual([(account, round(signed, 6)) for account, signed, _ in told], [("cohort:a", 5.0)])   # 10 coin at 2 coin a unit

    def test_an_economy_lender_is_told_its_loss_in_a_default_in_units(self):
        purses = purses_with({"cohort:a": (100.0, 0.05)})
        told = []
        purses.unit_observer = lambda account, signed, label: told.append((account, signed))
        purses.cover("firm:1", 100.0)   # 50 units are in the pool
        purses.write_off("firm:1")
        self.assertEqual([(account, round(signed, 6)) for account, signed in told], [("cohort:a", -50.0)])

    def test_renaming_a_lender_renames_it_among_the_pools_economy_lenders(self):
        purses = purses_with({"cohort:a": (100.0, 0.05)})
        purses.cover("firm:1", 10.0)
        purses.rename_account("cohort:a", "cohort:b")
        self.assertEqual(purses.unit_lenders, {"cohort:b"})


class BookkeepingReset(unittest.TestCase):
    def test_setting_a_net_position_below_zero_takes_nothing_from_the_economys_lenders(self):
        purses = purses_with({"cohort:a": (100.0, 0.05)})
        purses.set_net("firm:1", -50.0, "set")
        self.assertAlmostEqual(purses.book.balance("cohort:a", UNIT), 100.0)
        self.assertAlmostEqual(purses.debt("firm:1"), 50.0)


class SumsDoNotDependOnCreationOrder(unittest.TestCase):
    def test_the_contracts_are_listed_in_the_order_a_load_produces(self):
        contracts = Contracts()
        contracts.draw("firm:b", POOL, COIN, 1.0)
        contracts.draw("firm:a", POOL, COIN, 2.0)
        self.assertEqual([contract.borrower for contract in contracts.all()], ["firm:a", "firm:b"])


if __name__ == "__main__":
    unittest.main()
