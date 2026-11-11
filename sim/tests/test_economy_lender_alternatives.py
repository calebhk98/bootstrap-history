"""Complaint 641: a lender's lowest ask is the best of what else its money earns (time preference, a title to land, the
state's bonds) plus the loss it expects; a lost claim is a loss over its life; the market rate the engine reads is the year's
loan-weighted average."""

QUICK_TOPIC = True

import unittest

from sim.economy import credit, lender_ask, loss_memory
from sim.economy.credit_record import CreditRecord
from sim.economy.credit_view import CreditView
from sim.economy.market_memory import MarketMemory, YearView
from sim.economy.types import FundsOffer, Loan, LoanRequest


class _Areas:
    def goods(self):
        return ()


class PublicYieldTests(unittest.TestCase):
    def test_a_bond_yield_above_the_time_preference_lifts_the_ask(self):
        plain = lender_ask.lowest_ask(0.05, 0.0)
        lifted = lender_ask.lowest_ask(0.05, 0.0, public_yield=0.09)
        self.assertAlmostEqual(plain, 0.05)
        self.assertAlmostEqual(lifted, 0.09)

    def test_a_bond_yield_below_the_time_preference_leaves_the_ask(self):
        self.assertAlmostEqual(lender_ask.lowest_ask(0.05, 0.0, public_yield=0.03), 0.05)

    def test_the_loss_a_lender_expects_is_added_to_the_best_alternative(self):
        self.assertAlmostEqual(lender_ask.lowest_ask(0.05, 0.0, expected_loss_rate=0.02, public_yield=0.09), 0.11)

    def test_a_bond_yield_is_reachable_only_with_a_bond_market(self):
        self.assertEqual(lender_ask.reachable_public_yield(0.09, True), 0.09)
        self.assertIsNone(lender_ask.reachable_public_yield(0.09, False))
        self.assertIsNone(lender_ask.reachable_public_yield(None, True))

    def test_a_lifted_ask_is_the_rate_a_glut_clears_at(self):
        ask = lender_ask.lowest_ask(0.05, 0.0, public_yield=0.09)
        offers = [FundsOffer("saver:%d" % index, "coin", 1000.0, ask) for index in range(3)]
        request = LoanRequest("borrower", "coin", 10.0, 0.5, 1.0, 1e9, "working capital")
        _loans, rate, _unmet = credit.clear([request], offers, "coin", 0.0, {})
        self.assertAlmostEqual(rate, 0.09)


class LandYieldTests(unittest.TestCase):
    def test_the_land_yield_is_rent_over_the_price_a_hectare_changed_hands_at(self):
        self.assertAlmostEqual(lender_ask.land_yield(4.0, 80.0), 0.05)

    def test_without_a_sale_price_there_is_no_land_yield(self):
        self.assertIsNone(lender_ask.land_yield(4.0, None))
        self.assertIsNone(lender_ask.land_yield(4.0, 0.0))

    def test_a_land_yield_above_the_other_alternatives_lifts_the_ask(self):
        self.assertAlmostEqual(lender_ask.lowest_ask(0.05, 0.0, land_yield=0.08, public_yield=0.06), 0.08)


class ViewTests(unittest.TestCase):
    def test_the_view_gives_the_bond_yield_for_its_own_currency_only(self):
        view = CreditView(MarketMemory(), None, _Areas(), "coin", None, public_yield=lambda: 0.07)
        self.assertEqual(view.public_yield("coin"), 0.07)
        self.assertIsNone(view.public_yield("other"))

    def test_a_plain_view_has_no_bond_yield(self):
        self.assertIsNone(YearView(MarketMemory(), None, _Areas(), "coin", None).public_yield("coin"))


class LostClaimTests(unittest.TestCase):
    def test_a_lender_that_lost_its_only_claim_does_not_read_the_whole_as_one_years_loss(self):
        rates = loss_memory.blend({}, {"lender": 100.0}, {"lender": 0.0}, 1.0)
        self.assertAlmostEqual(rates["lender"], 1.0 / loss_memory.LOSS_CLAIM_LIFE_YEARS)

    def test_a_lost_claim_over_a_longer_life_is_a_smaller_yearly_rate(self):
        short = loss_memory.blend({}, {"lender": 100.0}, {"lender": 900.0}, 1.0, claim_life_years=1.0)["lender"]
        long = loss_memory.blend({}, {"lender": 100.0}, {"lender": 900.0}, 1.0, claim_life_years=5.0)["lender"]
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
