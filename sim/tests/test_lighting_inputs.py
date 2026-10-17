"""Lighting follows geography: where the crops grow, which wick, and the lamp's vessel (Complaint 531)."""

import json
import os
import unittest

from sim.geography import crop_climate

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _entries():
    merged = {}
    production = os.path.join(ROOT, "data", "production")
    for name in sorted(os.listdir(production)):
        if name.endswith(".json") and not name.startswith("_"):
            with open(os.path.join(production, name), encoding="utf-8") as handle:
                merged.update(json.load(handle).get("materials") or {})
    return merged


class LightingInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = _entries()

    def test_the_three_crops_declare_climates(self):
        for crop in ("olive_oil_kg", "wine_common_kg", "cotton_kg"):
            self.assertTrue(self.entries[crop].get(crop_climate.CLASSES_FIELD), crop)

    def test_a_cold_climate_cannot_grow_olives_but_a_mediterranean_one_can(self):
        olives = self.entries["olive_oil_kg"]
        self.assertFalse(crop_climate.territory_suits(olives, {"Dfc", "ET", "Cfb"}))
        self.assertTrue(crop_climate.territory_suits(olives, {"Csa"}))

    def test_cotton_needs_a_long_frost_free_season(self):
        cotton = self.entries["cotton_kg"]
        self.assertFalse(crop_climate.territory_suits(cotton, {"Dfb", "Cfb"}))
        self.assertTrue(crop_climate.territory_suits(cotton, {"Aw"}))

    def test_a_candle_can_use_a_wick_other_than_cotton(self):
        candles = [entry for entry in self.entries.values()
                   if (entry.get("satisfies") or {}).get("light") and "tallow_kg" in (entry.get("inputs") or {})]
        wicks = {wick for entry in candles for wick in entry["inputs"] if wick.startswith("wick_")}
        self.assertIn("wick_linen_m", wicks)
        self.assertIn("wick_cotton_m", wicks)
        self.assertNotIn("cotton_kg", self.entries["wick_linen_m"]["inputs"])

    def test_a_wax_candle_burns_wax(self):
        self.assertIn("wax_kg", self.entries["light_beeswax_candle"]["inputs"])

    def test_the_oil_lamp_takes_a_vessel(self):
        self.assertIn("ceramic_kg", self.entries["light_oil_lamp"]["inputs"])


if __name__ == "__main__":
    unittest.main()
