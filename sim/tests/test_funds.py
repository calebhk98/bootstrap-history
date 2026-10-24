"""Complaint 106: a fund pools shares and loans that households hold units in. A unit is worth the fund's cash and
marked holdings over its units; households buy and redeem at that worth, and it earns the dividends and interest its
holdings pay. Each rule is called on a record written out here, with a purse that moves balances and nothing else;
the secondary market is a recorder."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import funds, shares
from sim.economy.capital_state import CapitalState, Fund
from sim.economy.producers import Producer
from sim.economy.secondary_trade import BOND_MARKET, SHARE_TRADING, Shortfall
from sim.economy.types import FundsOffer, Loan, Transfer

MARKET_RATE = 0.05
BOTH = (SHARE_TRADING, BOND_MARKET)
MONEY = "coin"
MANAGER, SAVER, OTHER = "household:town:0", "household:farms:0", "household:farms:1"
PRODUCER = "producer:farm"
FUND = "fund:0"


class Purse:
    """Balances by agent; a transfer moves money from payer to payee."""
    def __init__(self, balances):
        self.balances = dict(balances)

    def balance(self, agent, currency):
        return self.balances.get(agent, 0.0)

    def transfer(self, transfer):
        self.balances[transfer.payer] = self.balance(transfer.payer, MONEY) - transfer.amount
        self.balances[transfer.payee] = self.balance(transfer.payee, MONEY) + transfer.amount

    def money_supply(self, currency):
        return sum(self.balances.values())


class FundFixture(unittest.TestCase):
    def setUp(self):
        self.setup = types.SimpleNamespace(currency_id=MONEY, opening_rate=0.05)
        self.record = types.SimpleNamespace(
            book=Purse({SAVER: 1000.0, OTHER: 1000.0}), capital=CapitalState(), shares={}, loans=[],
            remembered_defaults={}, last_dividends={PRODUCER: 20.0}, cohorts={},
            producers={PRODUCER: Producer(PRODUCER, MANAGER, "grow", "town", 4.0)})
        self.fund = Fund(FUND, MANAGER, 0)
        self.record.capital.funds[FUND] = self.fund
        self.money = MONEY
        self.manager, self.saver, self.other = MANAGER, SAVER, OTHER
        self.producer_id = PRODUCER
        self.supply = self.record.book.money_supply(MONEY)

    def balance(self, agent):
        return self.record.book.balance(agent, self.money)

    def price(self, rate=MARKET_RATE):
        return funds.unit_price(self.setup, self.record, self.fund, rate)

    def put_shares_in_fund(self, part=0.2):
        self.record.shares[self.producer_id] = {self.fund.agent_id: part}

    def subscribed(self, amount=100.0, holder=SAVER):
        """The fund as it stands after `holder` paid in `amount` at the first unit's price."""
        self.record.book.transfer(Transfer(holder, FUND, MONEY, amount, "subscribed"))
        self.fund.units[holder] = amount / funds.FIRST_UNIT_PRICE

    def fund_lends_out_its_cash(self, amount):
        self.record.book.transfer(Transfer(FUND, self.other, MONEY, amount, "invested elsewhere"))


class Units(FundFixture):
    def test_the_first_unit_costs_one_unit_of_money_and_a_new_fund_holds_nothing(self):
        self.assertEqual(self.price(), funds.FIRST_UNIT_PRICE)

    def test_a_new_fund_has_no_units_outstanding(self):
        self.assertEqual(funds.units_outstanding(self.fund), 0.0)

    def test_a_household_pays_into_the_fund_and_takes_units_at_the_unit_price(self):
        before = self.balance(self.saver)
        units = funds.subscribe(self.setup, self.record, self.fund, self.saver, 100.0, MARKET_RATE)
        self.assertAlmostEqual(units, 100.0)
        self.assertAlmostEqual(before - self.balance(self.saver), 100.0)
        self.assertAlmostEqual(self.balance(self.fund.agent_id), 100.0)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), self.supply)

    def test_a_household_cannot_pay_in_more_than_it_holds(self):
        funds.subscribe(self.setup, self.record, self.fund, "nobody:without cash", 100.0, MARKET_RATE)
        self.assertEqual(self.fund.units, {})

    def test_a_later_buyer_pays_the_worth_the_marked_holdings_have_given_each_unit(self):
        self.subscribed(100.0)
        self.fund_lends_out_its_cash(100.0)
        self.put_shares_in_fund(0.5)                     # the cash became shares worth more than it
        worth = funds.net_assets(self.setup, self.record, self.fund, MARKET_RATE)
        self.assertAlmostEqual(self.price(), worth / 100.0)
        units = funds.subscribe(self.setup, self.record, self.fund, self.other, 50.0, MARKET_RATE)
        self.assertAlmostEqual(units, 50.0 / (worth / 100.0))

    def test_buying_in_at_the_unit_price_leaves_the_earlier_holders_unit_worth_unchanged(self):
        self.subscribed(100.0)
        self.put_shares_in_fund(0.5)
        before = self.price()
        funds.subscribe(self.setup, self.record, self.fund, self.other, 40.0, MARKET_RATE)
        self.assertAlmostEqual(self.price(), before)

    def test_a_dearer_market_rate_lowers_what_the_holdings_and_so_the_unit_are_worth(self):
        self.subscribed(10.0)
        self.put_shares_in_fund(0.5)
        self.assertGreater(self.price(0.03), self.price(0.09))

    def test_a_fund_holding_loans_marks_them_at_the_rate_a_saver_would_ask(self):
        self.subscribed(10.0)
        self.record.loans.append(Loan("loan:0:1", self.fund.agent_id, self.producer_id, self.money, 100.0, rate=0.05,
                                      years_left=4.0, issued_year=0, collateral_value=100000.0))
        low, high = self.price(0.03), self.price(0.12)
        self.assertGreater(low, high)

    def test_the_fund_is_worth_nothing_when_its_cash_is_gone_and_it_holds_nothing_with_units_outstanding(self):
        self.subscribed(10.0)
        self.fund_lends_out_its_cash(10.0)
        self.assertIsNone(self.price())

    def test_a_fund_worth_nothing_sells_no_units(self):
        self.subscribed(10.0)
        self.fund_lends_out_its_cash(10.0)
        self.assertEqual(funds.subscribe(self.setup, self.record, self.fund, self.other, 5.0, MARKET_RATE), 0.0)


class Redeeming(FundFixture):
    def setUp(self):
        super().setUp()
        self.subscribed(100.0)

    def test_units_are_paid_at_their_worth_from_the_funds_purse(self):
        before = self.balance(self.saver)
        paid = funds.redeem(self.setup, self.record, self.fund, self.saver, 40.0, MARKET_RATE)
        self.assertAlmostEqual(paid, 40.0)
        self.assertAlmostEqual(self.balance(self.saver) - before, 40.0)
        self.assertAlmostEqual(self.fund.units[self.saver], 60.0)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), self.supply)

    def test_no_more_than_the_holder_owns_is_paid(self):
        paid = funds.redeem(self.setup, self.record, self.fund, self.saver, 500.0, MARKET_RATE)
        self.assertAlmostEqual(paid, 100.0)
        self.assertNotIn(self.saver, self.fund.units)

    def test_a_fund_with_less_cash_than_asked_pays_what_it_holds_and_the_units_given_up_are_those_paid_for(self):
        self.fund_lends_out_its_cash(70.0)
        self.put_shares_in_fund(0.5)
        price = self.price()
        paid = funds.redeem(self.setup, self.record, self.fund, self.saver, 90.0, MARKET_RATE)
        self.assertAlmostEqual(paid, 30.0)
        self.assertAlmostEqual(self.fund.units[self.saver], 100.0 - 30.0 / price)

    def test_a_fund_short_of_cash_offers_holdings_to_the_savers_as_a_seller_that_needs_the_cash(self):
        self.fund_lends_out_its_cash(100.0)
        self.put_shares_in_fund(0.5)
        offers = [FundsOffer(self.other, self.money, 5000.0, 0.04)]
        calls = []

        def market(setup, record, offered, shortfalls, market_rate, institutions, sellers=()):
            calls.append((offered, shortfalls, market_rate, institutions, list(sellers)))
            return offered, []

        wanted = min(50.0, 100.0 * self.price())
        with mock.patch.object(funds.secondary_trade, "run", market):
            funds.redeem_for_cash(self.setup, self.record, self.fund, self.saver, 50.0, offers, MARKET_RATE, BOTH)
        self.assertEqual(calls, [(offers, {self.fund.agent_id: Shortfall(wanted, MARKET_RATE)}, MARKET_RATE, BOTH,
                                  [self.fund.agent_id])])

    def test_a_fund_with_the_cash_does_not_go_to_the_market(self):
        calls = []
        with mock.patch.object(funds.secondary_trade, "run", lambda *arguments, **options: calls.append(arguments)):
            funds.redeem_for_cash(self.setup, self.record, self.fund, self.saver, 50.0, [], MARKET_RATE, BOTH)
        self.assertEqual(calls, [])

    def test_a_fund_with_a_market_that_sells_nothing_pays_only_the_cash_it_holds(self):
        self.fund_lends_out_its_cash(100.0)
        self.put_shares_in_fund(0.5)
        before = self.balance(self.saver)
        with mock.patch.object(funds.secondary_trade, "run", lambda setup, record, offers, *rest, **options: (offers, [])):
            funds.redeem_for_cash(self.setup, self.record, self.fund, self.saver, 50.0, [], MARKET_RATE, ())
        self.assertAlmostEqual(self.balance(self.saver), before)


class WhatTheFundEarnsAndBuys(FundFixture):
    def test_a_dividend_on_shares_the_fund_holds_is_paid_into_its_purse(self):
        self.put_shares_in_fund(0.25)
        paid = shares.split_dividend(self.record, Transfer(self.producer_id, self.record.producers[self.producer_id].owner,
                                                           self.money, 200.0, "dividend"))
        to_fund = [transfer for transfer in paid if transfer.payee == self.fund.agent_id]
        self.assertAlmostEqual(sum(transfer.amount for transfer in to_fund), 50.0)

    def test_the_expected_income_is_its_part_of_the_last_dividend_and_the_interest_on_its_loans(self):
        self.put_shares_in_fund(0.25)
        self.record.loans.append(Loan("loan:0:1", self.fund.agent_id, self.producer_id, self.money, 100.0, rate=0.07,
                                      years_left=4.0, issued_year=0))
        self.assertAlmostEqual(funds.expected_income(self.record, self.fund), 0.25 * 20.0 + 7.0)

    def test_the_yield_is_the_expected_income_over_the_worth(self):
        self.subscribed(100.0)
        self.record.last_dividends[self.producer_id] = 0.0
        self.record.loans.append(Loan("loan:0:1", self.fund.agent_id, self.producer_id, self.money, 100.0, rate=0.07,
                                      years_left=4.0, issued_year=0, collateral_value=100000.0))
        worth = funds.net_assets(self.setup, self.record, self.fund, MARKET_RATE)
        self.assertAlmostEqual(funds.yield_of(self.setup, self.record, self.fund, MARKET_RATE), 7.0 / worth)

    def test_a_fund_with_cash_offers_it_to_the_credit_market_at_the_market_rate(self):
        self.subscribed(400.0)
        offer = funds.offer_of(self.setup, self.record, self.fund, 0.04)
        self.assertEqual((offer.lender, offer.currency, offer.amount, offer.minimum_rate), (FUND, MONEY, 400.0, 0.04))

    def test_a_fund_with_no_cash_makes_no_offer(self):
        self.assertIsNone(funds.offer_of(self.setup, self.record, self.fund, MARKET_RATE))

    def test_the_units_a_household_holds_are_listed_by_fund(self):
        self.subscribed(100.0)
        self.assertEqual(funds.owned_by(self.record, self.saver), {self.fund.agent_id: 100.0})
        self.assertEqual(funds.owned_by(self.record, self.other), {})


if __name__ == "__main__":
    unittest.main()
