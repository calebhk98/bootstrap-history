"""Complaint 611: herding and milling are trades of their own and the herd and flour recipes book their hours to them, not to the unskilled labourer."""
QUICK_TOPIC = True

import json
import os
import unittest

from sim.engine.catalog import load_production_catalog

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PRODUCTION = load_production_catalog(_ROOT)
with open(os.path.join(_ROOT, "data", "world", "trades.json"), encoding="utf-8") as _handle:
    _TRADES = json.load(_handle)["trades"]

PLACEHOLDERS = {"labourer", "artisan"}

# recipe id -> the trades whose hours it must name (and so no longer books to the placeholders)
HERD_AND_MILL_RECIPES = {
    "wool_kg": {"herder"}, "milk_kg": {"herder"}, "meat_kg": {"herder"}, "sheep_kg": {"herder"},
    "goat_kg": {"herder"}, "cattle_kg": {"herder"}, "dairy_cattle_kg": {"herder"},
    "cashmere_goat_kg": {"herder"}, "angora_goat_kg": {"herder"}, "draught_animal_kg": {"herder"},
    "ox": {"herder"}, "mule": {"herder"}, "cheese_kg": {"herder"},
    "flour_kg": {"miller"}, "flour_kg_millet": {"miller"}, "flour_kg_maize": {"miller"},
    "flour_kg_wholemeal": {"miller"}, "flour_kg_millet_wholemeal": {"miller"},
    "flour_kg_maize_wholemeal": {"miller"},
}


class CraftTradesTests(unittest.TestCase):

    def test_herd_and_flour_recipes_book_herders_and_millers(self):
        for recipe_id, trades in HERD_AND_MILL_RECIPES.items():
            self.assertIn(recipe_id, _PRODUCTION, recipe_id)
            hours = _PRODUCTION[recipe_id]["labour_hours"]
            self.assertEqual(set(hours) & PLACEHOLDERS, set(), recipe_id)
            self.assertEqual(set(hours), trades, recipe_id)
            for trade in trades:
                self.assertIn(trade, _TRADES, trade)

    def test_each_new_trade_states_a_training_time_its_source_and_a_fatality_source(self):
        for trade in ("herder", "miller"):
            self.assertGreaterEqual(_TRADES[trade]["training_years"], 0, trade)
            self.assertTrue(_TRADES[trade].get("training_source"), trade)
            self.assertTrue(_TRADES[trade].get("fatality_source"), trade)
            self.assertTrue(_TRADES[trade].get("fatality_confidence"), trade)


if __name__ == "__main__":
    unittest.main()
