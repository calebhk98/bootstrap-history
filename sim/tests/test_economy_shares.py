"""Complaint 106: a producer sells shares for the expansion lenders would not fund; savers buy them through a market
that clears at the present value of the producer's expected dividends at the market rate; dividends are paid to
the holders by share; households count the shares they hold as the equity they own."""

QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.economy import credit, economy as economy_module, equity, ownership, shares
from sim.economy.economy import Economy
from sim.economy.record import EconomyRecord
from sim.economy.share_market import ShareBid, ShareIssue, clear, equity_value
from sim.economy.types import FundsOffer, LoanRequest, Transfer
from sim.economy.year_ledger import YearLedger
from sim.tests import economy_fixture as fixture

RATE = 0.05


class ShareMarketTests(unittest.TestCase):
    def test_a_share_is_priced_at_the_present_value_of_the_dividends_at_the_market_rate(self):
        issue = ShareIssue("firm", amount=100.0, expected_dividend=20.0)
        bids = [ShareBid("saver:a", 500.0, 0.02), ShareBid("saver:b", 500.0, 0.03)]
        fills, rate = clear([issue], bids, RATE)
        self.assertEqual(rate, RATE)
        whole = equity_value(20.0, RATE)
        self.assertAlmostEqual(whole, 400.0)
        self.assertAlmostEqual(sum(fill.paid for fill in fills), 100.0)
        for fill in fills:
            self.assertAlmostEqual(fill.paid, fill.share * whole)

    def test_the_issuer_raises_what_it_asked_and_the_buyers_pay_in_proportion_to_their_funds(self):
        issue = ShareIssue("firm", amount=100.0, expected_dividend=20.0)
        fills, _rate = clear([issue], [ShareBid("a", 60.0, 0.0), ShareBid("b", 20.0, 0.0), ShareBid("c", 100.0, 0.0)], RATE)
        paid = {fill.buyer: fill.paid for fill in fills}
        self.assertAlmostEqual(paid["a"], 3.0 * paid["b"])
        self.assertAlmostEqual(sum(paid.values()), 100.0)

    def test_when_only_buyers_who_ask_more_are_left_the_price_falls_and_more_of_the_firm_is_sold(self):
        issue = ShareIssue("firm", amount=100.0, expected_dividend=20.0)
        cheap, cheap_rate = clear([issue], [ShareBid("a", 500.0, 0.01)], RATE)
        dear, dear_rate = clear([issue], [ShareBid("a", 50.0, 0.01), ShareBid("b", 500.0, 0.15)], RATE)
        self.assertGreater(dear_rate, cheap_rate)
        self.assertLess(equity_value(20.0, dear_rate), equity_value(20.0, cheap_rate))
        self.assertGreater(sum(fill.share for fill in dear), sum(fill.share for fill in cheap))
        self.assertAlmostEqual(sum(fill.paid for fill in dear), 100.0)

    def test_buyers_funds_short_of_the_issue_fill_it_in_part_at_the_same_price(self):
        issue = ShareIssue("firm", amount=100.0, expected_dividend=20.0)
        fills, rate = clear([issue], [ShareBid("a", 40.0, 0.0)], RATE)
        self.assertAlmostEqual(sum(fill.paid for fill in fills), 40.0)
        self.assertAlmostEqual(sum(fill.share for fill in fills), 40.0 / equity_value(20.0, rate))

    def test_a_firm_expected_to_pay_nothing_sells_nothing(self):
        self.assertEqual(clear([ShareIssue("firm", 100.0, 0.0)], [ShareBid("a", 500.0, 0.0)], RATE)[0], [])

    def test_no_more_than_the_part_unsold_is_sold(self):
        issue = ShareIssue("firm", amount=1000.0, expected_dividend=1.0, available=0.2)
        fills, _rate = clear([issue], [ShareBid("a", 5000.0, 0.0)], RATE)
        self.assertAlmostEqual(sum(fill.share for fill in fills), 0.2)


def economy_with_a_producer():
    economy = Economy(fixture.small_setup())
    record = economy.record
    producer_id = sorted(record.producers)[0]
    return economy, record, producer_id


class SharesOnTheRecordTests(unittest.TestCase):
    def setUp(self):
        self.economy, self.record, self.producer_id = economy_with_a_producer()
        self.money = self.economy.setup.currency_id
        self.savers = sorted(self.record.cohorts)[:2]
        self.record.last_dividends[self.producer_id] = 10.0

    def unmet(self, amount=100.0, yearly_return=0.2):
        return [LoanRequest(self.producer_id, self.money, amount, yearly_return, 10.0, amount, shares.EXPAND_PURPOSE)]

    def offers(self):
        return [FundsOffer(saver, self.money, 60.0, 0.01) for saver in self.savers]

    def test_savers_buy_the_shares_of_a_producer_whose_expansion_was_not_funded_and_money_is_conserved(self):
        supply = self.record.book.money_supply(self.money)
        cash = self.record.book.balance(self.producer_id, self.money)
        raised = shares.raise_equity(self.record, self.money, self.unmet(), self.offers(), [], RATE, 0.0)
        self.assertAlmostEqual(raised[self.producer_id], 100.0)
        self.assertAlmostEqual(self.record.book.balance(self.producer_id, self.money), cash + 100.0)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), supply)
        held = self.record.shares[self.producer_id]
        self.assertEqual(sorted(held), self.savers)
        expected_dividend = 10.0 + 100.0 * 0.2
        self.assertAlmostEqual(sum(held.values()) * equity_value(expected_dividend, RATE + credit.risk_premium(100.0, 100.0, 0.0)), 100.0)

    def test_a_request_for_anything_but_plant_is_not_offered_as_shares(self):
        request = LoanRequest(self.producer_id, self.money, 100.0, 0.2, 1.0, 100.0, "working capital")
        self.assertEqual(shares.raise_equity(self.record, self.money, [request], self.offers(), [], RATE, 0.0), {})
        self.assertNotIn(self.producer_id, self.record.shares)

    def test_savers_who_lent_their_funds_have_less_to_buy_with(self):
        lent = [type("Loan", (), {"lender": saver, "principal": 1000.0})() for saver in self.savers]
        self.assertEqual(shares.raise_equity(self.record, self.money, self.unmet(), self.offers(), lent, RATE, 0.0), {})

    def test_a_second_issue_dilutes_the_first_holders(self):
        shares.raise_equity(self.record, self.money, self.unmet(), self.offers(), [], RATE, 0.0)
        before = dict(self.record.shares[self.producer_id])
        shares.raise_equity(self.record, self.money, self.unmet(), [FundsOffer(self.savers[0], self.money, 1000.0, 0.01)],
                            [], RATE, 0.0)
        after = self.record.shares[self.producer_id]
        self.assertLess(after[self.savers[1]], before[self.savers[1]])
        self.assertLessEqual(sum(after.values()), 1.0)

    def test_the_dividend_is_paid_to_the_holders_by_share_and_the_rest_to_the_owners_tile(self):
        self.record.shares[self.producer_id] = {self.savers[0]: 0.25, self.savers[1]: 0.15}
        owner = self.record.producers[self.producer_id].owner
        paid = ownership.spread(self.record, [Transfer(self.producer_id, owner, self.money, 200.0, "dividend")])
        by_payee = {}
        for transfer in paid:
            by_payee[transfer.payee] = by_payee.get(transfer.payee, 0.0) + transfer.amount
        self.assertAlmostEqual(sum(by_payee.values()), 200.0)
        self.assertGreaterEqual(by_payee[self.savers[0]], 50.0 - 1e-9)
        shared = [transfer for transfer in paid if transfer.purpose == shares.SHARE_DIVIDEND_PURPOSE]
        self.assertAlmostEqual(sum(transfer.amount for transfer in shared), 200.0 * 0.4)

    def test_households_count_the_shares_they_hold_as_part_of_the_producers_worth_not_the_owner_tiles(self):
        view = self.economy.view()
        before = equity.holdings(self.economy.setup, self.record, view)
        outsider = next(cohort for cohort in sorted(self.record.cohorts)
                        if self.record.cohorts[cohort].tile != self.record.cohorts[self.record.producers[self.producer_id].owner].tile)
        self.record.shares[self.producer_id] = {outsider: 0.25}
        after = equity.holdings(self.economy.setup, self.record, view)
        gained = after[outsider] - before.get(outsider, 0.0)
        self.assertGreater(gained, 0.0)
        self.assertAlmostEqual(sum(after.values()), sum(before.values()))     # shared out differently, not made
        owner_tile = self.record.cohorts[self.record.producers[self.producer_id].owner].tile
        lost = sum(before[cohort] - after[cohort] for cohort in before if self.record.cohorts[cohort].tile == owner_tile)
        self.assertAlmostEqual(lost, gained)

    def test_a_closed_producers_shares_are_dropped(self):
        self.record.shares[self.producer_id] = {self.savers[0]: 0.25}
        del self.record.producers[self.producer_id]
        shares.prune(self.record)
        self.assertEqual(self.record.shares, {})

    def test_the_shares_survive_the_save(self):
        self.record.shares[self.producer_id] = {self.savers[0]: 0.25}
        self.record.last_dividends[self.producer_id] = 7.5
        loaded = EconomyRecord.from_record(self.record.to_record())
        self.assertEqual(loaded.shares, self.record.shares)
        self.assertEqual(loaded.last_dividends, self.record.last_dividends)


class ExpansionThroughShares(unittest.TestCase):
    def test_a_plant_request_the_loan_market_leaves_unmet_is_built_from_the_shares_savers_buy(self):
        economy, record, producer_id = economy_with_a_producer()
        money = economy.setup.currency_id
        saver = sorted(record.cohorts)[0]
        record.last_dividends[producer_id] = 10.0
        request = LoanRequest(producer_id, money, 100.0, 0.25, 10.0, 100.0, shares.EXPAND_PURPOSE)
        record.loan_requests = [request]
        record.expansion_runs = {producer_id: 4.0}
        offers = [FundsOffer(saver, money, 500.0, 0.06)]
        cash = record.book.balance(producer_id, money)
        with mock.patch.object(economy_module.credit, "clear_with_cause", return_value=credit.Clearing([], 0.06, [request])):
            plant_runs = economy._lend(offers, economy.view(), {}, YearLedger())
        self.assertEqual(record.loans, [])
        self.assertAlmostEqual(plant_runs[producer_id], 4.0)
        self.assertIn(saver, record.shares[producer_id])
        self.assertAlmostEqual(record.book.balance(producer_id, money) - cash, 100.0)

    def test_a_project_that_does_not_earn_the_loan_rate_plus_the_risk_premium_sells_no_shares(self):
        economy, record, producer_id = economy_with_a_producer()
        money = economy.setup.currency_id
        request = LoanRequest(producer_id, money, 100.0, 0.08, 10.0, 0.0, shares.EXPAND_PURPOSE)   # no collateral: a premium
        record.last_dividends[producer_id] = 10.0
        self.assertEqual(shares.issues_for(record, [request], 0.06), [])

    def test_a_buyer_asks_the_premium_a_lender_would_over_the_market_rate(self):
        economy, record, producer_id = economy_with_a_producer()
        money = economy.setup.currency_id
        request = LoanRequest(producer_id, money, 100.0, 0.5, 10.0, 0.0, shares.EXPAND_PURPOSE)
        record.last_dividends[producer_id] = 10.0
        issue = shares.issues_for(record, [request], 0.06)[0]
        self.assertAlmostEqual(issue.premium, credit.risk_premium(100.0, 0.0, 0.0))
        self.assertGreater(issue.premium, 0.0)


if __name__ == "__main__":
    unittest.main()
