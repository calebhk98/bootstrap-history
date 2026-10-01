"""Complaints/127 (bloomery bar), 125 (electropolishing current), 56 (shaft
amortisation horizon) and 41 (tanning and fulling held by the civilisations
that used them).
"""
import inspect
import json
import os
import unittest

from sim import civ_start_check as start_check
from sim.engine.catalog import load_production_catalog

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

CIVILISATIONS_THAT_SMELT_IRON = ("rome_100ad", "england_1300", "norse_900ad", "han_china_100ad")


def _nodes():
    with open(os.path.join(ROOT, "data", "tech_tree.json"), encoding="utf-8") as handle:
        return {node["id"]: node for node in json.load(handle)["nodes"]}


def _civilisations():
    return start_check.load_civilisations(ROOT)


class BloomeryBarTests(unittest.TestCase):

    def test_every_iron_smelting_civilisation_can_make_iron_bar_from_its_own_starts(self):
        production = load_production_catalog(ROOT)
        makers = [entry for entry in production.values()
                  if "iron_bar_kg" in (entry.get("outputs") or {})]
        civilisations = _civilisations()
        for name in CIVILISATIONS_THAT_SMELT_IRON:
            held = set(civilisations[name]["starting_techs"])
            available = [entry for entry in makers
                         if entry.get("requires_node") is None or entry["requires_node"] in held]
            self.assertTrue(available, "%s cannot make iron_bar_kg" % name)

    def test_no_iron_smelting_civilisation_has_unmakeable_iron_bar(self):
        production = load_production_catalog(ROOT)
        nodes = _nodes()
        civilisations = _civilisations()
        for name in CIVILISATIONS_THAT_SMELT_IRON:
            blocked = start_check.unmakeable_materials(nodes, civilisations[name], production)
            self.assertFalse([node for node, materials in blocked.items()
                              if "iron_bar_kg" in materials],
                             "%s: nodes whose iron_bar_kg is unmakeable" % name)

    def test_bloomery_bar_yield_is_a_physical_mass_balance(self):
        production = load_production_catalog(ROOT)
        bloomery = [entry for entry in production.values()
                    if "iron_bar_kg" in (entry.get("outputs") or {})
                    and "iron_bloom_kg" in (entry.get("inputs") or {})]
        self.assertEqual(len(bloomery), 1)
        entry = bloomery[0]
        bloom_per_bar = entry["inputs"]["iron_bloom_kg"] / entry["outputs"]["iron_bar_kg"]
        # a bloom is mostly metal: more than a kilogram of it per kilogram of bar, never half again
        self.assertGreater(bloom_per_bar, 1.0)
        self.assertLess(bloom_per_bar, 1.5)
        self.assertTrue(entry["yield_basis"])


class ElectropolishingCurrentTests(unittest.TestCase):

    def test_electropolishing_current_group_accepts_a_dynamo_not_only_the_grid(self):
        node = _nodes()["el2_electropolishing_etching_surface_finish"]
        group = [entry for entry in node["req_any"] if entry["group"] == "current"][0]
        self.assertIn("power_grid", group["options"])
        self.assertIn("dynamo_shunt_wound", group["options"])


class ShaftAmortisationHorizonTests(unittest.TestCase):

    def test_shaft_amortisation_horizon_is_its_own_knob(self):
        from sim.world import deposits
        pool = [deposit for deposit in deposits.load_deposits("copper")
                if deposits.build_cost_labour_hours(deposit, deposit.quantity_tonnes_per_year) > 0]
        self.assertTrue(pool)
        deposit = pool[0]
        base = deposits.amortized_sinking_cost_labour_hours_per_kg(deposit)
        self.assertEqual(base, deposits.amortized_sinking_cost_labour_hours_per_kg(
            deposit, shaft_service_life_years=deposits.SHAFT_SERVICE_LIFE_YEARS))
        shorter = deposits.amortized_sinking_cost_labour_hours_per_kg(
            deposit, shaft_service_life_years=deposits.SHAFT_SERVICE_LIFE_YEARS / 2.0)
        self.assertAlmostEqual(shorter, 2.0 * base)

    def test_pricing_functions_take_no_reserve_knob(self):
        from sim.world import deposits
        for function in (deposits.supply_curve, deposits.find_marginal_deposit,
                         deposits.total_cost_labour_hours_per_kg):
            self.assertNotIn("working_life_years", inspect.signature(function).parameters)


class TanningAndFullingStartTests(unittest.TestCase):

    def test_tanning_held_by_every_civilisation_and_fulling_by_every_wool_one(self):
        for name, civilisation in _civilisations().items():
            held = set(civilisation["starting_techs"])
            self.assertIn("tex_vegetable_tanning", held, name)
            if name != "mexica_1500":
                self.assertIn("tx2_fulling", held, name)

    def test_leather_and_cloth_are_makeable_by_rome(self):
        production = load_production_catalog(ROOT)
        held = set(_civilisations()["rome_100ad"]["starting_techs"])
        for material in ("leather_kg", "cloth_kg"):
            gates = [entry.get("requires_node") for entry in production.values()
                     if material in (entry.get("outputs") or {})]
            self.assertTrue(any(gate is None or gate in held for gate in gates), material)


if __name__ == "__main__":
    unittest.main()
