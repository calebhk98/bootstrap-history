"""Lighting follows geography: where the crops grow, which wick, and the lamp's vessel (Complaint 531)."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.geography import crop_climate
from sim.world import need_basket

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
        # the grown crops (olives, grapes), not the oil and wine made from them
        for crop in ("olives_kg", "grapes_kg", "cotton_kg"):
            self.assertTrue(self.entries[crop].get(crop_climate.CLASSES_FIELD), crop)

    def test_a_cold_climate_cannot_grow_olives_but_a_mediterranean_one_can(self):
        olives = self.entries["olives_kg"]
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

    def test_tallow_comes_only_from_herds(self):
        makers = [name for name, entry in self.entries.items() if "fat_kg" in (entry.get("outputs") or {})]
        self.assertTrue(makers)
        for name in makers:
            # fat is rendered from animals: a held herd or a hunted wild stock
            entry = self.entries[name]
            self.assertTrue(entry.get("herd_stock") or entry.get("extracted_from") in ("forest", "wetland"), name)
        self.assertIn("fat_kg", self.entries["tallow_kg"]["inputs"])

    def test_a_rush_wick_candle_exists_and_the_rush_is_gathered_not_spun(self):
        self.assertIn("wick_rush_m", self.entries["light_tallow_rushlight"]["inputs"])
        self.assertTrue(self.entries["wick_rush_m"].get("extracted_from"))
        self.assertFalse(self.entries["wick_rush_m"]["inputs"])

    def test_olives_need_a_node_the_americas_do_not_hold(self):
        node = self.entries["olive_oil_kg"]["requires_node"]
        self.assertTrue(node)
        self.assertIn(node, _start("rome_100ad"))
        self.assertNotIn(node, _start("mexica_1500"))
        self.assertIn("olive_oil_kg", _read("data", "civilizations", "mexica_1500.json")["unsupplied_basket_goods"])


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return json.load(handle)


def _start(civilisation_id):
    return _read("data", "civilizations", civilisation_id + ".json")["starting_techs"]


def _light_shares(prices):
    spec = need_basket.NeedSpec("light", 1.0, 1.0, (("oil_lamp_x", 1.0), ("candle_x", 1.0)))
    basket = need_basket.Basket((spec,), 2.0, {})
    (light,) = need_basket.need_prices(basket, prices.get)
    return {good: share for good, _price, _effect, share in light.goods}


class LightSpendingShares(unittest.TestCase):
    def test_a_good_with_no_price_takes_none_of_the_light_spending(self):
        self.assertEqual(_light_shares({"candle_x": 3.0}), {"candle_x": 1.0})

    def test_the_cheaper_light_takes_the_bigger_share(self):
        shares = _light_shares({"oil_lamp_x": 1.0, "candle_x": 3.0})
        self.assertGreater(shares["oil_lamp_x"], shares["candle_x"])
        self.assertAlmostEqual(sum(shares.values()), 1.0)


if __name__ == "__main__":
    unittest.main()
