"""No money amount is written in the book's denarii: constants, effect specs and
the commodity ledger state physical quantities, converted to a coin on read."""
import glob
import json
import os
import unittest

from sim.constants import REGISTRY
import sim.engine.core  # noqa: F401  (declares the engine constants)
from sim.engine import commodities, money_units

QUICK_TOPIC = True
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HOUR_CONSTANTS = [
    "CREDIT_LINE_LABOUR_HOURS_PER_REPUTATION_POINT",
    "BRIBE_LABOUR_HOURS_PER_SCANDAL_POINT",
    "ARREARS_CHEAP_PROJECT_FLOOR_LABOUR_HOURS",
    "ARREARS_HARD_STOP_FLOOR_LABOUR_HOURS",
    "INSOLVENCY_FLOOR_MIN_LABOUR_HOURS",
    "AUTO_BRIBE_CAPITAL_THRESHOLD_LABOUR_HOURS",
    "AUTO_BRIBE_COST_LABOUR_HOURS_PER_SCANDAL_POINT",
    "BRIBE_SCANDAL_REDUCTION_LABOUR_HOURS_PER_POINT",
    "AUTO_FOREST_CAPITAL_LABOUR_HOURS_PER_HA",
    "NITRE_BED_SPEND_CEILING_LABOUR_HOURS",
]


class NoBookMoney(unittest.TestCase):

    def test_the_book_conversion_boundary_is_gone(self):
        self.assertFalse(hasattr(money_units, "book_to_money"))
        self.assertFalse(hasattr(money_units, "book_money_factor"))
        self.assertFalse(hasattr(money_units, "BOOK_LABOURER_WAGE_DENARII_PER_HOUR"))
        self.assertNotIn("BOOK_LABOURER_WAGE_DENARII_PER_HOUR", REGISTRY)

    def test_no_declared_constant_is_book_money(self):
        self.assertFalse([name for name, entry in REGISTRY.items() if entry.get("book_money")])

    def test_money_amounts_are_declared_in_labour_hours(self):
        for name in HOUR_CONSTANTS:
            self.assertIn(name, REGISTRY)
            self.assertIn("labour hour", REGISTRY[name]["unit"], name)

    def test_branch_data_names_no_book_money_effect(self):
        for path in glob.glob(os.path.join(ROOT, "data", "branches", "*.json")):
            self.assertNotIn('"book_money"', open(path).read(), path)

    def test_commodities_carry_no_denarii_price(self):
        with open(os.path.join(ROOT, "data", "world", "commodities.json")) as handle:
            text = handle.read()
        self.assertNotIn("denarii", text)
        for commodity in json.loads(text)["commodities"].values():
            self.assertIn("price_material", commodity)

    def test_ledger_price_comes_from_the_solved_table(self):
        ledger = commodities.CommodityLedger(price_hours_per_kg={"iron_bar_kg": 7.0})
        self.assertEqual(ledger.base_price_hours_per_kg("iron"), 7.0)
        self.assertEqual(ledger.price("iron", demand_t=1.0, supply_t=1.0), 7.0)
        self.assertIsNone(ledger.base_price_hours_per_kg("wool"))


if __name__ == "__main__":
    unittest.main()
