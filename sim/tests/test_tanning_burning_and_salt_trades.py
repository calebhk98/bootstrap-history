"""Complaint 612: tanning, charcoal burning, lime burning and salt working are trades of their own, their recipes book those hours, and leather has finished goods."""
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

# recipe id -> the trades whose hours it must name
BOOKED = {
    "charcoal_kg": {"charcoal_burner"},
    "lime_kg": {"lime_burner"}, "lime_wood_kg": {"lime_burner"},
    "leather_kg": {"tanner"}, "parchment_sheet": {"tanner"}, "vellum_kg": {"tanner"},
    "salt_kg": {"miner", "salt_worker"}, "salt_solar_kg": {"salt_worker"}, "salt_brine_kg": {"salt_worker"},
    "shoes_pair": {"leatherworker"}, "harness_set": {"leatherworker"}, "scabbard_leather": {"leatherworker"},
}
NEW_TRADES = ("tanner", "leatherworker", "charcoal_burner", "lime_burner", "salt_worker")
LEATHER_GOODS = ("shoes_pair", "harness_set", "scabbard_leather")


class TanningBurningAndSaltTradeTests(unittest.TestCase):

    def test_recipes_book_the_new_trades_and_not_the_placeholders(self):
        for recipe_id, trades in BOOKED.items():
            self.assertIn(recipe_id, _PRODUCTION, recipe_id)
            hours = _PRODUCTION[recipe_id]["labour_hours"]
            self.assertEqual(set(hours) & PLACEHOLDERS, set(), recipe_id)
            self.assertEqual(set(hours), trades, recipe_id)

    def test_each_new_trade_states_training_and_fatality_sources(self):
        for trade in NEW_TRADES:
            self.assertGreaterEqual(_TRADES[trade]["training_years"], 0, trade)
            self.assertTrue(_TRADES[trade].get("training_source"), trade)
            self.assertTrue(_TRADES[trade].get("fatality_source"), trade)
            self.assertTrue(_TRADES[trade].get("fatality_confidence"), trade)

    def test_leather_goods_are_made_from_the_tanners_leather(self):
        for good in LEATHER_GOODS:
            recipe = _PRODUCTION[good]
            self.assertIn(good, recipe["outputs"], good)
            self.assertGreater(recipe["inputs"]["leather_kg"], 0, good)
            self.assertGreater(recipe["unit_mass_kg"], 0, good)

    def test_households_can_buy_shoes_as_clothing(self):
        self.assertGreater(_PRODUCTION["shoes_pair"]["satisfies"]["clothing"], 0)


if __name__ == "__main__":
    unittest.main()
