"""Complaint 618: obsidian and flint are quarried, a knapper strikes blades and tools, and the implements need has a stone route."""
QUICK_TOPIC = True

import json
import os
import unittest

from sim.engine.catalog import load_production_catalog
from sim.engine.need_data import load_needs
from sim.world import need_basket

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PRODUCTION = load_production_catalog(_ROOT)
_NEEDS = load_needs(_ROOT)
_BASKET = need_basket.make_basket(_NEEDS, _PRODUCTION)
_IMPLEMENTS = next(spec for spec in _BASKET.needs if spec.need_id == "implements_and_arms")
_STONE_GOODS = ("obsidian_blade_kg", "flint_tool_kg")


def _civilisation(name):
    with open(os.path.join(_ROOT, "data", "civilizations", name + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


def _trades():
    with open(os.path.join(_ROOT, "data", "world", "trades.json"), encoding="utf-8") as handle:
        return json.load(handle)["trades"]


def _price_index(offered):
    priced = need_basket.priced_need(_IMPLEMENTS, 1.0 - _BASKET.substitution, lambda good: offered.get(good))
    return None if priced is None else priced.price_index


class StoneRouteTests(unittest.TestCase):

    def test_the_metals_a_mexica_household_would_buy_cannot_be_made_there(self):
        mexica = _civilisation("mexica_1500")
        held = set(mexica["starting_techs"])
        # iron and steel and brass are gated on nodes it lacks
        for good in ("iron_bar_kg", "steel_plate_kg", "tool_steel_kg", "cast_iron_kg", "brass_kg"):
            gates = [entry.get("requires_node") for entry in _PRODUCTION.values() if good in entry["outputs"]]
            self.assertFalse(any(gate is None or gate in held for gate in gates), good)
        # bronze is gated on a held node, but its tin is gated on one it lacks
        bronze = _PRODUCTION["bronze_kg"]
        self.assertIn(bronze["requires_node"], held)
        tin_gates = [entry.get("requires_node") for entry in _PRODUCTION.values() if "tin_kg" in entry["outputs"]]
        self.assertFalse(any(gate is None or gate in held for gate in tin_gates))

    def test_a_household_offered_only_stone_tools_meets_the_implements_need(self):
        for good in _STONE_GOODS:
            self.assertIn(good, dict(_IMPLEMENTS.goods))
            index = _price_index({good: 10.0})
            self.assertIsNotNone(index, good)
            self.assertGreater(index, 0.0)

    def test_without_any_implement_good_the_need_has_no_price(self):
        self.assertIsNone(_price_index({}))

    def test_at_equal_prices_the_more_effective_stone_good_takes_the_larger_share(self):
        priced = need_basket.priced_need(_IMPLEMENTS, 1.0 - _BASKET.substitution,
                                         {"obsidian_blade_kg": 10.0, "flint_tool_kg": 10.0}.get)
        shares = {good: share for good, _price, _effect, share in priced.goods}
        self.assertGreater(shares["obsidian_blade_kg"], shares["flint_tool_kg"])

    def test_the_blade_recipe_follows_the_measured_mass_balance(self):
        recipe = _PRODUCTION["obsidian_blade_kg"]
        self.assertEqual(recipe["requires_node"], "mat_obsidian_blade")
        self.assertIn("mat_obsidian_blade", _civilisation("mexica_1500")["starting_techs"])
        # 91 percent of a preformed core's weight leaves as blades (Sheets and Muto 1972)
        self.assertAlmostEqual(recipe["outputs"]["obsidian_blade_kg"] / recipe["inputs"]["obsidian_kg"], 0.91, places=2)
        self.assertEqual(set(recipe["labour_hours"]), {"knapper"})

    def test_raw_stone_is_extracted_without_inputs_and_flint_tools_need_no_node(self):
        for good in ("obsidian_kg", "flint_kg"):
            self.assertEqual(_PRODUCTION[good]["inputs"], {})
            self.assertEqual(_PRODUCTION[good]["extracted_from"], "quarry")
        self.assertIsNone(_PRODUCTION["flint_tool_kg"]["requires_node"])
        self.assertIn("flint_kg", _PRODUCTION["flint_tool_kg"]["inputs"])

    def test_a_knapper_trade_exists_with_training_and_a_source(self):
        knapper = _trades()["knapper"]
        self.assertGreater(knapper["training_years"], 0)
        self.assertTrue(knapper["training_source"])
        self.assertTrue(knapper["fatality_source"])

    def test_every_unsourced_stone_figure_names_its_retirement(self):
        for good in ("obsidian_kg", "flint_kg", "obsidian_blade_kg", "flint_tool_kg"):
            self.assertTrue(_PRODUCTION[good]["retire"], good)
            self.assertEqual(_PRODUCTION[good]["conf"], "D")


if __name__ == "__main__":
    unittest.main()
