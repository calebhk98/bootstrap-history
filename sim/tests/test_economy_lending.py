"""Who borrows and what follows: households for subsistence, merchants for cargo, and the default cascade."""

QUICK_TOPIC = True

import dataclasses
import types
import unittest

from sim.economy import credit, credit_claims, households, households_credit, lending, merchants_credit
from sim.economy.accounts import Book
from sim.economy.credit_view import CreditView
from sim.economy.households_basket import need_prices
from sim.economy.market_memory import MarketMemory
from sim.economy.record import EconomyRecord
from sim.economy.types import CurrencySpec, FundsOffer, Loan, Transfer

from sim.tests.test_economy_households import BASKET, SPECS, View, cohort
from sim.tests.test_economy_merchants import INTEREST_RATE, SPECS as TRADE_SPECS, merchant, world

MONEY = "coin"


def record_with(cash_by_agent):
    record = EconomyRecord(book=Book(), memory=MarketMemory(), currency=CurrencySpec(MONEY, "fiat", None, 0.0, None))
    for agent, amount in sorted(cash_by_agent.items()):
        record.book.transfer(Transfer("edge:legacy", agent, MONEY, amount, "opening"))
    return record


def setup_for(record):
    return types.SimpleNamespace(currency_id=MONEY, basket_for=lambda tile: BASKET, specs=SPECS)


def ledger():
    return types.SimpleNamespace(grown_units={})


def loan(loan_id, lender, borrower, principal, rate=0.1, years_left=4.0, arrears=0.0):
    return Loan(loan_id, lender, borrower, MONEY, principal, rate, years_left, 0.0, arrears)


class HouseholdBorrowingTests(unittest.TestCase):
    def floor_cost(self, people):
        return households_credit.floor_cost_unmet(cohort(people=people), need_prices(BASKET, View(), "t"), None)

    def test_a_household_short_of_its_floor_with_income_ahead_asks_for_the_shortfall(self):
        who = cohort(people=10.0, last_year_income=10000.0)
        asked = households_credit.subsistence_request(who, 500.0, MONEY, 0.05, 0.0)
        self.assertEqual((asked.borrower, asked.purpose, asked.collateral_value), (who.agent_id, "subsistence", 0.0))
        self.assertAlmostEqual(asked.amount, 500.0)
        self.assertGreater(asked.maximum_rate, 0.05)

    def test_no_income_ahead_no_request(self):
        self.assertIsNone(households_credit.subsistence_request(cohort(last_year_income=0.0), 500.0, MONEY, 0.05, 0.0))

    def test_the_request_is_cut_to_what_income_can_service(self):
        who = cohort(people=10.0, last_year_income=1000.0)
        asked = households_credit.subsistence_request(who, 50000.0, MONEY, 0.05, 0.0)
        service = asked.amount * (1.0 / households_credit.HOUSEHOLD_LOAN_YEARS + 0.05)
        self.assertLessEqual(service, households_credit.HOUSEHOLD_SERVICE_SHARE * 1000.0 + 1e-9)

    def test_debt_already_owed_uses_up_the_capacity(self):
        who = cohort(people=10.0, last_year_income=1000.0)
        free = households_credit.subsistence_request(who, 50000.0, MONEY, 0.05, 0.0)
        indebted = households_credit.subsistence_request(who, 50000.0, MONEY, 0.05, 300.0)
        self.assertLess(indebted.amount, free.amount)

    def test_a_household_with_cash_for_its_floors_does_not_ask(self):
        who = cohort(people=10.0, last_year_income=10000.0)
        record = record_with({who.agent_id: self.floor_cost(10.0) * 2.0})
        record.cohorts[who.agent_id] = who
        self.assertEqual(lending.household_requests(setup_for(record), record, View(), ledger(), {}), [])

    def test_a_household_without_cash_asks_through_the_year_loop(self):
        who = cohort(people=10.0, last_year_income=10000.0)
        record = record_with({who.agent_id: 100.0})
        record.cohorts[who.agent_id] = who
        requests = lending.household_requests(setup_for(record), record, View(), ledger(), {})
        self.assertEqual(len(requests), 1)
        self.assertAlmostEqual(requests[0].amount, self.floor_cost(10.0) - 100.0)

    def test_the_risk_premium_rations_a_borrower_with_no_collateral(self):
        who = cohort(people=10.0, last_year_income=10000.0)
        asked = households_credit.subsistence_request(who, 500.0, MONEY, 0.05, 0.0)
        funded, _rate, _unmet = credit.clear([asked], [FundsOffer("rich", MONEY, 5000.0, 0.05)], MONEY, 0.05, {})
        self.assertGreater(funded[0].rate, 0.05 + credit.LEVERAGE_PREMIUM * 0.99)
        thin = dataclasses.replace(asked, maximum_rate=0.1)
        refused, _rate, unmet = credit.clear([thin], [FundsOffer("rich", MONEY, 5000.0, 0.05)], MONEY, 0.05, {})
        self.assertEqual((refused, len(unmet)), ([], 1))

    def test_a_loan_is_bid_for_the_floors_it_was_for(self):
        who = cohort(people=10.0, last_year_income=10000.0)
        record = record_with({who.agent_id: 100.0, "rich": 10000.0})
        record.cohorts[who.agent_id] = who
        order_book = {}
        loans = [loan("loan:1", "rich", who.agent_id, 400.0)]
        lending.bid_household_loans(setup_for(record), record, View(), ledger(), loans, order_book, {})
        bids = [bid for bids_and_offers in order_book.values() for bid in bids_and_offers[0]]
        self.assertTrue(bids)
        self.assertAlmostEqual(sum(bid.budget for bid in bids), 400.0, places=6)
        self.assertTrue(all(bid.priority == 0 and bid.buyer == who.agent_id for bid in bids))


class MerchantBorrowingTests(unittest.TestCase):
    def request(self, cash, debt=0.0, capital=100.0, rate=INTEREST_RATE, prices=(2.0, 5.0)):
        carriage, area_map, area_a, area_b = world(("salt",))
        who = merchant()
        who.capital_base = capital
        who.expected_prices = {("salt", area_a["salt"]): prices[0], ("salt", area_b["salt"]): prices[1]}
        who.expected_volumes = {("salt", area_b["salt"]): 100.0}
        return merchants_credit.credit_request(who, View(), carriage, area_map, cash, {}, TRADE_SPECS, rate,
                                               debt, MONEY), who

    def test_cash_that_binds_on_a_profitable_route_asks_for_the_rest(self):
        asked, _who = self.request(cash=6.0)
        self.assertIsNotNone(asked)
        self.assertGreater(asked.amount, 0.0)
        self.assertGreater(asked.maximum_rate, INTEREST_RATE)

    def test_cash_that_covers_the_cargo_asks_for_nothing(self):
        asked, _who = self.request(cash=1e6)
        self.assertIsNone(asked)

    def test_a_route_that_does_not_pay_asks_for_nothing(self):
        asked, _who = self.request(cash=6.0, prices=(2.0, 2.2))
        self.assertIsNone(asked)

    def test_the_request_stays_within_the_leverage_limit(self):
        asked, _who = self.request(cash=0.0, capital=100.0)
        self.assertLessEqual(asked.amount, merchants_credit.MERCHANT_LEVERAGE_LIMIT * 100.0 + 1e-9)
        deep, _who = self.request(cash=0.0, capital=100.0, debt=100.0)
        self.assertIsNone(deep)

    def test_staked_capital_follows_borrowing_and_repayment(self):
        who = merchant()
        merchants_credit.stake({who.agent_id: who}, {who.agent_id: 50.0})
        self.assertAlmostEqual(who.capital_base, 150.0)
        merchants_credit.stake({who.agent_id: who}, {who.agent_id: -20.0})
        self.assertAlmostEqual(who.capital_base, 130.0)


class ServiceTimingTests(unittest.TestCase):
    def test_a_loan_made_this_year_is_not_due_until_next_year(self):
        record = record_with({"b": 1000.0, "l": 0.0})
        record.loans = [dataclasses.replace(loan("loan:new", "l", "b", 100.0), issued_year=5),
                        dataclasses.replace(loan("loan:old", "l", "b", 100.0), issued_year=4)]
        received = lending.service(record, MONEY, 5)
        self.assertAlmostEqual(received["l"], 100.0 * 0.1 + 100.0 / 4.0)         # the old loan only
        new = next(item for item in record.loans if item.loan_id == "loan:new")
        self.assertEqual((new.principal, new.years_left), (100.0, 4.0))

    def test_a_default_frees_a_merchant_so_the_write_off_shows_as_profit(self):
        record = record_with({"m": 0.0, "l": 0.0})
        record.merchants["m"] = merchant("m")
        record.merchants["m"].capital_base = 500.0
        record.loans = [dataclasses.replace(loan("loan:1", "l", "m", 200.0, 0.1, 2.0, arrears=95.0), issued_year=1)]
        lending.service(record, MONEY, 3)
        self.assertEqual(record.loans, [])
        self.assertAlmostEqual(record.merchants["m"].capital_base, 300.0)    # the debt in its stake is gone


class DefaultCascadeTests(unittest.TestCase):
    """household:t:0 lends 1000 to a producer and owes 400 to a bank. When the producer stops paying, the
    household has less cash and income, spends and lends less, falls behind on its own debt, and the bank's
    claim on it loses value."""

    def run_world(self, producer_pays, years=3):
        lender = "household:t:0"
        record = record_with({lender: 100.0, "producer": 1000.0 if producer_pays else 0.0, "bank": 5000.0})
        record.cohorts[lender] = cohort(people=10.0, last_year_income=2000.0)
        record.loans = [loan("loan:a", lender, "producer", 1000.0), loan("loan:b", "bank", lender, 400.0)]
        for year in range(1, years + 1):
            if producer_pays:
                record.book.transfer(Transfer("edge:legacy", "producer", MONEY, 400.0, "sales"))
            for agent, received in lending.service(record, MONEY, year).items():
                record.property_income[agent] = received      # what the year loop adds after the close
        return record, lender

    def test_the_default_is_the_lenders_loss_and_the_borrowers_record(self):
        record, lender = self.run_world(producer_pays=False, years=5)
        self.assertGreater(record.credit_losses.get(lender, 0.0), 0.0)
        self.assertIn("producer", record.remembered_defaults)
        self.assertTrue(record.book.check_conservation(1e-9).ok)

    def test_the_lender_has_less_cash_and_income_after_a_default(self):
        paid, lender = self.run_world(producer_pays=True)
        unpaid, _lender = self.run_world(producer_pays=False)
        self.assertLess(unpaid.book.balance(lender, MONEY), paid.book.balance(lender, MONEY))
        self.assertLess(unpaid.property_income.get(lender, 0.0), paid.property_income.get(lender, 0.0))

    def test_the_lender_spends_less_and_lends_less(self):
        paid, lender = self.run_world(producer_pays=True)
        unpaid, _lender = self.run_world(producer_pays=False)

        def orders(record):
            view = CreditView(MarketMemory(), record.book, _Areas(), MONEY, loans=lambda: record.loans)
            view.price = View().price
            view.area_of = View().area_of
            view.stock = View().stock
            return households.goods_orders(record.cohorts[lender], view, record.book.balance(lender, MONEY),
                                           record.property_income.get(lender, 0.0), BASKET, SPECS)
        spend_paid, spend_unpaid = orders(paid), orders(unpaid)
        self.assertLess(sum(bid.budget for bid in spend_unpaid.bids), sum(bid.budget for bid in spend_paid.bids))
        offered = lambda result: sum(offer.amount for offer in result.funds_offers)
        self.assertLessEqual(offered(spend_unpaid), offered(spend_paid))

    def test_the_lenders_own_creditor_feels_it(self):
        paid, _lender = self.run_world(producer_pays=True, years=3)
        unpaid, _lender = self.run_world(producer_pays=False, years=3)
        self.assertEqual(paid.credit_losses.get("bank", 0.0), 0.0)
        self.assertGreater(unpaid.credit_losses.get("bank", 0.0), 0.0)
        self.assertGreater(unpaid.credit_losses.get("household:t:0", 0.0), 0.0)


class _Areas:
    def goods(self):
        return ()


if __name__ == "__main__":
    unittest.main()
