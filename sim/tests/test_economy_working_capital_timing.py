"""Complaint 546: a working-capital loan asked at a year's close must reach the producer before that year's
plan, or it pays for nothing it was asked for. Its money arrived after the plan, sat through the year, and
left as a dividend at the close."""
import unittest
from unittest import mock

from sim.economy import lending, producers, producers_close
from sim.economy.economy import Economy
from sim.economy.types import LoanRequest, Transfer
from sim.tests import economy_fixture as fixture

ASKED = 50.0


def short_producer_economy():
    """A year in, with one producer's cash drained to the households and a working-capital request on file."""
    setup = fixture.small_setup()
    economy = Economy(setup)
    economy.step(fixture.quiet_year(setup))
    record = economy.record
    producer_id = sorted(record.producers)[0]
    cohort_id = sorted(record.cohorts)[0]
    drained = record.book.balance(producer_id, setup.currency_id)
    record.book.transfer(Transfer(producer_id, cohort_id, setup.currency_id, drained, "test"))
    record.loan_requests.clear()               # only the request this test files
    record.loan_requests.append(LoanRequest(producer_id, setup.currency_id, ASKED, 0.5, 1.0, ASKED,
                                            producers_close.WORKING_CAPITAL_PURPOSE))
    return economy, producer_id


class WorkingCapitalTimingTests(unittest.TestCase):
    def test_the_loan_is_struck_before_the_plan_and_falls_due_at_the_end_of_the_year_it_funds(self):
        economy, producer_id = short_producer_economy()
        year = economy.view().year
        loans_before = len(economy.record.loans)
        before = economy.record.book.balance(producer_id, economy.setup.currency_id)
        lending.lend_working_capital(economy.setup, economy.record, economy.view())
        loans = [loan for loan in economy.record.loans[loans_before:] if loan.borrower == producer_id]
        self.assertAlmostEqual(sum(loan.principal for loan in loans), ASKED)
        self.assertTrue(all(loan.issued_year == year - 1 for loan in loans))     # first payment due this year's end
        self.assertAlmostEqual(economy.record.book.balance(producer_id, economy.setup.currency_id) - before, ASKED)
        self.assertEqual([request for request in economy.record.loan_requests
                          if request.purpose == producers_close.WORKING_CAPITAL_PURPOSE], [])

    def test_other_requests_wait_for_the_year_s_ordinary_lending(self):
        economy, producer_id = short_producer_economy()
        other = LoanRequest(producer_id, economy.setup.currency_id, 5.0, 0.5, 5.0, 5.0, "plant")
        economy.record.loan_requests.append(other)
        lending.lend_working_capital(economy.setup, economy.record, economy.view())
        self.assertEqual(economy.record.loan_requests, [other])

    def test_the_plan_sees_the_cash_the_loan_brought(self):
        economy, producer_id = short_producer_economy()
        seen = {}
        real_plan = producers.plan

        def watching(producer, recipe, view, cash):
            seen[producer.agent_id] = cash
            return real_plan(producer, recipe, view, cash)

        with mock.patch.object(producers, "plan", watching):
            economy.step(fixture.quiet_year(economy.setup))
        self.assertGreaterEqual(seen[producer_id], ASKED - 1e-9)


if __name__ == "__main__":
    unittest.main()
