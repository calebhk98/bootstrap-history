"""Complaint 285: the `why`, `path` and `anatomy` screens follow the chosen units.

These screens need a technology as an argument, so a game would be needed to ask for them; the replies are
written by hand instead (the same shape the dispatchers build) and rendered through the same path a screen
takes: the reply gets its `_display` siblings, then render_pretty prints it.
"""

QUICK_TOPIC = True

import ast
import json
import os
import re
import unittest
from types import SimpleNamespace

from sim.engine import units as U
from sim.ui.proto.render_typed import render_pretty

NATIVE = re.compile(r"\bden\b|\bdenarii\b|\btonnes?\b|\bt/yr\b|\bkg\b|\bha\b|/ha\b")
BLOBS = {
    "blob_mass": {"name": "blob", "symbol": "blob", "dimension": "mass", "factor": 7.0},
    "blob_money": {"name": "blob", "symbol": "blob", "dimension": "money", "factor": 3.0},
}
WHY = {
    "ok": True, "id": "iron_works", "name": "Iron works", "cat": "metal",
    "cost": {"total": 600.0, "labour": 150.0, "capital": 300.0, "materials": 150.0,
             "civ_domain_factor": 1.0, "price_index": 1.0, "material_distance_factor": 1.0, "opposition_factor": 1.0},
    "material_rows": [{"material": "iron", "needed_tonnes": 14.0, "held_tonnes": 7.0, "missing_tonnes": 7.0,
                       "cost_of_missing": 30.0}],
    "upkeep": 12.0, "revenue": 30.0, "but_it_pays_YOU": 6.0, "because": "the smith is yours",
    "charge_to_open": 45.0, "chain_size": 3, "chain_size_counting_what_you_have_built": 4,
    "chain_founder_hours": 10.0, "chain_cost": 900.0, "critical_path_years": 5.0,
}
PATH = {
    "ok": True, "id": "steel", "name": "Steel", "remaining_count": 2, "startable_today_count": 1,
    "still_waiting_on_something_else": 1,
    "startable_today_toward_this": [{"id": "bloomery", "name": "Bloomery", "cost": 300.0, "founder_hours": 20,
                                     "earns_per_year": 60.0, "costs_per_year_after": 30.0, "net_per_year": 30.0}],
    "knowledge_loss_warning": {
        "name": "the sack", "years": [100, 102], "years_until": 3, "in_progress": False,
        "technologies_at_risk": 40, "expected_technologies_lost_per_sacking": 8.0,
        "cheapest_hedge": {"id": "archive", "steps_away": 1, "cost": 900.0,
                           "expected_technologies_lost_per_sacking_once_built": 2.0}},
}


class HandScreens(unittest.TestCase):
    def setUp(self):
        self.original = dict(U.PREFERENCES)
        registry = json.loads(json.dumps(U.load_units(U.ROOT)))
        registry["units"].update(BLOBS)
        U.set_registry(registry)
        self.game = SimpleNamespace(civ={"id": "rome_100ad", "currency_words": {"long": "denarii", "short": "den"}},
                                    labour=SimpleNamespace(money_per_labour_hour=lambda: 0.5))

    def tearDown(self):
        U.set_registry(None)
        U.set_preferences(self.original)

    def text(self, name, reply, chosen):
        U.set_preferences(chosen)
        return render_pretty(name, U.add_display(json.loads(json.dumps(reply)), self.game))

    def test_why_prints_money_and_mass_in_the_chosen_units(self):
        text = self.text("why", WHY, {"money": "blob_money", "mass": "blob_mass"})
        self.assertIsNone(NATIVE.search(text), text)
        self.assertIn("COST: 400 blob total", text)
        self.assertIn("UPKEEP: 8 blob/yr", text)
        self.assertIn("need 2,000, hold 1,000, missing 1,000 -> 20 blob", text)
        self.assertIn("STILL TO BUILD BEHIND IT", text)
        self.assertIn("600 blob", text)

    def test_why_by_default_still_reads_as_it_always_did(self):
        text = self.text("why", WHY, {})
        self.assertIn("COST: 600 den total", text)
        self.assertIn("need 14, hold 7, missing 7", text)

    def test_path_prints_the_table_and_the_warning_in_the_chosen_money(self):
        text = self.text("path", PATH, {"money": "blob_money"})
        self.assertIsNone(NATIVE.search(text), text)
        self.assertIn("about 600 blob", text)
        self.assertIn("200", text.split("bloomery", 1)[1].splitlines()[0])

    def test_path_by_default_names_the_civilisations_coin(self):
        text = self.text("path", PATH, {})
        self.assertIn("about 900 denarii", text)

    def test_anatomy_rows_carry_no_mass_area_money_or_temperature_unit(self):
        """The anatomy screen's rows are fractions, counts, flows and kilowatts; a unit it names must not be a
        registry unit of a dimension the player can change, or it would need converting."""
        path = os.path.join(U.ROOT, "sim", "ui", "proto", "anatomy.py")
        units_named = set()
        for node in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_row" and len(node.args) >= 3:
                if isinstance(node.args[2], ast.Constant) and isinstance(node.args[2].value, str):
                    units_named.add(node.args[2].value)
        registry = U.registry()
        words = {word.lower() for spec in registry["units"].values()
                 for word in (spec["name"], spec["symbol"], spec.get("plural")) if word}
        self.assertTrue(units_named, "the scan found the units the rows name")
        self.assertEqual({unit for unit in units_named if unit.lower() in words}, set())


if __name__ == "__main__":
    unittest.main()
