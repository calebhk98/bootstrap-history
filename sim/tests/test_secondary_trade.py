"""Complaint 106: holders of shares and loans sell them to savers once a year, at the price that clears the asks (what
the claim is worth to the holder, less for one short of cash) against the bids (what it is worth to a saver at the rate
it asks as a lender plus the issuer's premium). A society without the institution trades nothing. Rules on a stand-in
record with the claims built by hand."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.economy import credit, credit_claims, secondary_trade
from sim.book import Book
from sim.economy.secondary_trade import BOND_MARKET, SHARE_TRADING, Shortfall
from sim.economy.types import FundsOffer, Loan, Transfer

MARKET_RATE = 0.05
BOTH = (SHARE_TRADING, BOND_MARKET)


class TradeFixture(unittest.TestCase):
    def setUp(self):
        self.money = "coin"
        self.setup = SimpleNamespace(currency_id=self.money, opening_rate=MARKET_RATE)
        book = Book()
        for agent in ("household:a", "household:b", "household:c"):
            book.transfer(Transfer("edge:mint", agent, self.money, 1000.0, "opening"))
        self.holder, self.saver, self.other = "household:a", "household:b", "household:c"
        self.producer_id = "producer:one"
        self.record = SimpleNamespace(
            book=book, cohorts={self.holder: None, self.saver: None, self.other: None}, capital=SimpleNamespace(funds={}),
            loans=[], remembered_defaults={}, banks={}, producers={self.producer_id: None},
            last_dividends={self.producer_id: 20.0}, shares={self.producer_id: {self.holder: 0.3}})

    def balance(self, agent):
        return self.record.book.balance(agent, self.money)

    def offers(self, amount=500.0, rate=0.04, buyers=None):
        return [FundsOffer(buyer, self.money, amount, rate) for buyer in (buyers or [self.saver])]

    def run_trade(self, offers=None, short=None, institutions=BOTH):
        return secondary_trade.run(self.setup, self.record, self.offers() if offers is None else offers, short or {},
                                   MARKET_RATE, institutions)


class Shares(TradeFixture):
    def test_a_saver_who_asks_less_than_the_holder_buys_its_share_and_money_and_shares_are_conserved(self):
        supply = self.record.book.money_supply(self.money)
        before_holder, before_saver = self.balance(self.holder), self.balance(self.saver)
        offers, trades = self.run_trade()
        self.assertEqual(len(trades), 1)
        held = self.record.shares[self.producer_id]
        self.assertNotIn(self.holder, held)
        self.assertAlmostEqual(held[self.saver], 0.3)
        paid = trades[0].quantity * trades[0].price
        self.assertAlmostEqual(self.balance(self.holder) - before_holder, paid)
        self.assertAlmostEqual(before_saver - self.balance(self.saver), paid)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), supply)
        self.assertAlmostEqual(offers[0].amount, 500.0 - paid)

    def test_the_price_lies_between_what_the_holder_asks_and_what_the_saver_will_pay(self):
        _offers, trades = self.run_trade()
        holder_value = secondary_trade.share_value(self.record, self.producer_id, MARKET_RATE, 0.0)
        saver_value = secondary_trade.share_value(self.record, self.producer_id, 0.04, 0.0)
        self.assertGreaterEqual(trades[0].price, holder_value - 1e-6)
        self.assertLessEqual(trades[0].price, saver_value + 1e-6)

    def test_a_saver_who_asks_more_than_the_holder_buys_nothing(self):
        _offers, trades = self.run_trade(offers=self.offers(rate=0.09))
        self.assertEqual(trades, [])
        self.assertEqual(self.record.shares[self.producer_id], {self.holder: 0.3})

    def test_a_dearer_market_rate_lowers_the_price_a_saver_pays(self):
        cheap = secondary_trade.share_value(self.record, self.producer_id, 0.03, 0.0)
        dear = secondary_trade.share_value(self.record, self.producer_id, 0.08, 0.0)
        self.assertGreater(cheap, dear)

    def test_a_holder_short_of_cash_sells_for_less_than_it_values_the_share(self):
        shortfall = {self.holder: Shortfall(amount=20.0, borrowing_rate=0.25)}
        asks, _bids = secondary_trade.asks_and_bids(self.setup, self.record, self.offers(), shortfall, MARKET_RATE, 0.0, BOTH)
        asks = sorted(asks, key=lambda ask: ask.reserve)
        ordinary = secondary_trade.share_value(self.record, self.producer_id, MARKET_RATE, 0.0)
        self.assertLess(asks[0].reserve, ordinary)
        self.assertAlmostEqual(asks[0].quantity * asks[0].reserve, 20.0)

    def test_a_short_holder_gets_the_cash_it_needs_when_a_saver_will_pay(self):
        shortfall = {self.holder: Shortfall(amount=30.0, borrowing_rate=0.25)}
        before = self.balance(self.holder)
        _offers, trades = self.run_trade(short=shortfall)
        self.assertTrue(trades)
        self.assertGreaterEqual(self.balance(self.holder) - before, 30.0)

    def test_without_the_institution_nothing_is_traded(self):
        offers = self.offers()
        remaining, trades = self.run_trade(offers=offers, institutions=())
        self.assertEqual(trades, [])
        self.assertEqual(remaining, offers)
        self.assertEqual(self.record.shares[self.producer_id], {self.holder: 0.3})

    def test_the_bond_institution_alone_does_not_trade_shares(self):
        _remaining, trades = self.run_trade(institutions=(BOND_MARKET,))
        self.assertEqual(trades, [])

    def test_a_buyer_spends_no_more_than_it_offered(self):
        self.record.shares[self.producer_id] = {self.holder: 0.3, self.other: 0.5}
        offers, _trades = self.run_trade(offers=self.offers(amount=100.0))
        self.assertGreaterEqual(offers[0].amount, -1e-9)

    def test_the_result_is_the_same_when_the_holders_are_listed_in_another_order(self):
        self.record.shares[self.producer_id] = {self.holder: 0.2, self.other: 0.1}
        first = self.run_trade()[1]
        self.setUp()
        self.record.shares[self.producer_id] = {self.other: 0.1, self.holder: 0.2}
        second = self.run_trade()[1]
        self.assertEqual(first, second)


class Loans(TradeFixture):
    def setUp(self):
        super().setUp()
        self.record.shares = {}

    def make_loan(self, lender=None, borrower=None, principal=200.0, rate=0.05, years=5.0):
        """A loan to the producer; `rate` is the base rate it was struck at, and the premium the producer's own
        standing earns is on top, as the credit market charges it."""
        loan = Loan("loan:0:7", lender or self.holder, borrower or self.producer_id, self.money, principal,
                    rate=rate + credit.risk_premium(principal, 0.0, 0.0),
                    years_left=years, issued_year=0)
        self.record.loans.append(loan)
        return loan

    def test_a_bond_at_the_savers_rate_is_worth_its_face_to_that_saver(self):
        loan = self.make_loan()
        self.assertAlmostEqual(secondary_trade.loan_value(loan, loan.rate), loan.principal)

    def test_a_loan_is_worth_less_when_the_rate_a_buyer_asks_rises(self):
        loan = self.make_loan()
        self.assertGreater(secondary_trade.loan_value(loan, 0.03), secondary_trade.loan_value(loan, 0.09))

    def test_a_loan_s_value_counts_the_principal_as_it_falls_due(self):
        loan = self.make_loan(years=2.0)
        growth = 1.0 + 0.08
        expected = (loan.principal * loan.rate + loan.principal / 2.0) / growth + (loan.principal / 2.0 * loan.rate + loan.principal / 2.0) / growth ** 2
        self.assertAlmostEqual(secondary_trade.loan_value(loan, 0.08), expected)

    def test_a_lender_sells_a_loan_to_a_saver_who_asks_less_and_the_lender_changes(self):
        loan = self.make_loan()
        supply = self.record.book.money_supply(self.money)
        _offers, trades = self.run_trade(offers=self.offers(amount=1000.0, rate=0.03))
        self.assertEqual(len(trades), 1)
        self.assertEqual(loan.lender, self.saver)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), supply)
        self.assertGreater(trades[0].price, secondary_trade.loan_value(loan, MARKET_RATE + credit.risk_premium(200.0, 0.0, 0.0)) / 200.0)

    def test_a_lender_not_in_need_keeps_a_loan_when_every_saver_asks_more_than_it_does(self):
        loan = self.make_loan(rate=0.05)
        _offers, trades = self.run_trade(offers=self.offers(amount=1000.0, rate=0.07))
        self.assertEqual(trades, [])
        self.assertEqual(loan.lender, self.holder)

    def test_a_lender_short_of_cash_sells_below_the_face_to_savers_who_ask_more_than_the_coupon(self):
        self.make_loan(rate=0.05)
        shortfall = {self.holder: Shortfall(amount=50.0, borrowing_rate=0.2)}
        _offers, trades = self.run_trade(offers=self.offers(amount=1000.0, rate=0.07), short=shortfall)
        self.assertTrue(trades)
        self.assertLess(trades[0].price, 1.0)

    def test_funds_short_of_the_loan_buy_a_part_and_the_loan_is_split_between_seller_and_buyer(self):
        loan = self.make_loan(principal=200.0)
        _offers, trades = self.run_trade(offers=self.offers(amount=60.0, rate=0.03))
        bought = sum(trade.quantity for trade in trades)
        self.assertGreater(bought, 0.0)
        self.assertLess(bought, 200.0)
        mine = [each for each in self.record.loans if each.lender == self.saver]
        self.assertAlmostEqual(sum(each.principal for each in mine) + loan.principal, 200.0)
        self.assertAlmostEqual(sum(credit_claims.claims_by_lender(self.record.loans, self.money).values()), 200.0)

    def test_a_household_s_own_debt_is_not_traded(self):
        loan = self.make_loan(borrower=self.other)
        self.run_trade(offers=self.offers(amount=1000.0, rate=0.03))
        self.assertEqual(loan.lender, self.holder)

    def test_a_loan_pledging_land_is_not_traded(self):
        loan = self.make_loan()
        loan.collateral_tile = "farms"
        self.run_trade(offers=self.offers(amount=1000.0, rate=0.03))
        self.assertEqual(loan.lender, self.holder)

    def test_after_the_sale_the_claim_is_the_buyers_and_not_the_sellers(self):
        self.make_loan()
        self.run_trade(offers=self.offers(amount=1000.0, rate=0.03))
        held = credit_claims.claims_by_lender(self.record.loans, self.money)
        self.assertIn(self.saver, held)
        self.assertNotIn(self.holder, held)

    def test_without_the_bond_institution_loans_stay_with_their_lenders(self):
        loan = self.make_loan()
        self.run_trade(offers=self.offers(amount=1000.0, rate=0.03), institutions=(SHARE_TRADING,))
        self.assertEqual(loan.lender, self.holder)


if __name__ == "__main__":
    unittest.main()
