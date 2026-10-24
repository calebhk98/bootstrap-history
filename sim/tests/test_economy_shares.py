"""Complaint 106: a producer sells shares for the expansion lenders would not fund; savers buy them through a market
that clears at the present value of the producer's expected dividends at the market rate; dividends are paid to
the holders by share; households count the shares they hold as the equity they own."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import credit, equity, ownership, shares
from sim.economy.households_cohort import Cohort
from sim.economy.producers import Producer
from sim.economy.share_market import ShareBid, ShareIssue, clear, equity_value
from sim.economy.types import FundsOffer, LoanRequest, Recipe, Transfer

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


MONEY = "coin"
PRODUCER = "producer:farm"
SAVERS = ["household:farms:0", "household:farms:1"]
OWNER = "household:town:0"


class Book:
    """Records the transfers the record's book is asked to make and answers a balance."""
    def __init__(self, balances=None):
        self.transfers, self.balances = [], balances or {}

    def transfer_many(self, transfers):
        self.transfers.extend(transfers)

    def balance(self, agent, currency):
        return self.balances.get(agent, 0.0)


def cohort(agent_id, tile, ownership_share=1.0):
    return Cohort(agent_id, tile, 0, 100.0, 50.0, ownership_share)


def stand_in_record(balances=None):
    producers = {PRODUCER: Producer(PRODUCER, OWNER, "grow", "town", 4.0)}
    cohorts = {agent: cohort(agent, "farms") for agent in SAVERS}
    cohorts[OWNER] = cohort(OWNER, "town")
    return types.SimpleNamespace(
        book=Book(balances), producers=producers, cohorts=cohorts, shares={}, last_dividends={PRODUCER: 10.0},
        loans=[], remembered_defaults={}, capital=types.SimpleNamespace(funds={}))


def unmet(amount=100.0, yearly_return=0.2):
    return [LoanRequest(PRODUCER, MONEY, amount, yearly_return, 10.0, amount, shares.EXPAND_PURPOSE)]


def offers():
    return [FundsOffer(saver, MONEY, 60.0, 0.01) for saver in SAVERS]


class RaiseEquityTests(unittest.TestCase):
    def setUp(self):
        self.record = stand_in_record()

    def test_savers_buy_the_shares_of_a_producer_whose_expansion_was_not_funded_and_pay_it_what_it_raised(self):
        raised = shares.raise_equity(self.record, MONEY, unmet(), offers(), [], RATE, 0.0)
        self.assertAlmostEqual(raised[PRODUCER], 100.0)
        self.assertAlmostEqual(sum(transfer.amount for transfer in self.record.book.transfers if transfer.payee == PRODUCER), 100.0)
        self.assertEqual(sorted(transfer.payer for transfer in self.record.book.transfers), SAVERS)
        held = self.record.shares[PRODUCER]
        self.assertEqual(sorted(held), SAVERS)
        expected_dividend = 10.0 + 100.0 * 0.2
        self.assertAlmostEqual(sum(held.values()) * equity_value(
            expected_dividend, RATE + credit.risk_premium(100.0, 100.0, 0.0)), 100.0)

    def test_a_request_for_anything_but_plant_is_not_offered_as_shares(self):
        request = LoanRequest(PRODUCER, MONEY, 100.0, 0.2, 1.0, 100.0, "working capital")
        self.assertEqual(shares.raise_equity(self.record, MONEY, [request], offers(), [], RATE, 0.0), {})
        self.assertNotIn(PRODUCER, self.record.shares)

    def test_savers_who_lent_their_funds_have_less_to_buy_with(self):
        lent = [types.SimpleNamespace(lender=saver, principal=1000.0) for saver in SAVERS]
        self.assertEqual(shares.raise_equity(self.record, MONEY, unmet(), offers(), lent, RATE, 0.0), {})

    def test_a_second_issue_dilutes_the_first_holders(self):
        self.record.shares[PRODUCER] = {SAVERS[0]: 0.2, SAVERS[1]: 0.2}
        shares.raise_equity(self.record, MONEY, unmet(), [FundsOffer(SAVERS[0], MONEY, 1000.0, 0.01)], [], RATE, 0.0)
        after = self.record.shares[PRODUCER]
        self.assertLess(after[SAVERS[1]], 0.2)
        self.assertLessEqual(sum(after.values()), 1.0)


class DividendTests(unittest.TestCase):
    def test_the_dividend_is_paid_to_the_holders_by_share_and_the_rest_to_the_owners_tile(self):
        record = stand_in_record()
        record.shares[PRODUCER] = {SAVERS[0]: 0.25, SAVERS[1]: 0.15}
        paid = ownership.spread(record, [Transfer(PRODUCER, OWNER, MONEY, 200.0, "dividend")])
        by_payee = {}
        for transfer in paid:
            by_payee[transfer.payee] = by_payee.get(transfer.payee, 0.0) + transfer.amount
        self.assertAlmostEqual(sum(by_payee.values()), 200.0)
        self.assertAlmostEqual(by_payee[SAVERS[0]], 50.0)
        self.assertAlmostEqual(by_payee[SAVERS[1]], 30.0)
        shared = [transfer for transfer in paid if transfer.purpose == shares.SHARE_DIVIDEND_PURPOSE]
        self.assertAlmostEqual(sum(transfer.amount for transfer in shared), 200.0 * 0.4)


class HoldingsTests(unittest.TestCase):
    def holdings(self, record):
        setup = types.SimpleNamespace(currency_id=MONEY, recipes={"grow": Recipe("grow", {"grain": 1.0}, {}, {"labourer": 1.0})})
        return equity.holdings(setup, record, view=None)

    def test_households_count_the_shares_they_hold_as_part_of_the_producers_worth_not_the_owner_tiles(self):
        record = stand_in_record({PRODUCER: 1000.0})
        before = self.holdings(record)
        record.shares[PRODUCER] = {SAVERS[0]: 0.25}
        after = self.holdings(record)
        gained = after[SAVERS[0]] - before.get(SAVERS[0], 0.0)
        self.assertAlmostEqual(gained, 250.0)
        self.assertAlmostEqual(sum(after.values()), sum(before.values()))     # shared out differently, not made
        self.assertAlmostEqual(before[OWNER] - after[OWNER], gained)


class PruneTests(unittest.TestCase):
    def test_a_closed_producers_shares_are_dropped(self):
        record = stand_in_record()
        record.shares[PRODUCER] = {SAVERS[0]: 0.25}
        del record.producers[PRODUCER]
        shares.prune(record)
        self.assertEqual((record.shares, record.last_dividends), ({}, {}))


class IssuesForTests(unittest.TestCase):
    def test_a_project_that_does_not_earn_the_loan_rate_plus_the_risk_premium_sells_no_shares(self):
        request = LoanRequest(PRODUCER, MONEY, 100.0, 0.08, 10.0, 0.0, shares.EXPAND_PURPOSE)   # no collateral: a premium
        self.assertEqual(shares.issues_for(stand_in_record(), [request], 0.06), [])

    def test_a_buyer_asks_the_premium_a_lender_would_over_the_market_rate(self):
        request = LoanRequest(PRODUCER, MONEY, 100.0, 0.5, 10.0, 0.0, shares.EXPAND_PURPOSE)
        issue = shares.issues_for(stand_in_record(), [request], 0.06)[0]
        self.assertAlmostEqual(issue.premium, credit.risk_premium(100.0, 0.0, 0.0))
        self.assertGreater(issue.premium, 0.0)


if __name__ == "__main__":
    unittest.main()
