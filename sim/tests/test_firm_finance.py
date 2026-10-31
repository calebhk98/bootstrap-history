"""Complaint 473: a producer's year follows Eurace@Unibi's firm financial management (income statement, dividend
rule, liquidity needs, the two bankruptcy routes). Each test calls one function with written-out inputs."""

QUICK_TOPIC = True

import unittest

from sim.economy import firm_finance as finance
from sim.economy.types import Loan


class IncomeStatementTests(unittest.TestCase):
    def test_net_earnings_are_revenue_less_costs_interest_and_depreciation(self):
        self.assertAlmostEqual(finance.net_earnings(100.0, 60.0, 10.0, 5.0), 25.0)

    def test_history_keeps_only_the_last_years(self):
        kept = finance.appended((1.0, 2.0, 3.0, 4.0, 5.0, 6.0), 7.0)
        self.assertEqual(len(kept), finance.HISTORY_YEARS)
        self.assertEqual(kept[-1], 7.0)


class DividendTests(unittest.TestCase):
    def test_below_the_cash_threshold_the_payout_ratio_of_average_net_earnings_is_paid(self):
        amount, full = finance.dividend_total((10.0, 30.0), (100.0, 100.0), cash=1.0)
        self.assertAlmostEqual(amount, finance.DIVIDEND_EARNINGS_RATIO * 20.0)
        self.assertFalse(full)

    def test_above_the_cash_threshold_all_average_net_earnings_are_paid(self):
        cash = (finance.FULL_PAYOUT_YEARS_OF_REVENUE + 1.0) * 100.0
        amount, full = finance.dividend_total((10.0, 30.0), (100.0, 100.0), cash=cash)
        self.assertAlmostEqual(amount, 20.0)
        self.assertTrue(full)

    def test_negative_average_earnings_pay_nothing(self):
        self.assertEqual(finance.dividend_total((-10.0, -30.0), (100.0, 100.0), cash=1.0)[0], 0.0)

    def test_with_no_revenue_the_payout_ratio_applies_whatever_the_cash(self):
        amount, full = finance.dividend_total((10.0,), (0.0,), cash=1e9)
        self.assertAlmostEqual(amount, finance.DIVIDEND_EARNINGS_RATIO * 10.0)
        self.assertFalse(full)


class LiquidityTests(unittest.TestCase):
    def test_external_needs_are_what_the_cash_lacks_of_production_financial_and_dividend_needs(self):
        needs = finance.liquidity_needs(cash=50.0, production=40.0, financial=20.0, dividend=10.0)
        self.assertAlmostEqual(needs.total, 70.0)
        self.assertAlmostEqual(needs.external, 20.0)

    def test_cash_that_covers_the_needs_needs_no_credit(self):
        self.assertEqual(finance.liquidity_needs(cash=100.0, production=40.0, financial=20.0, dividend=10.0).external, 0.0)

    def test_cash_short_of_the_needs_but_over_the_commitments_is_a_crisis(self):
        self.assertEqual(finance.financial_state(cash=30.0, payable=20.0, total_needs=70.0), "crisis")

    def test_cash_short_of_the_commitments_is_illiquid(self):
        self.assertEqual(finance.financial_state(cash=10.0, payable=20.0, total_needs=70.0), "illiquid")

    def test_cash_over_the_needs_is_sound(self):
        self.assertEqual(finance.financial_state(cash=80.0, payable=20.0, total_needs=70.0), "ok")

    def test_a_crisis_pays_what_is_left_after_commitments_and_production_needs(self):
        self.assertAlmostEqual(finance.crisis_dividend(cash=75.0, financial=20.0, production=40.0), 15.0)
        self.assertEqual(finance.crisis_dividend(cash=50.0, financial=20.0, production=40.0), 0.0)


class CommitmentTests(unittest.TestCase):
    def test_commitments_are_interest_on_the_principal_plus_the_installment(self):
        loan = Loan("l1", "bank", "f1", "coin", 100.0, rate=0.1, years_left=4.0)
        self.assertAlmostEqual(finance.financial_commitments([loan], "f1"), 10.0 + 25.0)

    def test_a_loan_in_its_last_year_falls_due_whole(self):
        loan = Loan("l1", "bank", "f1", "coin", 100.0, rate=0.1, years_left=1.0)
        self.assertAlmostEqual(finance.financial_commitments([loan], "f1"), 110.0)

    def test_another_borrowers_loan_is_not_counted(self):
        loan = Loan("l1", "bank", "f2", "coin", 100.0, rate=0.1, years_left=4.0)
        self.assertEqual(finance.financial_commitments([loan], "f1"), 0.0)


class BankruptcyTests(unittest.TestCase):
    def test_negative_equity_is_insolvency(self):
        self.assertTrue(finance.insolvent(-0.01))
        self.assertFalse(finance.insolvent(0.0))

    def test_insolvent_debt_is_rescaled_to_the_factor_times_assets(self):
        ratio = finance.write_off_ratio(debt=300.0, assets=120.0, illiquid=False)
        self.assertAlmostEqual(ratio, 1.0 - finance.DEBT_RESCALING_FACTOR * 120.0 / 300.0)

    def test_illiquid_with_assets_beyond_the_debt_rescales_the_debt_itself(self):
        ratio = finance.write_off_ratio(debt=100.0, assets=900.0, illiquid=True)
        self.assertAlmostEqual(ratio, 1.0 - finance.DEBT_RESCALING_FACTOR)

    def test_no_debt_writes_nothing_off(self):
        self.assertEqual(finance.write_off_ratio(debt=0.0, assets=10.0, illiquid=False), 0.0)

    def test_written_off_loans_lose_the_ratio_of_principal_and_arrears(self):
        loan = Loan("l1", "bank", "f1", "coin", 100.0, arrears=40.0, arrears_interest=10.0)
        kept, lost = finance.written_down(loan, 0.5)
        self.assertAlmostEqual(kept.principal, 50.0)
        self.assertAlmostEqual(kept.arrears, 20.0)
        self.assertAlmostEqual(kept.arrears_interest, 5.0)
        self.assertAlmostEqual(lost, 70.0)


if __name__ == "__main__":
    unittest.main()


from types import SimpleNamespace

from sim.economy import firm_year
from sim.tests.test_economy_producers import farmer


def settle(**changes):
    inputs = dict(producer=farmer(), survivor=farmer(cash_target=40.0), revenue=100.0, running_costs=60.0, interest=0.0,
                  depreciation=0.0, commitments=20.0, arrears=0.0, cash=200.0, equity_value=300.0, assets=350.0, debt=50.0)
    inputs.update(changes)
    return firm_year.settled(**inputs)


class SettledTests(unittest.TestCase):
    def test_a_sound_producer_pays_the_ratio_of_its_net_earnings_and_remembers_the_year(self):
        year = settle(revenue=1000.0, running_costs=960.0, cash=100.0, equity_value=120.0, assets=170.0)
        self.assertEqual(year.state, "ok")
        self.assertAlmostEqual(year.dividend, finance.DIVIDEND_EARNINGS_RATIO * 40.0)
        self.assertEqual(year.producer.net_earnings_history, (40.0,))
        self.assertEqual(year.producer.idle_years, 0)

    def test_a_loss_year_pays_nothing_though_cash_is_high(self):
        self.assertEqual(settle(revenue=10.0).dividend, 0.0)

    def test_a_crisis_cuts_the_dividend_to_the_cash_after_commitments_and_production_needs(self):
        year = settle(cash=75.0)
        self.assertEqual(year.state, "crisis")
        self.assertAlmostEqual(year.dividend, 15.0)

    def test_arrears_left_after_service_are_illiquidity_and_idle_the_producer_without_dividend(self):
        year = settle(arrears=5.0, cash=0.0, assets=90.0, debt=150.0, equity_value=-60.0)
        self.assertEqual(year.state, "illiquid")
        self.assertEqual(year.dividend, 0.0)
        self.assertEqual(year.producer.idle_years, finance.BANKRUPTCY_IDLE_YEARS)
        self.assertGreater(year.write_off_ratio, 0.0)

    def test_negative_equity_is_insolvency(self):
        year = settle(equity_value=-1.0, assets=100.0, debt=101.0)
        self.assertEqual(year.state, "insolvent")
        self.assertEqual(year.dividend, 0.0)
        self.assertAlmostEqual(year.write_off_ratio, finance.write_off_ratio(101.0, 100.0, False))


class WriteOffTests(unittest.TestCase):
    def test_the_lender_books_its_loss_and_the_borrower_keeps_the_rest(self):
        record = SimpleNamespace(loans=[Loan("l1", "bank", "f1", "coin", 90.0), Loan("l2", "bank", "f2", "coin", 90.0)],
                                 credit_losses={}, remembered_defaults={})
        lost = firm_year.write_off(record, "f1", 0.5)
        self.assertAlmostEqual(lost, 45.0)
        self.assertAlmostEqual(record.credit_losses["bank"], 45.0)
        self.assertAlmostEqual(record.loans[0].principal, 45.0)
        self.assertAlmostEqual(record.loans[1].principal, 90.0)
        self.assertAlmostEqual(record.remembered_defaults["f1"], 45.0)

    def test_a_ratio_of_zero_changes_nothing(self):
        record = SimpleNamespace(loans=[Loan("l1", "bank", "f1", "coin", 90.0)], credit_losses={}, remembered_defaults={})
        self.assertEqual(firm_year.write_off(record, "f1", 0.0), 0.0)
        self.assertEqual(record.credit_losses, {})
