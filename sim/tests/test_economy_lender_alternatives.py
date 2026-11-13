"""Complaint 641: a lender's lowest ask is the best of what else its money earns (time preference, a title to land, the
state's bonds) plus the loss it expects; a lost claim is a loss over its life; the market rate the engine reads is the year's
loan-weighted average."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import claim_terms, credit, lender_ask, loss_memory
from sim.markets import port_public_debt
from sim.economy.credit_record import CreditRecord
from sim.economy.credit_view import CreditView
from sim.economy.market_memory import MarketMemory, YearView
from sim.economy.types import FundsOffer, Loan, LoanRequest


class _Areas:
    def goods(self):
        return ()


class PublicPremiumTests(unittest.TestCase):
    def test_a_state_premium_is_added_to_the_lenders_own_alternative(self):
        self.assertAlmostEqual(lender_ask.lowest_ask(0.05, 0.02, public_premium=0.04), 0.11)

    def test_a_state_paying_no_premium_leaves_the_ask_whatever_the_going_rate(self):
        plain = lender_ask.lowest_ask(0.05, 0.02)
        self.assertAlmostEqual(lender_ask.lowest_ask(0.05, 0.02, public_premium=0.0), plain)
        self.assertAlmostEqual(lender_ask.lowest_ask(0.05, 0.02, public_premium=-0.01), plain)

    def test_the_loss_a_lender_expects_is_added_to_the_best_alternative(self):
        self.assertAlmostEqual(lender_ask.lowest_ask(0.05, 0.0, expected_loss_rate=0.02, public_premium=0.04), 0.11)

    def test_a_bond_premium_is_reachable_only_with_a_bond_market(self):
        self.assertEqual(lender_ask.reachable_public_premium(0.09, True), 0.09)
        self.assertIsNone(lender_ask.reachable_public_premium(0.09, False))
        self.assertIsNone(lender_ask.reachable_public_premium(None, True))

    def test_a_lifted_ask_is_the_rate_a_glut_clears_at(self):
        ask = lender_ask.lowest_ask(0.05, 0.0, public_premium=0.04)
        offers = [FundsOffer("saver:%d" % index, "coin", 1000.0, ask) for index in range(3)]
        request = LoanRequest("borrower", "coin", 10.0, 0.5, 1.0, 1e9, "working capital")
        _loans, rate, _unmet = credit.clear([request], offers, "coin", ask, {})
        self.assertAlmostEqual(rate, 0.09)


class LandYieldTests(unittest.TestCase):
    def test_the_land_yield_is_rent_over_the_price_a_hectare_changed_hands_at(self):
        self.assertAlmostEqual(lender_ask.land_yield(4.0, 80.0), 0.05)

    def test_without_a_sale_price_there_is_no_land_yield(self):
        self.assertIsNone(lender_ask.land_yield(4.0, None))
        self.assertIsNone(lender_ask.land_yield(4.0, 0.0))

    def test_a_land_yield_above_the_other_alternatives_lifts_the_ask(self):
        self.assertAlmostEqual(lender_ask.lowest_ask(0.05, 0.0, land_yield=0.08, public_premium=0.01), 0.08)


class ClaimTermTests(unittest.TestCase):
    def test_a_lenders_life_is_the_worth_weighted_mean_term_of_its_claims(self):
        loans = [Loan("a", "lender", "b1", "coin", 100.0, rate=0.05, years_left=2.0, issued_year=8),     # ran 2 years, 2 left: term 4
                 Loan("b", "lender", "b2", "coin", 300.0, rate=0.05, years_left=6.0, issued_year=10),    # ran 0, 6 left: term 6
                 Loan("c", "other", "b3", "coin", 50.0, rate=0.05, years_left=1.0, issued_year=10)]      # term 1
        by_lender, book = claim_terms.mean_term_years(loans, 10, "coin")
        self.assertAlmostEqual(by_lender["lender"], (100.0 * 4.0 + 300.0 * 6.0) / 400.0)
        self.assertAlmostEqual(by_lender["other"], 1.0)
        self.assertAlmostEqual(book, (400.0 + 1800.0 + 50.0) / 450.0)

    def test_other_currencies_are_left_out(self):
        loans = [Loan("a", "lender", "b1", "coin", 100.0, rate=0.05, years_left=2.0, issued_year=10),
                 Loan("b", "lender", "b2", "shell", 100.0, rate=0.05, years_left=8.0, issued_year=10)]
        self.assertAlmostEqual(claim_terms.mean_term_years(loans, 10, "coin")[0]["lender"], 2.0)

    def test_an_empty_book_has_no_life(self):
        self.assertEqual(claim_terms.mean_term_years([], 10, "coin"), ({}, None))

    def test_the_table_and_the_list_agree(self):
        from sim.loans.store import LoanStore
        from sim.loans.view import LoanList
        loans = LoanList(LoanStore())
        loans.extend([Loan("a", "lender", "b1", "coin", 100.0, rate=0.05, years_left=2.0, issued_year=8),
                      Loan("b", "lender", "b2", "coin", 300.0, rate=0.05, years_left=6.0, issued_year=10)])
        by_lender, book = claim_terms.mean_term_years(loans, 10, "coin")
        self.assertAlmostEqual(by_lender["lender"], 5.5)
        self.assertAlmostEqual(book, 5.5)


class PublicPremiumPortTests(unittest.TestCase):
    @staticmethod
    def _sim(terms):
        from sim.agents.bonds import BondBook
        bonds = BondBook()
        if terms:
            bonds.set_terms("state", *terms)
        government = types.SimpleNamespace(account_id="state", purses=types.SimpleNamespace(bonds=bonds))
        countries = types.SimpleNamespace(government_of=lambda _none: government)
        return types.SimpleNamespace(scenario=types.SimpleNamespace(actors=types.SimpleNamespace(countries=countries)))

    def test_a_state_selling_above_its_coupon_offers_the_difference(self):
        self.assertAlmostEqual(port_public_debt.bond_premium_over_coupon(self._sim((0.05, 0.08))), 0.03)

    def test_a_state_selling_at_its_coupon_offers_no_premium(self):
        self.assertEqual(port_public_debt.bond_premium_over_coupon(self._sim((0.05, 0.05))), 0.0)

    def test_a_state_with_no_bonds_offers_none(self):
        self.assertIsNone(port_public_debt.bond_premium_over_coupon(self._sim(None)))


class ViewTests(unittest.TestCase):
    def test_the_view_gives_the_bond_premium_for_its_own_currency_only(self):
        view = CreditView(MarketMemory(), None, _Areas(), "coin", None, public_premium=lambda: 0.07)
        self.assertEqual(view.public_premium("coin"), 0.07)
        self.assertIsNone(view.public_premium("other"))

    def test_a_plain_view_has_no_bond_premium(self):
        self.assertIsNone(YearView(MarketMemory(), None, _Areas(), "coin", None).public_premium("coin"))


class LostClaimTests(unittest.TestCase):
    def test_a_lender_that_lost_its_only_claim_spreads_it_over_that_lenders_claim_life(self):
        rates = loss_memory.blend({}, {"lender": 100.0}, {"lender": 0.0}, 1.0, {"lender": 4.0}, 2.0)
        self.assertAlmostEqual(rates["lender"], 0.25)

    def test_a_lender_with_no_claims_on_the_book_takes_the_books_mean_life(self):
        rates = loss_memory.blend({}, {"lender": 100.0}, {"lender": 0.0}, 1.0, {"other": 4.0}, 2.0)
        self.assertAlmostEqual(rates["lender"], 0.5)

    def test_with_no_claim_anywhere_the_life_is_one_year(self):
        rates = loss_memory.blend({}, {"lender": 100.0}, {"lender": 0.0}, 1.0, {}, None)
        self.assertAlmostEqual(rates["lender"], 1.0)

    def test_a_lost_claim_over_a_longer_life_is_a_smaller_yearly_rate(self):
        short = loss_memory.blend({}, {"lender": 100.0}, {"lender": 900.0}, 1.0, {"lender": 1.0})["lender"]
        long = loss_memory.blend({}, {"lender": 100.0}, {"lender": 900.0}, 1.0, {"lender": 5.0})["lender"]
        self.assertAlmostEqual(short, 0.1)
        self.assertAlmostEqual(long, 100.0 / 1400.0)

    def test_a_lender_that_lost_asks_more_than_one_that_did_not(self):
        lost = loss_memory.blend({}, {"lender": 100.0}, {"lender": 900.0}, 0.3)["lender"]
        self.assertGreater(lender_ask.lowest_ask(0.05, 0.0, expected_loss_rate=lender_ask.loss_rate(lost)),
                           lender_ask.lowest_ask(0.05, 0.0, expected_loss_rate=lender_ask.loss_rate(0.0)))


def _loan(principal):
    return Loan("l", "lender", "borrower", "coin", principal, rate=0.05, years_left=1.0, issued_year=0)


class AverageRateTests(unittest.TestCase):
    def test_the_rate_is_none_before_a_clearing_lent(self):
        record = CreditRecord()
        record.note_clearing(3, 0.07, [], "no_offers")
        self.assertIsNone(record.average_rate())

    def test_the_average_weights_each_clearing_rate_by_what_it_lent(self):
        record = CreditRecord()
        record.note_clearing(3, 0.04, [_loan(100.0)], None)
        record.note_clearing(3, 0.10, [_loan(300.0)], None)
        self.assertAlmostEqual(record.average_rate(), (0.04 * 100.0 + 0.10 * 300.0) / 400.0)

    def test_a_new_years_first_lending_starts_the_average_afresh(self):
        record = CreditRecord()
        record.note_clearing(3, 0.04, [_loan(100.0)], None)
        record.note_clearing(4, 0.10, [_loan(300.0)], None)
        self.assertAlmostEqual(record.average_rate(), 0.10)

    def test_a_year_that_lent_nothing_keeps_the_last_average_and_stores_the_cause(self):
        record = CreditRecord()
        record.note_clearing(3, 0.04, [_loan(100.0)], None)
        record.note_clearing(4, 0.07, [], "no_offer_at_rate")
        self.assertAlmostEqual(record.average_rate(), 0.04)
        self.assertEqual(record.last_clearing_cause, "no_offer_at_rate")


if __name__ == "__main__":
    unittest.main()
