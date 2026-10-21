"""Complaint 106: a fund pools shares and loans that households hold units in. A unit is worth the fund's cash and
marked holdings over its units; households buy and redeem at that worth, the fund buys and sells in the secondary
market like a saver, and it earns the dividends and interest its holdings pay. Rules on the record built by hand."""

QUICK_TOPIC = True

import unittest

from sim.economy import funds, secondary_trade, shares
from sim.economy.economy import Economy
from sim.economy.record import EconomyRecord
from sim.economy.secondary_trade import BOND_MARKET, SHARE_TRADING
from sim.economy.types import FundsOffer, Loan, Transfer
from sim.tests import economy_fixture as fixture

MARKET_RATE = 0.05
BOTH = (SHARE_TRADING, BOND_MARKET)


class FundFixture(unittest.TestCase):
    def setUp(self):
        self.economy = Economy(fixture.small_setup())
        self.setup = self.economy.setup
        self.record = self.economy.record
        self.money = self.setup.currency_id
        self.manager, self.saver, self.other = sorted(self.record.cohorts)[:3]
        self.producer_id = sorted(self.record.producers)[0]
        self.record.last_dividends[self.producer_id] = 20.0
        self.fund = funds.found(self.record, self.manager, 0)
        self.supply = self.record.book.money_supply(self.money)

    def balance(self, agent):
        return self.record.book.balance(agent, self.money)

    def price(self, rate=MARKET_RATE):
        return funds.unit_price(self.setup, self.record, self.fund, rate)

    def put_shares_in_fund(self, part=0.2):
        self.record.shares[self.producer_id] = {self.fund.agent_id: part}


class Units(FundFixture):
    def test_the_first_unit_costs_one_unit_of_money_and_a_new_fund_holds_nothing(self):
        self.assertEqual(self.price(), funds.FIRST_UNIT_PRICE)
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
        funds.subscribe(self.setup, self.record, self.fund, self.saver, 100.0, MARKET_RATE)
        self.record.book.transfer(Transfer(self.fund.agent_id, self.other, self.money, 100.0, "invested elsewhere"))
        self.put_shares_in_fund(0.5)                     # the cash became shares worth more than it
        worth = funds.net_assets(self.setup, self.record, self.fund, MARKET_RATE)
        self.assertAlmostEqual(self.price(), worth / 100.0)
        units = funds.subscribe(self.setup, self.record, self.fund, self.other, 50.0, MARKET_RATE)
        self.assertAlmostEqual(units, 50.0 / (worth / 100.0))

    def test_buying_in_at_the_unit_price_leaves_the_earlier_holders_unit_worth_unchanged(self):
        funds.subscribe(self.setup, self.record, self.fund, self.saver, 100.0, MARKET_RATE)
        self.put_shares_in_fund(0.5)
        before = self.price()
        funds.subscribe(self.setup, self.record, self.fund, self.other, 40.0, MARKET_RATE)
        self.assertAlmostEqual(self.price(), before)

    def test_a_dearer_market_rate_lowers_what_the_holdings_and_so_the_unit_are_worth(self):
        funds.subscribe(self.setup, self.record, self.fund, self.saver, 10.0, MARKET_RATE)
        self.put_shares_in_fund(0.5)
        self.assertGreater(self.price(0.03), self.price(0.09))

    def test_a_fund_holding_loans_marks_them_at_the_rate_a_saver_would_ask(self):
        funds.subscribe(self.setup, self.record, self.fund, self.saver, 10.0, MARKET_RATE)
        loan = Loan("loan:0:1", self.fund.agent_id, self.producer_id, self.money, 100.0, rate=0.05, years_left=4.0,
                    issued_year=0, collateral_value=100000.0)
        self.record.loans.append(loan)
        low, high = self.price(0.03), self.price(0.12)
        self.assertGreater(low, high)

    def test_the_fund_is_worth_nothing_when_its_cash_is_gone_and_it_holds_nothing_with_units_outstanding(self):
        funds.subscribe(self.setup, self.record, self.fund, self.saver, 10.0, MARKET_RATE)
        self.record.book.transfer(Transfer(self.fund.agent_id, self.other, self.money, 10.0, "lost"))
        self.assertIsNone(self.price())
        self.assertEqual(funds.subscribe(self.setup, self.record, self.fund, self.other, 5.0, MARKET_RATE), 0.0)


class Redeeming(FundFixture):
    def setUp(self):
        super().setUp()
        funds.subscribe(self.setup, self.record, self.fund, self.saver, 100.0, MARKET_RATE)

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
        self.record.book.transfer(Transfer(self.fund.agent_id, self.other, self.money, 70.0, "invested elsewhere"))
        self.put_shares_in_fund(0.5)
        price = self.price()
        paid = funds.redeem(self.setup, self.record, self.fund, self.saver, 90.0, MARKET_RATE)
        self.assertAlmostEqual(paid, 30.0)
        self.assertAlmostEqual(self.fund.units[self.saver], 100.0 - 30.0 / price)

    def test_a_fund_short_of_cash_sells_holdings_to_savers_to_pay_the_redemption(self):
        self.record.book.transfer(Transfer(self.fund.agent_id, self.other, self.money, 100.0, "invested elsewhere"))
        self.put_shares_in_fund(0.5)
        offers = [FundsOffer(self.other, self.money, 5000.0, 0.04)]
        before = self.balance(self.saver)
        remaining = funds.redeem_for_cash(self.setup, self.record, self.fund, self.saver, 50.0, offers, MARKET_RATE, BOTH)
        self.assertGreater(self.balance(self.saver) - before, 0.0)
        self.assertLess(remaining[0].amount, 5000.0)
        self.assertLess(self.record.shares[self.producer_id][self.fund.agent_id], 0.5)
        self.assertIn(self.other, self.record.shares[self.producer_id])

    def test_without_a_market_for_its_holdings_a_fund_short_of_cash_pays_less_than_asked(self):
        self.record.book.transfer(Transfer(self.fund.agent_id, self.other, self.money, 100.0, "invested elsewhere"))
        self.put_shares_in_fund(0.5)
        before = self.balance(self.saver)
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
        funds.subscribe(self.setup, self.record, self.fund, self.saver, 100.0, MARKET_RATE)
        self.record.loans.append(Loan("loan:0:1", self.fund.agent_id, self.producer_id, self.money, 100.0, rate=0.07,
                                      years_left=4.0, issued_year=0, collateral_value=100000.0))
        worth = funds.net_assets(self.setup, self.record, self.fund, MARKET_RATE)
        self.assertAlmostEqual(funds.yield_of(self.setup, self.record, self.fund, MARKET_RATE), 7.0 / worth)

    def test_a_fund_with_cash_buys_shares_from_a_holder_in_the_secondary_market_like_a_saver(self):
        funds.subscribe(self.setup, self.record, self.fund, self.saver, 400.0, MARKET_RATE)
        self.record.shares[self.producer_id] = {self.other: 0.3}
        offer = funds.offer_of(self.setup, self.record, self.fund, 0.04)
        remaining, trades = secondary_trade.run(self.setup, self.record, [offer], {}, MARKET_RATE, BOTH)
        self.assertEqual(len(trades), 1)
        self.assertAlmostEqual(self.record.shares[self.producer_id][self.fund.agent_id], 0.3)
        self.assertLess(self.balance(self.fund.agent_id), 400.0)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), self.supply)

    def test_a_fund_with_no_cash_makes_no_offer(self):
        self.assertIsNone(funds.offer_of(self.setup, self.record, self.fund, MARKET_RATE))

    def test_the_units_a_household_holds_are_listed_by_fund(self):
        funds.subscribe(self.setup, self.record, self.fund, self.saver, 100.0, MARKET_RATE)
        self.assertEqual(funds.owned_by(self.record, self.saver), {self.fund.agent_id: 100.0})
        self.assertEqual(funds.owned_by(self.record, self.other), {})


class Saved(FundFixture):
    def test_the_fund_and_its_units_survive_the_save(self):
        funds.subscribe(self.setup, self.record, self.fund, self.saver, 100.0, MARKET_RATE)
        loaded = EconomyRecord.from_record(self.record.to_record())
        self.assertEqual(loaded.capital.funds[self.fund.agent_id].units, {self.saver: 100.0})


if __name__ == "__main__":
    unittest.main()
