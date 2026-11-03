"""One credit rule for an actor and the economy (design D1): how much of a draw the economy's own rule funds
(`credit_lines.actor_fundable`), what a lending opening records of the lenders, the economy's answers over that record
(`api.actor_fundable_amount`, `api.risk_premium`, `api.lender_listing`), and the markets' and finance's views over them.
Each test calls one function on written-out inputs."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import api, credit_lines
from sim.economy.credit_record import CreditRecord
from sim.economy.types import FundsOffer
from sim.finance.module import Finance
from sim.world import capital_market
from sim.markets.reads_prices import PriceReads
from sim.tests import module_harness

RATE = 0.1


class ActorFundable(unittest.TestCase):
    def fundable(self, amount, collateral, debt=0.0, arrears=0.0, ask=0.05):
        return credit_lines.actor_fundable(amount, debt, collateral, arrears, RATE, ask)

    def test_a_draw_well_inside_its_collateral_is_funded_whole(self):
        self.assertEqual(self.fundable(10.0, 1000.0), 10.0)

    def test_a_draw_far_past_its_collateral_is_funded_for_less(self):
        taken = self.fundable(10000.0, 100.0)
        self.assertLess(taken, 10000.0)

    def test_a_dearer_lender_funds_no_more_than_a_cheaper_one(self):
        self.assertLessEqual(self.fundable(10000.0, 100.0, ask=0.12), self.fundable(10000.0, 100.0, ask=0.05))

    def test_no_lender_asking_more_than_the_borrower_will_pay_funds_nothing(self):
        self.assertEqual(self.fundable(10.0, 1000.0, ask=5.0), 0.0)

    def test_a_draw_of_nothing_is_nothing(self):
        self.assertEqual(self.fundable(0.0, 1000.0), 0.0)


class OpenLending(unittest.TestCase):
    def test_the_opening_records_the_lowest_ask_the_funds_and_each_lender_offer(self):
        record = CreditRecord()
        record.open_lending([FundsOffer("a", "coin", 40.0, 0.08), FundsOffer("b", "coin", 60.0, 0.05),
                             FundsOffer("c", "other", 99.0, 0.01), FundsOffer("a", "coin", 10.0, 0.09)], "coin")
        self.assertEqual(record.funds_offered, 110.0)
        self.assertEqual(record.lowest_ask_offered, 0.05)
        self.assertEqual(record.offered_by_lender, {"a": 50.0, "b": 60.0})
        self.assertEqual(record.ask_by_lender, {"a": 0.08, "b": 0.05})

    def test_an_opening_with_no_offers_records_no_lowest_ask(self):
        record = CreditRecord()
        record.open_lending([], "coin")
        self.assertIsNone(record.lowest_ask_offered)
        self.assertEqual(record.funds_offered, 0.0)
        self.assertTrue(record.lenders_met)

    def test_a_record_no_lending_has_opened_has_not_met(self):
        self.assertFalse(CreditRecord().lenders_met)


def economy_over(credit, balances=None, cohorts=(), banks=(), coin_per_unit=2.0):
    book = types.SimpleNamespace(balance=lambda agent, currency: (balances or {}).get(agent, 0.0))
    record = types.SimpleNamespace(
        credit=credit, book=book, cohorts={name: None for name in cohorts},
        capital_markets=types.SimpleNamespace(banks={name: types.SimpleNamespace(agent_id=name, reserve_share=0.1) for name in banks}),
        memory=types.SimpleNamespace(rates={"coin": RATE}))
    return types.SimpleNamespace(record=record, setup=types.SimpleNamespace(currency_id="coin", opening_rate=RATE, coin_per_unit=coin_per_unit))


class EconomyAnswers(unittest.TestCase):
    def met(self):
        credit = CreditRecord()
        credit.open_lending([FundsOffer("saver", "coin", 100.0, 0.05), FundsOffer("bank", "coin", 50.0, 0.07),
                             FundsOffer("fund", "coin", 30.0, 0.06)], "coin")
        return economy_over(credit, {"saver": 90.0, "bank": 70.0, "fund": 10.0}, cohorts=("saver",), banks=("bank",))

    def test_before_lenders_have_met_there_is_no_answer(self):
        self.assertIsNone(api.actor_fundable_amount(economy_over(CreditRecord()), 10.0, 0.0, 1000.0, 0.0))

    def test_lenders_that_met_with_no_funds_fund_nothing_not_an_unknown_amount(self):
        credit = CreditRecord()
        credit.open_lending([], "coin")
        self.assertEqual(api.actor_fundable_amount(economy_over(credit), 10.0, 0.0, 1000.0, 0.0), 0.0)

    def test_once_they_have_met_a_small_draw_is_funded_whole(self):
        self.assertEqual(api.actor_fundable_amount(self.met(), 10.0, 0.0, 1000.0, 0.0), 10.0)

    def test_once_they_have_met_a_draw_past_the_collateral_is_cut(self):
        self.assertLess(api.actor_fundable_amount(self.met(), 10000.0, 0.0, 100.0, 0.0), 10000.0)

    def test_the_premium_is_the_economys_and_rises_with_the_debt(self):
        self.assertEqual(api.risk_premium(0.0, 100.0, 0.0), 0.0)
        self.assertGreater(api.risk_premium(200.0, 100.0, 0.0), api.risk_premium(50.0, 100.0, 0.0))

    def test_the_lenders_are_listed_cheapest_ask_first_with_kind_capacity_and_balance(self):
        listing = api.lender_listing(self.met())
        self.assertEqual([(each.lender, each.kind, round(each.capacity, 9), each.balance, each.ask) for each in listing["lenders"]],
                         [("saver", "cohort", round(capital_market.lendable_capacity(100.0), 9), 90.0, 0.05),
                          ("fund", "fund", round(capital_market.lendable_capacity(30.0), 9), 10.0, 0.06),
                          ("bank", "bank", 50.0, 70.0, 0.07)])   # a bank has held its reserve already
        self.assertEqual((listing["currency"], listing["coin_per_unit"]), ("coin", 2.0))


class MarketsView(unittest.TestCase):
    def reads(self):
        return PriceReads(types.SimpleNamespace(economy=lambda: economy_over(CreditRecord(), coin_per_unit=2.0)), None)

    def test_a_draw_in_coin_is_asked_in_units_and_answered_in_coin(self):
        reads = self.reads()
        reads.answers = lambda country=None: ({}, {}, RATE)
        with mock.patch.object(api, "actor_fundable_amount", return_value=5.0) as asked:
            self.assertEqual(reads.fundable_amount(40.0, 10.0, 20.0, 4.0), 10.0)
        asked.assert_called_once_with(mock.ANY, 20.0, 5.0, 10.0, 2.0)

    def test_no_answer_from_the_economy_stays_none(self):
        reads = self.reads()
        reads.answers = lambda country=None: ({}, {}, RATE)
        with mock.patch.object(api, "actor_fundable_amount", return_value=None):
            self.assertIsNone(reads.fundable_amount(40.0, 10.0, 20.0, 4.0))


class FinanceView(unittest.TestCase):
    def finance(self, answered, fundable):
        return module_harness.build(Finance, views={
            "agent_fundable_amount": lambda amount, debt, collateral, arrears: (answered, fundable)})

    def test_an_answering_economy_gives_its_fundable_amount(self):
        self.assertEqual(self.finance(True, 7.0).fundable_amount(10.0, 0.0, 5.0, 0.0), 7.0)

    def test_an_economy_still_opening_gives_none(self):
        self.assertIsNone(self.finance(False, None).fundable_amount(10.0, 0.0, 5.0, 0.0))


if __name__ == "__main__":
    unittest.main()
