"""One registry holds every debt: a facility draw and a term loan are contracts of different kinds in the same
book of debts, so an actor's total, a lender's exposure and a default's loss do not depend on which path made
the contract (Complaint 555)."""

QUICK_TOPIC = True

import unittest

from sim.agents import ledger
from sim.agents.api import ActorRecord, ActorsState
from sim.agents.firm import Firm
from sim.agents.purses import COIN, POOL, Purses
from sim.contracts import DEPOSIT, FACILITY, STATE_DEBT, TERM_LOAN, Contract, Contracts
from sim.economy.accounts import Book
from sim.economy.types import Loan


def actor_in_debt_on_both_paths():
    """A firm with 40 drawn on its facility and a term loan of 100 (arrears 5), in one shared registry."""
    state = ActorsState()
    firm = Firm("firm:a", ActorRecord(kind="firm", money=60.0))
    other = Firm("firm:b", ActorRecord(kind="firm"))
    for actor in (firm, other):
        actor.attach(state.purses)
    ledger.transfer(firm, other, 100.0, "buy")
    registry = Contracts()
    registry.term_loans.append(Loan("loan:1", "lender:x", "firm:a", COIN, 100.0, 0.1, 4.0, 0.0, arrears=5.0))
    state.purses.adopt_book(state.purses.book, registry)
    return state, registry


class OneRegistry(unittest.TestCase):
    def test_a_loan_is_a_contract_of_a_kind(self):
        self.assertEqual(Loan("loan:1", "a", "b", COIN, 1.0, 0.1, 2.0, 0.0).kind, TERM_LOAN)

    def test_an_actor_with_both_kinds_reports_one_total_from_one_query(self):
        state, registry = actor_in_debt_on_both_paths()
        self.assertIs(state.purses.contracts, registry)
        self.assertEqual(registry.debt("firm:a", COIN), 40.0 + 100.0 + 5.0)
        self.assertEqual(state.purses.debt("firm:a"), registry.debt("firm:a", COIN))
        self.assertEqual(registry.facility_of("firm:a"), {POOL: 40.0})

    def test_a_default_books_the_loss_once_on_both_sides(self):
        state, registry = actor_in_debt_on_both_paths()
        debt_before = registry.debt("firm:a", COIN)
        exposure_before = registry.exposure(currency=COIN)
        ended = registry.default("firm:a")
        lost = sum(contract.principal + contract.arrears for contract in ended)
        self.assertEqual(sorted(contract.kind for contract in ended), [FACILITY, TERM_LOAN])
        self.assertEqual(registry.debt("firm:a", COIN), 0.0)
        self.assertAlmostEqual(debt_before - registry.debt("firm:a", COIN), lost)
        self.assertAlmostEqual(exposure_before - registry.exposure(currency=COIN), 100.0 + 40.0)   # arrears are not principal
        self.assertEqual(state.purses.debt("firm:a"), 0.0)
        self.assertEqual(registry.default("firm:a"), [])      # nothing is booked a second time

    def test_a_lenders_exposure_counts_both_kinds(self):
        registry = Contracts()
        registry.draw("firm:a", "lender:x", COIN, 30.0)
        registry.term_loans.append(Loan("loan:1", "lender:x", "firm:b", COIN, 70.0, 0.1, 4.0, 0.0))
        self.assertEqual(registry.exposure("lender:x", COIN), 100.0)
        self.assertEqual(registry.exposure("lender:x", COIN, FACILITY), 30.0)

    def test_state_debt_is_a_kind_of_the_same_registry(self):
        registry = Contracts()
        registry.term_loans.append(Contract("bond:1", "lender:x", "state:a", COIN, 50.0, 0.05, 10.0, kind=STATE_DEBT))
        registry.draw("state:a", "lender:y", COIN, 10.0)
        self.assertEqual(registry.debt("state:a", COIN), 60.0)
        self.assertEqual([c.contract_id for c in registry.default("state:a", STATE_DEBT)], ["bond:1"])
        self.assertEqual(registry.debt("state:a", COIN), 10.0)

    def test_each_owner_saves_its_own_kind_and_a_load_restores_both(self):
        state, registry = actor_in_debt_on_both_paths()
        purse_record = state.purses.to_canon_dict()
        self.assertEqual(sorted(row["kind"] for row in purse_record["facilities"]), [DEPOSIT, FACILITY])
        self.assertEqual([row["kind"] for row in registry.to_records(facilities=False)], [TERM_LOAN])
        restored = Contracts()
        restored.load_records(registry.to_records(facilities=False))
        restored.adopt(Purses.from_record(purse_record).contracts)
        self.assertEqual(restored.debt("firm:a", COIN), registry.debt("firm:a", COIN))

    def test_adopting_the_economys_registry_carries_the_drawn_facilities_over(self):
        state = ActorsState()
        firm = Firm("firm:a", ActorRecord(kind="firm", money=10.0))
        other = Firm("firm:b", ActorRecord(kind="firm"))
        for actor in (firm, other):
            actor.attach(state.purses)
        ledger.transfer(firm, other, 25.0, "buy")
        registry = Contracts()
        state.purses.adopt_book(Book(), registry)
        self.assertIs(state.purses.contracts, registry)
        self.assertEqual(registry.debt("firm:a", COIN), 15.0)

if __name__ == "__main__":
    unittest.main()
