"""Complaint 424: mass-per-year fields follow the chosen mass unit, with a per-year label, on the changes and
market screens; the plain and the per-year rules do not shadow each other."""

QUICK_TOPIC = True

import json
import unittest

from sim.engine import units as U
from sim.ui.proto.render_typed import render_pretty

RATE_FIELDS = ("change_t_per_yr", "shortfall_t_per_yr", "market_available_tonnes_per_year")
BLOB = {"name": "blob", "symbol": "blob", "dimension": "mass", "factor": 7.0}

CHANGES = {"ok": True, "capacity_gained_or_lost": [{"material": "iron", "change_t_per_yr": 14.0}]}
MARKET = {"ok": True, "materials": {"offset": 0, "total": 1, "rows": [
    {"material": "iron", "buy_per_tonne": 1.0, "sell_per_tonne": 1.0, "own_supply": False,
     "market_available_tonnes_per_year": 14.0}]}}


class RateUnitTests(unittest.TestCase):
    def setUp(self):
        self.original = (U.registry(), dict(U.PREFERENCES))
        fakes = json.loads(json.dumps(U.load_units(U.ROOT)))
        fakes["units"]["blob_mass"] = BLOB
        U.set_registry(fakes)

    def tearDown(self):
        U.set_registry(self.original[0])
        U.set_preferences(self.original[1])

    def test_each_mass_per_year_field_has_a_rule_with_a_per_year_label(self):
        for field in RATE_FIELDS:
            rule = U.field_rule(U.registry(), field)
            self.assertIsNotNone(rule, field)
            self.assertEqual((rule["dimension"], rule.get("per")), ("mass", "yr"), field)

    def test_a_price_per_mass_is_a_compound_of_money_and_mass(self):
        rule = U.field_rule(U.registry(), "buy_per_tonne")
        self.assertEqual((rule["dimension"], rule["per_dimension"]), ("money", "mass"))

    def test_the_changes_and_market_screens_print_the_chosen_unit_per_year(self):
        U.set_preferences({"mass": "blob_mass"})
        for name, reply in (("changes", CHANGES), ("market", MARKET)):
            text = render_pretty(name, U.add_display(json.loads(json.dumps(reply)), None))
            self.assertIn("blob/yr", text.lower(), text)
            self.assertRegex(text, r"2,?000")                  # 14 t is 2000 blob
            self.assertNotIn("t/yr", text.lower().replace("blob/yr", ""), text)

    def test_the_default_keeps_tonnes_per_year(self):
        text = render_pretty("changes", json.loads(json.dumps(CHANGES)))
        self.assertIn("+14.0 t/yr", text)


if __name__ == "__main__":
    unittest.main()
