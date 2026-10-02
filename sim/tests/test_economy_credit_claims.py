"""Claims as assets: a lender's wealth includes its loans, a default is its loss, households spend from
wealth, and a default's loss moves on to the lender's own spending and borrowing."""
import dataclasses
import unittest

from sim.economy import credit, credit_claims, households
from sim.economy.accounts import Book
from sim.economy.credit_view import claims_of
from sim.economy.types import Loan, Transfer

from sim.tests.test_economy_households import BASKET, SPECS, View, cohort


def loan(loan_id, lender, borrower, principal, rate=0.1, years_left=4.0, arrears=0.0):
    return Loan(loan_id, lender, borrower, "coin", principal, rate, years_left, 0.0, arrears)


class ClaimTests(unittest.TestCase):
    def test_a_current_loan_is_worth_its_principal(self):
        self.assertAlmostEqual(credit_claims.claim_value(loan("a", "l", "b", 100.0)), 100.0)

    def test_arrears_are_worth_less_the_nearer_the_write_off(self):
        mild = credit_claims.claim_value(loan("a", "l", "b", 100.0, arrears=10.0))
        grave = credit_claims.claim_value(loan("a", "l", "b", 100.0, arrears=40.0))
        self.assertGreater(mild, 100.0)
        self.assertLess(grave - 100.0, mild - 100.0 + 30.0)
        self.assertLess((grave - 100.0) / 40.0, (mild - 100.0) / 10.0)

    def test_wealth_is_cash_plus_claims_less_debts_and_credit_adds_none_overall(self):
        book = Book()
        book.transfer(Transfer("edge:legacy", "l", "coin", 300.0, "opening"))
        book.transfer(Transfer("edge:legacy", "b", "coin", 50.0, "opening"))
        loans = [loan("a", "l", "b", 100.0)]
        book.transfer_many(credit.disbursements(loans))
        wealth_before = credit_claims.wealth(book, [], "l", "coin") + credit_claims.wealth(book, [], "b", "coin")
        wealth_after = credit_claims.wealth(book, loans, "l", "coin") + credit_claims.wealth(book, loans, "b", "coin")
        self.assertAlmostEqual(credit_claims.wealth(book, loans, "l", "coin"), 300.0)    # 200 cash and a claim of 100
        self.assertAlmostEqual(credit_claims.wealth(book, loans, "b", "coin"), 50.0)     # 150 cash and a debt of 100
        self.assertAlmostEqual(wealth_before, wealth_after)
        self.assertTrue(book.check_conservation(1e-9).ok)

    def test_a_default_lowers_the_lenders_wealth_and_frees_the_borrower(self):
        book = Book()
        book.transfer(Transfer("edge:legacy", "l", "coin", 100.0, "opening"))
        book.transfer(Transfer("edge:legacy", "b", "coin", 0.0, "opening"))
        loans = [loan("a", "l", "b", 100.0, 0.1, 2.0, arrears=45.0)]
        before = (credit_claims.wealth(book, loans, "l", "coin"), credit_claims.wealth(book, loans, "b", "coin"))
        _transfers, remaining, defaults = credit.service(loans, {"b": 0.0}, 1)
        after = (credit_claims.wealth(book, remaining, "l", "coin"), credit_claims.wealth(book, remaining, "b", "coin"))
        self.assertLess(after[0], before[0])
        self.assertGreater(after[1], before[1])
        self.assertEqual(credit_claims.losses_by_lender(defaults).keys(), {"l"})

    def test_a_defaulter_is_remembered_and_the_memory_fades(self):
        defaults = [credit.Default("a", "l", "b", "coin", 80.0)]
        remembered = credit_claims.remember_defaults({}, defaults)
        self.assertAlmostEqual(remembered["b"], 80.0)
        later = credit_claims.remember_defaults(remembered, [])
        self.assertLess(later["b"], 80.0)
        history = credit_claims.arrears_history([], later)
        self.assertGreater(credit.risk_premium(100.0, 100.0, history["b"]), credit.risk_premium(100.0, 100.0, 0.0))

    def test_a_remembered_default_rations_the_borrower_in_the_clearing(self):
        offers = [credit.FundsOffer("l", "coin", 1000.0, 0.05)]
        asking = [credit.LoanRequest("b", "coin", 100.0, 0.6, 3.0, 200.0, "x")]
        clean, _rate, _unmet = credit.clear(asking, offers, "coin", 0.05, {})
        history = credit_claims.arrears_history([], {"b": 100.0})
        marked, _rate, _unmet = credit.clear(asking, offers, "coin", 0.05, {}, history)
        self.assertGreater(marked[0].rate, clean[0].rate)


class HouseholdWealthTests(unittest.TestCase):
    def spending(self, claims):
        class Lender(View):
            def claims(self, agent, currency):
                return claims
        orders = households.goods_orders(cohort(people=10.0, last_year_spending=5000.0, last_year_income=5000.0),
                                         Lender(), cash=20000.0, income_this_year=5000.0, basket=BASKET, specs=SPECS)
        return sum(bid.flexible_quantity * bid.reference_price for bid in orders.bids)

    def test_a_view_without_loans_gives_no_claims(self):
        self.assertEqual(claims_of(View(), "household:t:0", "coin"), 0.0)

    def test_a_household_with_claims_spends_more_than_one_without(self):
        self.assertGreater(self.spending(10000.0), self.spending(0.0))

    def test_a_household_that_lost_its_claims_to_a_default_spends_less(self):
        self.assertLess(self.spending(0.0), self.spending(10000.0))


if __name__ == "__main__":
    unittest.main()
