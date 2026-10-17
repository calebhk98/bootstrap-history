"""Demand derives from what goods do: needs, effectiveness, recipes. No basket entry per good."""

QUICK_TOPIC = True

import copy
import json
import os
import tempfile
import unittest

from sim.engine import need_data
from sim.engine.mods import ModError
from sim.world import demand, need_demand

MOD_ID = "test_fantasy_k3f9"
POPULATION = 1_000_000.0
MEAN_INCOME = 550.0

BASE_PRODUCTION = {
    "wheat_kg": {"outputs": {"wheat_kg": 100.0}, "inputs": {},
                 "labour_hours": {"labourer": 10.0}},
    "bronze_kg": {"outputs": {"bronze_kg": 10.0}, "inputs": {},
                  "labour_hours": {"labourer": 20.0}},
    "iron_kg": {"outputs": {"iron_kg": 10.0}, "inputs": {},
                "labour_hours": {"labourer": 15.0}},
    "herb_kg": {"outputs": {"herb_kg": 10.0}, "inputs": {},
                "labour_hours": {"labourer": 20.0}},
    "ore_kg": {"outputs": {"ore_kg": 10.0}, "inputs": {},
               "labour_hours": {"labourer": 10.0}},
    "widget_unit": {"outputs": {"widget_unit": 1.0}, "inputs": {"ore_kg": 2.0},
                    "labour_hours": {"labourer": 1.0}},
    "idle_kg": {"outputs": {"idle_kg": 10.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}},
}

BASE_NEEDS = {
    "needs": {
        "food": {"surplus_budget_share": 0.4, "subsistence_per_capita_per_year": 200.0},
        "protection": {"surplus_budget_share": 0.4},
        "health": {"surplus_budget_share": 0.2},
    },
    "goods": {
        "wheat_kg": {"satisfies": {"food": 1.0}},
        "bronze_kg": {"satisfies": {"protection": 1.0}},
        "iron_kg": {"satisfies": {"protection": 2.0}},
        "herb_kg": {"satisfies": {"health": 1.0}},
        "widget_unit": {"satisfies": {"protection": 1.0}},
    },
}


def make_bins():
    return demand.income_bins(POPULATION, MEAN_INCOME)


def build(production=None, needs=None):
    return need_demand.NeedDemandModel(needs or BASE_NEEDS, production or BASE_PRODUCTION, make_bins())


def with_mithril(production=None, needs=None):
    """A mod-style addition: a far better, far rarer, harder-to-smelt metal."""
    production = copy.deepcopy(production or BASE_PRODUCTION)
    needs = copy.deepcopy(needs or BASE_NEEDS)
    production["mithril_kg"] = {
        "outputs": {"mithril_kg": 1.0}, "inputs": {"ore_kg": 5.0},
        "labour_hours": {"labourer": 200.0}}
    needs["goods"]["mithril_kg"] = {"satisfies": {"protection": 6.0}}
    return production, needs


class FinalDemandTests(unittest.TestCase):

    def test_households_spend_on_a_need_through_the_goods_that_satisfy_it(self):
        model = build()
        quantities = model.final_demand({"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 1.5,
                                         "herb_kg": 2.0, "widget_unit": 5.0})
        for material in ("wheat_kg", "bronze_kg", "iron_kg", "herb_kg"):
            self.assertGreater(quantities[material], 0.0, material)

    def test_a_good_no_need_wants_has_no_final_demand(self):
        model = build()
        quantities = model.final_demand({"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 1.5,
                                         "herb_kg": 2.0, "idle_kg": 1.0, "widget_unit": 5.0})
        self.assertNotIn("idle_kg", quantities)

    def test_spending_never_exceeds_income(self):
        model = build()
        prices = {"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 1.5, "herb_kg": 2.0,
                  "widget_unit": 5.0}
        quantities = model.final_demand(prices)
        spending = sum(prices[material] * quantity for material, quantity in quantities.items())
        self.assertAlmostEqual(spending, demand.total_income(make_bins()), delta=spending * 1e-6)

    def test_a_dearer_good_takes_a_smaller_share_of_its_need(self):
        model = build()
        cheap = model.final_demand({"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 2.0,
                                    "herb_kg": 2.0, "widget_unit": 50.0})
        dear = model.final_demand({"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 4.0,
                                   "herb_kg": 2.0, "widget_unit": 50.0})
        self.assertLess(dear["iron_kg"], cheap["iron_kg"])
        self.assertGreater(dear["bronze_kg"], cheap["bronze_kg"])


class SubstitutionTests(unittest.TestCase):

    def test_a_strictly_better_good_at_equal_cost_takes_most_of_the_need(self):
        model = build()
        quantities = model.final_demand({"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 2.0,
                                         "herb_kg": 2.0, "widget_unit": 500.0})
        self.assertGreater(quantities["iron_kg"], quantities["bronze_kg"])

    def test_share_follows_effectiveness_per_unit_cost(self):
        model = build()
        # Iron is twice as effective, so at twice the price it costs the same per effect.
        quantities = model.final_demand({"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 4.0,
                                         "herb_kg": 2.0, "widget_unit": 500.0})
        self.assertAlmostEqual(quantities["iron_kg"] * 2.0, quantities["bronze_kg"],
                               delta=quantities["bronze_kg"] * 1e-9)


class ModGoodsGetDemandTests(unittest.TestCase):

    def test_a_health_good_far_better_than_existing_medicine_takes_the_health_budget(self):
        production = copy.deepcopy(BASE_PRODUCTION)
        needs = copy.deepcopy(BASE_NEEDS)
        production[MOD_ID + ":panacea_kg"] = {
            "outputs": {MOD_ID + ":panacea_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 20.0}}
        needs["goods"][MOD_ID + ":panacea_kg"] = {"satisfies": {"health": 200.0}}
        model = build(production, needs)
        prices = {"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 1.5, "herb_kg": 2.0,
                  "widget_unit": 5.0, MOD_ID + ":panacea_kg": 20.0}
        quantities = model.final_demand(prices)
        panacea_spending = prices[MOD_ID + ":panacea_kg"] * quantities[MOD_ID + ":panacea_kg"]
        herb_spending = prices["herb_kg"] * quantities["herb_kg"]
        self.assertGreater(panacea_spending, 10.0 * herb_spending)
        without = build().final_demand({k: v for k, v in prices.items()
                                        if not k.startswith(MOD_ID)})
        self.assertGreater(quantities[MOD_ID + ":panacea_kg"] * 200.0,
                           without["herb_kg"] * 1.0)

    def test_the_effectiveness_can_sit_on_the_production_entry(self):
        production = copy.deepcopy(BASE_PRODUCTION)
        production["charm_kg"] = {
            "outputs": {"charm_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 5.0}, "satisfies": {"health": 3.0}}
        model = build(production)
        quantities = model.final_demand({"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 1.5,
                                         "herb_kg": 2.0, "widget_unit": 5.0, "charm_kg": 2.0})
        self.assertGreater(quantities["charm_kg"], 0.0)


class DerivedDemandTests(unittest.TestCase):

    PRICES = {"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 1.5, "herb_kg": 2.0,
              "widget_unit": 5.0, "ore_kg": 1.0}

    def test_an_input_is_demanded_because_a_wanted_good_consumes_it(self):
        model = build()
        total = model.total_demand(self.PRICES)
        final = model.final_demand(self.PRICES)
        self.assertNotIn("ore_kg", final)
        self.assertAlmostEqual(total["ore_kg"], 2.0 * final["widget_unit"],
                               delta=total["ore_kg"] * 1e-9)

    def test_removing_the_only_consuming_recipe_removes_the_derived_demand(self):
        production = copy.deepcopy(BASE_PRODUCTION)
        del production["widget_unit"]
        model = build(production)
        self.assertEqual(model.total_demand(self.PRICES).get("ore_kg", 0.0), 0.0)

    def test_a_good_nothing_uses_and_no_need_wants_has_no_demand(self):
        model = build()
        self.assertEqual(model.total_demand(self.PRICES).get("idle_kg", 0.0), 0.0)

    def test_demand_passes_through_a_chain_of_recipes(self):
        production = copy.deepcopy(BASE_PRODUCTION)
        production["ingot_kg"] = {"outputs": {"ingot_kg": 1.0}, "inputs": {"ore_kg": 3.0},
                                  "labour_hours": {"labourer": 1.0}}
        production["widget_unit"]["inputs"] = {"ingot_kg": 2.0}
        model = build(production)
        prices = dict(self.PRICES, ingot_kg=4.0)
        total = model.total_demand(prices)
        self.assertAlmostEqual(total["ore_kg"], 6.0 * total["widget_unit"],
                               delta=total["ore_kg"] * 1e-6)

    def test_build_materials_of_capital_are_demanded_too(self):
        production = copy.deepcopy(BASE_PRODUCTION)
        production["widget_unit"]["capital"] = [
            {"good": "kiln", "build_materials": {"iron_kg": 40.0},
             "service_life_years": 10.0, "annual_output_at_basis": 4.0}]
        model = build(production)
        total = model.total_demand(self.PRICES)
        final = model.final_demand(self.PRICES)
        self.assertGreater(total["iron_kg"], final["iron_kg"])

class ModMetalDisplacementTests(unittest.TestCase):

    def test_the_metals_a_better_one_displaces_lose_demand(self):
        production, needs = with_mithril()
        prices = {"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 1.5, "herb_kg": 2.0,
                  "widget_unit": 5.0, "mithril_kg": 3.0}
        with_mod = build(production, needs).final_demand(prices)
        without = build().final_demand({k: v for k, v in prices.items() if k != "mithril_kg"})
        self.assertLess(with_mod["iron_kg"], without["iron_kg"])


class NeedDataFileTests(unittest.TestCase):

    def _write_mod(self, parent, needs_file):
        folder = os.path.join(parent, "mods", MOD_ID)
        os.makedirs(os.path.join(folder, "data", "world"))
        with open(os.path.join(folder, "mod.json"), "w") as handle:
            json.dump({"id": MOD_ID, "name": "t", "version": "1",
                       "dependencies": [], "conflicts": []}, handle)
        with open(os.path.join(folder, "data", "world", "needs.json"), "w") as handle:
            json.dump(needs_file, handle)

    def _base_root(self, parent):
        os.makedirs(os.path.join(parent, "data", "world"))
        with open(os.path.join(parent, "data", "world", "needs.json"), "w") as handle:
            json.dump(BASE_NEEDS, handle)

    def test_a_mod_adds_a_need_and_goods_without_touching_base_data(self):
        with tempfile.TemporaryDirectory() as root:
            self._base_root(root)
            self._write_mod(root, {
                "needs": {MOD_ID + ":devotion": {"surplus_budget_share": 0.1}},
                "goods": {MOD_ID + ":relic_kg": {"satisfies": {MOD_ID + ":devotion": 4.0}},
                          "iron_kg": {"satisfies": {MOD_ID + ":devotion": 0.5}}}})
            merged = need_data.load_needs(root)
        self.assertIn(MOD_ID + ":devotion", merged["needs"])
        self.assertIn("protection", merged["needs"])
        self.assertEqual(merged["goods"]["iron_kg"]["satisfies"],
                         {"protection": 2.0, MOD_ID + ":devotion": 0.5})

    def test_a_mod_need_outside_its_namespace_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            self._base_root(root)
            self._write_mod(root, {"needs": {"devotion": {"surplus_budget_share": 0.1}}})
            with self.assertRaises(ModError):
                need_data.load_needs(root)

    def test_a_good_naming_an_unknown_need_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            self._base_root(root)
            self._write_mod(root, {"goods": {MOD_ID + ":relic_kg": {
                "satisfies": {"no_such_need": 1.0}}}})
            with self.assertRaises(ModError):
                need_data.load_needs(root)

    def test_the_base_file_names_only_real_materials_and_needs(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        loaded = need_data.load_needs(root)
        production = demand.production_data()
        made = set(production) | {good for entry in production.values() for good in entry["outputs"]}
        for material, attributes in loaded["goods"].items():
            self.assertIn(material, made, material)
            for need in attributes.get("satisfies", {}):
                self.assertIn(need, loaded["needs"], material)
        shares = [need["surplus_budget_share"] for need in loaded["needs"].values()]
        self.assertGreater(min(shares), 0.0)


class RealDataTests(unittest.TestCase):

    def test_no_basket_entry_exists_for_any_good(self):
        self.assertFalse(hasattr(demand, "DEFAULT_BASKET"))
        self.assertFalse(hasattr(demand, "PLATINUM"))


if __name__ == "__main__":
    unittest.main()
