"""SCENARIO (Complaint 560): Rome's opened economy holds no sugar or maize and eats grain first, from a pre-modern diet
(Garnsey, Food and Society in Classical Antiquity, 1999). The growing and knowledge rules are in test_sugar_maize_knowledge."""

import json
import os
import unittest

from sim.economy import opening
from sim.engine.economy_port_setup import build_setup
from sim.tests.harness import unopened_sim

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GRAINS = ("wheat_kg", "millet_kg", "flour_kg")


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return json.load(handle)


_OPENED = {}


def _production_entry(good):
    """The production entry whose id is the good (a prepared food is made by one recipe of its own name)."""
    directory = os.path.join(ROOT, "data", "production")
    for name in sorted(os.listdir(directory)):
        if name.endswith(".json"):
            entry = _read("data", "production", name).get("materials", {}).get(good)
            if entry is not None:
                return entry
    return None


def cereal_units(units, needs):
    """The food units of `units` that come from grain: a grain counts whole, and a food made from grain counts the part
    of its food that its grain inputs carry (bread is all flour; a meal is flour and vegetables), since a household that
    buys flour or bread rather than grinding eats the same cereal."""
    cereal = 0.0
    for good, value in units.items():
        if good in GRAINS:
            cereal += value
            continue
        entry = _production_entry(good)
        if entry is None or not value:
            continue
        food_of = lambda made: needs.get(made, {}).get("satisfies", {}).get("food", 0.0)
        inputs = entry.get("inputs", {})
        in_grain = sum(quantity * food_of(made) for made, quantity in inputs.items() if made in GRAINS)
        in_all = sum(quantity * food_of(made) for made, quantity in inputs.items())
        cereal += value * in_grain / in_all if in_all > 0.0 else 0.0
    return cereal


def _rome_opening():
    """Rome's setup and opened economy record, opened once for the topic (the opening is a few seconds of solving)."""
    if "rome" not in _OPENED:
        setup = build_setup(unopened_sim(civ="rome_100ad"))
        _OPENED["rome"] = (setup, opening.open_economy(setup)[0])
    return _OPENED["rome"]


class CerealUnitsTests(unittest.TestCase):
    def test_flour_and_bread_are_cereal_and_a_meal_is_cereal_by_its_flour(self):
        needs = _read("data", "world", "needs.json")["goods"]
        self.assertAlmostEqual(cereal_units({"flour_kg": 1.0, "bread_kg": 2.0}, needs), 3.0)
        flour_food = 300.0 * needs["flour_kg"]["satisfies"]["food"]
        vegetable_food = 200.0 * needs["vegetable_kg"]["satisfies"]["food"]
        self.assertAlmostEqual(cereal_units({"cooked_meal_kg": 1.0}, needs), flour_food / (flour_food + vegetable_food))
        self.assertEqual(cereal_units({"olive_oil_kg": 5.0}, needs), 0.0)


class RomeOpeningTests(unittest.TestCase):
    def test_rome_opens_with_no_sugar_or_maize_and_eats_grain_first(self):
        setup, record = _rome_opening()
        self.assertNotIn("mat_sugar", setup.opening_prices)
        self.assertNotIn("maize_kg", setup.opening_prices)
        needs = _read("data", "world", "needs.json")["goods"]
        units = {good: record.opening_basket.get(good, 0.0) * attributes["satisfies"]["food"]
                 for good, attributes in needs.items() if "food" in attributes["satisfies"]}
        self.assertEqual(units["mat_sugar"], 0.0)
        self.assertEqual(units["maize_kg"], 0.0)
        total = sum(units.values())
        grains = cereal_units(units, needs)
        self.assertGreater(grains / total, 0.5, {good: round(value / total, 3) for good, value in units.items() if value})

    def test_rome_food_units_follow_a_pre_modern_diet_and_no_one_good_dominates(self):
        # Roman diet composition (Garnsey, Food and Society in Classical Antiquity, 1999): cereals were the large
        # majority of calories; oil and wine were secondary. Cereals here must be a majority, and no other single
        # food may exceed a third of the units. Rendered fat is not a food in the model (Complaint 532).
        needs = _read("data", "world", "needs.json")["goods"]
        self.assertEqual(needs["fat_kg"]["satisfies"], {})
        _setup, record = _rome_opening()
        units = {good: record.opening_basket.get(good, 0.0) * attributes["satisfies"]["food"]
                 for good, attributes in needs.items() if "food" in attributes["satisfies"]}
        total = sum(units.values())
        shares = {good: value / total for good, value in units.items() if value}
        self.assertGreater(cereal_units(shares, needs), 0.5, shares)
        for good, share in shares.items():
            if good not in GRAINS:
                self.assertLess(share, 1 / 3, (good, shares))
        self.assertLess(max(shares.values()), 0.5, shares)


if __name__ == "__main__":
    unittest.main()
