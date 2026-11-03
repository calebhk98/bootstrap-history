"""The economy's lenders and the actors' pool: a lender's capacity is what it holds after its reserve and this year's loans, its
deposit in the pool is its asset, the interest the pool pays it is property income and a default's loss is its credit loss."""

QUICK_TOPIC = True

import types
import unittest

from sim.book import Book, Transfer
from sim.contracts import Contracts
from sim.economy import api as economy_api, banks, credit_lines, pool_deposits
from sim.economy.capital_markets_record import CapitalMarketsRecord
from sim.economy.credit_record import CreditRecord
from sim.economy.credit_view import CreditView
from sim.economy.market_memory import MarketMemory
from sim.world import capital_market


def record_with(offered, asks, lent=None, bank_ids=(), cohort_ids=("cohort:a",), balances=None):
    book = Book()
    for agent, amount in (balances or {}).items():
        book.transfer(Transfer("edge:legacy", agent, "coin", amount, "seed"))
    credit = CreditRecord()
    credit.offered_by_lender, credit.ask_by_lender, credit.lent_by_lender = dict(offered), dict(asks), dict(lent or {})
    markets = CapitalMarketsRecord()
    for bank_id in bank_ids:
        markets.banks[bank_id] = banks.Bank(bank_id, "cohort:a", 0)
    return types.SimpleNamespace(credit=credit, capital_markets=markets, book=book, cohorts={each: None for each in cohort_ids})


class LenderCapacity(unittest.TestCase):
    def test_a_cohorts_capacity_is_its_offer_after_the_reserve_less_what_the_years_loans_took(self):
        record = record_with({"cohort:a": 100.0}, {"cohort:a": 0.05}, lent={"cohort:a": 30.0}, balances={"cohort:a": 100.0})
        [standing] = credit_lines.lender_standings(record, "coin")
        self.assertAlmostEqual(standing.capacity, capital_market.lendable_capacity(100.0) - 30.0)
        self.assertEqual(standing.offer, 100.0)     # the full offer stays whole beside the capacity

    def test_a_banks_capacity_is_the_cash_it_holds_beyond_its_reserve_not_what_depositors_pledged(self):
        # the bank offered 500 (its own free cash and the reserve-cut pledges), but holds 60 and owes its depositors nothing yet
        record = record_with({"bank:0": 500.0}, {"bank:0": 0.06}, bank_ids=("bank:0",), cohort_ids=(), balances={"bank:0": 60.0})
        [standing] = credit_lines.lender_standings(record, "coin")
        self.assertEqual((standing.kind, standing.capacity, standing.offer), ("bank", 60.0, 500.0))

    def test_a_capacity_is_never_below_nothing(self):
        record = record_with({"cohort:a": 10.0}, {"cohort:a": 0.05}, lent={"cohort:a": 50.0}, balances={"cohort:a": 10.0})
        [standing] = credit_lines.lender_standings(record, "coin")
        self.assertEqual(standing.capacity, 0.0)

    def test_the_cheapest_ask_is_listed_first(self):
        record = record_with({"cohort:a": 10.0, "cohort:b": 10.0}, {"cohort:a": 0.09, "cohort:b": 0.04}, cohort_ids=("cohort:a", "cohort:b"))
        self.assertEqual([each.lender for each in credit_lines.lender_standings(record, "coin")], ["cohort:b", "cohort:a"])


class LendingOpensAndCounts(unittest.TestCase):
    def test_a_loan_struck_counts_against_its_lender_and_a_new_lending_starts_the_count_again(self):
        credit = CreditRecord()
        credit.note_lent(types.SimpleNamespace(borrower="firm", lender="cohort:a", principal=40.0))
        self.assertEqual(credit.lent_by_lender, {"cohort:a": 40.0})
        credit.open_lending([], "coin")
        self.assertEqual(credit.lent_by_lender, {})


class BeforeLendersMeet(unittest.TestCase):
    def test_a_draw_is_bounded_by_what_the_pool_holds_when_the_rule_allows_all_and_no_lender_is_listed(self):
        from sim.agents.purses import POOL, Purses
        purses = Purses()
        purses.limit = lambda account, amount: amount       # an account no borrower stands behind: the rule allows the whole draw
        purses.lenders_for = lambda account, amount: None   # lenders have not met
        purses.book.transfer(Transfer("edge:legacy", POOL, "engine_coin", 30.0, "seed"))
        self.assertEqual(purses.drawable("firm:1", 500.0), 30.0)
        purses.book.transfer(Transfer(POOL, "edge:legacy", "engine_coin", 30.0, "seed"))
        self.assertEqual(purses.drawable("firm:1", 500.0), 0.0)


class PoolDeposits(unittest.TestCase):
    def test_a_banks_assets_include_what_the_pool_owes_it_in_the_economys_unit(self):
        record = record_with({}, {}, bank_ids=("bank:0",), cohort_ids=(), balances={"bank:0": 60.0})
        record.credit.contracts.deposit("bank:0", "pool:credit", "engine_coin", 100.0, unit_value=0.5)   # 100 coin at 2 coin a unit
        self.assertAlmostEqual(banks.assets_of(record, "bank:0", "coin"), 60.0 + 50.0)

    def test_a_cohorts_claims_include_what_the_pool_owes_it(self):
        contracts = Contracts()
        contracts.deposit("cohort:a", "pool:credit", "engine_coin", 100.0, unit_value=0.5)
        view = CreditView(MarketMemory(), None, types.SimpleNamespace(goods=lambda: ()), "coin", None, None, pooled=contracts.deposit_value)
        self.assertAlmostEqual(view.claims("cohort:a", "coin"), 50.0)
        self.assertEqual(view.claims("cohort:b", "coin"), 0.0)

    def test_interest_the_pool_paid_is_taken_once_for_the_close(self):
        record = record_with({}, {})
        pool_deposits.note_pool_posting(record, "cohort:a", 5.0)
        pool_deposits.note_pool_posting(record, "cohort:a", 2.0)
        self.assertEqual(record.capital_markets.take_pool_income(), {"cohort:a": 7.0})
        self.assertEqual(record.capital_markets.last_pool_income, {"cohort:a": 7.0})   # kept for a fund's expected income
        self.assertEqual(record.capital_markets.take_pool_income(), {})

    def test_the_property_income_set_is_what_the_close_gives(self):
        record = record_with({}, {})
        record.capital_markets.set_property_income({"cohort:a": 25.0})
        self.assertEqual(record.capital_markets.property_income, {"cohort:a": 25.0})

    def test_a_loss_of_the_deposit_in_a_default_is_the_lenders_credit_loss(self):
        record = record_with({}, {})
        pool_deposits.note_pool_posting(record, "cohort:a", -7.0)
        self.assertEqual(record.credit.credit_losses, {"cohort:a": 7.0})
        self.assertEqual(record.capital_markets.pool_income, {})

    def test_the_api_door_books_a_pool_posting_on_the_economys_record(self):
        record = record_with({}, {})
        economy_api.note_pool_posting(types.SimpleNamespace(record=record), "cohort:a", -3.0)
        economy_api.note_pool_posting(types.SimpleNamespace(record=record), "cohort:a", 4.0)
        self.assertEqual((record.credit.credit_losses, record.capital_markets.pool_income), ({"cohort:a": 3.0}, {"cohort:a": 4.0}))


if __name__ == "__main__":
    unittest.main()
