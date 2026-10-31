"""Eurace credit rule (Credit/Bank_Credit_Functions.c): a borrower's default probability from its leverage, a bank's
lending capped by the value at risk its equity allows, the rate a base plus a markup on that probability."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import bank_credit_risk, credit
from sim.economy.types import FundsOffer, Loan, LoanRequest


class DefaultProbabilityTests(unittest.TestCase):
    def test_probability_rises_with_debt_over_equity(self):
        expected = 1.0 - math.exp(-bank_credit_risk.DEFAULT_PROBABILITY_SENSITIVITY * (40.0 + 10.0) / 100.0)
        self.assertAlmostEqual(bank_credit_risk.default_probability(40.0, 10.0, 100.0), expected)

    def test_no_equity_means_certain_default_not_a_division_by_zero(self):
        self.assertEqual(bank_credit_risk.default_probability(10.0, 10.0, 0.0), 1.0)

    def test_no_debt_and_no_request_means_no_default(self):
        self.assertEqual(bank_credit_risk.default_probability(0.0, 0.0, 100.0), 0.0)


class ValueAtRiskTests(unittest.TestCase):
    def test_value_at_risk_is_each_loan_times_its_default_probability(self):
        self.assertAlmostEqual(bank_credit_risk.value_at_risk([(100.0, 0.1), (50.0, 0.2)]), 20.0)

    def test_headroom_is_alpha_times_equity_less_value_at_risk(self):
        self.assertAlmostEqual(bank_credit_risk.var_headroom(100.0, 300.0),
                               bank_credit_risk.BANK_ALFA * 100.0 - 300.0)

    def test_headroom_is_nil_for_a_bank_with_no_equity_or_over_its_limit(self):
        self.assertEqual(bank_credit_risk.var_headroom(-5.0, 0.0), 0.0)
        self.assertEqual(bank_credit_risk.var_headroom(1.0, 1e9), 0.0)


class ExposureTests(unittest.TestCase):
    def test_a_loan_s_exposure_is_its_principal_and_its_borrower_s_default_probability(self):
        loan = Loan("loan:0", "bank", "b", "coin", 60.0, 0.05, 3.0, collateral_value=100.0)
        exposures = bank_credit_risk.exposures([loan], {"b": 80.0})
        self.assertEqual(len(exposures), 1)
        self.assertEqual(exposures[0][0], 60.0)
        self.assertAlmostEqual(exposures[0][1], bank_credit_risk.default_probability(80.0, 0.0, 100.0))


class RiskMarkupTests(unittest.TestCase):
    def test_the_leverage_markup_is_lambda_times_probability_times_the_reference_rate(self):
        probability = bank_credit_risk.default_probability(100.0, 0.0, 100.0)
        self.assertAlmostEqual(credit.risk_premium(100.0, 100.0, 0.0),
                               bank_credit_risk.markup(probability))
        self.assertAlmostEqual(bank_credit_risk.markup(probability), bank_credit_risk.BANK_LAMBDA
                               * probability * bank_credit_risk.MARKUP_REFERENCE_RATE)


class ValueAtRiskCapTests(unittest.TestCase):
    def test_a_lender_with_little_headroom_lends_less_than_it_holds(self):
        request = LoanRequest("b", "coin", 100.0, 0.9, 1.0, 100.0, "working capital")
        probability = bank_credit_risk.default_probability(0.0, 100.0, 100.0)
        offer = FundsOffer("bank", "coin", 1000.0, 0.05, risk_capacity=probability * 40.0)
        loans, _rate, unmet = credit.clear([request], [offer], "coin", None, {})
        self.assertEqual(loans, [])         # a request that does not fit the headroom is refused whole (the C)
        self.assertAlmostEqual(sum(item.amount for item in unmet), 100.0)

    def test_a_request_that_fits_the_headroom_is_lent_in_full(self):
        request = LoanRequest("b", "coin", 100.0, 0.9, 1.0, 100.0, "working capital")
        probability = bank_credit_risk.default_probability(0.0, 100.0, 100.0)
        offer = FundsOffer("bank", "coin", 1000.0, 0.05, risk_capacity=probability * 100.0 + 1e-6)
        loans, _rate, unmet = credit.clear([request], [offer], "coin", None, {})
        self.assertAlmostEqual(sum(item.principal for item in loans), 100.0)
        self.assertEqual(unmet, [])


if __name__ == "__main__":
    unittest.main()
