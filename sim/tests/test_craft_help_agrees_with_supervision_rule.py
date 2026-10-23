"""The `ventures` help and the supervision rule read one test: a labouring trade is named as not craft, and it
gives no craft supervision. (Complaints/583 closed the old text; this calls the two on a built trade table.)"""
QUICK_TOPIC = True

import types
import unittest

from sim.labour.labour_capacity import CapacityMixin
from sim.ui.proto.dispatch_ventures import _non_craft_labour_names

FAMILIES = {"labourer": "labour", "porter": "labour", "smith": "craft", "chemist": "scholar"}


class _Labour(CapacityMixin):
    def __init__(self):
        self._world = types.SimpleNamespace(wages={trade: 1.0 for trade in FAMILIES}, trade_family=FAMILIES.get)


class CraftHelpTests(unittest.TestCase):
    def test_the_rule_counts_only_craft_family_trades(self):
        labour = _Labour()
        self.assertFalse(labour.is_craft_trade("labourer"))
        self.assertTrue(labour.is_craft_trade("smith"))

    def test_the_report_the_help_prints_is_the_rules_own_split(self):
        labour = _Labour()
        report = labour.craft_trades_report()
        self.assertEqual(report["craft"], ["smith"])
        self.assertIn("labourer", report["not_craft"])

    def test_the_help_names_the_labouring_trades_as_not_craft(self):
        sim = types.SimpleNamespace(labour=_Labour())
        names = _non_craft_labour_names(sim)
        self.assertIn("labourers", names)
        self.assertNotIn("smiths", names)


if __name__ == "__main__":
    unittest.main()
