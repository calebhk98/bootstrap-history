"""Complaint 610: spinning, weaving and finishing cloth are trades of their own and the textile recipes book their hours to them, not to the unskilled labourer or the generic craftsman."""
QUICK_TOPIC = True

import json
import os
import unittest

from sim.content.catalog import load_production_catalog

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PRODUCTION = load_production_catalog(_ROOT)
with open(os.path.join(_ROOT, "data", "world", "trades.json"), encoding="utf-8") as _handle:
    _TRADES = json.load(_handle)["trades"]

PLACEHOLDERS = {"labourer", "artisan"}

# recipe id -> the trades whose hours it must name (and so no longer books to the placeholders)
TEXTILE_RECIPES = {
    "thread_kg": {"spinner"}, "fabric_kg": {"weaver"}, "cloth_kg": {"fuller"},
    "linen_kg": {"farmer", "spinner", "weaver"}, "canvas_kg": {"spinner", "weaver"},
    "sailcloth_kg": {"spinner", "weaver"}, "felt_kg": {"fuller"},
    "cotton_fabric_kg": {"spinner", "weaver"}, "silk_kg": {"spinner", "weaver"},
    "twine_kg": {"spinner"}, "cordage_kg": {"spinner"},
    "fabric_backstrap_cotton_kg": {"spinner", "weaver"}, "fabric_backstrap_maguey_kg": {"spinner", "weaver"},
    "cloth_backstrap_kg": {"fuller"}, "dye_kg": {"farmer"},
}


class CraftTradesTests(unittest.TestCase):

    def test_textile_recipes_book_spinners_weavers_and_fullers(self):
        for recipe_id, trades in TEXTILE_RECIPES.items():
            self.assertIn(recipe_id, _PRODUCTION, recipe_id)
            hours = _PRODUCTION[recipe_id]["labour_hours"]
            self.assertEqual(set(hours) & PLACEHOLDERS, set(), recipe_id)
            self.assertEqual(set(hours), trades, recipe_id)
            for trade in trades:
                self.assertIn(trade, _TRADES, trade)

    def test_each_new_trade_states_a_training_time_its_source_and_a_fatality_source(self):
        for trade in ("spinner", "weaver", "fuller"):
            self.assertGreaterEqual(_TRADES[trade]["training_years"], 0, trade)
            self.assertTrue(_TRADES[trade].get("training_source"), trade)
            self.assertTrue(_TRADES[trade].get("fatality_source"), trade)
            self.assertTrue(_TRADES[trade].get("fatality_confidence"), trade)


if __name__ == "__main__":
    unittest.main()
