"""Complaints/583: the craft help reads the supervision trade data.
The rule is a plain function (sim/labour/hire_outcome.py), called on built lists."""
QUICK_TOPIC = True

import unittest

from sim.engine.data import TRADE_FAMILY
from sim.labour.hire_outcome import craft_trades_report


class CraftTradesReportTests(unittest.TestCase):
    def test_the_report_splits_the_trades_by_the_test_it_is_given(self):
        report = craft_trades_report(["smith", "labourer", "mason", "scribe"], lambda trade: trade in ("smith", "mason"))
        self.assertEqual(report, {"craft": ["mason", "smith"], "not_craft": ["labourer", "scribe"]})

    def test_every_trade_is_in_exactly_one_list(self):
        trades = ["a", "b", "c", "d", "e"]
        report = craft_trades_report(trades, lambda trade: trade in "bd")
        self.assertEqual(sorted(report["craft"] + report["not_craft"]), trades)
        self.assertFalse(set(report["craft"]) & set(report["not_craft"]))

    def test_the_craft_trades_the_help_names_are_those_the_family_table_calls_craft(self):
        from sim.engine.data import trade_family
        report = craft_trades_report(TRADE_FAMILY, lambda trade: trade_family(trade) == "craft")
        self.assertEqual(sorted(report["craft"]), sorted(trade for trade, family in TRADE_FAMILY.items() if family == "craft"))
        self.assertTrue(report["craft"])

    def test_the_labourer_does_not_supervise_as_craft(self):
        from sim.engine.data import trade_family
        self.assertNotEqual(trade_family("labourer"), "craft")


if __name__ == "__main__":
    unittest.main()
