"""Complaint 516: every shipped civilisation has a deposit of each base-metal ore within its reach, or says in its
file why it bought the metal abroad (`imported_ores`); `validate` warns of a metal in demand with neither."""

import unittest

from sim.engine import validate_ore_reach
from sim.engine.civ_start_check import load_civilisations
from sim.engine.need_data import load_needs
from sim.engine.catalog import load_production_catalog
from sim.engine.data import MODDIR, ROOT
from sim.geography import api as geography

BASE_METALS = ("copper", "tin", "lead", "iron")
CIVILISATIONS = load_civilisations(ROOT)


class PureCheckTests(unittest.TestCase):

    def test_a_deposit_counts_when_worked_by_the_year_and_within_the_limit(self):
        deposits = {"tin": [("far", None), ("near", 500)], "lead": [("near", None)]}
        levels = {"near": 2, "far": 5}
        self.assertEqual(validate_ore_reach.resources_in_reach(deposits, levels, 1000, 2), {"tin", "lead"})
        self.assertEqual(validate_ore_reach.resources_in_reach(deposits, levels, 400, 2), {"lead"})
        self.assertEqual(validate_ore_reach.resources_in_reach(deposits, levels, 1000, 1), set())

    def test_demand_comes_from_coin_needs_and_runnable_techniques_only(self):
        goods = {"tin": {"tin_kg", "cassiterite_kg"}, "gold": {"gold_kg"}, "lead": {"lead_kg"}}
        production = {"bronze": {"inputs": {"tin_kg": 1}, "requires_node": "held"},
                      "later_lead": {"inputs": {"lead_kg": 1}, "requires_node": "not_held"},
                      "ungated": {"inputs": {"gold_kg": 1}}}
        civilisation = {"starting_techs": ["held"], "coin_standard": {"material": "silver_kg"}}
        self.assertEqual(validate_ore_reach.demanded_resources(civilisation, goods, production, ()), {"tin", "gold"})
        self.assertEqual(validate_ore_reach.demanded_resources(civilisation, goods, {}, ("lead_kg",)), {"lead"})

    def test_demand_goods_include_what_the_smelting_recipes_make(self):
        goods = validate_ore_reach.demand_goods({"tin": {"cassiterite_kg": ("tin_kg",)}}, {},
                                                {"tin_kg": {"outputs": {"tin_kg": 1.0, "slag_kg": 2.0}}})
        self.assertEqual(goods["tin"], {"cassiterite_kg", "tin_kg", "slag_kg"})


class ShippedCivilisationsTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ore_resources = sorted(geography.ore_goods())
        cls.supplied = {name: validate_ore_reach.supplied_resources(civilisation, cls.ore_resources)
                        for name, civilisation in CIVILISATIONS.items()}

    def test_every_civilisation_has_each_base_metal_in_reach_or_declares_the_import(self):
        for name, civilisation in sorted(CIVILISATIONS.items()):
            declared = civilisation.get("imported_ores") or {}
            for metal in BASE_METALS:
                self.assertTrue(metal in self.supplied[name] or metal in declared,
                                "%s has no %s deposit in reach and declares no import" % (name, metal))

    def test_a_declared_import_has_no_deposit_in_reach_and_a_real_reason(self):
        for name, civilisation in sorted(CIVILISATIONS.items()):
            for metal, reason in (civilisation.get("imported_ores") or {}).items():
                self.assertNotIn(metal, self.supplied[name], "%s lists %s but has a deposit in reach" % (name, metal))
                self.assertGreaterEqual(len(reason), validate_ore_reach.MINIMUM_REASON_LENGTH, (name, metal))

    def test_validate_finds_nothing_to_warn_of(self):
        production = load_production_catalog(ROOT, MODDIR)
        errors, warnings = validate_ore_reach.ore_reach_findings(
            CIVILISATIONS, production, load_needs(ROOT, MODDIR)["goods"])
        self.assertEqual((errors, warnings), ([], []))

    def test_a_civilisation_with_no_deposit_is_warned_for_the_metal_it_demands(self):
        production = {"alloy": {"inputs": {"tin_kg": 1.0}, "requires_node": None}}
        civilisation = dict(CIVILISATIONS["norse_900ad"], starting_techs=[], imported_ores={})
        errors, warnings = validate_ore_reach.ore_reach_findings({"norse": civilisation}, production, ())
        self.assertEqual(errors, [])
        self.assertTrue(any("norse: demands tin" in warning for warning in warnings), warnings)


if __name__ == "__main__":
    unittest.main()
