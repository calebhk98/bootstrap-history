"""Complaints 552, 613: the carriage report gives demanded and hired hours by carrier trade and the fee split."""
import unittest

from sim.book_types import Transfer
from sim.economy import carriage_report
from sim.economy.merchants import EDGE_CARRIAGE

QUICK_TOPIC = True


class CarriageReportTests(unittest.TestCase):
    def test_demanded_hours_sum_over_merchants_and_areas_by_trade(self):
        bids = [("m1", "carter", "a", 10.0, 1.0), ("m2", "carter", "b", 5.0, 1.0), ("m1", "porter", "a", 3.0, 1.0)]
        self.assertEqual(carriage_report.demanded_by_trade(bids), {"carter": 15.0, "porter": 3.0})

    def test_hired_hours_sum_over_merchants_and_areas_by_trade(self):
        bought = {"m1": {("carter", "a"): 4.0, ("porter", "a"): 1.0}, "m2": {("carter", "b"): 2.0}}
        self.assertEqual(carriage_report.hired_by_trade(bought), {"carter": 6.0, "porter": 1.0})

    def test_fee_split_separates_the_edge_account_from_households(self):
        fees = [Transfer("m1", "household_x", "coin", 7.0, "carriage of wheat"), Transfer("m1", EDGE_CARRIAGE, "coin", 2.0, "c"),
                Transfer("m2", "household_y", "coin", 1.0, "c")]
        self.assertEqual(carriage_report.fee_split(fees), carriage_report.FeeSplit(8.0, 2.0))

    def test_build_lists_every_trade_bid_or_hired_in_name_order(self):
        report = carriage_report.build([("m1", "sailor", "a", 8.0, 1.0)], {"m1": {("sailor", "a"): 6.0, ("porter", "a"): 1.0}}, [])
        self.assertEqual(report.trades, (carriage_report.TradeHours("porter", 0.0, 1.0), carriage_report.TradeHours("sailor", 8.0, 6.0)))
        self.assertEqual(report.fees, carriage_report.FeeSplit(0.0, 0.0))

    def test_format_prints_hired_share_and_fee(self):  # presentation: the report's layout
        text = carriage_report.format_report(carriage_report.build([("m", "carter", "a", 10.0, 1.0)], {"m": {("carter", "a"): 5.0}}, []))
        self.assertIn("carter", text)
        self.assertIn("0.500", text)
        self.assertIn("fallback", text)


if __name__ == "__main__":
    unittest.main()
