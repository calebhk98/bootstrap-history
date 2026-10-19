"""Lenders pool: a small firm's spare cash earns interest again, a borrower holds one claim whatever the number of
lenders, a default's loss is shared among the depositors once, and a year's contracts and postings grow with
borrowers plus lenders, not their product (Complaint 580)."""

QUICK_TOPIC = True

import unittest

from sim.agents.api import ActorRecord, ActorsState
from sim.agents.firm import Firm
from sim.agents.purses import COIN, EDGE_SAVERS, POOL, Purses


def market(lender_count, borrower_count, cash=100.0, savers=1e6):
    """Firms that offer their cash, firms that borrow, and the savers; the offers are set."""
    state = ActorsState()
    purses = state.purses
    lenders = [Firm("firm:lender%d" % index, ActorRecord(kind="firm", money=cash)) for index in range(lender_count)]
    borrowers = [Firm("firm:borrower%d" % index, ActorRecord(kind="firm")) for index in range(borrower_count)]
    for actor in lenders + borrowers:
        actor.attach(purses)
    purses.set_offers({EDGE_SAVERS: savers, **{lender.account_id: cash for lender in lenders}})
    return state, lenders, borrowers


def counting_postings(purses):
    calls = []
    original = purses.book.transfer
    purses.book.transfer = lambda posting: (calls.append(posting), original(posting))[1]
    return calls


class PooledLending(unittest.TestCase):
    def test_a_small_firms_spare_cash_earns_interest_again(self):
        state, lenders, borrowers = market(lender_count=300, borrower_count=1, savers=1e9)
        purses = state.purses
        small = lenders[0].account_id
        self.assertGreater(purses.deposit(small), 0.0)
        purses.cover(borrowers[0].account_id, 500.0)
        received = purses.pay_interest(borrowers[0].account_id, 50.0)
        self.assertEqual(list(received), [POOL])
        paid = purses.settle_interest()
        self.assertGreater(paid[small], 0.0)
        self.assertAlmostEqual(sum(paid.values()), 50.0)

    def test_a_borrower_holds_one_claim_whatever_the_number_of_lenders(self):
        for lender_count in (3, 30, 120):
            state, _lenders, borrowers = market(lender_count, 1)
            state.purses.cover(borrowers[0].account_id, 250.0)
            self.assertEqual(list(state.purses.contracts.facility_of(borrowers[0].account_id)), [POOL], lender_count)
            self.assertAlmostEqual(state.purses.debt(borrowers[0].account_id), 250.0)

    def test_a_lender_holds_one_deposit_not_a_claim_per_borrower(self):
        state, lenders, borrowers = market(2, 20)
        for borrower in borrowers:
            state.purses.cover(borrower.account_id, 5.0)
        deposits = state.purses.contracts.deposits
        self.assertEqual(sorted(deposits), sorted(lender.account_id for lender in lenders))
        self.assertEqual(sum(len(held) for held in state.purses.contracts.facilities.values()), len(borrowers))

    def test_a_default_books_the_loss_once_and_shares_it_among_the_depositors(self):
        state, lenders, borrowers = market(2, 1, savers=0.0)
        purses = state.purses
        purses.set_offers({lenders[0].account_id: 100.0, lenders[1].account_id: 100.0})
        purses.cover(borrowers[0].account_id, 100.0)
        before = [purses.deposit(lender.account_id) for lender in lenders]
        self.assertEqual(purses.write_off(borrowers[0].account_id), {POOL: 100.0})
        after = [purses.deposit(lender.account_id) for lender in lenders]
        self.assertAlmostEqual(before[0] - after[0], 50.0)
        self.assertAlmostEqual(before[1] - after[1], 50.0)
        self.assertEqual(purses.write_off(borrowers[0].account_id), {})      # nothing is booked a second time
        self.assertAlmostEqual(purses.deposit(lenders[0].account_id), 50.0)

    def test_the_pool_is_whole_after_a_default(self):
        state, lenders, borrowers = market(3, 2, savers=0.0)
        purses = state.purses
        purses.cover(borrowers[0].account_id, 150.0)
        purses.cover(borrowers[1].account_id, 60.0)
        purses.write_off(borrowers[0].account_id)
        claims = purses.contracts.total_deposits()
        assets = purses.purse(POOL) + purses.lent() - purses.contracts.exposure(None, COIN, "term_loan")
        self.assertAlmostEqual(claims, assets)

    def test_a_deposit_is_taken_back_before_a_facility_is_drawn(self):
        state, lenders, _borrowers = market(1, 0)
        purses = state.purses
        lender = lenders[0].account_id
        purses.cover(lender, 40.0)
        self.assertEqual(purses.contracts.facility_of(lender), {})
        self.assertAlmostEqual(purses.purse(lender), 40.0)
        self.assertAlmostEqual(purses.net(lender), 100.0)

    def test_postings_and_contracts_grow_with_borrowers_plus_lenders(self):
        counts = {}
        for lender_count, borrower_count in ((10, 10), (40, 40), (80, 80)):
            state, _lenders, borrowers = market(lender_count, borrower_count)
            purses = state.purses
            postings = counting_postings(purses)
            for borrower in borrowers:
                purses.cover(borrower.account_id, 20.0)
                purses.pay_interest(borrower.account_id, 2.0)
            purses.settle_interest()
            contracts = len(list(purses.contracts.all()))
            counts[lender_count] = (len(postings), contracts)
            self.assertLessEqual(len(postings), 6 * (lender_count + borrower_count))
            self.assertLessEqual(contracts, lender_count + borrower_count + 1)
        self.assertLess(counts[80][0] / counts[10][0], 12)   # a product would be 64 times more

    def test_the_book_round_trips(self):
        state, _lenders, borrowers = market(3, 2)
        state.purses.cover(borrowers[0].account_id, 30.0)
        state.purses.pay_interest(borrowers[0].account_id, 3.0)
        again = Purses.from_record(state.purses.to_canon_dict())
        self.assertEqual(again.contracts.to_records(facilities=True), state.purses.contracts.to_records(facilities=True))
        self.assertEqual(again.interest_pending, state.purses.interest_pending)


if __name__ == "__main__":
    unittest.main()
