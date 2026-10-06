"""Demand derives from what goods do: needs, effectiveness, recipes. No basket entry per good."""

QUICK_TOPIC = True

import copy
import json
import os
import tempfile
import unittest
import warnings

from sim.engine import solve_prices
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


def build(production=None, needs=None, technology_demand=None):
    return need_demand.NeedDemandModel(
        needs or BASE_NEEDS, production or BASE_PRODUCTION, make_bins(),
        technology_demand=technology_demand)


def with_mithril(production=None, needs=None):
    """A mod-style addition: a far better, far rarer, harder-to-smelt metal."""
    production = copy.deepcopy(production or BASE_PRODUCTION)
    needs = copy.deepcopy(needs or BASE_NEEDS)
    production["mithril_kg"] = {
        "outputs": {"mithril_kg": 1.0}, "inputs": {"ore_kg": 5.0},
        "labour_hours": {"labourer": 200.0}}
    needs["goods"]["mithril_kg"] = {"satisfies": {"protection": 6.0},
                                    "supply_per_year": 300.0}
    return production, needs


def solve_with(production, needs, technology_demand=None, use_demand=True):
    """Solved prices for a small fixture world, labour as numeraire."""
    producers = solve_prices.build_producers_index(production)
    resolvable = {material for entry in production.values() for material in entry["outputs"]}
    anchors = None
    if use_demand:
        anchors = need_demand.NeedDemandAnchors(
            build(production, needs, technology_demand),
            supply_by_material=need_demand.declared_supply(needs, production))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        prices, _iterations, _residual, _chosen = solve_prices.solve(
            production, producers, resolvable, {"labourer": 1.0}, demand_anchors=anchors)
    return prices


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

    def test_technology_being_pursued_demands_its_build_materials(self):
        nodes = [
            {"id": "open", "pre": ["held"], "mat": {"idle_kg": 100.0}, "build_yrs": 2.0},
            {"id": "far", "pre": ["open"], "mat": {"herb_kg": 900.0}, "build_yrs": 1.0},
            {"id": "held", "pre": [], "mat": {"bronze_kg": 900.0}, "build_yrs": 1.0}]
        pursued = need_demand.technology_material_demand(nodes, {"held"})
        self.assertEqual(pursued, {"idle_kg": 50.0})
        model = build(technology_demand=pursued)
        self.assertGreater(model.total_demand(self.PRICES)["idle_kg"], 0.0)

    def test_technology_lookahead_can_reach_further_down_the_tree(self):
        nodes = [
            {"id": "open", "pre": ["held"], "mat": {}, "build_yrs": 1.0},
            {"id": "far", "pre": ["open"], "mat": {"herb_kg": 900.0}, "build_yrs": 1.0}]
        self.assertEqual(need_demand.technology_material_demand(nodes, {"held"}), {})
        deep = need_demand.technology_material_demand(nodes, {"held"}, lookahead_depth=2)
        self.assertEqual(deep, {"herb_kg": 900.0})


class ScarcityPricingTests(unittest.TestCase):

    def test_a_far_rarer_better_metal_prices_above_the_metals_it_beats(self):
        production, needs = with_mithril()
        prices = solve_with(production, needs)
        self.assertGreater(prices["mithril_kg"], prices["iron_kg"])
        self.assertGreater(prices["mithril_kg"], prices["bronze_kg"])

    def test_mithril_costs_more_than_its_own_process_because_supply_is_short(self):
        production, needs = with_mithril()
        cost_only = solve_with(production, needs, use_demand=False)
        priced = solve_with(production, needs)
        self.assertGreater(priced["mithril_kg"], 2.0 * cost_only["mithril_kg"])

    def test_a_less_rare_supply_clears_lower(self):
        production, needs = with_mithril()
        scarce = solve_with(production, needs)["mithril_kg"]
        needs["goods"]["mithril_kg"]["supply_per_year"] = 30000.0
        plentiful = solve_with(production, needs)["mithril_kg"]
        self.assertLess(plentiful, scarce)

    def test_ample_supply_leaves_the_price_at_cost(self):
        production, needs = with_mithril()
        needs["goods"]["mithril_kg"]["supply_per_year"] = 1e15
        cost_only = solve_with(production, needs, use_demand=False)
        self.assertAlmostEqual(solve_with(production, needs)["mithril_kg"],
                               cost_only["mithril_kg"], places=6)

    def test_a_good_with_no_demand_is_priced_at_its_cost(self):
        production, needs = with_mithril()
        needs["goods"]["idle_kg"] = {"supply_per_year": 10.0}
        cost_only = solve_with(production, needs, use_demand=False)
        self.assertAlmostEqual(solve_with(production, needs)["idle_kg"],
                               cost_only["idle_kg"], places=6)

    def test_the_metals_a_better_one_displaces_lose_demand(self):
        production, needs = with_mithril()
        prices = {"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 1.5, "herb_kg": 2.0,
                  "widget_unit": 5.0, "mithril_kg": 3.0}
        with_mod = build(production, needs).final_demand(prices)
        without = build().final_demand({k: v for k, v in prices.items() if k != "mithril_kg"})
        self.assertLess(with_mod["iron_kg"], without["iron_kg"])

    def test_a_supply_limited_good_reports_the_price_that_clears_it(self):
        production, needs = with_mithril()
        model = build(production, needs)
        prices = {"wheat_kg": 1.0, "bronze_kg": 2.0, "iron_kg": 1.5, "herb_kg": 2.0,
                  "widget_unit": 5.0, "ore_kg": 1.0, "mithril_kg": 3.0}
        clearing = model.clearing_prices(prices, {"mithril_kg": 300.0})["mithril_kg"]
        probe = dict(prices, mithril_kg=clearing)
        quantity = model.total_demand(probe)["mithril_kg"]
        self.assertAlmostEqual(quantity, 300.0, delta=300.0 * 1e-3)


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
        for material, attributes in loaded["goods"].items():
            self.assertIn(material, production, material)
            for need in attributes.get("satisfies", {}):
                self.assertIn(need, loaded["needs"], material)
        shares = [need["surplus_budget_share"] for need in loaded["needs"].values()]
        self.assertGreater(min(shares), 0.0)


class RealDataTests(unittest.TestCase):

    def test_no_basket_entry_exists_for_any_good(self):
        self.assertFalse(hasattr(demand, "DEFAULT_BASKET"))
        self.assertFalse(hasattr(demand, "PLATINUM"))

    def test_platinum_is_wanted_because_it_satisfies_ornament_and_has_a_supply(self):
        from sim.engine import joint_allocation
        anchors = joint_allocation.build_demand_anchors()
        self.assertIn("platinum_g", anchors.supply_by_material)

    def test_germanium_gets_demand_once_a_technology_using_it_can_be_pursued(self):
        from sim.engine import catalog
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        nodes = list(catalog.load_mod_tree_nodes(root))
        held = {node["id"] for node in nodes} - {"com_semiconductor_diode"}
        pursued = need_demand.technology_material_demand(nodes, held)
        self.assertGreater(pursued["germanium_g"], 0.0)
        production = demand.production_data()
        model = need_demand.NeedDemandModel(
            need_data.load_needs(root), production, make_bins(), pursued)
        prices = {material: 1.0 for entry in production.values() for material in entry["outputs"]}
        self.assertGreater(model.demand_for("germanium_g", prices), 0.0)
        self.assertGreater(model.byproduct_supply(prices)["germanium_g"], 0.0)

    def test_germanium_has_no_demand_for_a_civilisation_far_from_semiconductors(self):
        from sim.engine import joint_allocation
        anchors = joint_allocation.build_demand_anchors()
        production = demand.production_data()
        prices = {material: 1.0 for entry in production.values() for material in entry["outputs"]}
        self.assertEqual(anchors.model.demand_for("germanium_g", prices), 0.0)


if __name__ == "__main__":
    unittest.main()
