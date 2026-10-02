"""The credit market: rates that follow funds, rationing of risky borrowers, servicing, default cascades."""
import random
import unittest

from sim.economy import credit
from sim.economy.types import FundsOffer, Loan, LoanRequest


def request(borrower, amount, maximum_rate, collateral=0.0, years=5.0):
    return LoanRequest(borrower, "coin", amount, maximum_rate, years, collateral, "working capital")


def funds(lender, amount, minimum_rate):
    return FundsOffer(lender, "coin", amount, minimum_rate)


def loan(loan_id, lender, borrower, principal, rate=0.1, years_left=4.0, arrears=0.0):
    return Loan(loan_id, lender, borrower, "coin", principal, rate, years_left, 0.0, arrears)


class RiskPremiumTests(unittest.TestCase):
    def test_leverage_raises_the_premium(self):
        self.assertLess(credit.risk_premium(100.0, 300.0, 0.0), credit.risk_premium(100.0, 20.0, 0.0))

    def test_arrears_raise_the_premium(self):
        self.assertLess(credit.risk_premium(100.0, 100.0, 0.0), credit.risk_premium(100.0, 100.0, 40.0))

    def test_no_debt_no_premium(self):
        self.assertEqual(credit.risk_premium(0.0, 0.0, 0.0), 0.0)


class ClearingTests(unittest.TestCase):
    def test_loans_fund_requests_and_disbursements_move_money(self):
        loans, base_rate, unmet = credit.clear([request("b", 100, 0.3, 500.0)], [funds("l", 150, 0.05)],
                                               "coin", None, {})
        self.assertAlmostEqual(sum(item.principal for item in loans), 100)
        self.assertEqual(unmet, [])
        self.assertGreater(base_rate, 0.05)
        transfers = credit.disbursements(loans)
        self.assertEqual({(t.payer, t.payee) for t in transfers}, {("l", "b")})
        self.assertAlmostEqual(sum(t.amount for t in transfers), 100)

    def test_scarce_funds_ration_requests_and_report_the_rest(self):
        loans, _rate, unmet = credit.clear([request("b1", 100, 0.5, 500.0), request("b2", 100, 0.5, 500.0)],
                                           [funds("l", 120, 0.05)], "coin", None, {})
        self.assertAlmostEqual(sum(item.principal for item in loans), 120)
        self.assertAlmostEqual(sum(item.amount for item in unmet), 80)

    def test_a_borrower_whose_risk_premium_exceeds_its_ceiling_gets_nothing(self):
        risky = request("risky", 100, 0.06, 0.0)
        safe = request("safe", 100, 0.5, 1000.0)
        loans, _rate, unmet = credit.clear([risky, safe], [funds("l", 500, 0.05)], "coin", None, {})
        self.assertEqual({item.borrower for item in loans}, {"safe"})
        self.assertEqual([item.borrower for item in unmet], ["risky"])

    def test_leverage_raises_the_rate_a_borrower_pays(self):
        offers = [funds("l", 1000, 0.05)]
        light, _, _ = credit.clear([request("b", 50, 0.9, 500.0)], offers, "coin", 0.05, {})
        heavy, _, _ = credit.clear([request("b", 50, 0.9, 500.0)], offers, "coin", 0.05, {"b": 2000.0})
        self.assertGreater(heavy[0].rate, light[0].rate)

    def test_base_rate_is_sticky_and_never_passes_the_clearing_rate(self):
        offers = [funds("l", 100, 0.04)]
        requests = [request("b", 200, 0.20, 10000.0)]
        _, first, _ = credit.clear(requests, offers, "coin", None, {})
        rate = 0.04
        rates = []
        for _ in range(10):
            _, rate, _ = credit.clear(requests, offers, "coin", rate, {})
            rates.append(rate)
        self.assertTrue(all(later >= earlier for earlier, later in zip(rates, rates[1:])))
        self.assertTrue(all(value <= first + 1e-9 for value in rates))
        self.assertGreater(rates[0], 0.04)

    def test_other_currencies_are_ignored(self):
        other = LoanRequest("b", "bronze", 10.0, 0.5, 5.0, 100.0, "x")
        loans, _rate, unmet = credit.clear([other], [funds("l", 100, 0.05)], "coin", None, {})
        self.assertEqual((loans, unmet), ([], []))

    def test_loan_ids_are_deterministic_and_input_order_does_not_matter(self):
        rng = random.Random(3)
        requests = [request("b%d" % i, 30 + i, 0.4, 100.0 * i) for i in range(6)]
        offers = [funds("l%d" % i, 40 + i, 0.03 + 0.01 * i) for i in range(4)]
        reference = credit.clear(requests, offers, "coin", 0.05, {"b1": 20.0}, year=3)
        for _ in range(5):
            rng.shuffle(requests)
            rng.shuffle(offers)
            self.assertEqual(credit.clear(requests, offers, "coin", 0.05, {"b1": 20.0}, year=3), reference)
        ids = [item.loan_id for item in reference[0]]
        self.assertEqual(len(ids), len(set(ids)))


class ServiceTests(unittest.TestCase):
    def test_a_borrower_with_cash_pays_interest_and_an_installment(self):
        transfers, updated, defaults = credit.service([loan("loan:1", "l", "b", 100.0, 0.1, 4.0)],
                                                      {"b": 1000.0}, 1)
        self.assertAlmostEqual(sum(t.amount for t in transfers), 10.0 + 25.0)
        self.assertEqual(defaults, [])
        self.assertAlmostEqual(updated[0].principal, 75.0)
        self.assertAlmostEqual(updated[0].years_left, 3.0)
        self.assertEqual(updated[0].arrears, 0.0)

    def test_a_loan_is_removed_when_repaid(self):
        _t, updated, defaults = credit.service([loan("loan:1", "l", "b", 100.0, 0.1, 1.0)], {"b": 1000.0}, 1)
        self.assertEqual((updated, defaults), ([], []))

    def test_a_short_borrower_pays_what_it_can_and_owes_the_rest(self):
        transfers, updated, defaults = credit.service([loan("loan:1", "l", "b", 100.0, 0.1, 10.0)],
                                                      {"b": 12.0}, 1)
        self.assertAlmostEqual(sum(t.amount for t in transfers), 12.0)
        self.assertAlmostEqual(updated[0].arrears, 20.0 - 12.0 + 0.0)
        self.assertEqual(defaults, [])

    def test_arrears_past_the_threshold_default_and_no_money_moves(self):
        transfers, updated, defaults = credit.service([loan("loan:1", "l", "b", 100.0, 0.1, 2.0, arrears=45.0)],
                                                      {"b": 0.0}, 1)
        self.assertEqual((transfers, updated), ([], []))
        self.assertEqual(len(defaults), 1)
        self.assertEqual((defaults[0].lender, defaults[0].borrower), ("l", "b"))
        self.assertGreater(defaults[0].loss, 0.0)

    def test_cash_is_shared_across_a_borrowers_loans(self):
        loans = [loan("loan:1", "l1", "b", 100.0, 0.1, 4.0), loan("loan:2", "l2", "b", 100.0, 0.1, 4.0)]
        transfers, _updated, _defaults = credit.service(loans, {"b": 40.0}, 1)
        self.assertAlmostEqual(sum(t.amount for t in transfers), 40.0)

    def test_default_cascades_up_a_chain_of_lenders(self):
        # c owes b and b owes a; c has no cash, so b has no inflow, so b cannot pay a either
        loans = [loan("loan:1", "b", "c", 100.0, 0.1, 3.0), loan("loan:2", "a", "b", 100.0, 0.1, 3.0)]
        cash = {"c": 0.0, "b": 0.0}
        defaulted = []
        for year in range(1, 6):
            transfers, loans, defaults = credit.service(loans, cash, year)
            defaulted.append([item.loan_id for item in defaults])
            for transfer in transfers:
                cash[transfer.payer] -= transfer.amount
                cash[transfer.payee] = cash.get(transfer.payee, 0.0) + transfer.amount
        flat = [loan_id for year in defaulted for loan_id in year]
        self.assertIn("loan:1", flat)
        self.assertIn("loan:2", flat)
        self.assertLess(flat.index("loan:1"), flat.index("loan:2") + 1)
        self.assertEqual(loans, [])


if __name__ == "__main__":
    unittest.main()
