"""Complaint 546: decisions follow what was paid and delivered, not what was proposed. A cashless producer
plans no runs it cannot pay for, a labour settlement that paid nothing delivers no hours, and a goods
market that could not settle in full records the volume that changed hands."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import producers, producers_close, year_goods
from sim.economy.accounts import Book
from sim.economy.market_memory import MarketMemory
from sim.economy.types import EDGE_MINT, Bid, Fill, GoodsMove, LabourResult, Offer, Transfer
from sim.economy.year_ledger import YearLedger
from sim.tests.test_economy_producers import FARM, farm_view, farmer
from sim.economy.types import CurrencySpec


class SmoothingKeepsAffordabilityTests(unittest.TestCase):
    def test_a_cashless_producer_does_not_plan_last_years_runs(self):
        producer = farmer(last_runs=10.0)
        plan = producers.plan(producer, FARM, farm_view(2.0), 21.0)     # a run costs 7: cash pays for 3
        self.assertAlmostEqual(plan.runs, 3.0)

    def test_a_producer_with_cash_still_smooths_toward_last_years_runs(self):
        producer = farmer(last_runs=10.0, expected_prices={"grain": 0.1})   # the price says stop; smoothing holds most
        self.assertGreater(producers.plan(producer, FARM, farm_view(2.0), 1000.0).runs, 5.0)


class CashPaysAtMarketPricesTests(unittest.TestCase):
    def test_cash_that_pays_for_every_run_at_market_prices_is_not_cut_by_a_dearer_lagging_expectation(self):
        # Inputs fell from the expected 2.0 to 1.0 a unit: a run costs 7 now, and the cash target is struck at that.
        producer = farmer(expected_prices={"seed": 2.0})
        plan = producers.plan(producer, FARM, farm_view(2.0), 7.0 * producer.capacity_runs)
        self.assertGreater(plan.runs, 9.9)         # the expected price would stop it at under 8 runs

    def test_cash_short_of_the_market_cost_still_limits_the_runs(self):
        producer = farmer(expected_prices={"seed": 0.5})
        plan = producers.plan(producer, FARM, farm_view(2.0), 21.0)         # a run costs 7 at the market price
        self.assertAlmostEqual(plan.runs, 3.0)


class UnpaidHoursTests(unittest.TestCase):
    @staticmethod
    def result():
        fills = (Fill("farm", "plough", "area", "t", 100.0, 2.0, "buy"),
                 Fill("family", "plough", "area", "t", 100.0, 2.0, "sell"))
        return LabourResult("plough", "area", "coin", 2.0, 100.0, 0.0, 0.0, fills)

    def test_a_settlement_that_paid_nothing_delivers_no_hours(self):
        ledger = YearLedger()
        ledger.note_labour(self.result(), [])
        self.assertEqual(ledger.hours_hired.get("farm", {}).get("plough", 0.0), 0.0)
        self.assertEqual(ledger.hours_sold.get("family", 0.0), 0.0)

    def test_a_caller_with_no_settlement_counts_the_fills_in_full(self):
        ledger = YearLedger()
        ledger.note_labour(self.result(), settled=False)
        self.assertEqual(ledger.hours_hired["farm"]["plough"], 100.0)
        self.assertEqual(ledger.hours_sold["family"], 100.0)


class DeliveredVolumeTests(unittest.TestCase):
    def test_the_volume_remembered_is_what_changed_hands(self):
        book = Book()
        book.transfer(Transfer(EDGE_MINT, "buyer", "coin", 4.0, "opening"))        # pays for less than it bid for
        book.move_many([GoodsMove(EDGE_MINT, "seller", "timber", "t", 10.0, "opening")])
        bids = [Bid("buyer", "timber", "area", "t", 10.0, 0.0, 1.0, 1.0, 1e9, 0)]
        offers = [Offer("seller", "timber", "area", "t", 10.0, 1.0)]
        setup = types.SimpleNamespace(recipes={}, tax_forms=[], currency_id="coin", port_tile="t", capital_tile="t",
                                      opening_prices={}, state_agent="state")
        record = types.SimpleNamespace(producers={}, book=book, currency=CurrencySpec("coin", "fiat", None, 0.0, None), memory=MarketMemory(), curves={}, volumes={}, unsold={}, unmet={})
        area_map = types.SimpleNamespace(area_of=lambda good, tile: "area", goods=lambda: {"timber"})
        ledger = YearLedger()
        with mock.patch.object(year_goods.seller_offers, "strategic_offers", lambda s, r, v, b, o, p, costs=None: list(o)), \
                mock.patch.object(year_goods.market_curves, "kept_areas", lambda *args: set()):
            year_goods.clear_goods(setup, record, None, area_map, {("timber", "area"): (bids, offers)}, {}, ledger)
        delivered = 10.0 - book.stock("seller", "timber", "t")
        self.assertGreater(ledger.unpaid.get("buyer", 0.0), 0.0)        # the buyer could not pay in full
        self.assertLess(delivered, ledger.clearings[0].quantity)
        self.assertAlmostEqual(record.volumes["timber|area"], delivered)
        self.assertAlmostEqual(record.memory.volume_weights["timber|area"], delivered)


class WorkingCapitalLoanTests(unittest.TestCase):
    def test_a_cash_short_producer_with_a_margin_asks_for_a_one_year_loan_for_the_runs_it_could_not_pay(self):
        producer = farmer(last_runs=10.0)
        result = producers_close.close_year(producer, FARM, 100.0, 70.0, farm_view(2.0, cash=14.0), worked_runs=10.0)
        request = result.loan_request
        self.assertIsNotNone(request)
        self.assertEqual(request.purpose, producers_close.WORKING_CAPITAL_PURPOSE)
        self.assertEqual(request.years, 1.0)
        self.assertGreater(request.amount, 0.0)
        self.assertGreater(request.maximum_rate, 0.0)
        self.assertEqual(result.expansion_runs, 0.0)         # it buys no plant

    def test_a_producer_whose_runs_would_not_pay_asks_for_nothing(self):
        producer = farmer(last_runs=10.0)
        result = producers_close.close_year(producer, FARM, 100.0, 70.0, farm_view(0.1, cash=14.0), worked_runs=10.0)
        self.assertIsNone(result.loan_request)

    def test_a_producer_with_cash_for_its_runs_asks_for_nothing(self):
        producer = farmer(last_runs=10.0)
        result = producers_close.close_year(producer, FARM, 100.0, 70.0, farm_view(2.0, cash=1e6), worked_runs=10.0)
        self.assertIsNone(result.loan_request)


if __name__ == "__main__":
    unittest.main()
