"""Complaint 533, stage 1: the dead-end check, the farm tool basket and dyed cloth. Each test calls the rule on built
inputs, then once on the shipped data."""
QUICK_TOPIC = True

import json  # noqa: F401
import os
import unittest

from sim.engine import validate_dead_ends
from sim.json_files import read_json
from sim.content.catalog import load_production_catalog
from sim.content.api import load_needs
from sim.labour import trade_data
from sim.world import need_basket

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _recipe(key, inputs=None, **extra):
    return dict({"outputs": {key: 1.0}, "inputs": inputs or {}}, **extra)


class DeadEndCheckTests(unittest.TestCase):

    def setUp(self):
        self.production = {
            "ore": _recipe("ore"), "bar": _recipe("bar", {"ore": 1.0}), "tool": _recipe("tool", {"bar": 1.0}),
            "dye": _recipe("dye"), "grain": _recipe("grain"),
            "cart": _recipe("cart", {"bar": 1.0}, carrier_use={"serves": {}}),
            "coin": _recipe("coin"), "spice": _recipe("spice"), "slag": _recipe("slag"),
            "hull": _recipe("hull", capital_asset=True),
        }

    def finds(self, **overrides):
        arguments = dict(production=self.production, need_goods={"grain": {"satisfies": {"food": 1.0}}},
                         service_lives={"tool": {"years": 4}}, trade_registry={}, state_goods={"coin"}, tree_materials=())
        arguments.update(overrides)
        return validate_dead_ends.dead_end_goods(**arguments)

    def test_a_good_nothing_takes_is_a_dead_end(self):
        nothing, _ = self.finds()
        self.assertEqual(nothing, ["dye", "slag", "spice"])

    def test_each_kind_of_consumer_removes_a_good_from_the_list(self):
        nothing, _ = self.finds(trade_registry={"farmer": {"tool_basket": ["dye"]}}, state_goods={"coin", "spice"})
        self.assertEqual(nothing, ["slag"])

    def test_a_recipe_that_takes_the_good_removes_it(self):
        self.production["dyed"] = _recipe("dyed", {"dye": 0.2, "tool": 1.0})
        nothing, _ = self.finds()
        self.assertNotIn("dye", nothing)
        self.assertIn("dyed", nothing)

    def test_goods_only_the_tree_takes_are_listed_apart(self):
        nothing, only_nodes = self.finds(tree_materials={"spice"})
        self.assertEqual((nothing, only_nodes), (["dye", "slag"], ["spice"]))

    def test_the_shipped_dye_and_iron_tools_have_consumers(self):
        lives = read_json(os.path.join(ROOT, "data", "world", "service_lives.json"))["years"]
        trades = read_json(os.path.join(ROOT, "data", "world", "trades.json"))["trades"]
        nothing, _ = validate_dead_ends.dead_end_goods(
            load_production_catalog(ROOT), load_needs(ROOT)["goods"], lives, trades, validate_dead_ends.state_goods())
        self.assertNotIn("dye_kg", nothing)
        self.assertNotIn("iron_tools_kg", nothing)


class ToolBasketTests(unittest.TestCase):

    REGISTRY = {"digger": {"tool_basket": ["spade"], "tool_stock_per_worker": {"spade": 2.0, "unlisted": 5.0}},
                "bystander": {}}

    def test_workers_hold_their_stock_and_wear_it_by_the_service_life(self):
        draw = trade_data.tool_draw(self.REGISTRY, "digger", 10.0, {"spade": 4.0})
        self.assertEqual(draw, {"spade": {"stock": 20.0, "wear_per_year": 5.0}})

    def test_a_good_with_no_service_life_wears_nothing_and_a_trade_without_tools_draws_none(self):
        self.assertEqual(trade_data.tool_draw(self.REGISTRY, "digger", 3.0, {})["spade"]["wear_per_year"], 0.0)
        self.assertEqual(trade_data.tool_draw(self.REGISTRY, "bystander", 3.0, {"spade": 4.0}), {})

    def test_the_shipped_farm_trade_draws_iron_tools_that_wear_out(self):
        trades = read_json(os.path.join(ROOT, "data", "world", "trades.json"))["trades"]
        lives = {good: spec["years"] for good, spec in
                 read_json(os.path.join(ROOT, "data", "world", "service_lives.json"))["years"].items()}
        draw = trade_data.tool_draw(trades, "farmer", 100.0, lives)["iron_tools_kg"]
        self.assertGreater(draw["stock"], 0.0)
        self.assertGreater(draw["wear_per_year"], 0.0)
        self.assertAlmostEqual(draw["wear_per_year"], draw["stock"] / lives["iron_tools_kg"])


class DyedClothTests(unittest.TestCase):

    def test_a_clothing_need_is_met_in_part_by_dyed_cloth(self):
        prices = {"cloth_kg": 10.0, "dyed_cloth_kg": 12.0}
        basket = need_basket.make_basket(load_needs(ROOT), {})
        clothing = [need for need in need_basket.need_prices(basket, prices.get) if need.spec.need_id == "clothing"][0]
        shares = {good: share for good, _, _, share in clothing.goods}
        self.assertGreater(shares["dyed_cloth_kg"], 0.0)
        self.assertGreater(shares["cloth_kg"], shares["dyed_cloth_kg"])   # dearer for the same cover, so a smaller share

    def test_the_dyed_cloth_recipe_consumes_dye_and_cloth(self):
        recipe = load_production_catalog(ROOT)["dyed_cloth_kg"]
        self.assertEqual(set(recipe["inputs"]), {"cloth_kg", "dye_kg"})


if __name__ == "__main__":
    unittest.main()
