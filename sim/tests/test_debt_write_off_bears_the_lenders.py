"""A debt forgiven (a seat household's settlement, bondage or seizure) is a default like an actor's: the claim is dropped and
the pool's lenders bear the loss; no edge pays it and no money appears. Called on `Contracts`, `Purses` and the ledger command."""

QUICK_TOPIC = True

import unittest

from sim.agents.purses import COIN, EDGE_OUTSIDE, POOL, Purses
from sim.contracts import Contracts
from sim.ledger.api import WriteOffHouseholdDebt

from .pool_lenders import lend_through, value
from .test_ledger_commands import seat_ledger


class ForgiveFacility(unittest.TestCase):
    def test_the_facility_principal_falls_by_the_amount_and_the_amount_is_answered(self):
        contracts = Contracts()
        contracts.draw("firm:1", POOL, COIN, 100.0)
        self.assertAlmostEqual(contracts.forgive_facility("firm:1", 30.0), 30.0)
        self.assertAlmostEqual(contracts.debt("firm:1", COIN), 70.0)

    def test_no_more_than_the_debt_is_forgiven(self):
        contracts = Contracts()
        contracts.draw("firm:1", POOL, COIN, 10.0)
        self.assertAlmostEqual(contracts.forgive_facility("firm:1", 30.0), 10.0)
        self.assertEqual(contracts.facility_of("firm:1"), {})


class PartialWriteOff(unittest.TestCase):
    def indebted(self):
        purses = Purses()
        lend_through(purses, {"cohort:a": (500.0, 0.05)}, coin_per_unit=1.0)
        purses.transfer("firm:1", EDGE_OUTSIDE, 100.0, "spend")   # drawn on credit
        return purses

    def test_a_partial_write_off_lowers_the_debt_by_the_amount_and_the_lenders_lose_it(self):
        purses = self.indebted()
        told = []
        purses.unit_observer = lambda account, signed, label: told.append((account, signed))
        lost = purses.write_off("firm:1", 40.0)
        self.assertAlmostEqual(purses.debt("firm:1"), 60.0)
        self.assertAlmostEqual(lost[POOL], 40.0)
        self.assertAlmostEqual(sum(signed for _account, signed in told), -40.0)

    def test_a_write_off_moves_no_money(self):
        purses = self.indebted()
        before = value(purses, 1.0)
        purses.write_off("firm:1", 40.0)
        self.assertAlmostEqual(value(purses, 1.0), before)


class WriteOffHouseholdDebtCommand(unittest.TestCase):
    def test_the_household_debt_falls_and_the_lenders_not_an_edge_bear_it(self):
        module, registry, _treasury = seat_ledger(0.0)
        purses = registry.state.purses
        lend_through(purses, {"cohort:a": (1000.0, 0.05)}, coin_per_unit=1.0)
        purses.set_net("founder", -300.0, "set")
        edge = registry.state.edge("edge:creditors")
        module.write_off_household_debt(WriteOffHouseholdDebt(250.0, "debts written off in settlement"))
        self.assertAlmostEqual(module.acting_balance(), -50.0)
        self.assertEqual(edge.balance(), 0.0)
        self.assertAlmostEqual(module.seat.cash_flow["debts written off in settlement"], 250.0)

    def test_a_household_out_of_debt_forgives_nothing(self):
        module, _registry, _treasury = seat_ledger(80.0)
        module.write_off_household_debt(WriteOffHouseholdDebt(250.0, "debts written off in settlement"))
        self.assertAlmostEqual(module.acting_balance(), 80.0)


if __name__ == "__main__":
    unittest.main()
