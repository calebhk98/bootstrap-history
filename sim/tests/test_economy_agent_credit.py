"""The agent economy's loanable-funds rate: savings with no borrowers pull it down toward lenders' asks,
more funds lower it, more borrowing raises it, and money lent is money moved, not made (Complaint 389).
Engine-free fixture; each test states a direction, not a figure."""
import unittest
from unittest import mock

from sim.economy import api as economy_api, credit, economy as economy_module
from sim.economy.economy import Economy
from sim.economy.types import FundsOffer, LoanRequest
from sim.world import capital_market
from sim.tests import economy_fixture as fixture, test_economy_agent_money as money

COIN = "coin"
START_RATE = 0.10


def lend_once(funds, requests=()):
    """The economy's own lending step, given `funds` and `requests`, with households and merchants silent."""
    economy = Economy(fixture.small_setup())
    economy.record.memory.rates[COIN] = START_RATE
    economy.record.loan_requests = list(requests)
    with mock.patch.object(economy_module.lending, "household_requests", return_value=[]), \
            mock.patch.object(economy_module.lending, "merchant_requests", return_value=[]):
        economy._lend(funds, economy.view(), {}, None)
    return economy


def offer(amount=1000.0, minimum_rate=0.02, lender="lender:a"):
    return FundsOffer(lender, COIN, amount, minimum_rate)


def request(amount=100.0, maximum_rate=0.5, borrower="borrower:a"):
    return LoanRequest(borrower, COIN, amount, maximum_rate, 4.0, 10 * amount, "test")


class SavingsWithNoBorrowersTests(unittest.TestCase):
    def test_the_rate_falls_toward_the_lowest_ask(self):
        economy = lend_once([offer(minimum_rate=0.02)])
        rate = economy.record.memory.rates[COIN]
        self.assertLess(rate, START_RATE)
        self.assertGreaterEqual(rate, 0.02)

    def test_it_falls_further_each_year_and_never_below_the_ask(self):
        economy = Economy(fixture.small_setup())
        economy.record.memory.rates[COIN] = START_RATE
        rates = [START_RATE]
        with mock.patch.object(economy_module.lending, "household_requests", return_value=[]), \
                mock.patch.object(economy_module.lending, "merchant_requests", return_value=[]):
            for _year in range(8):
                economy._lend([offer(minimum_rate=0.02)], economy.view(), {}, None)
                rates.append(economy.record.memory.rates[COIN])
        self.assertTrue(all(later <= earlier for earlier, later in zip(rates, rates[1:])))
        self.assertGreaterEqual(min(rates), 0.02 - 1e-12)
        self.assertLess(rates[-1], rates[1])

    def test_a_lender_who_asks_more_holds_the_rate_higher(self):
        cheap = lend_once([offer(minimum_rate=0.02)]).record.memory.rates[COIN]
        dear = lend_once([offer(minimum_rate=0.08)]).record.memory.rates[COIN]
        self.assertLess(cheap, dear)

    def test_the_lowest_ask_among_lenders_sets_the_floor(self):
        mixed = lend_once([offer(minimum_rate=0.08, lender="lender:b"), offer(minimum_rate=0.02)])
        alone = lend_once([offer(minimum_rate=0.02)])
        self.assertAlmostEqual(mixed.record.memory.rates[COIN], alone.record.memory.rates[COIN])

    def test_no_funds_and_no_borrowers_leave_the_rate_alone(self):
        self.assertEqual(lend_once([]).record.memory.rates[COIN], START_RATE)

    def test_nothing_is_lent_without_a_borrower(self):
        economy = lend_once([offer()])
        self.assertEqual(economy.record.loans, [])


class BorrowersAgainstFundsTests(unittest.TestCase):
    def test_borrowers_with_no_savings_pull_the_rate_up(self):
        economy = lend_once([], [request()])
        self.assertGreater(economy.record.memory.rates[COIN], START_RATE)

    def test_more_funds_against_the_same_borrowing_clear_at_a_lower_rate(self):
        borrowing = [request(amount=500.0)]
        scarce_funds = [offer(amount=100.0, minimum_rate=0.03)]
        plenty_funds = scarce_funds + [offer(amount=2000.0, minimum_rate=0.01, lender="lender:b")]
        scarce, scarce_rate, _unmet = credit.clear(borrowing, scarce_funds, COIN, None, {})
        plenty, plenty_rate, _unmet = credit.clear(borrowing, plenty_funds, COIN, None, {})
        self.assertLess(plenty_rate, scarce_rate)
        self.assertGreater(sum(loan.principal for loan in plenty), sum(loan.principal for loan in scarce))

    def test_more_borrowing_against_the_same_funds_clears_at_a_higher_rate(self):
        funds = [offer(amount=300.0, minimum_rate=0.01), offer(amount=300.0, minimum_rate=0.05, lender="lender:b")]
        few = credit.clear([request(amount=100.0)], funds, COIN, None, {})[1]
        many = credit.clear([request(amount=100.0), request(amount=500.0, borrower="borrower:b")],
                            funds, COIN, None, {})[1]
        self.assertGreater(many, few)

    def test_a_borrower_pays_the_base_rate_plus_a_premium_never_less(self):
        loans, rate, _unmet = credit.clear([request()], [offer()], COIN, None, {})
        self.assertTrue(loans)
        for loan in loans:
            self.assertGreaterEqual(loan.rate, rate)

    def test_a_borrower_who_cannot_pay_the_rate_is_rationed_not_served(self):
        loans, _rate, unmet = credit.clear([request(maximum_rate=0.001)], [offer(minimum_rate=0.05)], COIN, None, {})
        self.assertEqual(loans, [])
        self.assertEqual(len(unmet), 1)


class CreditRoomTests(unittest.TestCase):
    """What lenders will still advance comes from the same market that sets the rate."""

    def lent(self, asked=100.0):
        economy = Economy(fixture.small_setup())
        economy.record.memory.rates[COIN] = START_RATE
        lender = max(economy.record.cohorts, key=lambda agent: economy.record.book.balance(agent, COIN))
        funds = economy.record.book.balance(lender, COIN)
        economy.record.loan_requests = [request(amount=asked)]
        with mock.patch.object(economy_module.lending, "household_requests", return_value=[]), \
                mock.patch.object(economy_module.lending, "merchant_requests", return_value=[]):
            economy._lend([offer(amount=funds, lender=lender)], economy.view(), {}, None)
        return economy, funds

    def test_there_is_no_room_figure_before_lenders_have_met(self):
        self.assertIsNone(economy_api.credit_room(Economy(fixture.small_setup()), "borrower:a"))

    def test_room_is_what_lenders_will_lend_less_what_others_took_this_year(self):
        economy, funds = self.lent()
        self.assertAlmostEqual(economy_api.credit_room(economy, "borrower:b"),
                               capital_market.lendable_capacity(funds) - 100.0)

    def test_a_borrowers_own_loan_does_not_count_against_its_room(self):
        economy, funds = self.lent()
        self.assertAlmostEqual(economy_api.credit_room(economy, "borrower:a"),
                               capital_market.lendable_capacity(funds))

    def test_room_survives_a_save_and_load(self):
        economy, _funds = self.lent()
        again = economy_api.economy_from_record(economy.setup, economy_api.export_record(economy))
        self.assertEqual(economy_api.credit_room(again, "borrower:b"), economy_api.credit_room(economy, "borrower:b"))


class RateAgainstMoneyStockTests(unittest.TestCase):
    def test_a_larger_money_stock_does_not_raise_the_rate_before_prices_have_moved(self):
        control = [outcome.rate for outcome in money.with_windfall(1.0)[1][:2]]
        flush = [outcome.rate for outcome in money.with_windfall(3.0)[1][:2]]
        for rate_with_more, rate_control in zip(flush, control):
            self.assertLessEqual(rate_with_more, rate_control + 1e-9)


class LoansMoveMoneyTests(unittest.TestCase):
    def test_a_loan_moves_money_from_lender_to_borrower_and_leaves_the_supply_alone(self):
        economy = Economy(fixture.small_setup())
        book = economy.record.book
        lender, borrower = sorted(economy.record.cohorts)[:2]
        supply = book.money_supply(COIN)
        lender_before, borrower_before = book.balance(lender, COIN), book.balance(borrower, COIN)
        loans, _rate, _unmet = credit.clear([request(amount=50.0, borrower=borrower)],
                                            [offer(amount=50.0, lender=lender)], COIN, None, {})
        book.transfer_many(credit.disbursements(loans))
        self.assertAlmostEqual(book.balance(lender, COIN), lender_before - 50.0)
        self.assertAlmostEqual(book.balance(borrower, COIN), borrower_before + 50.0)
        self.assertAlmostEqual(book.money_supply(COIN), supply)

    def test_years_of_lending_and_servicing_leave_the_books_conserved(self):
        economy, outcomes = fixture.run(years=6)
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())
        for outcome in outcomes:
            self.assertTrue(outcome.money_audit.ok)

    def test_the_rate_the_economy_reports_is_what_its_credit_market_holds(self):
        economy, outcomes = fixture.run(years=3)
        self.assertEqual(outcomes[-1].rate, economy.record.memory.rates[COIN])
        self.assertGreaterEqual(outcomes[-1].rate, 0.0)


if __name__ == "__main__":
    unittest.main()
