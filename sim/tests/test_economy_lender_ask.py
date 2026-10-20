"""Complaint 641: a lender's lowest ask is the best return among its alternatives plus the loss it expects from the
defaults it has seen, so a glut of funds leaves the rate at the lenders' floor, not zero; a bank's spread follows its
loss record and how thin its capital is behind its loans."""

QUICK_TOPIC = True

import unittest

from sim.economy import bank_spread, banks, credit, credit_claims, lender_ask, loss_memory
from sim.economy.credit_view import CreditView, loss_rate_of
from sim.economy.economy import Economy
from sim.economy.households_orders import HOUSEHOLD_TIME_PREFERENCE
from sim.economy.market_memory import MarketMemory
from sim.economy.types import FundsOffer, Loan, LoanRequest
from sim.tests import economy_fixture as fixture


def _request(amount):
    return LoanRequest("borrower", "coin", amount, 0.5, 1.0, 1e9, "working capital")


class LowestAskTests(unittest.TestCase):
    def test_the_floor_is_time_preference_plus_expected_inflation_and_never_below_zero(self):
        self.assertAlmostEqual(lender_ask.lowest_ask(0.05, 0.02), 0.07)
        self.assertEqual(lender_ask.lowest_ask(0.05, -0.20), 0.0)

    def test_a_lender_with_past_losses_asks_more(self):
        clean = lender_ask.lowest_ask(0.05, 0.0, expected_loss_rate=lender_ask.loss_rate(0.0))
        burnt = lender_ask.lowest_ask(0.05, 0.0, expected_loss_rate=lender_ask.loss_rate(0.1))
        self.assertAlmostEqual(burnt - clean, 0.1)

    def test_land_with_a_higher_yield_raises_the_floor(self):
        low = lender_ask.lowest_ask(0.05, 0.0, land_yield_available=lender_ask.land_yield(3.0, 100.0))
        high = lender_ask.lowest_ask(0.05, 0.0, land_yield_available=lender_ask.land_yield(9.0, 100.0))
        self.assertAlmostEqual(low, 0.05)
        self.assertAlmostEqual(high, 0.09)

    def test_land_with_no_price_is_no_alternative(self):
        self.assertEqual(lender_ask.land_yield(9.0, None), 0.0)

    def test_public_debt_raises_the_floor(self):
        self.assertAlmostEqual(lender_ask.lowest_ask(0.05, 0.0, public_yield_available=0.08), 0.08)


class GlutTests(unittest.TestCase):
    def test_a_glut_of_funds_leaves_the_rate_at_the_lenders_floor_not_zero(self):
        floor = lender_ask.lowest_ask(HOUSEHOLD_TIME_PREFERENCE, 0.0)
        offers = [FundsOffer("saver:%d" % index, "coin", 1000.0, floor) for index in range(5)]
        _loans, rate, _unmet = credit.clear([_request(10.0)], offers, "coin", 0.0, {})
        self.assertAlmostEqual(rate, floor)
        self.assertGreater(rate, 0.0)

    def test_a_glut_does_not_pull_the_rate_below_a_scarred_lender_either(self):
        scarred = lender_ask.lowest_ask(0.05, 0.0, expected_loss_rate=0.1)
        offers = [FundsOffer("saver", "coin", 1000.0, scarred)]
        _loans, rate, _unmet = credit.clear([_request(10.0)], offers, "coin", 0.3, {})
        self.assertGreaterEqual(rate, scarred - 1e-12)


class BankSpreadTests(unittest.TestCase):
    TARGET = banks.BANK_CAPITAL_SHARE_OF_LOANS

    def test_a_bank_with_thin_capital_widens_its_spread(self):
        sound = bank_spread.spread(0.0, 1000.0, 2.0 * self.TARGET * 1000.0, self.TARGET)
        thin = bank_spread.spread(0.0, 1000.0, 0.5 * self.TARGET * 1000.0, self.TARGET)
        gone = bank_spread.spread(0.0, 1000.0, 0.0, self.TARGET)
        self.assertEqual(sound, 0.0)
        self.assertGreater(thin, sound)
        self.assertGreater(gone, thin)

    def test_a_bank_with_losses_widens_its_spread(self):
        capital = 2.0 * self.TARGET * 1000.0
        self.assertGreater(bank_spread.spread(0.05, 1000.0, capital, self.TARGET),
                           bank_spread.spread(0.0, 1000.0, capital, self.TARGET))

    def test_a_standing_bank_asks_its_depositors_rate_plus_the_spread_of_its_record(self):
        economy = Economy(fixture.small_setup())
        record, money = economy.record, economy.setup.currency_id
        founder, depositor = sorted(record.cohorts)[0], sorted(record.cohorts)[1]
        borrower = sorted(record.producers)[0]
        bank = banks.found(record, founder, 100.0, 0, money)
        record.loans.append(Loan("lent", bank.agent_id, borrower, money, 5000.0, rate=0.05, years_left=5.0,
                                 issued_year=0))
        record.loans.append(Loan("deposit", depositor, bank.agent_id, money, 4950.0, rate=0.03, years_left=1e9,
                                 issued_year=0))
        pledged = [FundsOffer(depositor, money, 100.0, 0.03)]
        thin = banks.ask_of(record, bank, money, pledged)
        record.loss_rates[bank.agent_id] = 0.1
        scarred = banks.ask_of(record, bank, money, pledged)
        self.assertGreater(thin, 0.03)
        self.assertGreater(scarred, thin)


def _years(rates, lost_by_year, claims_each_year, share=None):
    """Age one lender's rate through the years: `lost_by_year[i]` booked in year i against `claims_each_year`."""
    seen, lost_so_far = 0.0, 0.0
    for lost, claims in zip(lost_by_year, claims_each_year):
        lost_so_far += lost
        rates = loss_memory.blend(rates, {"lender": lost_so_far - seen}, {"lender": claims},
                                  loss_memory.LOSS_RATE_SMOOTHING_SHARE if share is None else share)
        seen = lost_so_far
    return rates


class AgingTests(unittest.TestCase):
    CLAIMS = 900.0

    def ask(self, rates):
        return lender_ask.lowest_ask(HOUSEHOLD_TIME_PREFERENCE, 0.0, expected_loss_rate=lender_ask.loss_rate(
            rates.get("lender", 0.0)))

    def test_a_lender_that_lost_once_long_ago_and_lent_cleanly_since_asks_near_its_floor(self):
        floor = lender_ask.lowest_ask(HOUSEHOLD_TIME_PREFERENCE, 0.0)
        rates = _years({}, [100.0] + [0.0] * 20, [self.CLAIMS] * 21)
        self.assertLess(self.ask(rates) - floor, 0.01)

    def test_an_old_loss_fades_year_by_year(self):
        rates, previous = {}, None
        for year in range(1, 8):
            rates = _years({}, [100.0] + [0.0] * year, [self.CLAIMS] * (year + 1))
            if previous is not None:
                self.assertLess(rates["lender"], previous)
            previous = rates["lender"]

    def test_a_lender_losing_every_year_asks_more_than_one_losing_once(self):
        once = _years({}, [100.0] + [0.0] * 9, [self.CLAIMS] * 10)
        always = _years({}, [100.0] * 10, [self.CLAIMS] * 10)
        self.assertGreater(self.ask(always), self.ask(once))

    def test_a_lender_with_no_losses_asks_its_floor(self):
        floor = lender_ask.lowest_ask(HOUSEHOLD_TIME_PREFERENCE, 0.0)
        self.assertEqual(self.ask(_years({}, [0.0] * 5, [self.CLAIMS] * 5)), floor)

    def test_a_glut_with_clean_lenders_clears_at_the_floor_not_the_ceiling(self):
        floor = lender_ask.lowest_ask(HOUSEHOLD_TIME_PREFERENCE, 0.0)
        rates = _years({}, [100.0] + [0.0] * 15, [self.CLAIMS] * 16)
        ask = self.ask(rates)
        offers = [FundsOffer("saver:%d" % index, "coin", 1000.0, ask) for index in range(5)]
        _loans, rate, _unmet = credit.clear([_request(10.0)], offers, "coin", 0.0, {}, rate_ceiling=4.0 * floor)
        self.assertLess(rate, 1.1 * floor)

    def test_age_reads_the_record_and_leaves_the_loss_stock_alone(self):
        record = Economy(fixture.small_setup()).record
        record.credit_losses["lender"] = 100.0
        loss_memory.age(record, "coin")
        first = record.loss_rates["lender"]
        loss_memory.age(record, "coin")
        self.assertEqual(record.credit_losses["lender"], 100.0)
        self.assertGreater(first, 0.0)
        self.assertLess(record.loss_rates["lender"], first)


class _Areas:
    def goods(self):
        return ()


class ViewTests(unittest.TestCase):
    def test_the_view_reads_a_lenders_loss_rate_from_its_record(self):
        loans = [Loan("l", "saver", "borrower", "coin", 900.0, rate=0.05, years_left=3.0, issued_year=0)]
        book = Economy(fixture.small_setup()).record.book
        view = CreditView(MarketMemory(), book, _Areas(), "coin", loans=lambda: loans, loss_rates=lambda: {"saver": 0.1})
        self.assertAlmostEqual(view.loss_rate("saver", "coin"), 0.1)
        self.assertEqual(loss_rate_of(object(), "saver", "coin"), 0.0)


if __name__ == "__main__":
    unittest.main()
