"""`credit.clear_with_cause` (the kernel `clear_loans` over a requests table and an offers table) against the Python it replaced
(`credit_clear_plain.py`), on random markets that reach every branch: no offers, no one able to borrow, a rate ceiling that rations
by risk or that no lender accepts, lenders with a risk capacity, requests cut to their collateral, ties in rates and names. The loans,
rate, unmet requests, cause and limited borrowers are equal to the last bit."""

QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.economy import credit, credit_clearing
from sim.loans.clearing_kernel import TABLE_FULL, clear_loans
from sim.loans.clearing_tables import CLEARED, NEW_LOANS, NewLoans
from sim.economy.types import FundsOffer, LoanRequest
from sim.tests import credit_clear_plain as plain

NAMES = ["household:%d" % number for number in range(9)] + ["bank:0", "fund:1"]


def random_market(seed: int):
    rng = random.Random(seed)
    rates = (0.0, 0.02, 0.05, rng.uniform(0.0, 0.2))
    requests = [LoanRequest(
        rng.choice(NAMES), rng.choice(("coin", "coin", "gold")), rng.choice((0.0, 5.0, rng.uniform(1.0, 400.0), rng.uniform(1.0, 400.0))),
        rng.choice((0.01, 0.05, rng.uniform(0.0, 0.5))), rng.choice((1, 2.0, 5.0)), rng.choice((0.0, 50.0, rng.uniform(0.0, 600.0))),
        rng.choice(("subsistence", "expand")), rng.choice(("", "tile:a")), rng.choice((0.0, 0.1, rng.random() * 0.4)))
        for _ in range(rng.randrange(0, 14))]
    offers = [FundsOffer(rng.choice(NAMES), rng.choice(("coin", "coin", "gold")), rng.choice((0.0, 20.0, rng.uniform(5.0, 600.0))),
                         rng.choice(rates), rng.choice((None, None, rng.uniform(0.0, 40.0))))
              for _ in range(rng.randrange(0, 8))]
    debt = {name: rng.choice((0.0, rng.uniform(0.0, 500.0))) for name in NAMES if rng.random() < 0.6}
    arrears = {name: rng.uniform(0.0, 80.0) for name in NAMES if rng.random() < 0.3}
    options = dict(last_rate=rng.choice((None, 0.05, rng.uniform(0.0, 0.2))), year=rng.randrange(0, 5),
                   rate_ceiling=rng.choice((None, None, 0.01, 0.06, 0.5)), expected_inflation=rng.choice((0.0, 0.02)),
                   clearing=rng.choice(("year", "working_capital")))
    return requests, offers, debt, arrears, options


def fields(result):
    return (result.loans, result.rate, result.unmet, result.cause, dict(result.limited))


class ClearingKernel(unittest.TestCase):
    def call(self, module, requests, offers, debt, arrears, options):
        return module.clear_with_cause(requests, offers, "coin", options["last_rate"], debt, arrears, year=options["year"],
                                       rate_ceiling=options["rate_ceiling"], expected_inflation=options["expected_inflation"],
                                       clearing=options["clearing"])

    def test_random_markets_clear_as_the_python_cleared_them(self):
        causes = set()
        for seed in range(400):
            requests, offers, debt, arrears, options = random_market(seed)
            wanted = fields(self.call(plain, requests, offers, debt, arrears, options))
            found = fields(self.call(credit, requests, offers, debt, arrears, options))
            self.assertEqual(found, wanted, "seed %d" % seed)
            causes.add(wanted[3])
        self.assertEqual(causes, {None, "no_offers", "no_borrower_at_ask", "no_offer_at_rate"})      # every way out was reached

    def test_the_markets_reach_rationing_by_risk_and_cut_requests(self):
        rationed = cut = capped = 0
        for seed in range(400):
            requests, offers, debt, arrears, options = random_market(seed)
            result = self.call(plain, requests, offers, debt, arrears, options)
            cut += bool(result.limited)
            capped += any(offer.risk_capacity is not None for offer in offers) and bool(result.loans)
            rationed += options["rate_ceiling"] is not None and result.rate is not None and bool(result.loans)
        self.assertGreater(cut, 5)
        self.assertGreater(capped, 5)
        self.assertGreater(rationed, 5)

    def test_a_loans_table_with_no_room_reports_it_and_a_bigger_one_clears(self):
        requests = [LoanRequest("household:%d" % number, "coin", 100.0, 0.5, 2.0, 1000.0, "expand") for number in range(6)]
        offers = [FundsOffer("fund:%d" % number, "coin", 3.0 + number % 3, 0.01) for number in range(6)]
        table, offered = credit_clearing.request_table(requests, {}, {}), credit_clearing.offer_table(offers)
        scalars = numpy.zeros(2)
        small = NEW_LOANS.new_table(NewLoans, 1)
        status = clear_loans(table, offered, credit_clearing.constants(), 0.05, True, 0.0, False, 0.0, small, scalars)
        self.assertEqual(status, TABLE_FULL)
        status, _scalars, loans = credit_clearing.run_kernel(table, offered, 0.05, None, 0.0)
        self.assertEqual(status, CLEARED)
        self.assertGreater(int(loans.row_count[0]), 1)


if __name__ == "__main__":
    unittest.main()
